from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from pessoas.models import Person
from usuarios.roles import (
    PASTOR_GROUP,
    PORTAL_ADMIN_GROUP,
    SECRETARY_GROUP,
    setup_portal_roles,
)

from .enums import ChurchStatus
from .models import ChurchJourney
from .selectors import (
    get_church_status,
    get_discipleship_completed_at,
    has_completed_discipleship,
    is_legacy_department_eligible,
    is_member,
    is_visitor,
)
from .services import CHURCH_JOURNEY_ALREADY_EXISTS, ChurchJourneyError, start_church_journey


class ChurchJourneyCompatibilitySelectorsTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()

    def create_person(self, name):
        return Person.objects.create(
            full_name=name,
            birth_date=date(1990, 1, 1),
        )

    def create_user_for_person(self, person, username, **kwargs):
        return self.user_model.objects.create_user(
            username=username,
            password="senha-forte-123",
            person=person,
            **kwargs,
        )

    def test_person_com_usuario_visitante_retorna_visitor(self):
        person = self.create_person("Visitante Teste")
        self.create_user_for_person(person, "visitante.teste")

        self.assertEqual(get_church_status(person), ChurchStatus.VISITOR)

    def test_person_com_usuario_membro_retorna_member(self):
        person = self.create_person("Membro Teste")
        self.create_user_for_person(
            person,
            "membro.teste",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )

        self.assertEqual(get_church_status(person), ChurchStatus.MEMBER)

    def test_person_sem_usuario_retorna_unknown(self):
        person = self.create_person("Pessoa Sem Usuario")

        self.assertEqual(get_church_status(person), ChurchStatus.UNKNOWN)

    def test_is_visitor_retorna_true_para_visitante(self):
        person = self.create_person("Visitante Legado")
        self.create_user_for_person(person, "visitante.legado")

        self.assertTrue(is_visitor(person))

    def test_is_member_retorna_true_para_membro(self):
        person = self.create_person("Membro Legado")
        self.create_user_for_person(
            person,
            "membro.legado",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )

        self.assertTrue(is_member(person))

    def test_membro_nao_e_visitante(self):
        person = self.create_person("Membro Nao Visitante")
        self.create_user_for_person(
            person,
            "membro.nao.visitante",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )

        self.assertFalse(is_visitor(person))

    def test_visitante_nao_e_membro(self):
        person = self.create_person("Visitante Nao Membro")
        self.create_user_for_person(person, "visitante.nao.membro")

        self.assertFalse(is_member(person))

    def test_person_sem_usuario_nao_e_membro_nem_visitante(self):
        person = self.create_person("Pessoa Indefinida")

        self.assertFalse(is_member(person))
        self.assertFalse(is_visitor(person))

    def test_discipulado_concluido_retorna_true(self):
        person = self.create_person("Discipulado Concluido")
        self.create_user_for_person(
            person,
            "discipulado.concluido",
            discipulado_concluido=True,
        )

        self.assertTrue(has_completed_discipleship(person))

    def test_discipulado_nao_concluido_retorna_false(self):
        person = self.create_person("Discipulado Pendente")
        self.create_user_for_person(person, "discipulado.pendente")

        self.assertFalse(has_completed_discipleship(person))

    def test_data_de_conclusao_do_discipulado_e_retornada(self):
        person = self.create_person("Discipulado Com Data")
        completed_at = date(2024, 5, 19)
        self.create_user_for_person(
            person,
            "discipulado.data",
            discipulado_concluido=True,
            discipulado_concluido_em=completed_at,
        )

        self.assertEqual(get_discipleship_completed_at(person), completed_at)

    def test_person_sem_usuario_nao_tem_discipulado(self):
        person = self.create_person("Sem Usuario Sem Discipulado")

        self.assertFalse(has_completed_discipleship(person))
        self.assertIsNone(get_discipleship_completed_at(person))

    def test_elegibilidade_departamental_legada_aceita_membro(self):
        person = self.create_person("Elegivel Membro")
        self.create_user_for_person(
            person,
            "elegivel.membro",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )

        self.assertTrue(is_legacy_department_eligible(person))

    def test_elegibilidade_departamental_legada_aceita_pastor(self):
        person = self.create_person("Elegivel Pastor")
        self.create_user_for_person(person, "elegivel.pastor", eh_pastor=True)

        self.assertTrue(is_legacy_department_eligible(person))

    def test_elegibilidade_departamental_legada_aceita_superuser(self):
        person = self.create_person("Elegivel Superuser")
        self.user_model.objects.create_superuser(
            username="elegivel.superuser",
            password="senha-forte-123",
            email="superuser@example.com",
            person=person,
        )

        self.assertTrue(is_legacy_department_eligible(person))

    def test_person_com_church_journey_retorna_visitor(self):
        person = self.create_person("Visitante Novo Dominio")
        ChurchJourney.objects.create(person=person)

        self.assertEqual(get_church_status(person), ChurchStatus.VISITOR)

    def test_person_sem_church_journey_com_legado_member_retorna_member(self):
        person = self.create_person("Membro Fallback Legado")
        self.create_user_for_person(
            person,
            "membro.fallback",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )

        self.assertEqual(get_church_status(person), ChurchStatus.MEMBER)

    def test_person_sem_church_journey_com_legado_visitor_retorna_visitor(self):
        person = self.create_person("Visitante Fallback Legado")
        self.create_user_for_person(person, "visitante.fallback")

        self.assertEqual(get_church_status(person), ChurchStatus.VISITOR)

    def test_novo_dominio_tem_prioridade_sobre_legado_membro(self):
        person = self.create_person("Prioridade Novo Dominio")
        self.create_user_for_person(
            person,
            "prioridade.novo",
            status_eclesiastico=self.user_model.StatusEclesiastico.MEMBRO,
        )
        ChurchJourney.objects.create(person=person)

        self.assertEqual(get_church_status(person), ChurchStatus.VISITOR)
        self.assertTrue(is_visitor(person))
        self.assertFalse(is_member(person))


