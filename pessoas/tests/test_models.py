from datetime import date, time

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from pessoas.availability import (
    INVALID_UNAVAILABILITY_DATE_RANGE,
    INVALID_UNAVAILABILITY_TIME_RANGE,
    UNAVAILABILITY_OVERLAP,
    UNAVAILABILITY_TIME_REQUIRES_SINGLE_DAY,
    UnavailabilityError,
    create_person_unavailability,
    deactivate_unavailability,
    get_person_availability,
    is_person_available,
)
from pessoas.models import Person, PersonUnavailability


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

        self.assertFalse(hasattr(person, "user_account"))

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

    def test_usuario_pode_se_relacionar_a_person(self):
        from django.contrib.auth import get_user_model

        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))
        usuario = get_user_model().objects.create_user(
            username="maria",
            password="senha-forte-123",
            person=person,
        )

        self.assertEqual(usuario.person, person)
        self.assertEqual(person.user_account, usuario)

    def test_person_nao_pode_estar_associada_a_dois_usuarios(self):
        from django.contrib.auth import get_user_model

        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))
        get_user_model().objects.create_user(username="maria", password="senha-forte-123", person=person)

        with self.assertRaises(IntegrityError):
            get_user_model().objects.create_user(username="maria2", password="senha-forte-123", person=person)

    def test_usuario_pode_existir_sem_person_nesta_fase(self):
        from django.contrib.auth import get_user_model

        usuario = get_user_model().objects.create_user(username="visitante", password="senha-forte-123")

        self.assertIsNone(usuario.person)

    def test_dados_de_person_independem_da_autenticacao(self):
        from django.contrib.auth import get_user_model

        person = Person.objects.create(
            full_name="Maria Silva",
            preferred_name="Mari",
            birth_date=date(1990, 5, 10),
            email="maria.person@example.com",
            phone="81999999999",
        )
        usuario = get_user_model().objects.create_user(
            username="maria",
            password="senha-forte-123",
            first_name="Maria Usuario",
            email="maria.user@example.com",
            person=person,
        )

        self.assertEqual(usuario.email, "maria.user@example.com")
        self.assertEqual(usuario.person.email, "maria.person@example.com")

    def test_deletar_usuario_nao_apaga_person(self):
        from django.contrib.auth import get_user_model

        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))
        usuario = get_user_model().objects.create_user(
            username="maria",
            password="senha-forte-123",
            person=person,
        )

        usuario.delete()

        self.assertTrue(Person.objects.filter(pk=person.pk).exists())

    def test_deletar_person_desvincula_usuario_com_set_null(self):
        from django.contrib.auth import get_user_model

        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))
        usuario = get_user_model().objects.create_user(
            username="maria",
            password="senha-forte-123",
            person=person,
        )

        person.delete()
        usuario.refresh_from_db()

        self.assertIsNone(usuario.person)

    def test_usuario_display_name_usa_person_quando_vinculada(self):
        from django.contrib.auth import get_user_model

        person = Person.objects.create(
            full_name="Maria Silva",
            preferred_name="Mari",
            birth_date=date(1990, 5, 10),
        )
        usuario = get_user_model().objects.create_user(
            username="maria",
            password="senha-forte-123",
            first_name="Legado",
            person=person,
        )

        self.assertEqual(usuario.display_name, "Mari")


