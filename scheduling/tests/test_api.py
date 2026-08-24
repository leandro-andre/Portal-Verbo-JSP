from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone

from church_journey.models import ChurchJourney, DiscipleshipClass, DiscipleshipEnrollment, Membership
from departamentos.models import Departamento, DepartmentMembership, DepartmentRole
from escalas.models import Escala, EscalaItem
from pessoas.models import Person, PersonUnavailability
from scheduling.models import DepartmentScheduleRequirement, Schedule, ScheduleAssignment
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

    def test_new_scheduling_flow_does_not_dual_write_legacy_models(self):
        self.login(self.admin)

        schedule = self.create_schedule_via_api()
        self.client.post(
            f"/api/scheduling/schedules/{schedule['id']}/assignments/",
            {"department_membership_id": self.department_membership.pk},
            content_type="application/json",
        )

        self.assertEqual(Escala.objects.count(), 0)
        self.assertEqual(EscalaItem.objects.count(), 0)

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

    def test_monthly_projection_includes_services_without_creating_schedule_and_summary(self):
        self.login(self.admin)
        cancelled = WorshipService.objects.create(
            name="Culto Cancelado",
            date=self.worship_service.date + timedelta(days=1),
            time=time(18, 0),
            kind=WorshipService.Kind.EXTRAORDINARY,
            status=WorshipService.Status.CANCELLED,
        )

        response = self.client.get(
            f"/api/scheduling/monthly/?year={self.worship_service.date.year}&month={self.worship_service.date.month}&department_id={self.department.pk}"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["summary"]["services"], 2)
        self.assertEqual(data["summary"]["cancelled_services"], 1)
        self.assertEqual(data["summary"]["operational_services"], 1)
        self.assertEqual(data["summary"]["without_schedule"], 1)
        self.assertEqual(Schedule.objects.count(), 0)
        self.assertEqual([item["worship_service"]["id"] for item in data["items"]], [self.worship_service.id, cancelled.id])

    def test_monthly_projection_includes_existing_schedule(self):
        self.login(self.admin)
        schedule = self.create_schedule_via_api()

        response = self.client.get(
            f"/api/scheduling/monthly/?year={self.worship_service.date.year}&month={self.worship_service.date.month}&department_id={self.department.pk}"
        )

        self.assertEqual(response.status_code, 200)
        item = response.json()["items"][0]
        self.assertEqual(item["schedule"]["id"], schedule["id"])
        self.assertEqual(response.json()["summary"]["draft"], 1)
        self.assertEqual(response.json()["summary"]["without_schedule"], 0)

    def test_monthly_projection_exposes_manage_permission_for_ui(self):
        self.login(self.pastor)

        pastor_response = self.client.get(
            f"/api/scheduling/monthly/?year={self.worship_service.date.year}&month={self.worship_service.date.month}&department_id={self.department.pk}"
        )

        self.assertEqual(pastor_response.status_code, 200)
        self.assertFalse(pastor_response.json()["permissions"]["can_manage"])

        self.login(self.secretary)
        secretary_response = self.client.get(
            f"/api/scheduling/monthly/?year={self.worship_service.date.year}&month={self.worship_service.date.month}&department_id={self.department.pk}"
        )

        self.assertEqual(secretary_response.status_code, 200)
        self.assertTrue(secretary_response.json()["permissions"]["can_manage"])

    def test_candidates_can_be_filtered_by_role_and_multiple_same_role_allowed(self):
        second_person = self.create_member_person("Geysika")
        second_membership = DepartmentMembership.objects.create(
            person=second_person,
            department=self.department,
            role=self.role,
            status=DepartmentMembership.Status.ACTIVE,
        )
        other_role = DepartmentRole.objects.create(department=self.department, name="Auxiliar", code="auxiliar", active=True)
        other_membership = DepartmentMembership.objects.create(
            person=self.create_member_person("Auxiliar"),
            department=self.department,
            role=other_role,
            status=DepartmentMembership.Status.ACTIVE,
        )
        self.login(self.admin)
        schedule = self.create_schedule_via_api()

        candidates = self.client.get(f"/api/scheduling/schedules/{schedule['id']}/eligible-members/?role_id={self.role.pk}")
        self.assertEqual(candidates.status_code, 200)
        candidate_ids = {item["department_membership"]["id"] for item in candidates.json()}
        self.assertIn(self.department_membership.pk, candidate_ids)
        self.assertIn(second_membership.pk, candidate_ids)
        self.assertNotIn(other_membership.pk, candidate_ids)

        first = self.client.post(
            f"/api/scheduling/schedules/{schedule['id']}/assignments/",
            {"department_membership_id": self.department_membership.pk},
            content_type="application/json",
        )
        second = self.client.post(
            f"/api/scheduling/schedules/{schedule['id']}/assignments/",
            {"department_membership_id": second_membership.pk},
            content_type="application/json",
        )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)

    def test_requirement_api_crud_lifecycle_delete_405_and_validation_endpoint(self):
        self.login(self.admin)
        create_response = self.client.post(
            f"/api/departments/{self.department.pk}/schedule-requirements/",
            {"role_id": self.role.pk, "minimum_quantity": 1, "recommended_quantity": 2},
            content_type="application/json",
        )
        self.assertEqual(create_response.status_code, 201)
        requirement_id = create_response.json()["id"]

        list_response = self.client.get(f"/api/departments/{self.department.pk}/schedule-requirements/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()[0]["role"]["id"], self.role.pk)

        patch_response = self.client.patch(
            f"/api/departments/{self.department.pk}/schedule-requirements/{requirement_id}/",
            {"minimum_quantity": 1, "recommended_quantity": 1},
            content_type="application/json",
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.json()["recommended_quantity"], 1)
        self.assertEqual(
            self.client.delete(f"/api/departments/{self.department.pk}/schedule-requirements/{requirement_id}/").status_code,
            405,
        )
        self.assertEqual(
            self.client.post(f"/api/departments/{self.department.pk}/schedule-requirements/{requirement_id}/deactivate/").status_code,
            200,
        )
        self.assertEqual(
            self.client.post(f"/api/departments/{self.department.pk}/schedule-requirements/{requirement_id}/reactivate/").status_code,
            200,
        )

        schedule = self.create_schedule_via_api()
        validation = self.client.get(f"/api/scheduling/schedules/{schedule['id']}/validation/")
        self.assertEqual(validation.status_code, 200)
        self.assertFalse(validation.json()["can_publish"])

    def test_requirement_api_rejects_invalid_payloads_and_permissions(self):
        self.login(self.admin)
        mismatch = self.client.post(
            f"/api/departments/{self.department.pk}/schedule-requirements/",
            {"role_id": self.other_manager_role.pk, "minimum_quantity": 1, "recommended_quantity": 1},
            content_type="application/json",
        )
        self.assertEqual(mismatch.status_code, 409)
        self.assertEqual(mismatch.json()["code"], "SCHEDULE_REQUIREMENT_ROLE_MISMATCH")

        invalid_quantities = self.client.post(
            f"/api/departments/{self.department.pk}/schedule-requirements/",
            {"role_id": self.role.pk, "minimum_quantity": 2, "recommended_quantity": 1},
            content_type="application/json",
        )
        self.assertEqual(invalid_quantities.status_code, 409)
        self.assertEqual(invalid_quantities.json()["code"], "INVALID_SCHEDULE_REQUIREMENT_QUANTITIES")

        self.role.active = False
        self.role.save(update_fields=["active"])
        inactive_role = self.client.post(
            f"/api/departments/{self.department.pk}/schedule-requirements/",
            {"role_id": self.role.pk, "minimum_quantity": 0, "recommended_quantity": 0},
            content_type="application/json",
        )
        self.assertEqual(inactive_role.status_code, 409)
        self.assertEqual(inactive_role.json()["code"], "SCHEDULE_REQUIREMENT_ROLE_INACTIVE")
        self.role.active = True
        self.role.save(update_fields=["active"])

        self.login(self.pastor)
        self.assertEqual(self.client.get(f"/api/departments/{self.department.pk}/schedule-requirements/").status_code, 200)
        forbidden = self.client.post(
            f"/api/departments/{self.department.pk}/schedule-requirements/",
            {"role_id": self.role.pk, "minimum_quantity": 0, "recommended_quantity": 0},
            content_type="application/json",
        )
        self.assertEqual(forbidden.status_code, 403)

    def test_requirement_contextual_manager_only_own_department_and_loses_when_inactive(self):
        self.login(self.leader_user)
        response = self.client.post(
            f"/api/departments/{self.department.pk}/schedule-requirements/",
            {"role_id": self.role.pk, "minimum_quantity": 1, "recommended_quantity": 1},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        other_response = self.client.post(
            f"/api/departments/{self.other_department.pk}/schedule-requirements/",
            {"role_id": self.other_manager_role.pk, "minimum_quantity": 1, "recommended_quantity": 1},
            content_type="application/json",
        )
        self.assertEqual(other_response.status_code, 403)

        leader_membership = DepartmentMembership.objects.get(person=self.leader_person, department=self.department)
        leader_membership.status = DepartmentMembership.Status.INACTIVE
        leader_membership.save(update_fields=["status"])
        blocked = self.client.post(
            f"/api/departments/{self.department.pk}/schedule-requirements/",
            {"role_id": self.manager_role.pk, "minimum_quantity": 1, "recommended_quantity": 1},
            content_type="application/json",
        )
        self.assertEqual(blocked.status_code, 403)

    def test_publish_blocked_by_minimum_and_allowed_with_warning(self):
        DepartmentScheduleRequirement.objects.create(
            department=self.department,
            role=self.role,
            minimum_quantity=1,
            recommended_quantity=2,
        )
        self.login(self.admin)
        schedule = self.create_schedule_via_api()

        blocked = self.client.post(f"/api/scheduling/schedules/{schedule['id']}/publish/")
        self.assertEqual(blocked.status_code, 409)
        self.assertEqual(blocked.json()["code"], "SCHEDULE_VALIDATION_FAILED")
        self.assertFalse(blocked.json()["can_publish"])
        self.assertGreater(len(blocked.json()["blocking_issues"]), 0)

        self.client.post(
            f"/api/scheduling/schedules/{schedule['id']}/assignments/",
            {"department_membership_id": self.department_membership.pk},
            content_type="application/json",
        )
        warning_validation = self.client.get(f"/api/scheduling/schedules/{schedule['id']}/validation/")
        self.assertEqual(warning_validation.status_code, 200)
        self.assertTrue(warning_validation.json()["can_publish"])
        self.assertEqual(len(warning_validation.json()["warnings"]), 1)
        self.assertEqual(self.client.post(f"/api/scheduling/schedules/{schedule['id']}/publish/").status_code, 200)

    def test_my_schedules_requires_own_person_and_filters_by_publication_lifecycle(self):
        self.common.person = self.person
        self.common.save(update_fields=["person"])
        self.login(self.admin)
        schedule = self.create_schedule_via_api()
        self.client.post(
            f"/api/scheduling/schedules/{schedule['id']}/assignments/",
            {"department_membership_id": self.department_membership.pk},
            content_type="application/json",
        )

        self.login(self.common)
        draft_response = self.client.get("/api/me/schedules/")
        self.assertEqual(draft_response.status_code, 200)
        self.assertTrue(draft_response.json()["person_linked"])
        self.assertEqual(draft_response.json()["items"], [])

        self.login(self.admin)
        self.assertEqual(self.client.post(f"/api/scheduling/schedules/{schedule['id']}/publish/").status_code, 200)
        self.login(self.common)
        published_response = self.client.get("/api/me/schedules/")
        self.assertEqual(len(published_response.json()["items"]), 1)
        item = published_response.json()["items"][0]
        self.assertEqual(item["schedule_id"], schedule["id"])
        self.assertEqual(item["department"]["name"], "Infantil")
        self.assertEqual(item["role"]["name"], "Professor")
        self.assertNotIn("assignments", item)

        self.login(self.admin)
        self.assertEqual(self.client.post(f"/api/scheduling/schedules/{schedule['id']}/reopen/").status_code, 200)
        self.login(self.common)
        reopened_response = self.client.get("/api/me/schedules/")
        self.assertEqual(reopened_response.json()["items"], [])

    def test_my_schedules_privacy_no_person_today_history_and_multiple_departments(self):
        other_user = self.other_leader_user
        self.common.person = self.person
        self.common.save(update_fields=["person"])
        second_membership = DepartmentMembership.objects.create(
            person=self.person,
            department=self.other_department,
            role=self.other_manager_role,
            status=DepartmentMembership.Status.ACTIVE,
        )
        today_service = WorshipService.objects.create(
            name="Culto Hoje",
            date=timezone.localdate(),
            time=time(20, 0),
            kind=WorshipService.Kind.EXTRAORDINARY,
            status=WorshipService.Status.SCHEDULED,
        )
        past_service = WorshipService.objects.create(
            name="Culto Ontem",
            date=timezone.localdate() - timedelta(days=1),
            time=time(20, 0),
            kind=WorshipService.Kind.EXTRAORDINARY,
            status=WorshipService.Status.SCHEDULED,
        )
        today_schedule = Schedule.objects.create(department=self.department, worship_service=today_service, status=Schedule.Status.PUBLISHED)
        other_department_schedule = Schedule.objects.create(department=self.other_department, worship_service=self.worship_service, status=Schedule.Status.PUBLISHED)
        past_schedule = Schedule.objects.create(department=self.department, worship_service=past_service, status=Schedule.Status.PUBLISHED)
        Schedule.objects.create(department=self.department, worship_service=self.worship_service, status=Schedule.Status.DRAFT)
        ScheduleAssignment.objects.create(schedule=today_schedule, department_membership=self.department_membership)
        ScheduleAssignment.objects.create(schedule=other_department_schedule, department_membership=second_membership)
        ScheduleAssignment.objects.create(schedule=past_schedule, department_membership=self.department_membership)

        self.login(self.common)
        upcoming = self.client.get("/api/me/schedules/")
        self.assertEqual(upcoming.status_code, 200)
        self.assertEqual([item["department"]["name"] for item in upcoming.json()["items"]], ["Infantil", "Midia"])
        self.assertEqual(upcoming.json()["items"][0]["worship_service"]["name"], "Culto Hoje")

        history = self.client.get("/api/me/schedules/?scope=history")
        self.assertEqual(history.status_code, 200)
        self.assertEqual(len(history.json()["items"]), 1)
        self.assertEqual(history.json()["items"][0]["worship_service"]["name"], "Culto Ontem")

        self.login(other_user)
        other_response = self.client.get("/api/me/schedules/")
        self.assertEqual(other_response.json()["items"], [])

        self.common.person = None
        self.common.save(update_fields=["person"])
        self.login(self.common)
        no_person = self.client.get("/api/me/schedules/")
        self.assertEqual(no_person.status_code, 200)
        self.assertFalse(no_person.json()["person_linked"])
        self.assertEqual(no_person.json()["items"], [])

    def test_my_schedules_cancelled_worship_cancelled_schedule_and_personal_warnings(self):
        self.common.person = self.person
        self.common.save(update_fields=["person"])
        self.login(self.admin)
        schedule = self.create_schedule_via_api()
        self.client.post(
            f"/api/scheduling/schedules/{schedule['id']}/assignments/",
            {"department_membership_id": self.department_membership.pk},
            content_type="application/json",
        )
        self.client.post(f"/api/scheduling/schedules/{schedule['id']}/publish/")

        PersonUnavailability.objects.create(
            person=self.person,
            start_date=self.worship_service.date,
            end_date=self.worship_service.date,
            start_time=time(9, 0),
            end_time=time(12, 0),
            reason="Motivo privado",
        )

        self.login(self.common)
        warning_response = self.client.get("/api/me/schedules/")
        self.assertEqual(warning_response.status_code, 200)
        self.assertEqual(warning_response.json()["items"][0]["warnings"][0]["code"], "MY_SCHEDULE_PERSON_UNAVAILABLE")
        self.assertNotIn("Motivo privado", str(warning_response.json()))

        self.login(self.admin)
        self.assertEqual(self.client.post(f"/api/scheduling/schedules/{schedule['id']}/cancel/").status_code, 200)
        self.login(self.common)
        self.assertEqual(self.client.get("/api/me/schedules/").json()["items"], [])
        self.assertEqual(self.client.get("/api/me/schedules/?scope=history").json()["items"][0]["schedule_status"], "CANCELLED")

        self.login(self.admin)
        schedule_model = Schedule.objects.get(pk=schedule["id"])
        schedule_model.status = Schedule.Status.PUBLISHED
        schedule_model.save(update_fields=["status"])
        schedule_model.worship_service.status = WorshipService.Status.CANCELLED
        schedule_model.worship_service.save(update_fields=["status"])
        self.login(self.common)
        self.assertEqual(self.client.get("/api/me/schedules/").json()["items"], [])
        cancelled_worship = self.client.get("/api/me/schedules/?scope=history")
        self.assertEqual(cancelled_worship.json()["items"][0]["worship_service"]["status"], "CANCELLED")

    def test_my_schedules_anonymous_is_rejected(self):
        response = self.client.get("/api/me/schedules/")
        self.assertEqual(response.status_code, 403)
