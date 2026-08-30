from datetime import timedelta
import importlib
from pathlib import Path
import os
import subprocess
import sys
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase, override_settings
from django.urls import clear_url_caches, reverse
from django.utils import timezone

from config.env import env_bool, env_list
from departamentos.models import Departamento, DepartmentMembership, DepartmentRole
from escalas.models import Escala
from pessoas.models import Person
from scheduling.models import Schedule, ScheduleAssignment
from worship.models import WorshipService

from .views import react_app
from .models import ContatoMensagem, SiteConfig


class ProductionReadinessTests(TestCase):
    def reload_project_urlconf(self):
        import config.urls

        clear_url_caches()
        importlib.reload(config.urls)
        clear_url_caches()

    def assert_spa_index_response(self, path, expected_content):
        response = self.client.get(path)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html")
        self.assertEqual(b"".join(response.streaming_content), expected_content)
        response.close()

    def test_health_check_publico_nao_expoe_detalhes(self):
        response = self.client.get(reverse("api-health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_env_bool_e_lista_tem_parsing_seguro(self):
        with patch.dict(os.environ, {"FLAG_FALSE": "False", "FLAG_TRUE": "sim", "HOSTS": "localhost, 127.0.0.1,,testserver"}):
            self.assertFalse(env_bool("FLAG_FALSE", True))
            self.assertTrue(env_bool("FLAG_TRUE", False))
            self.assertEqual(env_list("HOSTS"), ["localhost", "127.0.0.1", "testserver"])

    def test_production_settings_exigem_database_url(self):
        env = os.environ.copy()
        env.update(
            {
                "DJANGO_ENV": "production",
                "DJANGO_DEBUG": "False",
                "DJANGO_SECRET_KEY": "not-a-real-secret-for-test-only",
                "DJANGO_ALLOWED_HOSTS": "example.com",
            }
        )
        env.pop("DATABASE_URL", None)
        env.pop("DJANGO_DATABASE_URL", None)

        result = subprocess.run(
            [sys.executable, "manage.py", "check"],
            cwd=Path(__file__).resolve().parent.parent,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DATABASE_URL", result.stderr + result.stdout)

    def test_react_app_serve_index_do_build(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            build_dir = Path(temp_dir)
            (build_dir / "index.html").write_text("<div id=\"root\"></div>", encoding="utf-8")
            request = RequestFactory().get("/meu-perfil")
            with override_settings(REACT_BUILD_DIR=build_dir):
                response = react_app(request, "meu-perfil")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(b"".join(response.streaming_content), b"<div id=\"root\"></div>")
            response.close()

    def test_spa_fallback_serve_rotas_react_em_refresh_direto(self):
        index_content = b"<div id=\"root\">SPA</div>"
        self.addCleanup(self.reload_project_urlconf)

        with tempfile.TemporaryDirectory() as temp_dir:
            build_dir = Path(temp_dir)
            (build_dir / "index.html").write_bytes(index_content)

            with override_settings(SERVE_REACT_APP=True, REACT_BUILD_DIR=build_dir):
                self.reload_project_urlconf()
                for path in (
                    "/",
                    "/meu-perfil",
                    "/solicitacoes-acesso",
                    "/solicitacoes-acesso/1",
                    "/departamentos/novo",
                ):
                    with self.subTest(path=path):
                        self.assert_spa_index_response(path, index_content)
            self.reload_project_urlconf()

    def test_spa_fallback_nao_captura_prefixos_reservados(self):
        index_content = b"<div id=\"root\">SPA</div>"
        self.addCleanup(self.reload_project_urlconf)

        with tempfile.TemporaryDirectory() as temp_dir:
            build_dir = Path(temp_dir)
            (build_dir / "index.html").write_bytes(index_content)

            with override_settings(SERVE_REACT_APP=True, REACT_BUILD_DIR=build_dir):
                self.reload_project_urlconf()
                api_response = self.client.get("/api/health/")
                admin_response = self.client.get("/admin/")
                static_response = self.client.get("/static/spa-test.css")
                media_response = self.client.get("/media/spa-test.jpg")

                self.assertEqual(api_response.status_code, 200)
                self.assertEqual(api_response.json(), {"status": "ok"})
                self.assertNotEqual(admin_response.status_code, 200)
                self.assertNotEqual(static_response.status_code, 200)
                self.assertNotEqual(media_response.status_code, 200)
            self.reload_project_urlconf()


class ContatoViewTests(TestCase):
    def test_get_contato_exibe_formulario(self):
        response = self.client.get(reverse("core:contato"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Envie sua mensagem")
        self.assertIn("form", response.context)

    def test_post_valido_cria_mensagem_e_redireciona(self):
        response = self.client.post(
            reverse("core:contato"),
            {
                "nome": "Maria Souza",
                "email": "maria@example.com",
                "assunto": "Primeira visita",
                "mensagem": "Gostaria de saber os horarios dos cultos.",
            },
            follow=True,
        )

        self.assertRedirects(response, reverse("core:contato"))
        self.assertEqual(ContatoMensagem.objects.count(), 1)

        mensagem = ContatoMensagem.objects.get()
        self.assertEqual(mensagem.nome, "Maria Souza")
        self.assertEqual(mensagem.email, "maria@example.com")
        self.assertContains(response, "Mensagem enviada com sucesso")

    def test_post_invalido_nao_cria_mensagem(self):
        response = self.client.post(
            reverse("core:contato"),
            {
                "nome": "",
                "email": "email-invalido",
                "assunto": "",
                "mensagem": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContatoMensagem.objects.count(), 0)
        self.assertContains(response, "Nao foi possivel enviar sua mensagem")

    def test_usuario_logado_recebe_dados_iniciais_no_formulario(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="leandro",
            password="senha-forte-123",
            first_name="Leandro",
            last_name="Moura",
            email="leandro@example.com",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("core:contato"))
        form = response.context["form"]

        self.assertEqual(form.initial["nome"], "Leandro Moura")
        self.assertEqual(form.initial["email"], "leandro@example.com")


class SiteConfigIntegrationTests(TestCase):
    LONG_GOOGLE_MAPS_EMBED_URL = (
        "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2773.914690171594!"
        "2d-34.936052762083676!3d-8.0816985682327!2m3!1f0!2f0!3f0!3m2!1i1024!"
        "2i768!4f13.1!3m3!1m2!1s0x7ab1ebbe5efe551%3A0x19bcedaf3bb5e4d!"
        "2sIgreja%20Verbo%20da%20Vida%20-%20Jardim%20S%C3%A3o%20Paulo!5e0!3m2!"
        "1spt-BR!2sbr!4v1777231246540!5m2!1spt-BR!2sbr"
    )

    def test_home_usa_imagem_configurada_no_hero(self):
        SiteConfig.objects.update_or_create(
            id=1,
            defaults={
                "hero_home": SimpleUploadedFile(
                    "hero-home.jpg",
                    b"fake-image-content",
                    content_type="image/jpeg",
                ),
            },
        )

        response = self.client.get(reverse("core:home"))

        self.assertContains(response, "site/heroes/hero-home")

    def test_home_usa_youtube_normalizado_e_link_publico(self):
        SiteConfig.objects.update_or_create(
            id=1,
            defaults={
                "youtube_embed_url": "https://youtu.be/abcdefghijk?si=123",
            },
        )

        response = self.client.get(reverse("core:home"))

        self.assertContains(response, "https://www.youtube-nocookie.com/embed/abcdefghijk")
        self.assertContains(response, "https://www.youtube.com/watch?v=abcdefghijk")

    def test_contato_usa_endereco_e_mapa_do_siteconfig(self):
        SiteConfig.objects.update_or_create(
            id=1,
            defaults={
                "endereco": "Av. Exemplo, 100 - Recife - PE",
                "mapa_embed_url": "https://www.google.com/maps/embed?pb=teste",
            },
        )

        response = self.client.get(reverse("core:contato"))

        self.assertContains(response, "Av. Exemplo, 100 - Recife - PE")
        self.assertContains(response, "https://www.google.com/maps/embed?pb=teste")
        self.assertContains(response, "Av.+Exemplo%2C+100+-+Recife+-+PE")

    def test_siteconfig_aceita_url_longa_de_embed_do_google_maps(self):
        site, _ = SiteConfig.objects.update_or_create(
            id=1,
            defaults={
                "mapa_embed_url": self.LONG_GOOGLE_MAPS_EMBED_URL,
            },
        )

        site.refresh_from_db()

        self.assertEqual(site.mapa_embed_url, self.LONG_GOOGLE_MAPS_EMBED_URL)
        self.assertEqual(site.maps_embed_url_resolved, self.LONG_GOOGLE_MAPS_EMBED_URL)

    def test_sobre_usa_contato_e_horarios_do_siteconfig(self):
        SiteConfig.objects.update_or_create(
            id=1,
            defaults={
                "endereco": "Rua Central, 55 - Recife - PE",
                "whatsapp": "(81) 98888-1111",
                "email": "sobre@teste.com",
                "horarios_cultos": "Domingo - 10:00\nQuinta - 20:00",
            },
        )

        response = self.client.get(reverse("core:sobre"))

        self.assertContains(response, "Rua Central, 55 - Recife - PE")
        self.assertContains(response, "(81) 98888-1111")
        self.assertContains(response, "sobre@teste.com")
        self.assertContains(response, "Domingo - 10:00")
        self.assertContains(response, "Quinta - 20:00")


class AdminDashboardTests(TestCase):
    def test_admin_index_exibe_dashboard_customizado(self):
        user_model = get_user_model()
        admin_user = user_model.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="senha-forte-123",
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Painel Editorial")
        self.assertContains(response, "Mensagens de Contato")

    def test_admin_dashboard_usa_scheduling_e_ignora_escala_legada_futura(self):
        user_model = get_user_model()
        admin_user = user_model.objects.create_superuser(
            username="admin.dashboard",
            email="admin.dashboard@example.com",
            password="senha-forte-123",
        )
        departamento = Departamento.objects.create(nome="Midia Admin")
        role = DepartmentRole.objects.create(department=departamento, name="Camera", code="camera")
        person = Person.objects.create(full_name="Camera Admin", birth_date="1990-01-01")
        membership = DepartmentMembership.objects.create(
            person=person,
            department=departamento,
            role=role,
            status=DepartmentMembership.Status.ACTIVE,
        )
        Escala.objects.create(
            departamento=departamento,
            titulo="Escala Legada Admin",
            data=timezone.localdate() + timedelta(days=20),
            horario="19:00",
            ativa=True,
        )
        worship_service = WorshipService.objects.create(
            name="Culto Admin Novo",
            date=timezone.localdate() + timedelta(days=10),
            time="10:00",
            kind=WorshipService.Kind.EXTRAORDINARY,
            status=WorshipService.Status.SCHEDULED,
        )
        schedule = Schedule.objects.create(
            department=departamento,
            worship_service=worship_service,
            status=Schedule.Status.PUBLISHED,
        )
        ScheduleAssignment.objects.create(schedule=schedule, department_membership=membership)
        Schedule.objects.create(
            department=departamento,
            worship_service=WorshipService.objects.create(
                name="Culto Admin Rascunho",
                date=timezone.localdate() + timedelta(days=11),
                time="10:00",
                kind=WorshipService.Kind.EXTRAORDINARY,
            ),
            status=Schedule.Status.DRAFT,
        )

        self.client.force_login(admin_user)
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Culto Admin Novo")
        self.assertContains(response, "Escalas Publicadas")
        self.assertContains(response, "Escalas em Rascunho")
        self.assertContains(response, "Pessoas Escaladas")
        self.assertNotContains(response, "Escala Legada Admin")
