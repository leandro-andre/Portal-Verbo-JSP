from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from pessoas.models import Person


class PersonApiTests(APITestCase):
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

    def test_duplicidade_nao_e_bloqueada(self):
        payload = {"full_name": "Maria Silva", "birth_date": "1990-05-10"}

        first_response = self.client.post(reverse("person-list"), payload, format="json")
        second_response = self.client.post(reverse("person-list"), payload, format="json")

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Person.objects.filter(full_name="Maria Silva").count(), 2)
