from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
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
from .models import (
    DiscipleshipAttendance,
    DiscipleshipClass,
    DiscipleshipClassAssistant,
    DiscipleshipEnrollment,
    DiscipleshipLesson,
)
from .selectors import (
    get_church_status,
    get_discipleship_completed_at,
    has_completed_discipleship,
    is_legacy_department_eligible,
    is_member,
    is_visitor,
)
from .services import (
    CHURCH_JOURNEY_ALREADY_EXISTS,
    DISCIPLESHIP_CLASS_ALREADY_IN_PROGRESS,
    DISCIPLESHIP_CLASS_NOT_OPEN_FOR_ENROLLMENT,
    DISCIPLESHIP_CLASS_NOT_OPEN_FOR_LESSONS,
    DISCIPLESHIP_ENROLLMENT_ALREADY_EXISTS,
    DISCIPLESHIP_LESSON_DATE_CONFLICT,
    CANCELLED_DISCIPLESHIP_LESSON_DOES_NOT_ACCEPT_ATTENDANCE,
    DISCIPLESHIP_ATTENDANCE_CLASS_MISMATCH,
    DISCIPLESHIP_ENROLLMENT_NOT_ELIGIBLE_FOR_LESSON,
    DISCIPLESHIP_LESSON_NOT_YET_AVAILABLE_FOR_ATTENDANCE,
    INVALID_DISCIPLESHIP_ATTENDANCE_STATUS,
    INVALID_DISCIPLESHIP_CLASS_TRANSITION,
    INVALID_DISCIPLESHIP_ENROLLMENT_TRANSITION,
    INVALID_DISCIPLESHIP_LESSON_TRANSITION,
    PERSON_NOT_IN_CHURCH_JOURNEY,
    ChurchJourneyError,
    cancel_discipleship_class,
    cancel_discipleship_lesson,
    complete_discipleship_class,
    create_discipleship_class,
    create_discipleship_lesson,
    enroll_person_in_discipleship_class,
    get_eligible_enrollments_for_lesson,
    record_discipleship_attendance,
    record_discipleship_attendance_batch,
    start_church_journey,
    start_discipleship_class,
    update_discipleship_lesson,
    withdraw_discipleship_enrollment,
)


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


class DiscipleshipClassModelTests(TestCase):
    def setUp(self):
        self.teacher = Person.objects.create(
            full_name="Professor Discipulado",
            birth_date=date(1980, 1, 1),
        )

    def make_class(self, **kwargs):
        data = {
            "name": "Discipulado 2026.2",
            "teacher": self.teacher,
            "start_date": date(2026, 9, 5),
            "expected_end_date": date(2026, 11, 28),
            "planned_sessions": 12,
        }
        data.update(kwargs)
        return DiscipleshipClass.objects.create(**data)

    def test_criacao_valida(self):
        discipleship_class = self.make_class()

        self.assertEqual(discipleship_class.name, "Discipulado 2026.2")

    def test_status_default_e_planned(self):
        discipleship_class = self.make_class()

        self.assertEqual(discipleship_class.status, DiscipleshipClass.Status.PLANNED)

    def test_teacher_aponta_para_person(self):
        discipleship_class = self.make_class()

        self.assertEqual(discipleship_class.teacher, self.teacher)

    def test_planned_sessions_deve_ser_positivo(self):
        with self.assertRaises(Exception):
            self.make_class(planned_sessions=0)

    def test_expected_end_date_nao_pode_ser_anterior_ao_inicio(self):
        with self.assertRaises(Exception):
            self.make_class(expected_end_date=date(2026, 9, 4))

    def test_varias_planned_sao_permitidas(self):
        self.make_class(name="Discipulado 2026.2")
        self.make_class(
            name="Discipulado 2027.1",
            start_date=date(2027, 2, 1),
            expected_end_date=date(2027, 4, 30),
        )

        self.assertEqual(DiscipleshipClass.objects.count(), 2)

    def test_somente_uma_in_progress_e_permitida(self):
        self.make_class(name="Atual", status=DiscipleshipClass.Status.IN_PROGRESS)

        with self.assertRaises(Exception):
            self.make_class(name="Outra atual", status=DiscipleshipClass.Status.IN_PROGRESS)

    def test_completed_e_cancelled_historicas_sao_permitidas(self):
        self.make_class(name="Concluida", status=DiscipleshipClass.Status.COMPLETED)
        self.make_class(name="Cancelada", status=DiscipleshipClass.Status.CANCELLED)

        self.assertEqual(DiscipleshipClass.objects.count(), 2)


class DiscipleshipClassLifecycleTests(TestCase):
    def setUp(self):
        self.teacher = Person.objects.create(
            full_name="Professor Lifecycle",
            birth_date=date(1980, 1, 1),
        )

    def make_class(self, **kwargs):
        status_value = kwargs.pop("status", None)
        data = {
            "name": "Discipulado Lifecycle",
            "teacher": self.teacher,
            "start_date": date(2026, 9, 5),
            "expected_end_date": date(2026, 11, 28),
            "planned_sessions": 12,
        }
        data.update(kwargs)
        discipleship_class = create_discipleship_class(**data)
        if status_value is not None:
            discipleship_class.status = status_value
            discipleship_class.save(update_fields=["status", "updated_at"])
        return discipleship_class

    def test_planned_para_in_progress(self):
        discipleship_class = self.make_class()

        start_discipleship_class(discipleship_class)

        self.assertEqual(discipleship_class.status, DiscipleshipClass.Status.IN_PROGRESS)

    def test_planned_para_cancelled(self):
        discipleship_class = self.make_class()

        cancel_discipleship_class(discipleship_class)

        self.assertEqual(discipleship_class.status, DiscipleshipClass.Status.CANCELLED)

    def test_in_progress_para_completed(self):
        discipleship_class = self.make_class()
        start_discipleship_class(discipleship_class)

        complete_discipleship_class(discipleship_class)

        self.assertEqual(discipleship_class.status, DiscipleshipClass.Status.COMPLETED)

    def test_in_progress_para_cancelled(self):
        discipleship_class = self.make_class()
        start_discipleship_class(discipleship_class)

        cancel_discipleship_class(discipleship_class)

        self.assertEqual(discipleship_class.status, DiscipleshipClass.Status.CANCELLED)

    def test_completed_nao_volta_para_in_progress(self):
        discipleship_class = self.make_class(status=DiscipleshipClass.Status.COMPLETED)

        with self.assertRaises(ChurchJourneyError) as context:
            start_discipleship_class(discipleship_class)

        self.assertEqual(context.exception.code, INVALID_DISCIPLESHIP_CLASS_TRANSITION)

    def test_cancelled_nao_volta_para_in_progress(self):
        discipleship_class = self.make_class(status=DiscipleshipClass.Status.CANCELLED)

        with self.assertRaises(ChurchJourneyError) as context:
            start_discipleship_class(discipleship_class)

        self.assertEqual(context.exception.code, INVALID_DISCIPLESHIP_CLASS_TRANSITION)

    def test_planned_nao_conclui_diretamente(self):
        discipleship_class = self.make_class()

        with self.assertRaises(ChurchJourneyError) as context:
            complete_discipleship_class(discipleship_class)

        self.assertEqual(context.exception.code, INVALID_DISCIPLESHIP_CLASS_TRANSITION)

    def test_start_bloqueia_segunda_turma_em_andamento(self):
        self.make_class(name="Em andamento", status=DiscipleshipClass.Status.IN_PROGRESS)
        planned = self.make_class(name="Planejada")

        with self.assertRaises(ChurchJourneyError) as context:
            start_discipleship_class(planned)

        self.assertEqual(context.exception.code, DISCIPLESHIP_CLASS_ALREADY_IN_PROGRESS)

    def test_complete_nao_altera_discipulado_legado_do_usuario(self):
        user_model = get_user_model()
        usuario = user_model.objects.create_user(
            username="aluno.legado",
            password="senha-forte-123",
            person=Person.objects.create(
                full_name="Aluno Legado",
                birth_date=date(1990, 1, 1),
            ),
        )
        discipleship_class = self.make_class()
        start_discipleship_class(discipleship_class)

        complete_discipleship_class(discipleship_class)

        usuario.refresh_from_db()
        self.assertFalse(usuario.discipulado_concluido)
        self.assertIsNone(usuario.discipulado_concluido_em)


