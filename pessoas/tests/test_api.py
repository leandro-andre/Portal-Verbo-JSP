from datetime import date, time

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from pessoas.models import Person, PersonUnavailability
from usuarios.roles import PASTOR_GROUP, PORTAL_ADMIN_GROUP, SECRETARY_GROUP, setup_portal_roles


class PersonApiTests(APITestCase):
    def setUp(self):
        setup_portal_roles()
        self.user = get_user_model().objects.create_user(
            username="person.api",
            password="senha-forte-123",
        )
        self.user.groups.add(Group.objects.get(name=PORTAL_ADMIN_GROUP))
        self.client.force_authenticate(self.user)

    def test_get_people_exige_autenticacao(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(reverse("person-list"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_people_retorna_200(self):
        response = self.client.get(reverse("person-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_lista_vazia_funciona(self):
        response = self.client.get(reverse("person-list"))

        self.assertEqual(response.json(), [])

    def test_lista_retorna_pessoas_cadastradas(self):
        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))

        response = self.client.get(reverse("person-list"))

        self.assertEqual(response.json()[0]["id"], person.id)
        self.assertEqual(response.json()[0]["full_name"], "Maria Silva")

    def test_campos_esperados_estao_presentes(self):
        Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))

        response = self.client.get(reverse("person-list"))

        self.assertEqual(
            set(response.json()[0].keys()),
            {
                "id",
                "full_name",
                "preferred_name",
                "display_name",
                "birth_date",
                "email",
                "phone",
                "status",
                "portal_user",
                "has_church_journey",
                "discipleship",
                "created_at",
                "updated_at",
            },
        )

    def test_display_name_e_retornado_corretamente(self):
        Person.objects.create(
            full_name="Maria Silva",
            preferred_name="Mari",
            birth_date=date(1990, 5, 10),
        )

        response = self.client.get(reverse("person-list"))

        self.assertEqual(response.json()[0]["display_name"], "Mari")

    def test_post_cria_person_valida(self):
        response = self.client.post(
            reverse("person-list"),
            {
                "full_name": "Maria Silva",
                "birth_date": "1990-05-10",
                "email": "maria@example.com",
                "phone": "81999999999",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Person.objects.filter(full_name="Maria Silva").exists())

    def test_post_normaliza_celular_com_mascara(self):
        response = self.client.post(
            reverse("person-list"),
            {
                "full_name": "Maria Silva",
                "birth_date": "1990-05-10",
                "phone": "(81) 99644-0827",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["phone"], "81996440827")
        self.assertEqual(Person.objects.get().phone, "81996440827")

    def test_post_rejeita_celular_invalido(self):
        response = self.client.post(
            reverse("person-list"),
            {
                "full_name": "Maria Silva",
                "birth_date": "1990-05-10",
                "phone": "(81) 8644-0827",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone", response.json())

    def test_post_exige_full_name(self):
        response = self.client.post(
            reverse("person-list"),
            {"birth_date": "1990-05-10"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("full_name", response.json())

    def test_post_exige_birth_date(self):
        response = self.client.post(
            reverse("person-list"),
            {"full_name": "Maria Silva"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("birth_date", response.json())

    def test_campos_opcionais_podem_ficar_vazios(self):
        response = self.client.post(
            reverse("person-list"),
            {
                "full_name": "Maria Silva",
                "preferred_name": "",
                "birth_date": "1990-05-10",
                "email": "",
                "phone": "",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["email"], "")
        self.assertEqual(response.json()["phone"], "")

    def test_patch_altera_person(self):
        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))

        response = self.client.patch(
            reverse("person-detail", args=[person.pk]),
            {"preferred_name": "Mari"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        person.refresh_from_db()
        self.assertEqual(person.preferred_name, "Mari")

    def test_patch_valido_retorna_sucesso(self):
        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))

        response = self.client.patch(
            reverse("person-detail", args=[person.pk]),
            {"email": "maria@example.com", "phone": "81999999999"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["email"], "maria@example.com")
        self.assertEqual(response.json()["phone"], "81999999999")

    def test_patch_normaliza_celular_com_mascara(self):
        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))

        response = self.client.patch(
            reverse("person-detail", args=[person.pk]),
            {"phone": "(81) 99644-0827"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        person.refresh_from_db()
        self.assertEqual(person.phone, "81996440827")

    def test_list_search_filtra_por_nome_preferido_e_email(self):
        Person.objects.create(
            full_name="Maria Silva",
            preferred_name="Carminha",
            birth_date=date(1990, 5, 10),
            email="maria@example.com",
        )
        Person.objects.create(full_name="Ana Souza", birth_date=date(1985, 2, 20))

        response = self.client.get(reverse("person-list"), {"q": "carminha"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["display_name"], "Carminha")

    def test_patch_com_nome_e_nascimento_do_proprio_registro_nao_gera_duplicidade(self):
        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))

        response = self.client.patch(
            reverse("person-detail", args=[person.pk]),
            {"full_name": "Maria Silva", "birth_date": "1990-05-10"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_que_colide_com_outra_person_retorna_possivel_duplicidade(self):
        Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))
        person = Person.objects.create(full_name="Ana Souza", birth_date=date(1985, 2, 20))

        response = self.client.patch(
            reverse("person-detail", args=[person.pk]),
            {"full_name": "Maria Silva", "birth_date": "1990-05-10"},
            format="json",
        )
        body = response.json()

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(body["code"], "POSSIBLE_DUPLICATE")
        self.assertEqual(body["candidates"][0]["full_name"], "Maria Silva")
        person.refresh_from_db()
        self.assertEqual(person.full_name, "Ana Souza")

    def test_patch_com_confirmacao_de_duplicidade_permite_alteracao(self):
        Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))
        person = Person.objects.create(full_name="Ana Souza", birth_date=date(1985, 2, 20))

        response = self.client.patch(
            reverse("person-detail", args=[person.pk]),
            {
                "full_name": "Maria Silva",
                "birth_date": "1990-05-10",
                "allow_possible_duplicate": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        person.refresh_from_db()
        self.assertEqual(person.full_name, "Maria Silva")
        self.assertEqual(person.birth_date, date(1990, 5, 10))

    def test_confirmacao_de_duplicidade_no_patch_nao_e_persistida(self):
        person = Person.objects.create(full_name="Ana Souza", birth_date=date(1985, 2, 20))

        response = self.client.patch(
            reverse("person-detail", args=[person.pk]),
            {"allow_possible_duplicate": True, "preferred_name": "Ana"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        person.refresh_from_db()
        self.assertFalse(hasattr(person, "allow_possible_duplicate"))
        self.assertEqual(person.preferred_name, "Ana")

    def test_patch_status_active_para_inactive(self):
        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))

        response = self.client.patch(
            reverse("person-detail", args=[person.pk]),
            {"status": Person.Status.INACTIVE},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        person.refresh_from_db()
        self.assertEqual(person.status, Person.Status.INACTIVE)

    def test_person_continua_existindo_apos_inativacao(self):
        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))

        self.client.patch(
            reverse("person-detail", args=[person.pk]),
            {"status": Person.Status.INACTIVE},
            format="json",
        )

        self.assertTrue(Person.objects.filter(pk=person.pk).exists())

    def test_patch_status_inactive_para_active(self):
        person = Person.objects.create(
            full_name="Maria Silva",
            birth_date=date(1990, 5, 10),
            status=Person.Status.INACTIVE,
        )

        response = self.client.patch(
            reverse("person-detail", args=[person.pk]),
            {"status": Person.Status.ACTIVE},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        person.refresh_from_db()
        self.assertEqual(person.status, Person.Status.ACTIVE)

    def test_delete_person_nao_e_permitido(self):
        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))

        response = self.client.delete(reverse("person-detail", args=[person.pk]))

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(Person.objects.filter(pk=person.pk).exists())

    def test_lista_continua_retornando_person_inactive(self):
        person = Person.objects.create(
            full_name="Maria Silva",
            birth_date=date(1990, 5, 10),
            status=Person.Status.INACTIVE,
        )

        response = self.client.get(reverse("person-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()[0]["id"], person.id)
        self.assertEqual(response.json()[0]["status"], "INACTIVE")

    def test_detalhe_continua_retornando_person_inactive(self):
        person = Person.objects.create(
            full_name="Maria Silva",
            birth_date=date(1990, 5, 10),
            status=Person.Status.INACTIVE,
        )

        response = self.client.get(reverse("person-detail", args=[person.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], "INACTIVE")

    def test_get_detalhe_retorna_person(self):
        person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))

        response = self.client.get(reverse("person-detail", args=[person.pk]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], person.id)

    def test_status_e_serializado_corretamente(self):
        Person.objects.create(
            full_name="Maria Silva",
            birth_date=date(1990, 5, 10),
            status=Person.Status.INACTIVE,
        )

        response = self.client.get(reverse("person-list"))

        self.assertEqual(response.json()[0]["status"], "INACTIVE")

    def test_possivel_duplicidade_sem_confirmacao_nao_cria_person(self):
        Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))
        payload = {"full_name": "Maria Silva", "birth_date": "1990-05-10"}

        response = self.client.post(reverse("person-list"), payload, format="json")
        body = response.json()

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(body["code"], "POSSIBLE_DUPLICATE")
        self.assertEqual(len(body["candidates"]), 1)
        self.assertEqual(body["candidates"][0]["full_name"], "Maria Silva")
        self.assertEqual(Person.objects.filter(full_name="Maria Silva").count(), 1)

    def test_possivel_duplicidade_com_confirmacao_cria_person(self):
        Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))
        payload = {
            "full_name": "Maria Silva",
            "birth_date": "1990-05-10",
            "allow_possible_duplicate": True,
        }

        response = self.client.post(reverse("person-list"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Person.objects.filter(full_name="Maria Silva").count(), 2)

    def test_confirmacao_de_duplicidade_nao_e_campo_do_model(self):
        field_names = {field.name for field in Person._meta.fields}

        self.assertNotIn("allow_possible_duplicate", field_names)

    def test_duas_pessoas_identicas_podem_existir_apos_confirmacao(self):
        payload = {"full_name": "Maria Silva", "birth_date": "1990-05-10"}

        first_response = self.client.post(reverse("person-list"), payload, format="json")
        second_response = self.client.post(
            reverse("person-list"),
            {**payload, "allow_possible_duplicate": True},
            format="json",
        )

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Person.objects.filter(full_name="Maria Silva").count(), 2)

    def test_duplicidade_detecta_nome_case_insensitive(self):
        Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))

        response = self.client.post(
            reverse("person-list"),
            {"full_name": "maria silva", "birth_date": "1990-05-10"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.json()["code"], "POSSIBLE_DUPLICATE")

    def test_data_diferente_nao_gera_duplicidade(self):
        Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))

        response = self.client.post(
            reverse("person-list"),
            {"full_name": "Maria Silva", "birth_date": "1991-05-10"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Person.objects.filter(full_name="Maria Silva").count(), 2)


class PersonUnavailabilityApiTests(APITestCase):
    def setUp(self):
        setup_portal_roles()
        self.user_model = get_user_model()
        self.person = Person.objects.create(full_name="Maria Silva", birth_date=date(1990, 5, 10))
        self.other_person = Person.objects.create(full_name="Ana Souza", birth_date=date(1991, 6, 20))
        self.admin = self.make_user("unavailability.admin", PORTAL_ADMIN_GROUP)
        self.secretary = self.make_user("unavailability.secretary", SECRETARY_GROUP)
        self.pastor = self.make_user("unavailability.pastor", PASTOR_GROUP)
        self.self_user = self.user_model.objects.create_user(
            username="unavailability.self",
            password="senha-forte-123",
            person=self.person,
        )
        self.common = self.user_model.objects.create_user(
            username="unavailability.common",
            password="senha-forte-123",
        )

    def make_user(self, username, group_name):
        user = self.user_model.objects.create_user(username=username, password="senha-forte-123")
        user.groups.add(Group.objects.get(name=group_name))
        return user

    def valid_payload(self):
        return {
            "start_date": "2026-09-10",
            "end_date": "2026-09-10",
            "start_time": "18:00",
            "end_time": "22:00",
            "reason": "Viagem",
        }

    def test_self_service_cria_lista_edita_e_lifecycle(self):
        self.client.force_authenticate(self.self_user)

        create_response = self.client.post(reverse("my-unavailability-list"), self.valid_payload(), format="json")
        unavailability_id = create_response.json()["id"]
        list_response = self.client.get(reverse("my-unavailability-list"))
        update_response = self.client.patch(
            reverse("my-unavailability-detail", args=[unavailability_id]),
            {"reason": "Compromisso"},
            format="json",
        )
        deactivate_response = self.client.post(reverse("my-unavailability-deactivate", args=[unavailability_id]))
        reactivate_response = self.client.post(reverse("my-unavailability-reactivate", args=[unavailability_id]))

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.json()["person"], self.person.pk)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.json()), 1)
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.json()["reason"], "Compromisso")
        self.assertEqual(deactivate_response.json()["status"], PersonUnavailability.Status.INACTIVE)
        self.assertEqual(reactivate_response.json()["status"], PersonUnavailability.Status.ACTIVE)

    def test_self_service_nao_acessa_indisponibilidade_de_outra_person(self):
        other_unavailability = PersonUnavailability.objects.create(
            person=self.other_person,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 10),
        )
        self.client.force_authenticate(self.self_user)

        response = self.client.patch(
            reverse("my-unavailability-detail", args=[other_unavailability.pk]),
            {"reason": "Tentativa"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_e_secretaria_gerenciam_person_sem_usuario(self):
        self.client.force_authenticate(self.secretary)

        response = self.client.post(
            reverse("person-unavailability-list", args=[self.other_person.pk]),
            {"start_date": "2026-09-10", "end_date": "2026-09-15", "reason": "Historico"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(hasattr(self.other_person, "user_account"))
        self.assertEqual(PersonUnavailability.objects.get(person=self.other_person).reason, "Historico")

        self.client.force_authenticate(self.admin)
        admin_list = self.client.get(reverse("person-unavailability-list", args=[self.other_person.pk]))
        self.assertEqual(admin_list.status_code, status.HTTP_200_OK)

    def test_pastor_visualiza_mas_nao_gerencia(self):
        PersonUnavailability.objects.create(
            person=self.person,
            start_date=date(2026, 9, 10),
            end_date=date(2026, 9, 10),
            reason="Privado",
        )
        self.client.force_authenticate(self.pastor)

        list_response = self.client.get(reverse("person-unavailability-list", args=[self.person.pk]))
        post_response = self.client.post(
            reverse("person-unavailability-list", args=[self.person.pk]),
            self.valid_payload(),
            format="json",
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.json()[0]["reason"], "Privado")
        self.assertEqual(post_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_comum_sem_person_nao_possui_self_service_nem_admin(self):
        self.client.force_authenticate(self.common)

        self.assertEqual(self.client.get(reverse("my-unavailability-list")).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            self.client.get(reverse("person-unavailability-list", args=[self.person.pk])).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_api_valida_regras_e_overlap(self):
        self.client.force_authenticate(self.self_user)

        invalid_time = self.client.post(
            reverse("my-unavailability-list"),
            {
                "start_date": "2026-09-10",
                "end_date": "2026-09-15",
                "start_time": "18:00",
                "end_time": "22:00",
            },
            format="json",
        )
        valid = self.client.post(reverse("my-unavailability-list"), self.valid_payload(), format="json")
        overlap = self.client.post(
            reverse("my-unavailability-list"),
            {
                "start_date": "2026-09-10",
                "end_date": "2026-09-10",
                "start_time": "19:00",
                "end_time": "21:00",
            },
            format="json",
        )
        adjacent = self.client.post(
            reverse("my-unavailability-list"),
            {
                "start_date": "2026-09-10",
                "end_date": "2026-09-10",
                "start_time": "22:00",
                "end_time": "23:00",
            },
            format="json",
        )

        self.assertEqual(invalid_time.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(invalid_time.json()["code"], "UNAVAILABILITY_TIME_REQUIRES_SINGLE_DAY")
        self.assertEqual(valid.status_code, status.HTTP_201_CREATED)
        self.assertEqual(overlap.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(overlap.json()["code"], "UNAVAILABILITY_OVERLAP")
        self.assertEqual(adjacent.status_code, status.HTTP_201_CREATED)

    def test_inactive_nao_bloqueia_nova_criacao(self):
        self.client.force_authenticate(self.self_user)
        first = self.client.post(reverse("my-unavailability-list"), self.valid_payload(), format="json")
        self.client.post(reverse("my-unavailability-deactivate", args=[first.json()["id"]]))

        second = self.client.post(reverse("my-unavailability-list"), self.valid_payload(), format="json")

        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
