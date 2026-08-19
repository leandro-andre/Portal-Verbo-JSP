from datetime import date
from io import StringIO
from os import environ
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from departamentos.models import Departamento, DepartamentoMembro
from departamentos.permissions import usuario_pode_acessar_departamentos
from escalas.permissions import usuario_pode_acessar_escalas
from ministros.models import Ministro
from pessoas.models import Person
from usuarios.context_processors import internal_permissions
from usuarios.roles import (
    PASTOR_GROUP,
    PORTAL_ADMIN_GROUP,
    SECRETARY_GROUP,
    setup_portal_roles,
)

from .models import AccessRequest
from .permissions import (
    usuario_eh_lider_departamento,
    usuario_eh_lider_em_algum_departamento,
    usuario_eh_membro,
    usuario_eh_ministro,
    usuario_eh_pastor,
    usuario_eh_secretaria,
    usuario_eh_visitante,
    usuario_pode_montar_escala,
    usuario_pode_ser_escalado_verbo_no_lar,
    usuario_tem_acesso_midia,
    usuario_tem_acesso_secretaria,
    usuario_tem_acesso_tecnico_total,
    usuario_tem_acesso_total_pastoral,
    usuario_tem_acesso_total_sistema,
)


def assign_role(usuario, group_name):
    setup_portal_roles()
    usuario.groups.add(Group.objects.get(name=group_name))


class UsuarioQualificacaoTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()

    def test_usuario_novo_nasce_como_visitante(self):
        usuario = self.user_model.objects.create_user(
            username="visitante",
            password="senha-forte-123",
        )

        self.assertTrue(usuario_eh_visitante(usuario))
        self.assertFalse(usuario_eh_membro(usuario))

    def test_qualificar_como_membro_registra_responsavel_e_data(self):
        secretaria = self.user_model.objects.create_user(
            username="secretaria",
            password="senha-forte-123",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )
        visitante = self.user_model.objects.create_user(
            username="novo.membro",
            password="senha-forte-123",
        )

        visitante.qualificar_como_membro(secretaria)
        visitante.save()

        visitante.refresh_from_db()
        self.assertTrue(usuario_eh_membro(visitante))
        self.assertTrue(visitante.discipulado_concluido)
        self.assertEqual(visitante.qualificado_por, secretaria)
        self.assertIsNotNone(visitante.qualificado_em)

    def test_lideranca_vem_do_vinculo_departamental(self):
        lider = self.user_model.objects.create_user(
            username="lider",
            password="senha-forte-123",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )
        departamento = Departamento.objects.create(nome="Louvor", codigo="louvor")
        DepartamentoMembro.objects.create(
            membro=lider,
            departamento=departamento,
            papel=DepartamentoMembro.Papel.LIDER,
        )

        self.assertTrue(usuario_eh_lider_departamento(lider, departamento))

    def test_ministro_vem_do_vinculo_ministerial(self):
        usuario = self.user_model.objects.create_user(
            username="ministro",
            password="senha-forte-123",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )
        Ministro.objects.create(
            usuario=usuario,
            nome_completo="Ministro Teste",
            tipo=Ministro.Tipo.CASA,
            status=Ministro.Status.APROVADO,
            ativo=True,
        )

        self.assertTrue(usuario_eh_ministro(usuario))
        self.assertTrue(usuario_pode_ser_escalado_verbo_no_lar(usuario))

    def test_pastor_tem_acesso_total_pastoral_sem_ser_staff(self):
        pastor = self.user_model.objects.create_user(
            username="pastor",
            password="senha-forte-123",
            eh_pastor=True,
        )

        self.assertFalse(pastor.is_staff)
        self.assertTrue(usuario_eh_pastor(pastor))
        self.assertTrue(usuario_tem_acesso_total_pastoral(pastor))

    def test_login_continua_funcionando_com_usuario_sem_person(self):
        self.user_model.objects.create_user(
            username="login.sem.person",
            password="senha-forte-123",
        )

        response = self.client.post(
            reverse("usuarios:login"),
            {"username": "login.sem.person", "password": "senha-forte-123"},
        )

        self.assertRedirects(response, reverse("usuarios:dashboard"))

    def test_registro_aceita_person_existente_sem_expor_onboarding_completo(self):
        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))

        response = self.client.post(
            reverse("usuarios:registro"),
            {
                "username": "maria.person",
                "person": person.pk,
                "first_name": "Maria",
                "last_name": "Silva",
                "email": "maria@example.com",
                "telefone": "81999999999",
                "password1": "senha-forte-123",
                "password2": "senha-forte-123",
            },
        )

        self.assertRedirects(response, reverse("usuarios:dashboard"))
        usuario = self.user_model.objects.get(username="maria.person")
        self.assertEqual(usuario.person, person)

    def test_admin_continua_acessivel(self):
        admin = self.user_model.objects.create_superuser(
            username="admin.identity",
            password="senha-forte-123",
            email="admin@example.com",
        )
        self.client.force_login(admin)

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)


class AccessRequestApiTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.url = reverse("access-request-create")

    def valid_payload(self):
        return {
            "full_name": "Maria Silva",
            "birth_date": "1990-05-10",
            "email": "maria@example.com",
            "phone": "(81) 99999-9999",
        }

    def test_criacao_valida_retorna_sucesso(self):
        response = self.client.post(self.url, self.valid_payload(), content_type="application/json")

        self.assertEqual(response.status_code, 201)
        self.assertTrue(AccessRequest.objects.filter(email="maria@example.com").exists())

    def test_status_padrao_pending(self):
        self.client.post(self.url, self.valid_payload(), content_type="application/json")

        access_request = AccessRequest.objects.get()
        self.assertEqual(access_request.status, AccessRequest.Status.PENDING)

    def test_criacao_nao_cria_person(self):
        self.client.post(self.url, self.valid_payload(), content_type="application/json")

        self.assertFalse(Person.objects.exists())

    def test_criacao_nao_cria_usuario(self):
        self.client.post(self.url, self.valid_payload(), content_type="application/json")

        self.assertFalse(self.user_model.objects.exists())

    def test_full_name_obrigatorio(self):
        payload = self.valid_payload()
        payload["full_name"] = "   "

        response = self.client.post(self.url, payload, content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("full_name", response.json())

    def test_birth_date_obrigatoria(self):
        payload = self.valid_payload()
        payload.pop("birth_date")

        response = self.client.post(self.url, payload, content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("birth_date", response.json())

    def test_email_obrigatorio(self):
        payload = self.valid_payload()
        payload["email"] = ""

        response = self.client.post(self.url, payload, content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json())

    def test_phone_obrigatorio(self):
        payload = self.valid_payload()
        payload["phone"] = "   "

        response = self.client.post(self.url, payload, content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("phone", response.json())

    def test_data_futura_rejeitada(self):
        payload = self.valid_payload()
        payload["birth_date"] = "2999-01-01"

        response = self.client.post(self.url, payload, content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("birth_date", response.json())

    def test_email_invalido_rejeitado(self):
        payload = self.valid_payload()
        payload["email"] = "email-invalido"

        response = self.client.post(self.url, payload, content_type="application/json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json())

    def test_solicitacao_pendente_com_mesmo_email_e_bloqueada(self):
        AccessRequest.objects.create(**self.valid_payload())
        payload = self.valid_payload()
        payload["phone"] = "(81) 98888-8888"

        response = self.client.post(self.url, payload, content_type="application/json")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "PENDING_ACCESS_REQUEST_EXISTS")
        self.assertEqual(AccessRequest.objects.count(), 1)

    def test_solicitacao_pendente_com_mesmo_telefone_e_bloqueada(self):
        AccessRequest.objects.create(**self.valid_payload())
        payload = self.valid_payload()
        payload["email"] = "outra@example.com"

        response = self.client.post(self.url, payload, content_type="application/json")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "PENDING_ACCESS_REQUEST_EXISTS")
        self.assertEqual(AccessRequest.objects.count(), 1)

    def test_comparacao_de_email_e_case_insensitive(self):
        AccessRequest.objects.create(**self.valid_payload())
        payload = self.valid_payload()
        payload["email"] = "MARIA@EXAMPLE.COM"
        payload["phone"] = "(81) 97777-7777"

        response = self.client.post(self.url, payload, content_type="application/json")

        self.assertEqual(response.status_code, 409)

    def test_solicitacao_approved_nao_bloqueia_nova_solicitacao(self):
        payload = self.valid_payload()
        AccessRequest.objects.create(**payload, status=AccessRequest.Status.APPROVED)

        response = self.client.post(self.url, payload, content_type="application/json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(AccessRequest.objects.count(), 2)

    def test_solicitacao_rejected_nao_bloqueia_nova_solicitacao(self):
        payload = self.valid_payload()
        AccessRequest.objects.create(**payload, status=AccessRequest.Status.REJECTED)

        response = self.client.post(self.url, payload, content_type="application/json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(AccessRequest.objects.count(), 2)

    def test_cliente_nao_consegue_enviar_status_arbitrario(self):
        payload = {**self.valid_payload(), "status": AccessRequest.Status.APPROVED}

        response = self.client.post(self.url, payload, content_type="application/json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(AccessRequest.objects.get().status, AccessRequest.Status.PENDING)

    def test_cliente_nao_consegue_enviar_person(self):
        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))
        payload = {**self.valid_payload(), "person": person.pk}

        response = self.client.post(self.url, payload, content_type="application/json")

        self.assertEqual(response.status_code, 201)
        self.assertIsNone(AccessRequest.objects.get().person)

    def test_cliente_nao_consegue_enviar_reviewed_by(self):
        reviewer = self.user_model.objects.create_user(username="secretaria")
        payload = {**self.valid_payload(), "reviewed_by": reviewer.pk}

        response = self.client.post(self.url, payload, content_type="application/json")

        self.assertEqual(response.status_code, 201)
        self.assertIsNone(AccessRequest.objects.get().reviewed_by)

    def test_endpoint_nao_expoe_listagem_publica(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

    def test_endpoint_nao_permite_delete_publico(self):
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, 405)


class AuthApiTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.client = Client(enforce_csrf_checks=True)

    def _csrf_headers(self):
        response = self.client.get(reverse("auth-csrf"))
        self.assertEqual(response.status_code, 200)
        return {"HTTP_X_CSRFTOKEN": response.cookies["csrftoken"].value}

    def _activation_payload(self, usuario, password="Senha-forte-123"):
        uid = urlsafe_base64_encode(force_bytes(usuario.pk))
        token = default_token_generator.make_token(usuario)
        return {
            "uid": uid,
            "token": token,
            "password": password,
            "password_confirm": password,
        }

    def test_current_user_anonimo_retorna_nao_autenticado(self):
        response = self.client.get(reverse("auth-current-user"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_authenticated"])
        self.assertIsNone(response.json()["user"])

    def test_login_exige_csrf(self):
        self.user_model.objects.create_user(
            username="login.csrf",
            password="Senha-forte-123",
            email="login.csrf@example.com",
        )

        response = self.client.post(
            reverse("auth-login"),
            {"username": "login.csrf", "password": "Senha-forte-123"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_login_com_username_cria_sessao(self):
        usuario = self.user_model.objects.create_user(
            username="login.user",
            password="Senha-forte-123",
            email="login.user@example.com",
        )
        headers = self._csrf_headers()

        response = self.client.post(
            reverse("auth-login"),
            {"username": "login.user", "password": "Senha-forte-123"},
            content_type="application/json",
            **headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_authenticated"])
        self.assertEqual(response.json()["user"]["id"], usuario.id)
        self.assertIn("_auth_user_id", self.client.session)

    def test_login_com_email_funciona(self):
        usuario = self.user_model.objects.create_user(
            username="login.email",
            password="Senha-forte-123",
            email="login.email@example.com",
        )
        headers = self._csrf_headers()

        response = self.client.post(
            reverse("auth-login"),
            {"username": "LOGIN.EMAIL@example.com", "password": "Senha-forte-123"},
            content_type="application/json",
            **headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["user"]["username"], usuario.username)

    def test_login_rejeita_usuario_inativo(self):
        self.user_model.objects.create_user(
            username="login.inactive",
            password="Senha-forte-123",
            is_active=False,
        )
        headers = self._csrf_headers()

        response = self.client.post(
            reverse("auth-login"),
            {"username": "login.inactive", "password": "Senha-forte-123"},
            content_type="application/json",
            **headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "INVALID_CREDENTIALS")

    def test_logout_exige_csrf(self):
        usuario = self.user_model.objects.create_user(
            username="logout.csrf",
            password="Senha-forte-123",
        )
        self.client.force_login(usuario)

        response = self.client.post(reverse("auth-logout"))

        self.assertEqual(response.status_code, 403)

    def test_logout_remove_sessao(self):
        usuario = self.user_model.objects.create_user(
            username="logout.user",
            password="Senha-forte-123",
        )
        self.client.force_login(usuario)
        headers = self._csrf_headers()

        response = self.client.post(reverse("auth-logout"), **headers)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_activate_exige_csrf(self):
        usuario = self.user_model.objects.create_user(
            username="activate.csrf",
            is_active=False,
        )
        usuario.set_unusable_password()
        usuario.save()

        response = self.client.post(
            reverse("auth-activate"),
            self._activation_payload(usuario),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_activate_define_senha_e_ativa_usuario(self):
        usuario = self.user_model.objects.create_user(
            username="activate.user",
            email="activate.user@example.com",
            is_active=False,
        )
        usuario.set_unusable_password()
        usuario.save()
        headers = self._csrf_headers()

        response = self.client.post(
            reverse("auth-activate"),
            self._activation_payload(usuario),
            content_type="application/json",
            **headers,
        )

        self.assertEqual(response.status_code, 200)
        usuario.refresh_from_db()
        self.assertTrue(usuario.is_active)
        self.assertTrue(usuario.check_password("Senha-forte-123"))

    def test_activate_nao_faz_login_automatico(self):
        usuario = self.user_model.objects.create_user(
            username="activate.no.login",
            is_active=False,
        )
        usuario.set_unusable_password()
        usuario.save()
        headers = self._csrf_headers()

        self.client.post(
            reverse("auth-activate"),
            self._activation_payload(usuario),
            content_type="application/json",
            **headers,
        )

        self.assertNotIn("_auth_user_id", self.client.session)

    def test_activate_rejeita_token_invalido(self):
        usuario = self.user_model.objects.create_user(
            username="activate.invalid",
            is_active=False,
        )
        usuario.set_unusable_password()
        usuario.save()
        payload = self._activation_payload(usuario)
        payload["token"] = "invalid-token"
        headers = self._csrf_headers()

        response = self.client.post(
            reverse("auth-activate"),
            payload,
            content_type="application/json",
            **headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("token", response.json())
        usuario.refresh_from_db()
        self.assertFalse(usuario.is_active)

    def test_activate_rejeita_conta_ja_ativa(self):
        usuario = self.user_model.objects.create_user(
            username="activate.already",
            password="Senha-forte-123",
            is_active=True,
        )
        headers = self._csrf_headers()

        response = self.client.post(
            reverse("auth-activate"),
            self._activation_payload(usuario),
            content_type="application/json",
            **headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("token", response.json())

    def test_activate_rejeita_senhas_diferentes(self):
        usuario = self.user_model.objects.create_user(
            username="activate.mismatch",
            is_active=False,
        )
        usuario.set_unusable_password()
        usuario.save()
        payload = self._activation_payload(usuario)
        payload["password_confirm"] = "Outra-senha-123"
        headers = self._csrf_headers()

        response = self.client.post(
            reverse("auth-activate"),
            payload,
            content_type="application/json",
            **headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("password_confirm", response.json())

    def test_activate_usa_validadores_de_senha_do_django(self):
        usuario = self.user_model.objects.create_user(
            username="activate.weak",
            is_active=False,
        )
        usuario.set_unusable_password()
        usuario.save()
        headers = self._csrf_headers()

        response = self.client.post(
            reverse("auth-activate"),
            self._activation_payload(usuario, password="123"),
            content_type="application/json",
            **headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.json())
        usuario.refresh_from_db()
        self.assertFalse(usuario.is_active)


class AdminAccessRequestApiTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.superuser = self.user_model.objects.create_superuser(
            username="admin.access",
            password="senha-forte-123",
            email="admin.access@example.com",
        )
        self.regular_user = self.user_model.objects.create_user(
            username="regular.access",
            password="senha-forte-123",
        )
        self.access_request = AccessRequest.objects.create(
            full_name="Maria Silva",
            birth_date=date(1990, 5, 10),
            email="maria@example.com",
            phone="81999999999",
        )

    def make_secretaria(self):
        secretaria = self.user_model.objects.create_user(
            username="secretaria.access",
            password="senha-forte-123",
        )
        departamento = Departamento.objects.create(nome="Secretaria", codigo=Departamento.CodigoSistema.SECRETARIA)
        DepartamentoMembro.objects.create(
            membro=secretaria,
            departamento=departamento,
            papel=DepartamentoMembro.Papel.LIDER,
            ativo=True,
        )
        return secretaria

    def test_endpoint_administrativo_exige_autenticacao_ou_autorizacao(self):
        response = self.client.get(reverse("access-request-admin-list"))

        self.assertEqual(response.status_code, 403)

    def test_usuario_nao_autorizado_recebe_403(self):
        self.client.force_login(self.regular_user)

        response = self.client.get(reverse("access-request-admin-list"))

        self.assertEqual(response.status_code, 403)

    def test_usuario_autorizado_lista_solicitacoes(self):
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("access-request-admin-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["id"], self.access_request.id)

    def test_departamento_secretaria_nao_concede_global_role(self):
        self.client.force_login(self.make_secretaria())

        response = self.client.get(reverse("access-request-admin-list"))

        self.assertEqual(response.status_code, 403)

    def test_global_role_secretaria_pode_listar_solicitacoes(self):
        secretaria = self.user_model.objects.create_user(
            username="secretaria.group",
            password="senha-forte-123",
        )
        assign_role(secretaria, SECRETARY_GROUP)
        self.client.force_login(secretaria)

        response = self.client.get(reverse("access-request-admin-list"))

        self.assertEqual(response.status_code, 200)

    def test_filtro_pending(self):
        AccessRequest.objects.create(
            full_name="Aprovada",
            birth_date=date(1980, 1, 1),
            email="aprovada@example.com",
            phone="81111111111",
            status=AccessRequest.Status.APPROVED,
        )
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("access-request-admin-list"), {"status": "PENDING"})

        self.assertEqual([item["status"] for item in response.json()], ["PENDING"])

    def test_filtro_approved(self):
        approved = AccessRequest.objects.create(
            full_name="Aprovada",
            birth_date=date(1980, 1, 1),
            email="aprovada@example.com",
            phone="81111111111",
            status=AccessRequest.Status.APPROVED,
        )
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("access-request-admin-list"), {"status": "APPROVED"})

        self.assertEqual(response.json()[0]["id"], approved.id)
        self.assertEqual(response.json()[0]["status"], "APPROVED")

    def test_filtro_rejected(self):
        rejected = AccessRequest.objects.create(
            full_name="Rejeitada",
            birth_date=date(1980, 1, 1),
            email="rejeitada@example.com",
            phone="81222222222",
            status=AccessRequest.Status.REJECTED,
        )
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("access-request-admin-list"), {"status": "REJECTED"})

        self.assertEqual(response.json()[0]["id"], rejected.id)
        self.assertEqual(response.json()[0]["status"], "REJECTED")

    def test_detalhe_funciona_e_retorna_candidatos(self):
        Person.objects.create(
            full_name="Maria Silva",
            birth_date=date(1990, 5, 10),
            email="maria.person@example.com",
            phone="81888888888",
        )
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("access-request-admin-detail", args=[self.access_request.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.access_request.id)
        self.assertEqual(response.json()["candidates"][0]["full_name"], "Maria Silva")

    def test_aprovar_pending_com_person_existente(self):
        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse("access-request-admin-approve", args=[self.access_request.pk]),
            {"person_id": person.pk},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("/ativar-conta/", response.json()["created_user"]["activation_url"])
        self.assertFalse(response.json()["created_user"]["is_active"])
        self.access_request.refresh_from_db()
        self.assertEqual(self.access_request.person, person)
        self.assertEqual(self.access_request.status, AccessRequest.Status.APPROVED)

    def test_aprovar_cria_usuario_relacionado_a_person(self):
        person = Person.objects.create(
            full_name="Maria Silva",
            birth_date=date(1990, 5, 10),
            email="maria.person@example.com",
            phone="81888888888",
        )
        self.client.force_login(self.superuser)

        self.client.post(
            reverse("access-request-admin-approve", args=[self.access_request.pk]),
            {"person_id": person.pk},
            content_type="application/json",
        )

        usuario = self.user_model.objects.get(person=person)
        self.assertEqual(usuario.email, "maria.person@example.com")
        self.assertEqual(usuario.telefone, "81888888888")

    def test_aprovar_com_person_existente_nao_cria_segunda_person(self):
        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))
        self.client.force_login(self.superuser)

        self.client.post(
            reverse("access-request-admin-approve", args=[self.access_request.pk]),
            {"person_id": person.pk},
            content_type="application/json",
        )

        self.assertEqual(Person.objects.count(), 1)

    def test_aprovar_criando_nova_person(self):
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse("access-request-admin-approve", args=[self.access_request.pk]),
            {"create_new_person": True},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        person = Person.objects.get()
        self.assertEqual(person.full_name, "Maria Silva")
        self.assertEqual(person.birth_date, date(1990, 5, 10))
        self.assertEqual(person.email, "maria@example.com")
        self.assertEqual(person.phone, "81999999999")

    def test_usuario_recebe_person_criada(self):
        self.client.force_login(self.superuser)

        self.client.post(
            reverse("access-request-admin-approve", args=[self.access_request.pk]),
            {"create_new_person": True},
            content_type="application/json",
        )

        person = Person.objects.get()
        usuario = self.user_model.objects.get(person=person)
        self.assertEqual(usuario.person, person)

    def test_usuario_usa_senha_inutilizavel(self):
        self.client.force_login(self.superuser)

        self.client.post(
            reverse("access-request-admin-approve", args=[self.access_request.pk]),
            {"create_new_person": True},
            content_type="application/json",
        )

        usuario = self.user_model.objects.get(person=Person.objects.get())
        self.assertFalse(usuario.has_usable_password())

    def test_usuario_nasce_inativo(self):
        self.client.force_login(self.superuser)

        self.client.post(
            reverse("access-request-admin-approve", args=[self.access_request.pk]),
            {"create_new_person": True},
            content_type="application/json",
        )

        usuario = self.user_model.objects.get(person=Person.objects.get())
        self.assertFalse(usuario.is_active)

    def test_username_e_criado_corretamente(self):
        self.client.force_login(self.superuser)

        self.client.post(
            reverse("access-request-admin-approve", args=[self.access_request.pk]),
            {"create_new_person": True},
            content_type="application/json",
        )

        self.assertTrue(self.user_model.objects.filter(username="maria.silva").exists())

    def test_colisao_de_username_gera_alternativa(self):
        self.user_model.objects.create_user(username="maria.silva")
        self.client.force_login(self.superuser)

        self.client.post(
            reverse("access-request-admin-approve", args=[self.access_request.pk]),
            {"create_new_person": True},
            content_type="application/json",
        )

        self.assertTrue(self.user_model.objects.filter(username="maria.silva2").exists())

    def test_person_que_ja_possui_usuario_retorna_erro_de_negocio(self):
        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))
        self.user_model.objects.create_user(username="maria.existente", person=person)
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse("access-request-admin-approve", args=[self.access_request.pk]),
            {"person_id": person.pk},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "PERSON_ALREADY_HAS_USER")

    def test_aprovacao_preenche_reviewed_by_e_reviewed_at(self):
        self.client.force_login(self.superuser)

        self.client.post(
            reverse("access-request-admin-approve", args=[self.access_request.pk]),
            {"create_new_person": True},
            content_type="application/json",
        )

        self.access_request.refresh_from_db()
        self.assertEqual(self.access_request.reviewed_by, self.superuser)
        self.assertIsNotNone(self.access_request.reviewed_at)

    def test_approved_nao_pode_ser_aprovado_novamente(self):
        self.access_request.status = AccessRequest.Status.APPROVED
        self.access_request.save(update_fields=["status"])
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse("access-request-admin-approve", args=[self.access_request.pk]),
            {"create_new_person": True},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "ACCESS_REQUEST_NOT_PENDING")

    def test_aprovacao_e_atomica(self):
        self.client.force_login(self.superuser)

        with patch("usuarios.services.generate_username", side_effect=RuntimeError("falha")):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    reverse("access-request-admin-approve", args=[self.access_request.pk]),
                    {"create_new_person": True},
                    content_type="application/json",
                )

        self.access_request.refresh_from_db()
        self.assertEqual(self.access_request.status, AccessRequest.Status.PENDING)
        self.assertFalse(Person.objects.exists())
        self.assertEqual(self.user_model.objects.count(), 2)

    def test_rejeitar_pending(self):
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse("access-request-admin-reject", args=[self.access_request.pk]),
            {},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.access_request.refresh_from_db()
        self.assertEqual(self.access_request.status, AccessRequest.Status.REJECTED)

    def test_rejeicao_salva_motivo_opcional(self):
        self.client.force_login(self.superuser)

        self.client.post(
            reverse("access-request-admin-reject", args=[self.access_request.pk]),
            {"rejection_reason": "Dados nao conferem."},
            content_type="application/json",
        )

        self.access_request.refresh_from_db()
        self.assertEqual(self.access_request.rejection_reason, "Dados nao conferem.")

    def test_rejeicao_preenche_reviewed_by_e_reviewed_at(self):
        self.client.force_login(self.superuser)

        self.client.post(
            reverse("access-request-admin-reject", args=[self.access_request.pk]),
            {},
            content_type="application/json",
        )

        self.access_request.refresh_from_db()
        self.assertEqual(self.access_request.reviewed_by, self.superuser)
        self.assertIsNotNone(self.access_request.reviewed_at)

    def test_rejeicao_nao_cria_person_ou_usuario(self):
        self.client.force_login(self.superuser)

        self.client.post(
            reverse("access-request-admin-reject", args=[self.access_request.pk]),
            {},
            content_type="application/json",
        )

        self.assertFalse(Person.objects.exists())
        self.assertEqual(self.user_model.objects.count(), 2)

    def test_rejected_nao_pode_ser_rejeitada_novamente(self):
        self.access_request.status = AccessRequest.Status.REJECTED
        self.access_request.save(update_fields=["status"])
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse("access-request-admin-reject", args=[self.access_request.pk]),
            {},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "ACCESS_REQUEST_NOT_PENDING")


class AdminUserAccessLifecycleApiTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.superuser = self.user_model.objects.create_superuser(
            username="admin.users",
            password="Senha-forte-123",
            email="admin.users@example.com",
        )
        self.regular_user = self.user_model.objects.create_user(
            username="regular.users",
            password="Senha-forte-123",
        )
        self.person = Person.objects.create(
            full_name="Maria Silva",
            birth_date=date(1990, 5, 10),
            status=Person.Status.ACTIVE,
        )
        self.portal_user = self.user_model.objects.create_user(
            username="maria.silva",
            password="Senha-forte-123",
            person=self.person,
        )

    def test_lista_usuarios_exige_autenticacao(self):
        response = self.client.get(reverse("admin-user-list"))

        self.assertEqual(response.status_code, 403)

    def test_usuario_comum_recebe_403_na_lista(self):
        self.client.force_login(self.regular_user)

        response = self.client.get(reverse("admin-user-list"))

        self.assertEqual(response.status_code, 403)

    def test_superuser_lista_usuarios(self):
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("admin-user-list"))

        self.assertEqual(response.status_code, 200)
        usernames = {item["username"] for item in response.json()}
        self.assertIn("maria.silva", usernames)

    def test_serializer_nao_retorna_password(self):
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("admin-user-detail", args=[self.portal_user.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("password", response.json())

    def test_access_status_pending_activation(self):
        pending = self.user_model.objects.create_user(
            username="pending.activation",
            person=Person.objects.create(full_name="Ana Pessoa", birth_date=date(1991, 1, 1)),
            is_active=False,
        )
        pending.set_unusable_password()
        pending.save()
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("admin-user-detail", args=[pending.pk]))

        self.assertEqual(response.json()["access_status"], "PENDING_ACTIVATION")

    def test_access_status_active(self):
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("admin-user-detail", args=[self.portal_user.pk]))

        self.assertEqual(response.json()["access_status"], "ACTIVE")

    def test_access_status_blocked(self):
        self.portal_user.is_active = False
        self.portal_user.save(update_fields=["is_active"])
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("admin-user-detail", args=[self.portal_user.pk]))

        self.assertEqual(response.json()["access_status"], "BLOCKED")

    def test_bloquear_active_vira_blocked(self):
        self.client.force_login(self.superuser)

        response = self.client.post(reverse("admin-user-disable", args=[self.portal_user.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["access_status"], "BLOCKED")
        self.portal_user.refresh_from_db()
        self.assertFalse(self.portal_user.is_active)

    def test_person_nao_e_alterada_ao_bloquear(self):
        self.client.force_login(self.superuser)

        self.client.post(reverse("admin-user-disable", args=[self.portal_user.pk]))

        self.person.refresh_from_db()
        self.assertEqual(self.person.status, Person.Status.ACTIVE)

    def test_usuario_bloqueado_nao_faz_login(self):
        self.portal_user.is_active = False
        self.portal_user.save(update_fields=["is_active"])

        response = self.client.post(
            reverse("auth-login"),
            {"username": "maria.silva", "password": "Senha-forte-123"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "INVALID_CREDENTIALS")

    def test_sessao_antiga_de_usuario_bloqueado_perde_current_user(self):
        self.client.force_login(self.portal_user)
        self.portal_user.is_active = False
        self.portal_user.save(update_fields=["is_active"])

        response = self.client.get(reverse("auth-current-user"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_authenticated"])
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_sessao_antiga_de_usuario_bloqueado_perde_acesso_api(self):
        self.client.force_login(self.portal_user)
        self.portal_user.is_active = False
        self.portal_user.save(update_fields=["is_active"])

        response = self.client.get(reverse("person-list"))

        self.assertEqual(response.status_code, 403)

    def test_reativar_blocked_vira_active(self):
        self.portal_user.is_active = False
        self.portal_user.save(update_fields=["is_active"])
        self.client.force_login(self.superuser)

        response = self.client.post(reverse("admin-user-enable", args=[self.portal_user.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["access_status"], "ACTIVE")
        self.portal_user.refresh_from_db()
        self.assertTrue(self.portal_user.is_active)

    def test_person_nao_e_alterada_ao_reativar(self):
        self.portal_user.is_active = False
        self.portal_user.save(update_fields=["is_active"])
        self.client.force_login(self.superuser)

        self.client.post(reverse("admin-user-enable", args=[self.portal_user.pk]))

        self.person.refresh_from_db()
        self.assertEqual(self.person.status, Person.Status.ACTIVE)

    def test_senha_continua_a_mesma_apos_reativacao(self):
        original_password = self.portal_user.password
        self.portal_user.is_active = False
        self.portal_user.save(update_fields=["is_active"])
        self.client.force_login(self.superuser)

        self.client.post(reverse("admin-user-enable", args=[self.portal_user.pk]))

        self.portal_user.refresh_from_db()
        self.assertEqual(self.portal_user.password, original_password)
        self.assertTrue(self.portal_user.check_password("Senha-forte-123"))

    def test_pending_activation_nao_pode_ser_reativado_como_blocked(self):
        pending = self.user_model.objects.create_user(
            username="pending.enable",
            is_active=False,
        )
        pending.set_unusable_password()
        pending.save()
        self.client.force_login(self.superuser)

        response = self.client.post(reverse("admin-user-enable", args=[pending.pk]))

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "USER_ACCESS_NOT_BLOCKED")

    def test_usuario_nao_pode_bloquear_propria_conta(self):
        self.client.force_login(self.superuser)

        response = self.client.post(reverse("admin-user-disable", args=[self.superuser.pk]))

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "CANNOT_DISABLE_OWN_ACCOUNT")
        self.superuser.refresh_from_db()
        self.assertTrue(self.superuser.is_active)

    def test_superuser_nao_pode_ser_bloqueado_pelo_fluxo_funcional(self):
        other_superuser = self.user_model.objects.create_superuser(
            username="admin.other",
            password="Senha-forte-123",
        )
        self.client.force_login(self.superuser)

        response = self.client.post(reverse("admin-user-disable", args=[other_superuser.pk]))

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["code"], "CANNOT_DISABLE_SUPERUSER")
        other_superuser.refresh_from_db()
        self.assertTrue(other_superuser.is_active)

    def test_usuario_comum_nao_pode_bloquear(self):
        self.client.force_login(self.regular_user)

        response = self.client.post(reverse("admin-user-disable", args=[self.portal_user.pk]))

        self.assertEqual(response.status_code, 403)

    def test_detalhe_protegido(self):
        response = self.client.get(reverse("admin-user-detail", args=[self.portal_user.pk]))

        self.assertEqual(response.status_code, 403)


class GlobalRolesSetupTests(TestCase):
    def test_setup_portal_roles_cria_grupos(self):
        setup_portal_roles()

        self.assertTrue(Group.objects.filter(name=PORTAL_ADMIN_GROUP).exists())
        self.assertTrue(Group.objects.filter(name=SECRETARY_GROUP).exists())
        self.assertTrue(Group.objects.filter(name=PASTOR_GROUP).exists())

    def test_setup_portal_roles_e_idempotente(self):
        setup_portal_roles()
        setup_portal_roles()

        self.assertEqual(Group.objects.filter(name=PORTAL_ADMIN_GROUP).count(), 1)
        self.assertEqual(Group.objects.filter(name=SECRETARY_GROUP).count(), 1)
        self.assertEqual(Group.objects.filter(name=PASTOR_GROUP).count(), 1)

    def test_administrador_recebe_permissions_esperadas(self):
        setup_portal_roles()
        group = Group.objects.get(name=PORTAL_ADMIN_GROUP)

        self.assertTrue(group.permissions.filter(codename="add_person").exists())
        self.assertTrue(group.permissions.filter(codename="approve_accessrequest").exists())
        self.assertTrue(group.permissions.filter(codename="disable_usuario").exists())

    def test_secretaria_recebe_permissions_esperadas(self):
        setup_portal_roles()
        group = Group.objects.get(name=SECRETARY_GROUP)

        self.assertTrue(group.permissions.filter(codename="change_person").exists())
        self.assertTrue(group.permissions.filter(codename="reject_accessrequest").exists())
        self.assertTrue(group.permissions.filter(codename="view_usuario").exists())
        self.assertFalse(group.permissions.filter(codename="disable_usuario").exists())

    def test_pastor_recebe_permissions_esperadas(self):
        setup_portal_roles()
        group = Group.objects.get(name=PASTOR_GROUP)

        self.assertTrue(group.permissions.filter(codename="view_person").exists())
        self.assertTrue(group.permissions.filter(codename="view_accessrequest").exists())
        self.assertTrue(group.permissions.filter(codename="view_usuario").exists())
        self.assertFalse(group.permissions.filter(codename="approve_accessrequest").exists())

    def test_midia_nao_e_criada_como_global_role(self):
        setup_portal_roles()

        self.assertFalse(Group.objects.filter(name="Midia").exists())
        self.assertFalse(Group.objects.filter(name="Mídia").exists())

    def test_papeis_departamentais_nao_sao_criados_como_groups_globais(self):
        setup_portal_roles()

        self.assertFalse(Group.objects.filter(name="Lider").exists())
        self.assertFalse(Group.objects.filter(name="Professor").exists())
        self.assertFalse(Group.objects.filter(name="Auxiliar").exists())


class GlobalRolesAuthorizationMatrixTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))
        self.access_request = AccessRequest.objects.create(
            full_name="Ana Souza",
            birth_date=date(1991, 6, 11),
            email="ana@example.com",
            phone="81988887777",
        )
        self.target_user = self.user_model.objects.create_user(
            username="target.user",
            password="Senha-forte-123",
            person=self.person,
        )

    def make_user_with_role(self, username, group_name):
        usuario = self.user_model.objects.create_user(
            username=username,
            password="Senha-forte-123",
        )
        assign_role(usuario, group_name)
        return usuario

    def test_administrador_funcional_nao_superuser_gerencia_modulos(self):
        admin = self.make_user_with_role("portal.admin.functional", PORTAL_ADMIN_GROUP)
        self.client.force_login(admin)

        people_list = self.client.get(reverse("person-list"))
        people_create = self.client.post(
            reverse("person-list"),
            {"full_name": "Nova Pessoa", "birth_date": "1995-01-01"},
            content_type="application/json",
        )
        people_update = self.client.patch(
            reverse("person-detail", args=[self.person.pk]),
            {"preferred_name": "Mari"},
            content_type="application/json",
        )
        request_list = self.client.get(reverse("access-request-admin-list"))
        approve = self.client.post(
            reverse("access-request-admin-approve", args=[self.access_request.pk]),
            {"create_new_person": True},
            content_type="application/json",
        )
        users_list = self.client.get(reverse("admin-user-list"))
        disable = self.client.post(reverse("admin-user-disable", args=[self.target_user.pk]))
        enable = self.client.post(reverse("admin-user-enable", args=[self.target_user.pk]))

        self.assertFalse(admin.is_superuser)
        self.assertEqual(people_list.status_code, 200)
        self.assertEqual(people_create.status_code, 201)
        self.assertEqual(people_update.status_code, 200)
        self.assertEqual(request_list.status_code, 200)
        self.assertEqual(approve.status_code, 200)
        self.assertEqual(users_list.status_code, 200)
        self.assertEqual(disable.status_code, 200)
        self.assertEqual(enable.status_code, 200)

    def test_secretaria_pode_fluxo_de_pessoas_e_solicitacoes_mas_nao_lifecycle_usuario(self):
        secretaria = self.make_user_with_role("secretary.functional", SECRETARY_GROUP)
        self.client.force_login(secretaria)

        self.assertEqual(self.client.get(reverse("person-list")).status_code, 200)
        self.assertEqual(
            self.client.post(
                reverse("person-list"),
                {"full_name": "Pessoa Secretaria", "birth_date": "1995-01-01"},
                content_type="application/json",
            ).status_code,
            201,
        )
        self.assertEqual(
            self.client.patch(
                reverse("person-detail", args=[self.person.pk]),
                {"preferred_name": "Mari"},
                content_type="application/json",
            ).status_code,
            200,
        )
        self.assertEqual(self.client.get(reverse("access-request-admin-list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin-user-list")).status_code, 200)
        self.assertEqual(self.client.post(reverse("admin-user-disable", args=[self.target_user.pk])).status_code, 403)

    def test_pastor_tem_somente_leitura_nos_modulos_novos(self):
        pastor = self.make_user_with_role("pastor.functional", PASTOR_GROUP)
        self.client.force_login(pastor)

        self.assertEqual(self.client.get(reverse("person-list")).status_code, 200)
        self.assertEqual(
            self.client.post(
                reverse("person-list"),
                {"full_name": "Pessoa Pastor", "birth_date": "1995-01-01"},
                content_type="application/json",
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.patch(
                reverse("person-detail", args=[self.person.pk]),
                {"preferred_name": "Mari"},
                content_type="application/json",
            ).status_code,
            403,
        )
        self.assertEqual(self.client.get(reverse("access-request-admin-list")).status_code, 200)
        self.assertEqual(
            self.client.post(
                reverse("access-request-admin-approve", args=[self.access_request.pk]),
                {"create_new_person": True},
                content_type="application/json",
            ).status_code,
            403,
        )
        self.assertEqual(self.client.get(reverse("admin-user-list")).status_code, 200)
        self.assertEqual(self.client.post(reverse("admin-user-disable", args=[self.target_user.pk])).status_code, 403)

    def test_usuario_comum_recebe_403_sem_logout(self):
        comum = self.user_model.objects.create_user(
            username="common.no.roles",
            password="Senha-forte-123",
        )
        self.client.force_login(comum)

        response = self.client.get(reverse("person-list"))

        self.assertEqual(response.status_code, 403)
        self.assertIn("_auth_user_id", self.client.session)

    def test_superuser_passa_sem_group_mas_nao_recebe_role_funcional(self):
        superuser = self.user_model.objects.create_superuser(
            username="technical.superuser",
            password="Senha-forte-123",
        )
        self.client.force_login(superuser)

        self.assertEqual(self.client.get(reverse("person-list")).status_code, 200)
        current_user = self.client.get(reverse("auth-current-user")).json()["user"]
        self.assertEqual(current_user["roles"], [])
        self.assertIn("PEOPLE_VIEW", current_user["capabilities"])

    def test_current_user_retorna_roles_e_capabilities(self):
        secretaria = self.make_user_with_role("secretary.current", SECRETARY_GROUP)
        self.client.force_login(secretaria)

        current_user = self.client.get(reverse("auth-current-user")).json()["user"]

        self.assertEqual(current_user["roles"], ["SECRETARY"])
        self.assertIn("PEOPLE_VIEW", current_user["capabilities"])
        self.assertIn("ACCESS_REQUEST_APPROVE", current_user["capabilities"])
        self.assertNotIn("USER_DISABLE", current_user["capabilities"])


class PermissoesPorPerfilTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.departamento = Departamento.objects.create(nome="Louvor Permissoes Globais")

        self.visitante = self.user_model.objects.create_user(
            username="perfil.visitante",
            password="senha-forte-123",
        )
        self.membro = self.user_model.objects.create_user(
            username="perfil.membro",
            password="senha-forte-123",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )
        self.liderado = self.user_model.objects.create_user(
            username="perfil.liderado",
            password="senha-forte-123",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )
        self.lider = self.user_model.objects.create_user(
            username="perfil.lider",
            password="senha-forte-123",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )
        self.ministro = self.user_model.objects.create_user(
            username="perfil.ministro",
            password="senha-forte-123",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )
        self.pastor = self.user_model.objects.create_user(
            username="perfil.pastor",
            password="senha-forte-123",
            eh_pastor=True,
        )
        self.superuser = self.user_model.objects.create_superuser(
            username="perfil.superuser",
            password="senha-forte-123",
            email="perfil.superuser@example.com",
        )

        DepartamentoMembro.objects.create(
            membro=self.liderado,
            departamento=self.departamento,
            papel=DepartamentoMembro.Papel.LIDERADO,
            ativo=True,
        )
        DepartamentoMembro.objects.create(
            membro=self.lider,
            departamento=self.departamento,
            papel=DepartamentoMembro.Papel.LIDER,
            ativo=True,
        )
        Ministro.objects.create(
            usuario=self.ministro,
            nome_completo="Ministro Perfil",
            tipo=Ministro.Tipo.CASA,
            status=Ministro.Status.APROVADO,
            ativo=True,
        )

    def test_identidades_globais_nao_confundem_acesso(self):
        self.assertTrue(usuario_eh_visitante(self.visitante))
        self.assertTrue(usuario_eh_membro(self.membro))
        self.assertTrue(usuario_eh_lider_departamento(self.lider, self.departamento))
        self.assertTrue(usuario_eh_lider_em_algum_departamento(self.lider))
        self.assertTrue(usuario_eh_ministro(self.ministro))
        self.assertTrue(usuario_eh_pastor(self.pastor))
        self.assertTrue(usuario_tem_acesso_tecnico_total(self.superuser))

        self.assertFalse(usuario_eh_secretaria(self.pastor))
        self.assertFalse(usuario_eh_lider_em_algum_departamento(self.pastor))
        self.assertFalse(usuario_eh_ministro(self.pastor))
        self.assertFalse(usuario_eh_pastor(self.superuser))

    def test_acesso_a_secretaria_por_perfil(self):
        self.assertFalse(usuario_tem_acesso_secretaria(self.visitante))
        self.assertFalse(usuario_tem_acesso_secretaria(self.membro))
        self.assertFalse(usuario_tem_acesso_secretaria(self.liderado))
        self.assertFalse(usuario_tem_acesso_secretaria(self.lider))
        self.assertFalse(usuario_tem_acesso_secretaria(self.ministro))
        self.assertTrue(usuario_tem_acesso_secretaria(self.pastor))
        self.assertTrue(usuario_tem_acesso_secretaria(self.superuser))

    def test_acesso_a_midia_por_perfil(self):
        self.assertFalse(usuario_tem_acesso_midia(self.visitante))
        self.assertFalse(usuario_tem_acesso_midia(self.membro))
        self.assertFalse(usuario_tem_acesso_midia(self.liderado))
        self.assertFalse(usuario_tem_acesso_midia(self.lider))
        self.assertFalse(usuario_tem_acesso_midia(self.ministro))
        self.assertTrue(usuario_tem_acesso_midia(self.pastor))
        self.assertTrue(usuario_tem_acesso_midia(self.superuser))

    def test_acesso_a_escalas_por_perfil(self):
        self.assertFalse(usuario_pode_acessar_escalas(self.visitante))
        self.assertFalse(usuario_pode_acessar_escalas(self.membro))
        self.assertFalse(usuario_pode_acessar_escalas(self.liderado))
        self.assertTrue(usuario_pode_acessar_escalas(self.lider))
        self.assertFalse(usuario_pode_acessar_escalas(self.ministro))
        self.assertTrue(usuario_pode_acessar_escalas(self.pastor))
        self.assertTrue(usuario_pode_acessar_escalas(self.superuser))

        self.assertTrue(usuario_pode_montar_escala(self.lider, self.departamento))
        self.assertTrue(usuario_pode_montar_escala(self.pastor, self.departamento))
        self.assertTrue(usuario_pode_montar_escala(self.superuser, self.departamento))
        self.assertFalse(usuario_pode_montar_escala(self.liderado, self.departamento))

    def test_acesso_a_departamentos_por_perfil(self):
        self.assertFalse(usuario_pode_acessar_departamentos(self.visitante))
        self.assertFalse(usuario_pode_acessar_departamentos(self.membro))
        self.assertTrue(usuario_pode_acessar_departamentos(self.liderado))
        self.assertTrue(usuario_pode_acessar_departamentos(self.lider))
        self.assertFalse(usuario_pode_acessar_departamentos(self.ministro))
        self.assertTrue(usuario_pode_acessar_departamentos(self.pastor))
        self.assertTrue(usuario_pode_acessar_departamentos(self.superuser))

    def test_acesso_total_do_sistema_e_apenas_pastoral_ou_tecnico(self):
        self.assertFalse(usuario_tem_acesso_total_sistema(self.visitante))
        self.assertFalse(usuario_tem_acesso_total_sistema(self.lider))
        self.assertFalse(usuario_tem_acesso_total_sistema(self.ministro))
        self.assertTrue(usuario_tem_acesso_total_sistema(self.pastor))
        self.assertTrue(usuario_tem_acesso_total_sistema(self.superuser))


class InternalPermissionsContextProcessorTests(TestCase):
    def test_context_processor_reutiliza_cache_por_request(self):
        user = get_user_model().objects.create_user(
            username="cache.context.processor",
            password="senha-forte-123",
        )
        request = SimpleNamespace(user=user)
        departamentos_do_usuario = Mock()
        departamentos_do_usuario.exists.return_value = False
        departamentos_gerenciaveis = Mock()
        departamentos_gerenciaveis.exists.return_value = False

        patches = (
            patch(
                "usuarios.context_processors.get_departamentos_do_usuario",
                return_value=departamentos_do_usuario,
            ),
            patch(
                "usuarios.context_processors.get_departamentos_gerenciaveis",
                return_value=departamentos_gerenciaveis,
            ),
            patch("usuarios.context_processors.usuario_pode_criar_departamentos", return_value=False),
            patch("usuarios.context_processors.usuario_pode_visualizar_infantil", return_value=False),
            patch("usuarios.context_processors.usuario_pode_acessar_painel_secretaria", return_value=False),
            patch("usuarios.context_processors.usuario_pode_acessar_painel_midia", return_value=False),
            patch("usuarios.context_processors.usuario_pode_gerenciar_eventos", return_value=False),
            patch("usuarios.context_processors.usuario_pode_gerenciar_ministros", return_value=False),
            patch("usuarios.context_processors.usuario_pode_acessar_verbo_no_lar", return_value=False),
            patch("usuarios.context_processors.usuario_pode_gerenciar_financeiro", return_value=False),
        )

        with patches[0] as get_departamentos, patches[1] as get_gerenciaveis, patches[2] as pode_criar, patches[
            3
        ], patches[4], patches[5], patches[6], patches[7], patches[8], patches[9]:
            first_result = internal_permissions(request)
            second_result = internal_permissions(request)

        self.assertIs(first_result, second_result)
        self.assertIs(request._internal_permissions_cache, first_result)
        get_departamentos.assert_called_once_with(user)
        get_gerenciaveis.assert_called_once_with(user)
        pode_criar.assert_called_once_with(user)
        self.assertFalse(first_result["can_view_departamentos"])
        self.assertFalse(first_result["can_manage_escalas"])


class ResetTestDataCommandTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()

    def test_reset_test_data_bloqueia_producao(self):
        with patch.dict(environ, {"DJANGO_ENV": "prod"}):
            with self.assertRaises(CommandError):
                call_command("reset_test_data", "--yes", stdout=StringIO())

    def test_reset_test_data_preserva_superuser_por_padrao(self):
        superuser = self.user_model.objects.create_superuser(
            username="admin.reset",
            password="senha-forte-123",
            email="admin.reset@example.com",
        )
        usuario = self.user_model.objects.create_user(
            username="usuario.reset",
            password="senha-forte-123",
        )
        Person.objects.create(full_name="Pessoa Reset", birth_date=date(1990, 5, 10))

        call_command("reset_test_data", "--yes", stdout=StringIO())

        self.assertTrue(self.user_model.objects.filter(pk=superuser.pk).exists())
        self.assertFalse(self.user_model.objects.filter(pk=usuario.pk).exists())
        self.assertFalse(Person.objects.exists())

    def test_reset_test_data_usa_transaction_atomic(self):
        with patch("pessoas.management.commands.reset_test_data.atomic") as atomic:
            call_command("reset_test_data", "--yes", stdout=StringIO())

        atomic.assert_called_once()