class PersonUnavailabilityModelTests(TestCase):
    def setUp(self):
        self.person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))
        self.other_person = Person.objects.create(full_name="Ana Souza", birth_date=date(1991, 6, 20))

    def test_cria_indisponibilidade_de_um_dia(self):
        unavailability = create_person_unavailability(
            person=self.person,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 10),
        )

        self.assertEqual(unavailability.person, self.person)
        self.assertEqual(unavailability.status, PersonUnavailability.Status.ACTIVE)
        self.assertTrue(unavailability.is_full_day)

    def test_cria_periodo_de_varios_dias_sem_horario(self):
        unavailability = create_person_unavailability(
            person=self.person,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 15),
        )

        self.assertEqual(unavailability.end_date, date(2026, 9, 15))

    def test_cria_faixa_horaria_em_um_dia(self):
        unavailability = create_person_unavailability(
            person=self.person,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 10),
            start_time=time(18, 0),
            end_time=time(22, 0),
        )

        self.assertEqual(unavailability.start_time, time(18, 0))
        self.assertEqual(unavailability.end_time, time(22, 0))

    def test_valida_datas_e_horarios(self):
        cases = [
            (
                {"start_date": date(2026, 9, 11), "end_date": date(2026, 9, 10)},
                INVALID_UNAVAILABILITY_DATE_RANGE,
            ),
            (
                {"start_date": date(2026, 9, 10), "end_date": date(2026, 9, 10), "start_time": time(18, 0)},
                INVALID_UNAVAILABILITY_TIME_RANGE,
            ),
            (
                {
                    "start_date": date(2026, 9, 10),
                    "end_date": date(2026, 9, 15),
                    "start_time": time(18, 0),
                    "end_time": time(22, 0),
                },
                UNAVAILABILITY_TIME_REQUIRES_SINGLE_DAY,
            ),
            (
                {
                    "start_date": date(2026, 9, 10),
                    "end_date": date(2026, 9, 10),
                    "start_time": time(18, 0),
                    "end_time": time(18, 0),
                },
                INVALID_UNAVAILABILITY_TIME_RANGE,
            ),
        ]

        for payload, code in cases:
            with self.subTest(code=code):
                with self.assertRaises(UnavailabilityError) as ctx:
                    create_person_unavailability(person=self.person, **payload)
                self.assertEqual(ctx.exception.code, code)

    def test_overlap_periodo_integral_e_horario(self):
        create_person_unavailability(
            person=self.person,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 15),
        )

        with self.assertRaises(UnavailabilityError) as ctx:
            create_person_unavailability(
                person=self.person,
                start_date=date(2026, 9, 12),
                end_date=date(2026, 9, 12),
                start_time=time(18, 0),
                end_time=time(20, 0),
            )

        self.assertEqual(ctx.exception.code, UNAVAILABILITY_OVERLAP)

    def test_overlap_horario_real_bloqueia_e_adjacente_permite(self):
        create_person_unavailability(
            person=self.person,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 10),
            start_time=time(18, 0),
            end_time=time(20, 0),
        )

        with self.assertRaises(UnavailabilityError):
            create_person_unavailability(
                person=self.person,
                start_date=date(2026, 9, 10),
                end_date=date(2026, 9, 10),
                start_time=time(19, 0),
                end_time=time(21, 0),
            )

        adjacent = create_person_unavailability(
            person=self.person,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 10),
            start_time=time(20, 0),
            end_time=time(22, 0),
        )

        self.assertEqual(adjacent.start_time, time(20, 0))

    def test_inactive_e_outra_person_nao_conflitam(self):
        inactive = create_person_unavailability(
            person=self.person,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 12),
        )
        deactivate_unavailability(inactive)

        self.assertTrue(
            create_person_unavailability(
                person=self.person,
                start_date=date(2026, 9, 10),
                end_date=date(2026, 9, 12),
            )
        )
        self.assertTrue(
            create_person_unavailability(
                person=self.other_person,
                start_date=date(2026, 9, 10),
                end_date=date(2026, 9, 12),
            )
        )

    def test_selectors_de_disponibilidade(self):
        self.assertTrue(is_person_available(self.person, date(2026, 9, 10)))
        create_person_unavailability(
            person=self.person,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 10),
            start_time=time(18, 0),
            end_time=time(22, 0),
        )

        self.assertFalse(is_person_available(self.person, date(2026, 9, 10)))
        self.assertTrue(is_person_available(self.person, date(2026, 9, 10), time(10, 0)))
        self.assertFalse(is_person_available(self.person, date(2026, 9, 10), time(19, 0)))
        self.assertTrue(is_person_available(self.person, date(2026, 9, 11)))
        self.assertFalse(get_person_availability(self.person, date(2026, 9, 10)).available)
