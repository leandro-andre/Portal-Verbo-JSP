from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from pessoas.models import Person


class PersonModelTests(TestCase):
    def test_criacao_valida_de_person(self):
        person = Person.objects.create(
            full_name="Maria Silva",
            preferred_name="Maria",
            birth_date=date(1990, 5, 10),
            email="maria@example.com",
            phone="81999999999",
        )

        self.assertEqual(person.full_name, "Maria Silva")
        self.assertEqual(person.birth_date, date(1990, 5, 10))

    def test_full_name_obrigatorio(self):
        person = Person(full_name="   ", birth_date=date(1990, 5, 10))

        with self.assertRaises(ValidationError):
            person.full_clean()

    def test_birth_date_obrigatorio(self):
        person = Person(full_name="Maria Silva")

        with self.assertRaises(ValidationError):
            person.full_clean()

    def test_status_padrao_active(self):
        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))

        self.assertEqual(person.status, Person.Status.ACTIVE)

    def test_display_name_usa_preferred_name_quando_preenchido(self):
        person = Person(full_name="Maria Silva", preferred_name="Mari", birth_date=date(1990, 5, 10))

        self.assertEqual(person.display_name, "Mari")

    def test_display_name_usa_full_name_sem_preferred_name(self):
        person = Person(full_name="Maria Silva", birth_date=date(1990, 5, 10))

        self.assertEqual(person.display_name, "Maria Silva")

    def test_email_pode_ser_vazio(self):
        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10), email="")

        self.assertEqual(person.email, "")

    def test_phone_pode_ser_vazio(self):
        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10), phone="")

        self.assertEqual(person.phone, "")

    def test_preferred_name_pode_ser_vazio(self):
        person = Person.objects.create(
            full_name="Maria Silva",
            preferred_name="",
            birth_date=date(1990, 5, 10),
        )

        self.assertEqual(person.preferred_name, "")

    def test_person_pode_existir_sem_usuario(self):
        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))

        self.assertFalse(hasattr(person, "usuario"))

    def test_detecta_possivel_duplicidade_por_mesmo_nome_e_mesma_data(self):
        birth_date = date(1990, 5, 10)
        person = Person.objects.create(full_name="Maria Silva", birth_date=birth_date)

        duplicates = Person.objects.possible_duplicates(full_name="Maria Silva", birth_date=birth_date)

        self.assertEqual(list(duplicates), [person])

    def test_busca_de_duplicidade_e_case_insensitive_para_full_name(self):
        birth_date = date(1990, 5, 10)
        person = Person.objects.create(full_name="Maria Silva", birth_date=birth_date)

        duplicates = Person.objects.possible_duplicates(full_name="maria silva", birth_date=birth_date)

        self.assertEqual(list(duplicates), [person])

    def test_nomes_iguais_com_datas_diferentes_nao_sao_duplicidade(self):
        Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))

        duplicates = Person.objects.possible_duplicates(
            full_name="Maria Silva",
            birth_date=date(1991, 5, 10),
        )

        self.assertEqual(list(duplicates), [])

    def test_mesma_data_com_nomes_diferentes_nao_e_duplicidade(self):
        birth_date = date(1990, 5, 10)
        Person.objects.create(full_name="Maria Silva", birth_date=birth_date)

        duplicates = Person.objects.possible_duplicates(full_name="Joao Silva", birth_date=birth_date)

        self.assertEqual(list(duplicates), [])

    def test_duas_pessoas_com_mesmo_nome_e_mesma_data_nao_sao_bloqueadas(self):
        birth_date = date(1990, 5, 10)
        Person.objects.create(full_name="Maria Silva", birth_date=birth_date)
        Person.objects.create(full_name="Maria Silva", birth_date=birth_date)

        self.assertEqual(
            Person.objects.possible_duplicates(full_name="Maria Silva", birth_date=birth_date).count(),
            2,
        )

    def test_normaliza_espacos_em_full_name(self):
        person = Person.objects.create(full_name="  Maria Silva  ", birth_date=date(1990, 5, 10))

        self.assertEqual(person.full_name, "Maria Silva")