class ChurchJourneyModelAndServiceTests(TestCase):
    def create_person(self, name="Pessoa Jornada"):
        return Person.objects.create(
            full_name=name,
            birth_date=date(1990, 1, 1),
        )

    def test_person_pode_existir_sem_church_journey(self):
        person = self.create_person()

        self.assertFalse(hasattr(person, "church_journey"))

    def test_church_journey_exige_person(self):
        with self.assertRaises(IntegrityError):
            ChurchJourney.objects.create(person=None)

    def test_person_possui_no_maximo_uma_church_journey(self):
        person = self.create_person()
        ChurchJourney.objects.create(person=person)

        with self.assertRaises(IntegrityError):
            ChurchJourney.objects.create(person=person)

    def test_started_at_pode_ser_informado(self):
        person = self.create_person()
        started_at = date(2026, 8, 19)

        journey = ChurchJourney.objects.create(person=person, started_at=started_at)

        self.assertEqual(journey.started_at, started_at)

    def test_started_at_default_usa_data_atual(self):
        person = self.create_person()

        journey = ChurchJourney.objects.create(person=person)

        self.assertEqual(journey.started_at, timezone.localdate())

    def test_apagar_church_journey_nao_apaga_person(self):
        person = self.create_person()
        journey = ChurchJourney.objects.create(person=person)

        journey.delete()

        self.assertTrue(Person.objects.filter(pk=person.pk).exists())

    def test_start_church_journey_cria_jornada(self):
        person = self.create_person()
        started_at = date(2026, 8, 19)

        journey = start_church_journey(person, started_at=started_at)

        self.assertEqual(journey.person, person)
        self.assertEqual(journey.started_at, started_at)

    def test_start_church_journey_duplicada_gera_erro_de_dominio(self):
        person = self.create_person()
        start_church_journey(person)

        with self.assertRaises(ChurchJourneyError) as context:
            start_church_journey(person)

        self.assertEqual(context.exception.code, CHURCH_JOURNEY_ALREADY_EXISTS)


