from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone

from church_journey.models import ChurchJourney, DiscipleshipClass, DiscipleshipEnrollment, Membership
from departamentos.models import Departamento, DepartmentMembership, DepartmentRole
from pessoas.models import Person, PersonUnavailability
from scheduling.models import Schedule
from usuarios.roles import PASTOR_GROUP, PORTAL_ADMIN_GROUP, SECRETARY_GROUP, setup_portal_roles
from worship.models import WorshipService


class SchedulingApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        setup_portal_roles()
        User = get_user_model()
        cls.admin = User.objects.create_user(username="admin", password="senha")
        cls.secretary = User.objects.create_user(username="secretaria", password="senha")
        cls.pastor = User.objects.create_user(username="pastor", password="senha")
        cls.common = User.objects.create_user(username="comum", password="senha")
        cls.leader_user = User.objects.create_user(username="lider", password="senha")
        cls.other_leader_user = User.objects.create_user(username="lider2", password="senha")
        cls.admin.groups.add(Group.objects.get(name=PORTAL_ADMIN_GROUP))
        cls.secretary.groups.add(Group.objects.get(name=SECRETARY_GROUP))
        cls.pastor.groups.add(Group.objects.get(name=PASTOR_GROUP))

    def setUp(self):
        self.person = self.create_member_person("Maria")
        self.leader_person = self.create_member_person("Lider")
        self.other_leader_person = self.create_member_person("Outro Lider")
        self.leader_user.person = self.leader_person
        self.leader_user.save(update_fields=["person"])
        self.other_leader_user.person = self.other_leader_person
        self.other_leader_user.save(update_fields=["person"])
        self.department = Departamento.objects.create(nome="Infantil")
        self.other_department = Departamento.objects.create(nome="Midia")
        self.role = DepartmentRole.objects.create(department=self.department, name="Professor", code="professor", active=True)
        self.manager_role = DepartmentRole.objects.create(
            department=self.department,
            name="Lider",
            code="lider",
            active=True,
            can_manage_schedules=True,
        )
        self.other_manager_role = DepartmentRole.objects.create(
            department=self.other_department,
            name="Lider",
            code="lider",
            active=True,
            can_manage_schedules=True,
        )
        self.department_membership = DepartmentMembership.objects.create(
            person=self.person,
            department=self.department,
            role=self.role,
            status=DepartmentMembership.Status.ACTIVE,
        )
        DepartmentMembership.objects.create(
            person=self.leader_person,
            department=self.department,
            role=self.manager_role,
            status=DepartmentMembership.Status.ACTIVE,
        )
        DepartmentMembership.objects.create(
            person=self.other_leader_person,
            department=self.other_department,
            role=self.other_manager_role,
            status=DepartmentMembership.Status.ACTIVE,
        )
        self.worship_service = WorshipService.objects.create(
            name="Culto Domingo",
            date=timezone.localdate() + timedelta(days=20),
            time=time(10, 0),
            kind=WorshipService.Kind.EXTRAORDINARY,
            status=WorshipService.Status.SCHEDULED,
        )

    def create_member_person(self, name):
        person = Person.objects.create(full_name=name, birth_date=date(1990, 1, 1))
        ChurchJourney.objects.create(person=person, started_at=date(2026, 1, 1))
        teacher = Person.objects.create(full_name=f"Professor {name}", birth_date=date(1980, 1, 1))
        discipleship_class = DiscipleshipClass.objects.create(
            name=f"Discipulado {name}",
            teacher=teacher,
            start_date=date(2026, 1, 1),
            expected_end_date=date(2026, 2, 1),
            planned_sessions=4,
            status=DiscipleshipClass.Status.COMPLETED,
        )
        DiscipleshipEnrollment.objects.create(
            person=person,
            discipleship_class=discipleship_class,
            status=DiscipleshipEnrollment.Status.COMPLETED,
            enrolled_at=date(2026, 1, 1),
            completed_at=date(2026, 2, 1),
        )
        Membership.objects.create(person=person, status=Membership.Status.ACTIVE, member_since=date(2026, 2, 1))
        return person

    def login(self, user):
        self.client.force_login(user)

    def create_schedule_via_api(self):
        response = self.client.post(
            "/api/scheduling/schedules/",
            {"department_id": self.department.pk, "worship_service_id": self.worship_service.pk},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    def test_admin_create_detail_assignment_lifecycle_and_delete_schedule_405(self):
        self.login(self.admin)
        schedule = self.create_schedule_via_api()

        detail = self.client.get(f"/api/scheduling/schedules/{schedule['id']}/")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["department"]["nome"], "Infantil")

        candidates = self.client.get(f"/api/scheduling/schedules/{schedule['id']}/eligible-members/")
        self.assertEqual(candidates.status_code, 200)
        self.assertTrue(any(item["eligible"] for item in candidates.json()))

        assignment = self.client.post(
            f"/api/scheduling/schedules/{schedule['id']}/assignments/",
            {"department_membership_id": self.department_membership.pk},
            content_type="application/json",
        )
        self.assertEqual(assignment.status_code, 201)

        self.assertEqual(self.client.post(f"/api/scheduling/schedules/{schedule['id']}/publish/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/scheduling/schedules/{schedule['id']}/reopen/").status_code, 200)
        self.assertEqual(
            self.client.delete(f"/api/scheduling/schedules/{schedule['id']}/assignments/{assignment.json()['id']}/").status_code,
            204,
        )
        self.assertEqual(self.client.post(f"/api/scheduling/schedules/{schedule['id']}/cancel/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/scheduling/schedules/{schedule['id']}/reactivate/").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/scheduling/schedules/{schedule['id']}/").status_code, 405)

    def test_secretary_manages_and_pastor_is_view_only(self):
        self.login(self.secretary)
        schedule = self.create_schedule_via_api()
        self.login(self.pastor)
        self.assertEqual(self.client.get("/api/scheduling/schedules/").status_code, 200)
        response = self.client.post(
            "/api/scheduling/schedules/",
            {"department_id": self.department.pk, "worship_service_id": self.worship_service.pk},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Schedule.objects.filter(pk=schedule["id"]).exists())

    def test_contextual_leader_only_manages_own_department(self):
        self.login(self.leader_user)
        self.assertEqual(
            self.client.post(
                "/api/scheduling/schedules/",
                {"department_id": self.department.pk, "worship_service_id": self.worship_service.pk},
                content_type="application/json",
            ).status_code,
            201,
        )
        other_worship = WorshipService.objects.create(
            name="Culto Noite",
            date=timezone.localdate() + timedelta(days=21),
            time=time(18, 0),
            kind=WorshipService.Kind.EXTRAORDINARY,
            status=WorshipService.Status.SCHEDULED,
        )
        self.assertEqual(
            self.client.post(
                "/api/scheduling/schedules/",
                {"department_id": self.other_department.pk, "worship_service_id": other_worship.pk},
                content_type="application/json",
            ).status_code,
            403,
        )

    def test_role_without_schedule_flag_and_inactive_membership_cannot_manage(self):
        self.manager_role.can_manage_schedules = False
        self.manager_role.save(update_fields=["can_manage_schedules"])
        self.login(self.leader_user)
        response = self.client.post(
            "/api/scheduling/schedules/",
            {"department_id": self.department.pk, "worship_service_id": self.worship_service.pk},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_candidate_unavailability_does_not_expose_reason(self):
        self.login(self.admin)
        schedule = self.create_schedule_via_api()
        PersonUnavailability.objects.create(
            person=self.person,
            start_date=self.worship_service.date,
            end_date=self.worship_service.date,
            start_time=time(9, 0),
            end_time=time(12, 0),
            reason="Motivo privado",
        )
        response = self.client.get(f"/api/scheduling/schedules/{schedule['id']}/eligible-members/")
        self.assertEqual(response.status_code, 200)
        body = str(response.json())
        self.assertIn("PERSON_UNAVAILABLE_FOR_WORSHIP_SERVICE", body)
        self.assertNotIn("Motivo privado", body)