class DiscipleshipClassApiTests(APITestCase):
    def setUp(self):
        setup_portal_roles()
        self.user_model = get_user_model()
        self.teacher = Person.objects.create(
            full_name="Professor API",
            birth_date=date(1980, 1, 1),
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

    def make_payload(self, **kwargs):
        payload = {
            "name": "Discipulado API",
            "teacher_id": self.teacher.pk,
            "start_date": "2026-09-05",
            "expected_end_date": "2026-11-28",
            "planned_sessions": 12,
        }
        payload.update(kwargs)
        return payload

    def make_class(self, **kwargs):
        data = {
            "name": "Discipulado API",
            "teacher": self.teacher,
            "start_date": date(2026, 9, 5),
            "expected_end_date": date(2026, 11, 28),
            "planned_sessions": 12,
        }
        data.update(kwargs)
        return DiscipleshipClass.objects.create(**data)

    def test_list(self):
        self.authenticate_role("secretaria.discipleship.list", SECRETARY_GROUP)
        self.make_class()

        response = self.client.get(reverse("discipleship-class-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0]["teacher"]["display_name"], "Professor API")

    def test_detail(self):
        self.authenticate_role("secretaria.discipleship.detail", SECRETARY_GROUP)
        discipleship_class = self.make_class()

        response = self.client.get(reverse("discipleship-class-detail", args=[discipleship_class.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["name"], "Discipulado API")

    def test_create(self):
        self.authenticate_role("secretaria.discipleship.create", SECRETARY_GROUP)

        response = self.client.post(
            reverse("discipleship-class-list"),
            self.make_payload(status=DiscipleshipClass.Status.IN_PROGRESS),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["status"], DiscipleshipClass.Status.PLANNED)

    def test_update(self):
        self.authenticate_role("secretaria.discipleship.update", SECRETARY_GROUP)
        discipleship_class = self.make_class()

        response = self.client.patch(
            reverse("discipleship-class-detail", args=[discipleship_class.pk]),
            {"name": "Discipulado Editado", "planned_sessions": 10},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["name"], "Discipulado Editado")
        self.assertEqual(response.json()["planned_sessions"], 10)

    def test_start(self):
        self.authenticate_role("secretaria.discipleship.start", SECRETARY_GROUP)
        discipleship_class = self.make_class()

        response = self.client.post(reverse("discipleship-class-start", args=[discipleship_class.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], DiscipleshipClass.Status.IN_PROGRESS)

    def test_start_segunda_turma_retorna_erro_estruturado(self):
        self.authenticate_role("secretaria.discipleship.start.conflict", SECRETARY_GROUP)
        self.make_class(name="Atual", status=DiscipleshipClass.Status.IN_PROGRESS)
        planned = self.make_class(name="Planejada")

        response = self.client.post(reverse("discipleship-class-start", args=[planned.pk]))

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.json()["code"], DISCIPLESHIP_CLASS_ALREADY_IN_PROGRESS)

    def test_complete(self):
        self.authenticate_role("secretaria.discipleship.complete", SECRETARY_GROUP)
        discipleship_class = self.make_class(status=DiscipleshipClass.Status.IN_PROGRESS)

        response = self.client.post(reverse("discipleship-class-complete", args=[discipleship_class.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], DiscipleshipClass.Status.COMPLETED)

    def test_cancel(self):
        self.authenticate_role("secretaria.discipleship.cancel", SECRETARY_GROUP)
        discipleship_class = self.make_class()

        response = self.client.post(reverse("discipleship-class-cancel", args=[discipleship_class.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], DiscipleshipClass.Status.CANCELLED)

    def test_delete_nao_e_permitido(self):
        self.authenticate_role("secretaria.discipleship.delete", SECRETARY_GROUP)
        discipleship_class = self.make_class()

        response = self.client.delete(reverse("discipleship-class-detail", args=[discipleship_class.pk]))

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_usuario_comum_recebe_403(self):
        comum = self.user_model.objects.create_user(
            username="comum.discipleship",
            password="senha-forte-123",
        )
        self.client.force_authenticate(comum)

        response = self.client.get(reverse("discipleship-class-list"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_pastor_visualiza_mas_nao_cria(self):
        self.authenticate_role("pastor.discipleship", PASTOR_GROUP)

        self.assertEqual(self.client.get(reverse("discipleship-class-list")).status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.post(reverse("discipleship-class-list"), self.make_payload(), format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )


class DiscipleshipClassRolePermissionsTests(TestCase):
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

    def assert_can_manage_discipleship(self, usuario):
        self.assertTrue(usuario.has_perm("church_journey.view_discipleshipclass"))
        self.assertTrue(usuario.has_perm("church_journey.add_discipleshipclass"))
        self.assertTrue(usuario.has_perm("church_journey.change_discipleshipclass"))
        self.assertTrue(usuario.has_perm("church_journey.start_discipleshipclass"))
        self.assertTrue(usuario.has_perm("church_journey.complete_discipleshipclass"))
        self.assertTrue(usuario.has_perm("church_journey.cancel_discipleshipclass"))

    def test_administrador_tem_todas_acoes(self):
        admin = self.make_user_with_role("admin.discipleship.perms", PORTAL_ADMIN_GROUP)

        self.assert_can_manage_discipleship(admin)

    def test_secretaria_tem_todas_acoes(self):
        secretaria = self.make_user_with_role("secretaria.discipleship.perms", SECRETARY_GROUP)

        self.assert_can_manage_discipleship(secretaria)

    def test_pastor_tem_apenas_view(self):
        pastor = self.make_user_with_role("pastor.discipleship.perms", PASTOR_GROUP)

        self.assertTrue(pastor.has_perm("church_journey.view_discipleshipclass"))
        self.assertFalse(pastor.has_perm("church_journey.add_discipleshipclass"))
        self.assertFalse(pastor.has_perm("church_journey.start_discipleshipclass"))

    def test_usuario_comum_nao_tem_permissao(self):
        comum = self.user_model.objects.create_user(
            username="comum.discipleship.perms",
            password="senha-forte-123",
        )

        self.assertFalse(comum.has_perm("church_journey.view_discipleshipclass"))


class DiscipleshipEnrollmentModelTests(TestCase):
    def setUp(self):
        self.teacher = Person.objects.create(full_name="Professor Matricula", birth_date=date(1980, 1, 1))
        self.person = Person.objects.create(full_name="Aluno Matricula", birth_date=date(1990, 1, 1))
        ChurchJourney.objects.create(person=self.person)
        self.discipleship_class = DiscipleshipClass.objects.create(
            name="Discipulado Matricula",
            teacher=self.teacher,
            start_date=date(2026, 9, 5),
            expected_end_date=date(2026, 11, 28),
            planned_sessions=12,
        )

    def test_matricula_valida(self):
        enrollment = DiscipleshipEnrollment.objects.create(
            person=self.person,
            discipleship_class=self.discipleship_class,
        )

        self.assertEqual(enrollment.person, self.person)
        self.assertEqual(enrollment.discipleship_class, self.discipleship_class)

    def test_default_enrolled_e_datas(self):
        enrollment = DiscipleshipEnrollment.objects.create(
            person=self.person,
            discipleship_class=self.discipleship_class,
        )

        self.assertEqual(enrollment.status, DiscipleshipEnrollment.Status.ENROLLED)
        self.assertEqual(enrollment.enrolled_at, timezone.localdate())
        self.assertIsNone(enrollment.withdrawn_at)

    def test_unicidade_person_class(self):
        DiscipleshipEnrollment.objects.create(
            person=self.person,
            discipleship_class=self.discipleship_class,
        )

        with self.assertRaises(IntegrityError):
            DiscipleshipEnrollment.objects.create(
                person=self.person,
                discipleship_class=self.discipleship_class,
            )

    def test_mesma_person_pode_participar_de_outra_turma(self):
        other_class = DiscipleshipClass.objects.create(
            name="Discipulado Futuro",
            teacher=self.teacher,
            start_date=date(2027, 2, 1),
            expected_end_date=date(2027, 4, 30),
            planned_sessions=10,
        )

        DiscipleshipEnrollment.objects.create(person=self.person, discipleship_class=self.discipleship_class)
        DiscipleshipEnrollment.objects.create(person=self.person, discipleship_class=other_class)

        self.assertEqual(DiscipleshipEnrollment.objects.filter(person=self.person).count(), 2)


class DiscipleshipEnrollmentDomainTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.teacher = Person.objects.create(full_name="Professor Dominio", birth_date=date(1980, 1, 1))
        self.person = Person.objects.create(full_name="Aluno Dominio", birth_date=date(1990, 1, 1))
        self.person_without_journey = Person.objects.create(
            full_name="Sem Jornada",
            birth_date=date(1991, 1, 1),
        )
        ChurchJourney.objects.create(person=self.person)
        self.discipleship_class = DiscipleshipClass.objects.create(
            name="Discipulado Dominio",
            teacher=self.teacher,
            start_date=date(2026, 9, 5),
            expected_end_date=date(2026, 11, 28),
            planned_sessions=12,
        )

    def make_class(self, **kwargs):
        data = {
            "name": "Discipulado Extra",
            "teacher": self.teacher,
            "start_date": date(2027, 2, 1),
            "expected_end_date": date(2027, 4, 30),
            "planned_sessions": 10,
        }
        data.update(kwargs)
        return DiscipleshipClass.objects.create(**data)

    def test_person_com_church_journey_pode_ser_matriculada(self):
        enrollment = enroll_person_in_discipleship_class(
            person=self.person,
            discipleship_class=self.discipleship_class,
        )

        self.assertEqual(enrollment.status, DiscipleshipEnrollment.Status.ENROLLED)

    def test_person_sem_church_journey_nao_pode_ser_matriculada(self):
        with self.assertRaises(ChurchJourneyError) as context:
            enroll_person_in_discipleship_class(
                person=self.person_without_journey,
                discipleship_class=self.discipleship_class,
            )

        self.assertEqual(context.exception.code, PERSON_NOT_IN_CHURCH_JOURNEY)

    def test_matricula_em_planned_e_in_progress_permitida(self):
        in_progress = self.make_class(
            name="Em andamento",
            status=DiscipleshipClass.Status.IN_PROGRESS,
        )
        other_person = Person.objects.create(full_name="Outro Aluno", birth_date=date(1992, 1, 1))
        ChurchJourney.objects.create(person=other_person)

        planned_enrollment = enroll_person_in_discipleship_class(
            person=self.person,
            discipleship_class=self.discipleship_class,
        )
        in_progress_enrollment = enroll_person_in_discipleship_class(
            person=other_person,
            discipleship_class=in_progress,
        )

        self.assertEqual(planned_enrollment.status, DiscipleshipEnrollment.Status.ENROLLED)
        self.assertEqual(in_progress_enrollment.status, DiscipleshipEnrollment.Status.ENROLLED)

    def test_matricula_em_completed_e_cancelled_bloqueada(self):
        for closed_status in (DiscipleshipClass.Status.COMPLETED, DiscipleshipClass.Status.CANCELLED):
            closed_class = self.make_class(name=f"Fechada {closed_status}", status=closed_status)
            with self.assertRaises(ChurchJourneyError) as context:
                enroll_person_in_discipleship_class(
                    person=self.person,
                    discipleship_class=closed_class,
                )
            self.assertEqual(context.exception.code, DISCIPLESHIP_CLASS_NOT_OPEN_FOR_ENROLLMENT)

    def test_duplicidade_bloqueada(self):
        enroll_person_in_discipleship_class(person=self.person, discipleship_class=self.discipleship_class)

        with self.assertRaises(ChurchJourneyError) as context:
            enroll_person_in_discipleship_class(person=self.person, discipleship_class=self.discipleship_class)

        self.assertEqual(context.exception.code, DISCIPLESHIP_ENROLLMENT_ALREADY_EXISTS)

    def test_withdraw_enrolled_funciona_e_preserva_relacoes(self):
        enrollment = enroll_person_in_discipleship_class(person=self.person, discipleship_class=self.discipleship_class)
        person_id = self.person.pk
        journey_id = self.person.church_journey.pk
        class_id = self.discipleship_class.pk

        withdraw_discipleship_enrollment(enrollment)

        self.assertEqual(enrollment.status, DiscipleshipEnrollment.Status.WITHDRAWN)
        self.assertEqual(enrollment.withdrawn_at, timezone.localdate())
        self.assertTrue(Person.objects.filter(pk=person_id).exists())
        self.assertTrue(ChurchJourney.objects.filter(pk=journey_id).exists())
        self.assertTrue(DiscipleshipClass.objects.filter(pk=class_id).exists())

    def test_segunda_desistencia_bloqueada(self):
        enrollment = enroll_person_in_discipleship_class(person=self.person, discipleship_class=self.discipleship_class)
        withdraw_discipleship_enrollment(enrollment)

        with self.assertRaises(ChurchJourneyError) as context:
            withdraw_discipleship_enrollment(enrollment)

        self.assertEqual(context.exception.code, INVALID_DISCIPLESHIP_ENROLLMENT_TRANSITION)

    def test_matricula_nao_altera_legado_nem_status(self):
        usuario = self.user_model.objects.create_user(
            username="enrollment.legado",
            password="senha-forte-123",
            person=self.person,
        )
        original_person_status = self.person.status

        enroll_person_in_discipleship_class(person=self.person, discipleship_class=self.discipleship_class)

        usuario.refresh_from_db()
        self.person.refresh_from_db()
        self.assertEqual(self.person.status, original_person_status)
        self.assertEqual(get_church_status(self.person), ChurchStatus.VISITOR)
        self.assertEqual(usuario.status_eclesiastico, self.user_model.StatusEclesiastico.VISITANTE)
        self.assertFalse(usuario.discipulado_concluido)
        self.assertIsNone(usuario.discipulado_concluido_em)


class DiscipleshipEnrollmentApiTests(APITestCase):
    def setUp(self):
        setup_portal_roles()
        self.user_model = get_user_model()
        self.teacher = Person.objects.create(full_name="Professor API Matricula", birth_date=date(1980, 1, 1))
        self.person = Person.objects.create(full_name="Aluno API Matricula", birth_date=date(1990, 1, 1))
        ChurchJourney.objects.create(person=self.person)
        self.discipleship_class = DiscipleshipClass.objects.create(
            name="Discipulado API Matricula",
            teacher=self.teacher,
            start_date=date(2026, 9, 5),
            expected_end_date=date(2026, 11, 28),
            planned_sessions=12,
        )

    def authenticate_role(self, username, group_name):
        usuario = self.user_model.objects.create_user(username=username, password="senha-forte-123")
        usuario.groups.add(Group.objects.get(name=group_name))
        self.client.force_authenticate(usuario)
        return usuario

    def list_url(self, discipleship_class=None):
        return reverse("discipleship-enrollment-list", args=[(discipleship_class or self.discipleship_class).pk])

    def detail_url(self, enrollment):
        return reverse("discipleship-enrollment-detail", args=[self.discipleship_class.pk, enrollment.pk])

    def withdraw_url(self, enrollment):
        return reverse("discipleship-enrollment-withdraw", args=[self.discipleship_class.pk, enrollment.pk])

    def test_get_list_detail_e_post_valido(self):
        self.authenticate_role("secretaria.enrollment.api", SECRETARY_GROUP)

        create_response = self.client.post(
            self.list_url(),
            {"person_id": self.person.pk, "status": DiscipleshipEnrollment.Status.WITHDRAWN},
            format="json",
        )
        enrollment = DiscipleshipEnrollment.objects.get()
        list_response = self.client.get(self.list_url())
        detail_response = self.client.get(self.detail_url(enrollment))

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.json()["status"], DiscipleshipEnrollment.Status.ENROLLED)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)

    def test_post_sem_church_journey_retorna_erro(self):
        self.authenticate_role("secretaria.enrollment.nojourney", SECRETARY_GROUP)
        person = Person.objects.create(full_name="Sem Jornada API", birth_date=date(1991, 1, 1))

        response = self.client.post(self.list_url(), {"person_id": person.pk}, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.json()["code"], PERSON_NOT_IN_CHURCH_JOURNEY)

    def test_post_duplicado_retorna_erro(self):
        self.authenticate_role("secretaria.enrollment.duplicate", SECRETARY_GROUP)
        DiscipleshipEnrollment.objects.create(person=self.person, discipleship_class=self.discipleship_class)

        response = self.client.post(self.list_url(), {"person_id": self.person.pk}, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.json()["code"], DISCIPLESHIP_ENROLLMENT_ALREADY_EXISTS)

    def test_post_em_in_progress_permitido_e_completed_cancelled_bloqueados(self):
        self.authenticate_role("secretaria.enrollment.status", SECRETARY_GROUP)
        in_progress = DiscipleshipClass.objects.create(
            name="Em andamento API",
            teacher=self.teacher,
            start_date=date(2027, 2, 1),
            expected_end_date=date(2027, 4, 30),
            planned_sessions=10,
            status=DiscipleshipClass.Status.IN_PROGRESS,
        )
        completed = DiscipleshipClass.objects.create(
            name="Concluida API",
            teacher=self.teacher,
            start_date=date(2025, 2, 1),
            expected_end_date=date(2025, 4, 30),
            planned_sessions=10,
            status=DiscipleshipClass.Status.COMPLETED,
        )
        other_person = Person.objects.create(full_name="Outro API", birth_date=date(1992, 1, 1))
        ChurchJourney.objects.create(person=other_person)

        allowed = self.client.post(self.list_url(in_progress), {"person_id": self.person.pk}, format="json")
        blocked = self.client.post(self.list_url(completed), {"person_id": other_person.pk}, format="json")

        self.assertEqual(allowed.status_code, status.HTTP_201_CREATED)
        self.assertEqual(blocked.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(blocked.json()["code"], DISCIPLESHIP_CLASS_NOT_OPEN_FOR_ENROLLMENT)

    def test_withdraw_valido_e_invalido(self):
        self.authenticate_role("secretaria.enrollment.withdraw", SECRETARY_GROUP)
        enrollment = DiscipleshipEnrollment.objects.create(person=self.person, discipleship_class=self.discipleship_class)

        first = self.client.post(self.withdraw_url(enrollment))
        second = self.client.post(self.withdraw_url(enrollment))

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(first.json()["status"], DiscipleshipEnrollment.Status.WITHDRAWN)
        self.assertEqual(second.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(second.json()["code"], INVALID_DISCIPLESHIP_ENROLLMENT_TRANSITION)

    def test_delete_nao_e_permitido(self):
        self.authenticate_role("secretaria.enrollment.delete", SECRETARY_GROUP)
        enrollment = DiscipleshipEnrollment.objects.create(person=self.person, discipleship_class=self.discipleship_class)

        response = self.client.delete(self.detail_url(enrollment))

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_permissions_pastor_view_comum_403_professor_sem_bypass(self):
        enrollment = DiscipleshipEnrollment.objects.create(person=self.person, discipleship_class=self.discipleship_class)
        pastor = self.authenticate_role("pastor.enrollment.view", PASTOR_GROUP)
        self.assertEqual(self.client.get(self.list_url()).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.post(self.list_url(), {"person_id": self.person.pk}, format="json").status_code, status.HTTP_403_FORBIDDEN)

        professor_user = self.user_model.objects.create_user(
            username="professor.no.bypass",
            password="senha-forte-123",
            person=self.teacher,
        )
        self.client.force_authenticate(professor_user)
        self.assertEqual(self.client.get(self.list_url()).status_code, status.HTTP_403_FORBIDDEN)

        comum = self.user_model.objects.create_user(username="comum.enrollment", password="senha-forte-123")
        self.client.force_authenticate(comum)
        self.assertEqual(self.client.get(self.detail_url(enrollment)).status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(pastor.has_perm("church_journey.view_discipleshipenrollment"))


class DiscipleshipEnrollmentRolePermissionsTests(TestCase):
    def setUp(self):
        setup_portal_roles()
        self.user_model = get_user_model()

    def make_user_with_role(self, username, group_name):
        usuario = self.user_model.objects.create_user(username=username, password="senha-forte-123")
        usuario.groups.add(Group.objects.get(name=group_name))
        return usuario

    def test_admin_e_secretaria_gerenciam_matriculas(self):
        for group_name in (PORTAL_ADMIN_GROUP, SECRETARY_GROUP):
            usuario = self.make_user_with_role(f"{group_name}.enrollment", group_name)
            self.assertTrue(usuario.has_perm("church_journey.view_discipleshipenrollment"))
            self.assertTrue(usuario.has_perm("church_journey.add_discipleshipenrollment"))
            self.assertTrue(usuario.has_perm("church_journey.withdraw_discipleshipenrollment"))

    def test_pastor_apenas_visualiza_e_comum_nao_tem_acesso(self):
        pastor = self.make_user_with_role("pastor.enrollment.perms", PASTOR_GROUP)
        comum = self.user_model.objects.create_user(username="comum.enrollment.perms", password="senha-forte-123")

        self.assertTrue(pastor.has_perm("church_journey.view_discipleshipenrollment"))
        self.assertFalse(pastor.has_perm("church_journey.add_discipleshipenrollment"))
        self.assertFalse(pastor.has_perm("church_journey.withdraw_discipleshipenrollment"))
        self.assertFalse(comum.has_perm("church_journey.view_discipleshipenrollment"))


class DiscipleshipLessonModelTests(TestCase):
    def setUp(self):
        self.teacher = Person.objects.create(full_name="Professor Aula", birth_date=date(1980, 1, 1))
        self.discipleship_class = DiscipleshipClass.objects.create(
            name="Discipulado Aulas",
            teacher=self.teacher,
            start_date=date(2026, 9, 5),
            expected_end_date=date(2026, 11, 28),
            planned_sessions=2,
        )

    def make_class(self, name, start_date):
        return DiscipleshipClass.objects.create(
            name=name,
            teacher=self.teacher,
            start_date=start_date,
            expected_end_date=date(start_date.year, 11, 28),
            planned_sessions=1,
        )

    def test_criacao_valida_e_default_scheduled(self):
        lesson = DiscipleshipLesson.objects.create(
            discipleship_class=self.discipleship_class,
            title="Identidade em Cristo",
            lesson_date=date(2026, 9, 5),
        )

        self.assertEqual(lesson.discipleship_class, self.discipleship_class)
        self.assertEqual(lesson.status, DiscipleshipLesson.Status.SCHEDULED)

    def test_title_obrigatorio(self):
        lesson = DiscipleshipLesson(
            discipleship_class=self.discipleship_class,
            title="   ",
            lesson_date=date(2026, 9, 5),
        )

        with self.assertRaisesMessage(Exception, "Informe o titulo da aula."):
            lesson.full_clean()

    def test_turma_fk_obrigatoria(self):
        with self.assertRaises(IntegrityError):
            DiscipleshipLesson.objects.create(
                discipleship_class=None,
                title="Sem turma",
                lesson_date=date(2026, 9, 5),
            )

    def test_mesma_turma_mesma_data_bloqueada(self):
        DiscipleshipLesson.objects.create(
            discipleship_class=self.discipleship_class,
            title="Aula 1",
            lesson_date=date(2026, 9, 5),
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            DiscipleshipLesson.objects.create(
                discipleship_class=self.discipleship_class,
                title="Aula duplicada",
                lesson_date=date(2026, 9, 5),
            )

    def test_turmas_diferentes_mesma_data_permitido(self):
        other_class = self.make_class("Outra turma", date(2026, 9, 6))

        DiscipleshipLesson.objects.create(
            discipleship_class=self.discipleship_class,
            title="Aula Turma A",
            lesson_date=date(2026, 9, 5),
        )
        DiscipleshipLesson.objects.create(
            discipleship_class=other_class,
            title="Aula Turma B",
            lesson_date=date(2026, 9, 5),
        )

        self.assertEqual(DiscipleshipLesson.objects.count(), 2)

    def test_planned_sessions_nao_limita_quantidade(self):
        for day in (5, 12, 19):
            DiscipleshipLesson.objects.create(
                discipleship_class=self.discipleship_class,
                title=f"Aula {day}",
                lesson_date=date(2026, 9, day),
            )

        self.assertEqual(self.discipleship_class.planned_sessions, 2)
        self.assertEqual(DiscipleshipLesson.objects.count(), 3)

    def test_aula_cancelada_permanece_no_historico_e_ocupa_data(self):
        lesson = DiscipleshipLesson.objects.create(
            discipleship_class=self.discipleship_class,
            title="Aula cancelada",
            lesson_date=date(2026, 9, 5),
            status=DiscipleshipLesson.Status.CANCELLED,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            DiscipleshipLesson.objects.create(
                discipleship_class=self.discipleship_class,
                title="Nova aula",
                lesson_date=lesson.lesson_date,
            )

        self.assertTrue(DiscipleshipLesson.objects.filter(pk=lesson.pk).exists())


class DiscipleshipLessonDomainTests(TestCase):
    def setUp(self):
        self.teacher = Person.objects.create(full_name="Professor Dominio Aula", birth_date=date(1980, 1, 1))
        self.discipleship_class = DiscipleshipClass.objects.create(
            name="Discipulado Dominio Aula",
            teacher=self.teacher,
            start_date=date(2026, 9, 5),
            expected_end_date=date(2026, 11, 28),
            planned_sessions=1,
        )

    def make_class(self, **kwargs):
        data = {
            "name": "Discipulado Aula Extra",
            "teacher": self.teacher,
            "start_date": date(2027, 2, 1),
            "expected_end_date": date(2027, 4, 30),
            "planned_sessions": 1,
        }
        data.update(kwargs)
        return DiscipleshipClass.objects.create(**data)

    def test_criar_em_planned_e_in_progress(self):
        in_progress = self.make_class(name="Aulas em andamento", status=DiscipleshipClass.Status.IN_PROGRESS)

        planned_lesson = create_discipleship_lesson(
            discipleship_class=self.discipleship_class,
            title="Identidade em Cristo",
            lesson_date=date(2026, 9, 5),
        )
        progress_lesson = create_discipleship_lesson(
            discipleship_class=in_progress,
            title="Palavra de Deus",
            lesson_date=date(2027, 2, 1),
        )

        self.assertEqual(planned_lesson.status, DiscipleshipLesson.Status.SCHEDULED)
        self.assertEqual(progress_lesson.status, DiscipleshipLesson.Status.SCHEDULED)

    def test_bloquear_em_completed_e_cancelled(self):
        for closed_status in (DiscipleshipClass.Status.COMPLETED, DiscipleshipClass.Status.CANCELLED):
            closed_class = self.make_class(name=f"Aula fechada {closed_status}", status=closed_status)

            with self.assertRaises(ChurchJourneyError) as context:
                create_discipleship_lesson(
                    discipleship_class=closed_class,
                    title="Aula fechada",
                    lesson_date=date(2027, 2, 1),
                )

            self.assertEqual(context.exception.code, DISCIPLESHIP_CLASS_NOT_OPEN_FOR_LESSONS)

    def test_editar_titulo_e_data(self):
        lesson = create_discipleship_lesson(
            discipleship_class=self.discipleship_class,
            title="Titulo antigo",
            lesson_date=date(2026, 9, 5),
        )

        update_discipleship_lesson(
            lesson,
            title="Titulo novo",
            lesson_date=date(2026, 9, 12),
        )

        lesson.refresh_from_db()
        self.assertEqual(lesson.title, "Titulo novo")
        self.assertEqual(lesson.lesson_date, date(2026, 9, 12))

    def test_conflito_apos_edicao_de_data(self):
        create_discipleship_lesson(
            discipleship_class=self.discipleship_class,
            title="Aula 1",
            lesson_date=date(2026, 9, 5),
        )
        lesson = create_discipleship_lesson(
            discipleship_class=self.discipleship_class,
            title="Aula 2",
            lesson_date=date(2026, 9, 12),
        )

        with self.assertRaises(ChurchJourneyError) as context:
            update_discipleship_lesson(lesson, lesson_date=date(2026, 9, 5))

        self.assertEqual(context.exception.code, DISCIPLESHIP_LESSON_DATE_CONFLICT)

    def test_cancelar_scheduled_e_preservar_aula(self):
        lesson = create_discipleship_lesson(
            discipleship_class=self.discipleship_class,
            title="Aula para cancelar",
            lesson_date=date(2026, 9, 5),
        )

        cancel_discipleship_lesson(lesson)

        lesson.refresh_from_db()
        self.assertEqual(lesson.status, DiscipleshipLesson.Status.CANCELLED)
        self.assertTrue(DiscipleshipLesson.objects.filter(pk=lesson.pk).exists())

    def test_segundo_cancelamento_bloqueado(self):
        lesson = create_discipleship_lesson(
            discipleship_class=self.discipleship_class,
            title="Aula cancelada",
            lesson_date=date(2026, 9, 5),
        )
        cancel_discipleship_lesson(lesson)

        with self.assertRaises(ChurchJourneyError) as context:
            cancel_discipleship_lesson(lesson)

        self.assertEqual(context.exception.code, INVALID_DISCIPLESHIP_LESSON_TRANSITION)


class DiscipleshipLessonApiTests(APITestCase):
    def setUp(self):
        setup_portal_roles()
        self.user_model = get_user_model()
        self.teacher = Person.objects.create(full_name="Professor API Aula", birth_date=date(1980, 1, 1))
        self.discipleship_class = DiscipleshipClass.objects.create(
            name="Discipulado API Aula",
            teacher=self.teacher,
            start_date=date(2026, 9, 5),
            expected_end_date=date(2026, 11, 28),
            planned_sessions=1,
        )

    def authenticate_role(self, username, group_name):
        usuario = self.user_model.objects.create_user(username=username, password="senha-forte-123")
        usuario.groups.add(Group.objects.get(name=group_name))
        self.client.force_authenticate(usuario)
        return usuario

    def list_url(self, discipleship_class=None):
        return reverse("discipleship-lesson-list", args=[(discipleship_class or self.discipleship_class).pk])

    def detail_url(self, lesson, discipleship_class=None):
        return reverse(
            "discipleship-lesson-detail",
            args=[(discipleship_class or self.discipleship_class).pk, lesson.pk],
        )

    def cancel_url(self, lesson, discipleship_class=None):
        return reverse(
            "discipleship-lesson-cancel",
            args=[(discipleship_class or self.discipleship_class).pk, lesson.pk],
        )

    def test_get_list_detail_post_patch_cancel(self):
        self.authenticate_role("secretaria.lesson.api", SECRETARY_GROUP)

        create_response = self.client.post(
            self.list_url(),
            {
                "title": "  Identidade em Cristo  ",
                "lesson_date": "2026-09-05",
                "status": DiscipleshipLesson.Status.CANCELLED,
            },
            format="json",
        )
        lesson = DiscipleshipLesson.objects.get()
        list_response = self.client.get(self.list_url())
        detail_response = self.client.get(self.detail_url(lesson))
        patch_response = self.client.patch(
            self.detail_url(lesson),
            {"title": "Palavra de Deus", "lesson_date": "2026-09-12", "status": DiscipleshipLesson.Status.CANCELLED},
            format="json",
        )
        cancel_response = self.client.post(self.cancel_url(lesson))

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.json()["title"], "Identidade em Cristo")
        self.assertEqual(create_response.json()["status"], DiscipleshipLesson.Status.SCHEDULED)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.json()["status"], DiscipleshipLesson.Status.SCHEDULED)
        self.assertEqual(cancel_response.status_code, status.HTTP_200_OK)
        self.assertEqual(cancel_response.json()["status"], DiscipleshipLesson.Status.CANCELLED)

    def test_class_id_da_url_e_respeitado(self):
        self.authenticate_role("secretaria.lesson.url", SECRETARY_GROUP)
        other_class = DiscipleshipClass.objects.create(
            name="Outra turma API Aula",
            teacher=self.teacher,
            start_date=date(2027, 2, 1),
            expected_end_date=date(2027, 4, 30),
            planned_sessions=1,
        )

        response = self.client.post(
            self.list_url(other_class),
            {
                "title": "Aula outra turma",
                "lesson_date": "2027-02-01",
                "discipleship_class_id": self.discipleship_class.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["discipleship_class_id"], other_class.pk)

    def test_conflito_de_data_e_status_fechado_retorna_erro_estruturado(self):
        self.authenticate_role("secretaria.lesson.errors", SECRETARY_GROUP)
        DiscipleshipLesson.objects.create(
            discipleship_class=self.discipleship_class,
            title="Aula 1",
            lesson_date=date(2026, 9, 5),
        )
        completed = DiscipleshipClass.objects.create(
            name="Turma concluida aula",
            teacher=self.teacher,
            start_date=date(2025, 2, 1),
            expected_end_date=date(2025, 4, 30),
            planned_sessions=1,
            status=DiscipleshipClass.Status.COMPLETED,
        )

        conflict = self.client.post(
            self.list_url(),
            {"title": "Aula duplicada", "lesson_date": "2026-09-05"},
            format="json",
        )
        closed = self.client.post(
            self.list_url(completed),
            {"title": "Aula fechada", "lesson_date": "2025-02-01"},
            format="json",
        )

        self.assertEqual(conflict.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(conflict.json()["code"], DISCIPLESHIP_LESSON_DATE_CONFLICT)
        self.assertEqual(closed.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(closed.json()["code"], DISCIPLESHIP_CLASS_NOT_OPEN_FOR_LESSONS)

    def test_patch_conflito_cancelamento_invalido_e_delete_405(self):
        self.authenticate_role("secretaria.lesson.more", SECRETARY_GROUP)
        DiscipleshipLesson.objects.create(
            discipleship_class=self.discipleship_class,
            title="Aula 1",
            lesson_date=date(2026, 9, 5),
        )
        lesson = DiscipleshipLesson.objects.create(
            discipleship_class=self.discipleship_class,
            title="Aula 2",
            lesson_date=date(2026, 9, 12),
        )

        conflict = self.client.patch(self.detail_url(lesson), {"lesson_date": "2026-09-05"}, format="json")
        first_cancel = self.client.post(self.cancel_url(lesson))
        second_cancel = self.client.post(self.cancel_url(lesson))
        delete_response = self.client.delete(self.detail_url(lesson))

        self.assertEqual(conflict.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(conflict.json()["code"], DISCIPLESHIP_LESSON_DATE_CONFLICT)
        self.assertEqual(first_cancel.status_code, status.HTTP_200_OK)
        self.assertEqual(second_cancel.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(second_cancel.json()["code"], INVALID_DISCIPLESHIP_LESSON_TRANSITION)
        self.assertEqual(delete_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_permissions_pastor_view_comum_403_professor_sem_bypass(self):
        lesson = DiscipleshipLesson.objects.create(
            discipleship_class=self.discipleship_class,
            title="Aula permissionada",
            lesson_date=date(2026, 9, 5),
        )
        pastor = self.authenticate_role("pastor.lesson.view", PASTOR_GROUP)

        self.assertEqual(self.client.get(self.list_url()).status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.post(self.list_url(), {"title": "Nova", "lesson_date": "2026-09-12"}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.patch(self.detail_url(lesson), {"title": "Editada"}, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(self.client.post(self.cancel_url(lesson)).status_code, status.HTTP_403_FORBIDDEN)

        professor_user = self.user_model.objects.create_user(
            username="professor.lesson.no.bypass",
            password="senha-forte-123",
            person=self.teacher,
        )
        self.client.force_authenticate(professor_user)
        self.assertEqual(self.client.get(self.list_url()).status_code, status.HTTP_403_FORBIDDEN)

        comum = self.user_model.objects.create_user(username="comum.lesson", password="senha-forte-123")
        self.client.force_authenticate(comum)
        self.assertEqual(self.client.get(self.detail_url(lesson)).status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(pastor.has_perm("church_journey.view_discipleshiplesson"))


class DiscipleshipLessonRolePermissionsTests(TestCase):
    def setUp(self):
        setup_portal_roles()
        self.user_model = get_user_model()

    def make_user_with_role(self, username, group_name):
        usuario = self.user_model.objects.create_user(username=username, password="senha-forte-123")
        usuario.groups.add(Group.objects.get(name=group_name))
        return usuario

    def assert_can_manage_lessons(self, usuario):
        self.assertTrue(usuario.has_perm("church_journey.view_discipleshiplesson"))
        self.assertTrue(usuario.has_perm("church_journey.add_discipleshiplesson"))
        self.assertTrue(usuario.has_perm("church_journey.change_discipleshiplesson"))
        self.assertTrue(usuario.has_perm("church_journey.cancel_discipleshiplesson"))

    def test_admin_e_secretaria_gerenciam_aulas(self):
        for group_name in (PORTAL_ADMIN_GROUP, SECRETARY_GROUP):
            usuario = self.make_user_with_role(f"{group_name}.lesson", group_name)
            self.assert_can_manage_lessons(usuario)

    def test_pastor_apenas_visualiza_e_comum_nao_tem_acesso(self):
        pastor = self.make_user_with_role("pastor.lesson.perms", PASTOR_GROUP)
        comum = self.user_model.objects.create_user(username="comum.lesson.perms", password="senha-forte-123")

        self.assertTrue(pastor.has_perm("church_journey.view_discipleshiplesson"))
        self.assertFalse(pastor.has_perm("church_journey.add_discipleshiplesson"))
        self.assertFalse(pastor.has_perm("church_journey.change_discipleshiplesson"))
        self.assertFalse(pastor.has_perm("church_journey.cancel_discipleshiplesson"))
        self.assertFalse(comum.has_perm("church_journey.view_discipleshiplesson"))


class DiscipleshipAttendanceModelTests(TestCase):
    def setUp(self):
        self.teacher = Person.objects.create(full_name="Professor Presenca", birth_date=date(1980, 1, 1))
        self.person = Person.objects.create(full_name="Aluno Presenca", birth_date=date(1990, 1, 1))
        ChurchJourney.objects.create(person=self.person)
        self.discipleship_class = DiscipleshipClass.objects.create(
            name="Discipulado Presenca",
            teacher=self.teacher,
            start_date=date(2026, 8, 1),
            expected_end_date=date(2026, 10, 1),
            planned_sessions=8,
        )
        self.enrollment = DiscipleshipEnrollment.objects.create(
            person=self.person,
            discipleship_class=self.discipleship_class,
            enrolled_at=date(2026, 8, 1),
        )
        self.lesson = DiscipleshipLesson.objects.create(
            discipleship_class=self.discipleship_class,
            title="Vida de oracao",
            lesson_date=timezone.localdate(),
        )
        self.user = get_user_model().objects.create_user(username="recorded.by", password="senha-forte-123")

    def test_criacao_present_absent_justified_recorded_by_e_timestamps(self):
        for attendance_status in (
            DiscipleshipAttendance.Status.PRESENT,
            DiscipleshipAttendance.Status.ABSENT,
            DiscipleshipAttendance.Status.JUSTIFIED,
        ):
            lesson = DiscipleshipLesson.objects.create(
                discipleship_class=self.discipleship_class,
                title=f"Aula {attendance_status}",
                lesson_date=timezone.localdate() - timedelta(days=len(attendance_status)),
            )
            attendance = DiscipleshipAttendance.objects.create(
                enrollment=self.enrollment,
                lesson=lesson,
                status=attendance_status,
                recorded_by=self.user,
            )

            self.assertEqual(attendance.enrollment, self.enrollment)
            self.assertEqual(attendance.lesson, lesson)
            self.assertEqual(attendance.status, attendance_status)
            self.assertEqual(attendance.recorded_by, self.user)
            self.assertIsNotNone(attendance.created_at)
            self.assertIsNotNone(attendance.updated_at)

    def test_unicidade_enrollment_lesson(self):
        DiscipleshipAttendance.objects.create(
            enrollment=self.enrollment,
            lesson=self.lesson,
            status=DiscipleshipAttendance.Status.PRESENT,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            DiscipleshipAttendance.objects.create(
                enrollment=self.enrollment,
                lesson=self.lesson,
                status=DiscipleshipAttendance.Status.ABSENT,
            )


class DiscipleshipAttendanceDomainTests(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.teacher = Person.objects.create(full_name="Professor Chamada", birth_date=date(1980, 1, 1))
        self.person = Person.objects.create(full_name="Maria Chamada", birth_date=date(1990, 1, 1))
        ChurchJourney.objects.create(person=self.person)
        self.discipleship_class = DiscipleshipClass.objects.create(
            name="Discipulado Chamada",
            teacher=self.teacher,
            start_date=date(2026, 8, 1),
            expected_end_date=date(2026, 10, 1),
            planned_sessions=8,
        )
        self.enrollment = DiscipleshipEnrollment.objects.create(
            person=self.person,
            discipleship_class=self.discipleship_class,
            enrolled_at=date(2026, 8, 1),
        )
        self.lesson = DiscipleshipLesson.objects.create(
            discipleship_class=self.discipleship_class,
            title="Aula hoje",
            lesson_date=timezone.localdate(),
        )
        self.actor = self.user_model.objects.create_user(username="attendance.actor", password="senha-forte-123")

    def make_lesson(self, lesson_date, **kwargs):
        data = {
            "discipleship_class": self.discipleship_class,
            "title": f"Aula {lesson_date}",
            "lesson_date": lesson_date,
        }
        data.update(kwargs)
        return DiscipleshipLesson.objects.create(**data)

    def test_registra_present_absent_justified_validos(self):
        for index, attendance_status in enumerate(
            (
                DiscipleshipAttendance.Status.PRESENT,
                DiscipleshipAttendance.Status.ABSENT,
                DiscipleshipAttendance.Status.JUSTIFIED,
            )
        ):
            lesson = self.make_lesson(timezone.localdate() - timedelta(days=index + 1))
            attendance = record_discipleship_attendance(
                enrollment=self.enrollment,
                lesson=lesson,
                status=attendance_status,
                recorded_by=self.actor,
            )
            self.assertEqual(attendance.status, attendance_status)
            self.assertEqual(attendance.recorded_by, self.actor)

    def test_aula_futura_bloqueada_e_aula_hoje_passada_permitidas(self):
        future = self.make_lesson(timezone.localdate() + timedelta(days=1))
        past = self.make_lesson(timezone.localdate() - timedelta(days=1))

        with self.assertRaises(ChurchJourneyError) as context:
            record_discipleship_attendance(
                enrollment=self.enrollment,
                lesson=future,
                status=DiscipleshipAttendance.Status.PRESENT,
            )

        today_attendance = record_discipleship_attendance(
            enrollment=self.enrollment,
            lesson=self.lesson,
            status=DiscipleshipAttendance.Status.PRESENT,
        )
        past_attendance = record_discipleship_attendance(
            enrollment=self.enrollment,
            lesson=past,
            status=DiscipleshipAttendance.Status.ABSENT,
        )

        self.assertEqual(context.exception.code, DISCIPLESHIP_LESSON_NOT_YET_AVAILABLE_FOR_ATTENDANCE)
        self.assertEqual(today_attendance.status, DiscipleshipAttendance.Status.PRESENT)
        self.assertEqual(past_attendance.status, DiscipleshipAttendance.Status.ABSENT)

    def test_aula_cancelada_turma_diferente_status_invalido_bloqueados(self):
        cancelled = self.make_lesson(
            timezone.localdate() - timedelta(days=1),
            status=DiscipleshipLesson.Status.CANCELLED,
        )
        other_class = DiscipleshipClass.objects.create(
            name="Outra turma chamada",
            teacher=self.teacher,
            start_date=date(2026, 8, 1),
            expected_end_date=date(2026, 10, 1),
            planned_sessions=8,
        )
        other_lesson = DiscipleshipLesson.objects.create(
            discipleship_class=other_class,
            title="Outra aula",
            lesson_date=timezone.localdate(),
        )

        with self.assertRaises(ChurchJourneyError) as cancelled_context:
            record_discipleship_attendance(
                enrollment=self.enrollment,
                lesson=cancelled,
                status=DiscipleshipAttendance.Status.PRESENT,
            )
        with self.assertRaises(ChurchJourneyError) as mismatch_context:
            record_discipleship_attendance(
                enrollment=self.enrollment,
                lesson=other_lesson,
                status=DiscipleshipAttendance.Status.PRESENT,
            )
        with self.assertRaises(ChurchJourneyError) as invalid_context:
            record_discipleship_attendance(enrollment=self.enrollment, lesson=self.lesson, status="PENDING")

        self.assertEqual(
            cancelled_context.exception.code,
            CANCELLED_DISCIPLESHIP_LESSON_DOES_NOT_ACCEPT_ATTENDANCE,
        )
        self.assertEqual(mismatch_context.exception.code, DISCIPLESHIP_ATTENDANCE_CLASS_MISMATCH)
        self.assertEqual(invalid_context.exception.code, INVALID_DISCIPLESHIP_ATTENDANCE_STATUS)

    def test_matricula_tardia_e_desistencia_definem_elegibilidade(self):
        late_person = Person.objects.create(full_name="Maria Tardia", birth_date=date(1991, 1, 1))
        withdrawn_person = Person.objects.create(full_name="Joao Desistente", birth_date=date(1992, 1, 1))
        ChurchJourney.objects.create(person=late_person)
        ChurchJourney.objects.create(person=withdrawn_person)
        base_date = timezone.localdate() - timedelta(days=40)
        late_enrollment = DiscipleshipEnrollment.objects.create(
            person=late_person,
            discipleship_class=self.discipleship_class,
            enrolled_at=base_date + timedelta(days=14),
        )
        withdrawn_enrollment = DiscipleshipEnrollment.objects.create(
            person=withdrawn_person,
            discipleship_class=self.discipleship_class,
            enrolled_at=base_date,
            status=DiscipleshipEnrollment.Status.WITHDRAWN,
            withdrawn_at=base_date + timedelta(days=14),
        )
        lessons = {
            offset: self.make_lesson(base_date + timedelta(days=offset))
            for offset in (0, 7, 14, 21)
        }

        self.assertNotIn(late_enrollment, get_eligible_enrollments_for_lesson(lessons[0]))
        self.assertNotIn(late_enrollment, get_eligible_enrollments_for_lesson(lessons[7]))
        self.assertIn(late_enrollment, get_eligible_enrollments_for_lesson(lessons[14]))
        self.assertIn(late_enrollment, get_eligible_enrollments_for_lesson(lessons[21]))
        self.assertIn(withdrawn_enrollment, get_eligible_enrollments_for_lesson(lessons[0]))
        self.assertIn(withdrawn_enrollment, get_eligible_enrollments_for_lesson(lessons[7]))
        self.assertIn(withdrawn_enrollment, get_eligible_enrollments_for_lesson(lessons[14]))
        self.assertNotIn(withdrawn_enrollment, get_eligible_enrollments_for_lesson(lessons[21]))

        with self.assertRaises(ChurchJourneyError) as early_context:
            record_discipleship_attendance(
                enrollment=late_enrollment,
                lesson=lessons[7],
                status=DiscipleshipAttendance.Status.PRESENT,
            )
        with self.assertRaises(ChurchJourneyError) as after_withdraw_context:
            record_discipleship_attendance(
                enrollment=withdrawn_enrollment,
                lesson=lessons[21],
                status=DiscipleshipAttendance.Status.ABSENT,
            )

        self.assertEqual(early_context.exception.code, DISCIPLESHIP_ENROLLMENT_NOT_ELIGIBLE_FOR_LESSON)
        self.assertEqual(after_withdraw_context.exception.code, DISCIPLESHIP_ENROLLMENT_NOT_ELIGIBLE_FOR_LESSON)

    def test_correcao_mantem_mesma_linha_e_nao_cria_absent_automatico(self):
        attendance = record_discipleship_attendance(
            enrollment=self.enrollment,
            lesson=self.lesson,
            status=DiscipleshipAttendance.Status.PRESENT,
        )
        attendance_id = attendance.pk

        attendance = record_discipleship_attendance(
            enrollment=self.enrollment,
            lesson=self.lesson,
            status=DiscipleshipAttendance.Status.ABSENT,
        )
        attendance = record_discipleship_attendance(
            enrollment=self.enrollment,
            lesson=self.lesson,
            status=DiscipleshipAttendance.Status.JUSTIFIED,
        )
        attendance = record_discipleship_attendance(
            enrollment=self.enrollment,
            lesson=self.lesson,
            status=DiscipleshipAttendance.Status.PRESENT,
        )
        empty_lesson = self.make_lesson(timezone.localdate() - timedelta(days=2))

        self.assertEqual(attendance.pk, attendance_id)
        self.assertEqual(DiscipleshipAttendance.objects.filter(enrollment=self.enrollment, lesson=self.lesson).count(), 1)
        self.assertFalse(DiscipleshipAttendance.objects.filter(enrollment=self.enrollment, lesson=empty_lesson).exists())


class DiscipleshipAttendanceApiTests(APITestCase):
    def setUp(self):
        setup_portal_roles()
        self.user_model = get_user_model()
        self.teacher = Person.objects.create(full_name="Professor API Chamada", birth_date=date(1980, 1, 1))
        self.person = Person.objects.create(full_name="Aluno API Chamada", birth_date=date(1990, 1, 1))
        self.assistant_person = Person.objects.create(full_name="Auxiliar API Chamada", birth_date=date(1991, 1, 1))
        ChurchJourney.objects.create(person=self.person)
        self.discipleship_class = DiscipleshipClass.objects.create(
            name="Discipulado API Chamada",
            teacher=self.teacher,
            start_date=date(2026, 8, 1),
            expected_end_date=date(2026, 10, 1),
            planned_sessions=8,
        )
        self.enrollment = DiscipleshipEnrollment.objects.create(
            person=self.person,
            discipleship_class=self.discipleship_class,
            enrolled_at=date(2026, 8, 1),
        )
        self.lesson = DiscipleshipLesson.objects.create(
            discipleship_class=self.discipleship_class,
            title="Aula API Chamada",
            lesson_date=timezone.localdate(),
        )

    def authenticate_role(self, username, group_name):
        usuario = self.user_model.objects.create_user(username=username, password="senha-forte-123")
        usuario.groups.add(Group.objects.get(name=group_name))
        self.client.force_authenticate(usuario)
        return usuario

    def url(self, lesson=None, discipleship_class=None):
        return reverse(
            "discipleship-lesson-attendance",
            args=[(discipleship_class or self.discipleship_class).pk, (lesson or self.lesson).pk],
        )

    def test_get_chamada_e_salvar_corrigir_status(self):
        secretaria = self.authenticate_role("secretaria.attendance.api", SECRETARY_GROUP)

        get_response = self.client.get(self.url())
        first = self.client.post(
            self.url(),
            {"records": [{"enrollment_id": self.enrollment.pk, "status": DiscipleshipAttendance.Status.PRESENT}]},
            format="json",
        )
        second = self.client.post(
            self.url(),
            {"records": [{"enrollment_id": self.enrollment.pk, "status": DiscipleshipAttendance.Status.ABSENT}]},
            format="json",
        )
        third = self.client.post(
            self.url(),
            {"records": [{"enrollment_id": self.enrollment.pk, "status": DiscipleshipAttendance.Status.JUSTIFIED}]},
            format="json",
        )

        attendance = DiscipleshipAttendance.objects.get()
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.json()["summary"]["eligible"], 1)
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(third.status_code, status.HTTP_200_OK)
        self.assertEqual(attendance.status, DiscipleshipAttendance.Status.JUSTIFIED)
        self.assertEqual(attendance.recorded_by, secretaria)
        self.assertEqual(DiscipleshipAttendance.objects.count(), 1)

    def test_batch_parcial_e_batch_invalido_rollback(self):
        self.authenticate_role("secretaria.attendance.batch", SECRETARY_GROUP)
        other_person = Person.objects.create(full_name="Outro Aluno API", birth_date=date(1992, 1, 1))
        ChurchJourney.objects.create(person=other_person)
        other_enrollment = DiscipleshipEnrollment.objects.create(
            person=other_person,
            discipleship_class=self.discipleship_class,
            enrolled_at=date(2026, 8, 1),
        )
        other_class = DiscipleshipClass.objects.create(
            name="Outra turma API Chamada",
            teacher=self.teacher,
            start_date=date(2026, 8, 1),
            expected_end_date=date(2026, 10, 1),
            planned_sessions=8,
        )
        outside_person = Person.objects.create(full_name="Fora Turma API", birth_date=date(1993, 1, 1))
        ChurchJourney.objects.create(person=outside_person)
        outside_enrollment = DiscipleshipEnrollment.objects.create(
            person=outside_person,
            discipleship_class=other_class,
            enrolled_at=date(2026, 8, 1),
        )

        partial = self.client.post(
            self.url(),
            {"records": [{"enrollment_id": self.enrollment.pk, "status": DiscipleshipAttendance.Status.PRESENT}]},
            format="json",
        )
        invalid = self.client.post(
            self.url(),
            {
                "records": [
                    {"enrollment_id": other_enrollment.pk, "status": DiscipleshipAttendance.Status.ABSENT},
                    {"enrollment_id": outside_enrollment.pk, "status": DiscipleshipAttendance.Status.PRESENT},
                ]
            },
            format="json",
        )

        self.assertEqual(partial.status_code, status.HTTP_200_OK)
        self.assertEqual(partial.json()["summary"]["recorded"], 1)
        self.assertEqual(invalid.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(invalid.json()["code"], DISCIPLESHIP_ATTENDANCE_CLASS_MISMATCH)
        self.assertFalse(DiscipleshipAttendance.objects.filter(enrollment=other_enrollment).exists())

    def test_erros_aula_futura_cancelada_matricula_inelegivel_status_invalido_e_delete(self):
        self.authenticate_role("secretaria.attendance.errors", SECRETARY_GROUP)
        future = DiscipleshipLesson.objects.create(
            discipleship_class=self.discipleship_class,
            title="Futura",
            lesson_date=timezone.localdate() + timedelta(days=1),
        )
        cancelled = DiscipleshipLesson.objects.create(
            discipleship_class=self.discipleship_class,
            title="Cancelada",
            lesson_date=timezone.localdate() - timedelta(days=1),
            status=DiscipleshipLesson.Status.CANCELLED,
        )
        late_person = Person.objects.create(full_name="Tardio API", birth_date=date(1995, 1, 1))
        ChurchJourney.objects.create(person=late_person)
        late_enrollment = DiscipleshipEnrollment.objects.create(
            person=late_person,
            discipleship_class=self.discipleship_class,
            enrolled_at=timezone.localdate() + timedelta(days=1),
        )

        future_response = self.client.post(
            self.url(future),
            {"records": [{"enrollment_id": self.enrollment.pk, "status": DiscipleshipAttendance.Status.PRESENT}]},
            format="json",
        )
        cancelled_response = self.client.post(
            self.url(cancelled),
            {"records": [{"enrollment_id": self.enrollment.pk, "status": DiscipleshipAttendance.Status.PRESENT}]},
            format="json",
        )
        ineligible_response = self.client.post(
            self.url(),
            {"records": [{"enrollment_id": late_enrollment.pk, "status": DiscipleshipAttendance.Status.PRESENT}]},
            format="json",
        )
        invalid_status = self.client.post(
            self.url(),
            {"records": [{"enrollment_id": self.enrollment.pk, "status": "PENDING"}]},
            format="json",
        )
        delete_response = self.client.delete(self.url())

        self.assertEqual(future_response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(future_response.json()["code"], DISCIPLESHIP_LESSON_NOT_YET_AVAILABLE_FOR_ATTENDANCE)
        self.assertEqual(cancelled_response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(cancelled_response.json()["code"], CANCELLED_DISCIPLESHIP_LESSON_DOES_NOT_ACCEPT_ATTENDANCE)
        self.assertEqual(ineligible_response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(ineligible_response.json()["code"], DISCIPLESHIP_ENROLLMENT_NOT_ELIGIBLE_FOR_LESSON)
        self.assertEqual(invalid_status.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(invalid_status.json()["code"], INVALID_DISCIPLESHIP_ATTENDANCE_STATUS)
        self.assertEqual(delete_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_permissions_globais_contextuais_professor_e_auxiliar(self):
        admin = self.authenticate_role("admin.attendance", PORTAL_ADMIN_GROUP)
        self.assertEqual(self.client.post(self.url(), {"records": []}, format="json").status_code, status.HTTP_200_OK)

        pastor = self.authenticate_role("pastor.attendance", PASTOR_GROUP)
        self.assertEqual(self.client.get(self.url()).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.post(self.url(), {"records": []}, format="json").status_code, status.HTTP_403_FORBIDDEN)

        teacher_user = self.user_model.objects.create_user(
            username="teacher.contextual",
            password="senha-forte-123",
            person=self.teacher,
        )
        self.client.force_authenticate(teacher_user)
        self.assertEqual(self.client.get(self.url()).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.post(self.url(), {"records": []}, format="json").status_code, status.HTTP_200_OK)

        other_teacher_person = Person.objects.create(full_name="Outro Professor", birth_date=date(1981, 1, 1))
        other_teacher = self.user_model.objects.create_user(
            username="teacher.other",
            password="senha-forte-123",
            person=other_teacher_person,
        )
        self.client.force_authenticate(other_teacher)
        self.assertEqual(self.client.get(self.url()).status_code, status.HTTP_403_FORBIDDEN)

        assistant_user = self.user_model.objects.create_user(
            username="assistant.contextual",
            password="senha-forte-123",
            person=self.assistant_person,
        )
        DiscipleshipClassAssistant.objects.create(
            discipleship_class=self.discipleship_class,
            person=self.assistant_person,
        )
        self.client.force_authenticate(assistant_user)
        self.assertEqual(self.client.get(self.url()).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.post(self.url(), {"records": []}, format="json").status_code, status.HTTP_200_OK)

        unrelated_assistant_person = Person.objects.create(full_name="Auxiliar Nao Relacionado", birth_date=date(1988, 1, 1))
        unrelated_assistant = self.user_model.objects.create_user(
            username="assistant.unrelated",
            password="senha-forte-123",
            person=unrelated_assistant_person,
        )
        self.client.force_authenticate(unrelated_assistant)
        self.assertEqual(self.client.get(self.url()).status_code, status.HTTP_403_FORBIDDEN)

        comum = self.user_model.objects.create_user(username="comum.attendance", password="senha-forte-123")
        self.client.force_authenticate(comum)
        self.assertEqual(self.client.get(self.url()).status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(admin.has_perm("church_journey.change_discipleshipattendance"))


class DiscipleshipAttendanceRolePermissionsTests(TestCase):
    def setUp(self):
        setup_portal_roles()
        self.user_model = get_user_model()

    def make_user_with_role(self, username, group_name):
        usuario = self.user_model.objects.create_user(username=username, password="senha-forte-123")
        usuario.groups.add(Group.objects.get(name=group_name))
        return usuario

    def test_admin_e_secretaria_gerenciam_presencas(self):
        for group_name in (PORTAL_ADMIN_GROUP, SECRETARY_GROUP):
            usuario = self.make_user_with_role(f"{group_name}.attendance", group_name)
            self.assertTrue(usuario.has_perm("church_journey.view_discipleshipattendance"))
            self.assertTrue(usuario.has_perm("church_journey.add_discipleshipattendance"))
            self.assertTrue(usuario.has_perm("church_journey.change_discipleshipattendance"))

    def test_pastor_apenas_visualiza_e_comum_nao_tem_acesso(self):
        pastor = self.make_user_with_role("pastor.attendance.perms", PASTOR_GROUP)
        comum = self.user_model.objects.create_user(username="comum.attendance.perms", password="senha-forte-123")

        self.assertTrue(pastor.has_perm("church_journey.view_discipleshipattendance"))
        self.assertFalse(pastor.has_perm("church_journey.add_discipleshipattendance"))
        self.assertFalse(pastor.has_perm("church_journey.change_discipleshipattendance"))
        self.assertFalse(comum.has_perm("church_journey.view_discipleshipattendance"))