class ChurchJourneyApiTests(APITestCase):
    def setUp(self):
        setup_portal_roles()
        self.user_model = get_user_model()
        self.person = Person.objects.create(
            full_name="Pessoa API Jornada",
            birth_date=date(1990, 1, 1),
        )

    def make_user_with_role(self, username, group_name):
        usuario = self.user_model.objects.create_user(
            username=username,
            password="senha-forte-123",
        )
        usuario.groups.add(Group.objects.get(name=group_name))
        return usuario

    def authenticate_role(self, username, group_name):
        usuario = self.make_user_with_role(username, group_name)
        self.client.force_authenticate(usuario)
        return usuario

    def endpoint(self, person=None):
        return reverse("person-church-journey", args=[(person or self.person).pk])

    def test_usuario_autorizado_consulta_church_journey(self):
        self.authenticate_role("secretaria.view.journey", SECRETARY_GROUP)
        journey = ChurchJourney.objects.create(person=self.person, started_at=date(2026, 8, 19))

        response = self.client.get(self.endpoint())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], journey.id)
        self.assertEqual(response.json()["church_status"], ChurchStatus.VISITOR.value)

    def test_usuario_sem_permission_recebe_403_no_get(self):
        comum = self.user_model.objects.create_user(
            username="comum.view.journey",
            password="senha-forte-123",
        )
        self.client.force_authenticate(comum)

        response = self.client.get(self.endpoint())

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_sem_church_journey_retorna_404(self):
        self.authenticate_role("secretaria.get.empty", SECRETARY_GROUP)

        response = self.client.get(self.endpoint())

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_criar_church_journey_autorizado(self):
        self.authenticate_role("secretaria.create.journey", SECRETARY_GROUP)

        response = self.client.post(
            self.endpoint(),
            {"started_at": "2026-08-19"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ChurchJourney.objects.filter(person=self.person).exists())
        self.assertEqual(response.json()["started_at"], "2026-08-19")

    def test_usuario_sem_add_permission_nao_cria(self):
        self.authenticate_role("pastor.no.create", PASTOR_GROUP)

        response = self.client.post(self.endpoint(), {"started_at": "2026-08-19"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(ChurchJourney.objects.filter(person=self.person).exists())

    def test_duplicidade_e_bloqueada(self):
        self.authenticate_role("secretaria.duplicate", SECRETARY_GROUP)
        ChurchJourney.objects.create(person=self.person)

        response = self.client.post(self.endpoint(), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.json()["code"], CHURCH_JOURNEY_ALREADY_EXISTS)

    def test_person_inexistente_retorna_404(self):
        self.authenticate_role("secretaria.missing.person", SECRETARY_GROUP)

        response = self.client.post(
            reverse("person-church-journey", args=[999999]),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_nao_cria_usuario(self):
        self.authenticate_role("secretaria.no.user", SECRETARY_GROUP)
        before_count = self.user_model.objects.count()

        self.client.post(self.endpoint(), {}, format="json")

        self.assertEqual(self.user_model.objects.count(), before_count)

    def test_post_nao_altera_status_eclesiastico_legado(self):
        self.authenticate_role("secretaria.no.legacy", SECRETARY_GROUP)
        usuario = self.user_model.objects.create_user(
            username="legado.visitante",
            password="senha-forte-123",
            person=self.person,
        )

        self.client.post(self.endpoint(), {}, format="json")

        usuario.refresh_from_db()
        self.assertEqual(usuario.status_eclesiastico, self.user_model.StatusEclesiastico.VISITANTE)

    def test_post_nao_cria_membership(self):
        self.authenticate_role("secretaria.no.membership", SECRETARY_GROUP)

        response = self.client.post(self.endpoint(), {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(hasattr(self.person, "membership"))


class ChurchJourneyRolePermissionsTests(TestCase):
    def setUp(self):
        setup_portal_roles()
        self.user_model = get_user_model()

    def make_user_with_role(self, username, group_name):
        usuario = self.user_model.objects.create_user(
            username=username,
            password="senha-forte-123",
        )
        usuario.groups.add(Group.objects.get(name=group_name))
        return usuario

    def test_administrador_tem_view_add_change(self):
        admin = self.make_user_with_role("admin.journey.perms", PORTAL_ADMIN_GROUP)

        self.assertTrue(admin.has_perm("church_journey.view_churchjourney"))
        self.assertTrue(admin.has_perm("church_journey.add_churchjourney"))
        self.assertTrue(admin.has_perm("church_journey.change_churchjourney"))

    def test_secretaria_tem_view_add_change(self):
        secretaria = self.make_user_with_role("secretaria.journey.perms", SECRETARY_GROUP)

        self.assertTrue(secretaria.has_perm("church_journey.view_churchjourney"))
        self.assertTrue(secretaria.has_perm("church_journey.add_churchjourney"))
        self.assertTrue(secretaria.has_perm("church_journey.change_churchjourney"))

    def test_pastor_tem_apenas_view(self):
        pastor = self.make_user_with_role("pastor.journey.perms", PASTOR_GROUP)

        self.assertTrue(pastor.has_perm("church_journey.view_churchjourney"))
        self.assertFalse(pastor.has_perm("church_journey.add_churchjourney"))
        self.assertFalse(pastor.has_perm("church_journey.change_churchjourney"))

    def test_usuario_comum_nao_tem_permissoes_administrativas(self):
        comum = self.user_model.objects.create_user(
            username="comum.journey.perms",
            password="senha-forte-123",
        )

        self.assertFalse(comum.has_perm("church_journey.view_churchjourney"))
        self.assertFalse(comum.has_perm("church_journey.add_churchjourney"))
        self.assertFalse(comum.has_perm("church_journey.change_churchjourney"))
