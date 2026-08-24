from datetime import date, time

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from departamentos.models import Departamento, DepartamentoMembro
from usuarios.roles import PASTOR_GROUP, PORTAL_ADMIN_GROUP, SECRETARY_GROUP, setup_portal_roles
from worship.models import Weekday, WorshipService, WorshipServiceTemplate
from worship.services import create_worship_service_template, generate_worship_services_for_month


class WorshipApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        setup_portal_roles()
        User = get_user_model()
        cls.admin = User.objects.create_user(username="admin", password="senha")
        cls.secretary = User.objects.create_user(username="secretaria", password="senha")
        cls.pastor = User.objects.create_user(username="pastor", password="senha")
        cls.common = User.objects.create_user(username="comum", password="senha")
        cls.leader = User.objects.create_user(username="lider", password="senha")
        cls.admin.groups.add(Group.objects.get(name=PORTAL_ADMIN_GROUP))
        cls.secretary.groups.add(Group.objects.get(name=SECRETARY_GROUP))
        cls.pastor.groups.add(Group.objects.get(name=PASTOR_GROUP))
        departamento = Departamento.objects.create(nome="Louvor")
        DepartamentoMembro.objects.create(membro=cls.leader, departamento=departamento, papel=DepartamentoMembro.Papel.LIDER)

    def login(self, user):
        self.client.force_login(user)

    def test_admin_manages_templates_and_delete_is_405(self):
        self.login(self.admin)

        response = self.client.post(
            "/api/worship/templates/",
            {"name": "Culto Domingo Manha", "weekday": Weekday.SUNDAY, "time": "10:00"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["weekday_label"], "Domingo")
        template_id = response.json()["id"]

        detail = self.client.get(f"/api/worship/templates/{template_id}/")
        self.assertEqual(detail.status_code, 200)

        updated = self.client.patch(
            f"/api/worship/templates/{template_id}/",
            {"name": "Culto Domingo Noite", "time": "18:00", "active": False},
            content_type="application/json",
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["name"], "Culto Domingo Noite")
        self.assertTrue(updated.json()["active"])

        deactivated = self.client.post(f"/api/worship/templates/{template_id}/deactivate/")
        self.assertEqual(deactivated.status_code, 200)
        self.assertFalse(deactivated.json()["active"])

        reactivated = self.client.post(f"/api/worship/templates/{template_id}/reactivate/")
        self.assertEqual(reactivated.status_code, 200)
        self.assertTrue(reactivated.json()["active"])

        self.assertEqual(self.client.delete(f"/api/worship/templates/{template_id}/").status_code, 405)

    def test_secretary_generates_month_and_generation_is_explicit(self):
        template = create_worship_service_template(name="Culto Domingo Manha", weekday=Weekday.SUNDAY, time=time(10, 0))
        self.login(self.secretary)

        empty_month = self.client.get("/api/worship/services/?year=2026&month=9")
        self.assertEqual(empty_month.status_code, 200)
        self.assertEqual(empty_month.json(), [])
        self.assertFalse(WorshipService.objects.exists())

        generated = self.client.post(
            "/api/worship/services/generate/",
            {"year": 2026, "month": 9},
            content_type="application/json",
        )
        self.assertEqual(generated.status_code, 200)
        self.assertEqual(generated.json(), {"created_count": 4, "existing_count": 0})
        self.assertEqual(WorshipService.objects.filter(template=template).count(), 4)

        generated_again = self.client.post(
            "/api/worship/services/generate/",
            {"year": 2026, "month": 9},
            content_type="application/json",
        )
        self.assertEqual(generated_again.status_code, 200)
        self.assertEqual(generated_again.json(), {"created_count": 0, "existing_count": 4})

    def test_service_update_does_not_accept_derived_fields(self):
        template = create_worship_service_template(name="Culto Domingo Manha", weekday=Weekday.SUNDAY, time=time(10, 0))
        generate_worship_services_for_month(year=2026, month=9)
        service = WorshipService.objects.get(template=template, source_date=date(2026, 9, 6))
        self.login(self.admin)

        response = self.client.patch(
            f"/api/worship/services/{service.pk}/",
            {
                "name": "Culto Ajustado",
                "time": "11:00",
                "kind": "EXTRAORDINARY",
                "status": "CANCELLED",
                "source_date": "2026-09-08",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        service.refresh_from_db()
        self.assertEqual(service.name, "Culto Ajustado")
        self.assertEqual(service.time, time(11, 0))
        self.assertEqual(service.kind, WorshipService.Kind.REGULAR)
        self.assertEqual(service.status, WorshipService.Status.SCHEDULED)
        self.assertEqual(service.source_date, date(2026, 9, 6))

    def test_extraordinary_create_update_cancel_reactivate_and_delete_405(self):
        self.login(self.secretary)

        response = self.client.post(
            "/api/worship/services/extraordinary/",
            {"name": "Conferencia de Fe", "date": "2026-09-19", "time": "19:00", "notes": "Noite especial"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["kind"], "EXTRAORDINARY")
        self.assertIsNone(response.json()["template"])
        service_id = response.json()["id"]

        updated = self.client.patch(
            f"/api/worship/services/{service_id}/",
            {"name": "Conferencia de Fe - Noite 1", "time": "19:30"},
            content_type="application/json",
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["time"], "19:30:00")

        cancelled = self.client.post(f"/api/worship/services/{service_id}/cancel/")
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.json()["status"], "CANCELLED")

        reactivated = self.client.post(f"/api/worship/services/{service_id}/reactivate/")
        self.assertEqual(reactivated.status_code, 200)
        self.assertEqual(reactivated.json()["status"], "SCHEDULED")

        self.assertEqual(self.client.delete(f"/api/worship/services/{service_id}/").status_code, 405)

    def test_pastor_is_view_only(self):
        create_worship_service_template(name="Culto Domingo Manha", weekday=Weekday.SUNDAY, time=time(10, 0))
        self.login(self.pastor)

        self.assertEqual(self.client.get("/api/worship/templates/").status_code, 200)
        response = self.client.post(
            "/api/worship/templates/",
            {"name": "Culto Quinta", "weekday": Weekday.THURSDAY, "time": "20:00"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_common_and_department_leader_do_not_administer_schedule(self):
        for user in (self.common, self.leader):
            self.login(user)
            self.assertEqual(self.client.get("/api/worship/templates/").status_code, 403)
            response = self.client.post(
                "/api/worship/services/generate/",
                {"year": 2026, "month": 9},
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 403)

    def test_unauthenticated_requests_are_forbidden(self):
        self.assertEqual(self.client.get("/api/worship/services/?year=2026&month=9").status_code, 403)
