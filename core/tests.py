from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import ContatoMensagem, SiteConfig


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
