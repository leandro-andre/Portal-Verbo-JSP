from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from church_journey.models import ChurchJourney, DiscipleshipClass, DiscipleshipEnrollment, Membership
from departamentos.models import Departamento, DepartmentMembership, DepartmentRole
from pessoas.models import Person, PersonUnavailability
from scheduling.models import DepartmentScheduleRequirement, Schedule, ScheduleAssignment
from scheduling.selectors import get_assignment_eligibility, get_schedule_composition_validation
from scheduling.services import (
    DEPARTMENT_MEMBERSHIP_WRONG_DEPARTMENT,
    DEPARTMENT_NOT_ACTIVE,
    PERSON_ALREADY_ASSIGNED_TO_WORSHIP_SERVICE,
    PERSON_SCHEDULE_TIME_CONFLICT,
    PERSON_UNAVAILABLE_FOR_WORSHIP_SERVICE,
    SCHEDULE_REQUIREMENT_ALREADY_EXISTS,
    SCHEDULE_REQUIREMENT_ROLE_INACTIVE,
    SCHEDULE_REQUIREMENT_ROLE_MISMATCH,
    SCHEDULE_VALIDATION_FAILED,
    SCHEDULE_NOT_EDITABLE,
    WORSHIP_SERVICE_IN_PAST,
    WORSHIP_SERVICE_NOT_SCHEDULED,
    SchedulingError,
    cancel_schedule,
    create_schedule,
    create_schedule_assignment,
    create_schedule_requirement,
    delete_schedule_assignment,
    publish_schedule,
    reactivate_schedule,
    reactivate_schedule_requirement,
    reopen_schedule,
    update_schedule_requirement,
)
from worship.models import WorshipService


class SchedulingServiceTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="admin", password="senha")
        self.person = self.create_member_person("Maria")
        self.other_person = self.create_member_person("Joao")
        self.department = Departamento.objects.create(nome="Infantil")
        self.other_department = Departamento.objects.create(nome="Midia")
        self.role = DepartmentRole.objects.create(
            department=self.department,
            name="Professor",
            code="professor",
            active=True,
            can_manage_schedules=True,
        )
        self.other_role = DepartmentRole.objects.create(
            department=self.other_department,
            name="Operador",
            code="operador",
            active=True,
        )
        self.department_membership = DepartmentMembership.objects.create(
            person=self.person,
            department=self.department,
            role=self.role,
            status=DepartmentMembership.Status.ACTIVE,
        )
        self.other_department_membership = DepartmentMembership.objects.create(
            person=self.person,
            department=self.other_department,
            role=self.other_role,
            status=DepartmentMembership.Status.ACTIVE,
        )
        self.worship_service = self.create_worship_service(date=timezone.localdate() + timedelta(days=20))

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

    def create_worship_service(self, *, date, time_value=time(10, 0), status=WorshipService.Status.SCHEDULED):
        return WorshipService.objects.create(
            name="Culto Domingo Manha",
            date=date,
            time=time_value,
            kind=WorshipService.Kind.EXTRAORDINARY,
            status=status,
        )

    def assert_error_code(self, expected_code, callback):
        with self.assertRaises(SchedulingError) as context:
            callback()
        self.assertEqual(context.exception.code, expected_code)

    def test_create_schedule_and_unique_identity(self):
        schedule = create_schedule(
            department=self.department,
            worship_service=self.worship_service,
            created_by=self.user,
        )

        self.assertEqual(schedule.status, Schedule.Status.DRAFT)
        self.assertEqual(schedule.created_by, self.user)
        self.assert_error_code(
            "SCHEDULE_ALREADY_EXISTS",
            lambda: create_schedule(department=self.department, worship_service=self.worship_service),
        )

    def test_create_schedule_blocks_inactive_department_cancelled_worship_and_past(self):
        self.department.ativo = False
        self.department.save(update_fields=["ativo"])
        self.assert_error_code(
            DEPARTMENT_NOT_ACTIVE,
            lambda: create_schedule(department=self.department, worship_service=self.worship_service),
        )
        self.department.ativo = True
        self.department.save(update_fields=["ativo"])
        cancelled = self.create_worship_service(date=timezone.localdate() + timedelta(days=21), status=WorshipService.Status.CANCELLED)
        self.assert_error_code(
            WORSHIP_SERVICE_NOT_SCHEDULED,
            lambda: create_schedule(department=self.department, worship_service=cancelled),
        )
        past = self.create_worship_service(date=timezone.localdate() - timedelta(days=1))
        self.assert_error_code(
            WORSHIP_SERVICE_IN_PAST,
            lambda: create_schedule(department=self.department, worship_service=past),
        )

    def test_assignment_requires_same_department_and_person_without_user_is_allowed(self):
        schedule = create_schedule(department=self.department, worship_service=self.worship_service)

        assignment = create_schedule_assignment(
            schedule=schedule,
            department_membership=self.department_membership,
            created_by=self.user,
        )

        self.assertEqual(assignment.department_membership.person, self.person)
        self.assert_error_code(
            DEPARTMENT_MEMBERSHIP_WRONG_DEPARTMENT,
            lambda: create_schedule_assignment(schedule=schedule, department_membership=self.other_department_membership),
        )

    def test_assignment_blocks_operational_ineligible_membership_role_department_and_unavailability(self):
        schedule = create_schedule(department=self.department, worship_service=self.worship_service)
        self.department_membership.status = DepartmentMembership.Status.INACTIVE
        self.department_membership.save(update_fields=["status"])
        self.assert_error_code(
            "DEPARTMENT_MEMBERSHIP_NOT_ELIGIBLE",
            lambda: create_schedule_assignment(schedule=schedule, department_membership=self.department_membership),
        )
        self.department_membership.status = DepartmentMembership.Status.ACTIVE
        self.department_membership.save(update_fields=["status"])
        PersonUnavailability.objects.create(
            person=self.person,
            start_date=self.worship_service.date,
            end_date=self.worship_service.date,
            start_time=time(9, 0),
            end_time=time(12, 0),
            reason="Motivo privado",
        )
        eligibility = get_assignment_eligibility(schedule, self.department_membership)
        self.assertFalse(eligibility.eligible)
        self.assertIn(PERSON_UNAVAILABLE_FOR_WORSHIP_SERVICE, [reason.code for reason in eligibility.reasons])
        self.assertNotIn("Motivo privado", str(eligibility.as_dict()))
        self.assert_error_code(
            PERSON_UNAVAILABLE_FOR_WORSHIP_SERVICE,
            lambda: create_schedule_assignment(schedule=schedule, department_membership=self.department_membership),
        )

    def test_person_conflicts_same_worship_and_same_datetime(self):
        schedule = create_schedule(department=self.department, worship_service=self.worship_service)
        create_schedule_assignment(schedule=schedule, department_membership=self.department_membership)

        other_schedule = create_schedule(department=self.other_department, worship_service=self.worship_service)
        self.assert_error_code(
            PERSON_ALREADY_ASSIGNED_TO_WORSHIP_SERVICE,
            lambda: create_schedule_assignment(schedule=other_schedule, department_membership=self.other_department_membership),
        )

        other_worship = self.create_worship_service(date=self.worship_service.date, time_value=self.worship_service.time)
        other_schedule_same_time = create_schedule(department=self.other_department, worship_service=other_worship)
        self.assert_error_code(
            PERSON_SCHEDULE_TIME_CONFLICT,
            lambda: create_schedule_assignment(schedule=other_schedule_same_time, department_membership=self.other_department_membership),
        )

        cancel_schedule(schedule)
        create_schedule_assignment(schedule=other_schedule_same_time, department_membership=self.other_department_membership)

    def test_lifecycle_and_editability(self):
        schedule = create_schedule(department=self.department, worship_service=self.worship_service)
        self.assert_error_code(SCHEDULE_VALIDATION_FAILED, lambda: publish_schedule(schedule))
        assignment = create_schedule_assignment(schedule=schedule, department_membership=self.department_membership)

        publish_schedule(schedule)
        schedule.refresh_from_db()
        self.assertEqual(schedule.status, Schedule.Status.PUBLISHED)
        self.assert_error_code(SCHEDULE_NOT_EDITABLE, lambda: delete_schedule_assignment(assignment))

        reopen_schedule(schedule)
        schedule.refresh_from_db()
        self.assertEqual(schedule.status, Schedule.Status.DRAFT)
        delete_schedule_assignment(assignment)
        self.assertFalse(ScheduleAssignment.objects.filter(pk=assignment.pk).exists())

        cancel_schedule(schedule)
        schedule.refresh_from_db()
        self.assertEqual(schedule.status, Schedule.Status.CANCELLED)
        self.assert_error_code("INVALID_SCHEDULE_TRANSITION", lambda: publish_schedule(schedule))

        reactivate_schedule(schedule)
        schedule.refresh_from_db()
        self.assertEqual(schedule.status, Schedule.Status.DRAFT)

    def test_requirement_creation_validation_unique_and_lifecycle(self):
        requirement = create_schedule_requirement(
            department=self.department,
            role=self.role,
            minimum_quantity=1,
            recommended_quantity=2,
        )

        self.assertTrue(requirement.active)
        self.assertEqual(requirement.minimum_quantity, 1)
        self.assert_error_code(
            SCHEDULE_REQUIREMENT_ALREADY_EXISTS,
            lambda: create_schedule_requirement(department=self.department, role=self.role),
        )
        self.assert_error_code(
            SCHEDULE_REQUIREMENT_ROLE_MISMATCH,
            lambda: create_schedule_requirement(department=self.department, role=self.other_role),
        )
        self.assert_error_code(
            "INVALID_SCHEDULE_REQUIREMENT_QUANTITIES",
            lambda: update_schedule_requirement(requirement, minimum_quantity=2, recommended_quantity=1),
        )

        requirement.active = False
        requirement.save(update_fields=["active"])
        requirement.role.active = False
        requirement.role.save(update_fields=["active"])
        self.assert_error_code(SCHEDULE_REQUIREMENT_ROLE_INACTIVE, lambda: reactivate_schedule_requirement(requirement))

    def test_composition_minimum_recommended_and_publish(self):
        create_schedule_requirement(department=self.department, role=self.role, minimum_quantity=1, recommended_quantity=2)
        schedule = create_schedule(department=self.department, worship_service=self.worship_service)

        validation = get_schedule_composition_validation(schedule)
        self.assertFalse(validation.can_publish)
        self.assertFalse(validation.requirements[0].minimum_met)

        create_schedule_assignment(schedule=schedule, department_membership=self.department_membership)
        validation = get_schedule_composition_validation(schedule)

        self.assertTrue(validation.can_publish)
        self.assertTrue(validation.requirements[0].minimum_met)
        self.assertFalse(validation.requirements[0].recommended_met)
        self.assertEqual(len(validation.warnings), 1)
        publish_schedule(schedule)
        schedule.refresh_from_db()
        self.assertEqual(schedule.status, Schedule.Status.PUBLISHED)

    def test_publish_blocks_minimum_and_keeps_published_when_requirement_changes_later(self):
        requirement = create_schedule_requirement(department=self.department, role=self.role, minimum_quantity=1, recommended_quantity=1)
        schedule = create_schedule(department=self.department, worship_service=self.worship_service)
        self.assert_error_code(SCHEDULE_VALIDATION_FAILED, lambda: publish_schedule(schedule))

        create_schedule_assignment(schedule=schedule, department_membership=self.department_membership)
        publish_schedule(schedule)
        schedule.refresh_from_db()
        self.assertEqual(schedule.status, Schedule.Status.PUBLISHED)

        update_schedule_requirement(requirement, minimum_quantity=2, recommended_quantity=2)
        schedule.refresh_from_db()
        validation = get_schedule_composition_validation(schedule)
        self.assertFalse(validation.can_publish)
        self.assertEqual(schedule.status, Schedule.Status.PUBLISHED)

    def test_invalid_assignment_and_later_unavailability_do_not_delete_assignment(self):
        create_schedule_requirement(department=self.department, role=self.role, minimum_quantity=1, recommended_quantity=1)
        schedule = create_schedule(department=self.department, worship_service=self.worship_service)
        assignment = create_schedule_assignment(schedule=schedule, department_membership=self.department_membership)

        self.department_membership.status = DepartmentMembership.Status.INACTIVE
        self.department_membership.save(update_fields=["status"])
        validation = get_schedule_composition_validation(schedule)
        self.assertFalse(validation.can_publish)
        self.assertEqual(validation.requirements[0].assigned_quantity, 0)
        self.assertTrue(ScheduleAssignment.objects.filter(pk=assignment.pk).exists())

        self.department_membership.status = DepartmentMembership.Status.ACTIVE
        self.department_membership.save(update_fields=["status"])
        PersonUnavailability.objects.create(
            person=self.person,
            start_date=self.worship_service.date,
            end_date=self.worship_service.date,
            start_time=time(9, 0),
            end_time=time(12, 0),
            reason="Motivo privado",
        )
        validation = get_schedule_composition_validation(schedule)
        self.assertFalse(validation.can_publish)
        self.assertNotIn("Motivo privado", str(validation.as_dict()))
