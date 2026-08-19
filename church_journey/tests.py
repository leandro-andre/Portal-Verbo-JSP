from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from pessoas.models import Person

from .enums import ChurchStatus
from .selectors import (
    get_church_status,
    get_discipleship_completed_at,
    has_completed_discipleship,
    is_legacy_department_eligible,
    is_member,
    is_visitor,
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
