from datetime import date
from io import StringIO
from os import environ
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

from departamentos.models import Departamento, DepartamentoMembro
from departamentos.permissions import usuario_pode_acessar_departamentos
from escalas.permissions import usuario_pode_acessar_escalas
from ministros.models import Ministro
from pessoas.models import Person
from usuarios.context_processors import internal_permissions

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

    def test_secretaria_atual_pode_listar_solicitacoes(self):
        self.client.force_login(self.make_secretaria())

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
