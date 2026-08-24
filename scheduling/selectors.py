from dataclasses import dataclass

from django.db.models import Q

from departamentos.models import DepartmentMembership
from departamentos.selectors import get_department_membership_eligibility
from pessoas.availability import is_person_available
from worship.models import WorshipService

from .models import Schedule, ScheduleAssignment


DEPARTMENT_MEMBERSHIP_WRONG_DEPARTMENT = "DEPARTMENT_MEMBERSHIP_WRONG_DEPARTMENT"
PERSON_UNAVAILABLE_FOR_WORSHIP_SERVICE = "PERSON_UNAVAILABLE_FOR_WORSHIP_SERVICE"
PERSON_ALREADY_ASSIGNED_TO_WORSHIP_SERVICE = "PERSON_ALREADY_ASSIGNED_TO_WORSHIP_SERVICE"
PERSON_SCHEDULE_TIME_CONFLICT = "PERSON_SCHEDULE_TIME_CONFLICT"

REASON_MESSAGES = {
    DEPARTMENT_MEMBERSHIP_WRONG_DEPARTMENT: "O vinculo nao pertence ao departamento desta escala.",
    PERSON_UNAVAILABLE_FOR_WORSHIP_SERVICE: "Pessoa indisponivel para este culto.",
    PERSON_ALREADY_ASSIGNED_TO_WORSHIP_SERVICE: "Pessoa ja escalada para este culto.",
    PERSON_SCHEDULE_TIME_CONFLICT: "Pessoa ja escalada em outro culto no mesmo horario.",
}


@dataclass(frozen=True)
class ScheduleEligibilityReason:
    code: str
    message: str

    def as_dict(self):
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True)
class ScheduleAssignmentEligibilityResult:
    eligible: bool
    reasons: tuple[ScheduleEligibilityReason, ...]

    def as_dict(self):
        return {
            "eligible": self.eligible,
            "reasons": [reason.as_dict() for reason in self.reasons],
        }


def _reason(code, message=None):
    return ScheduleEligibilityReason(code=code, message=message or REASON_MESSAGES[code])


def _result(reasons):
    return ScheduleAssignmentEligibilityResult(eligible=not reasons, reasons=tuple(reasons))


def get_schedule(schedule_id):
    return (
        Schedule.objects.select_related("department", "worship_service", "created_by")
        .prefetch_related("assignments")
        .get(pk=schedule_id)
    )


def get_department_schedule_for_worship_service(*, department, worship_service):
    return Schedule.objects.filter(department=department, worship_service=worship_service).first()


def get_schedule_assignments(schedule):
    return (
        ScheduleAssignment.objects.filter(schedule=schedule)
        .select_related(
            "department_membership__person",
            "department_membership__role",
            "created_by",
        )
        .order_by("department_membership__person__full_name", "id")
    )


def get_person_schedule_conflicts(*, person, worship_service, exclude_schedule=None):
    queryset = (
        ScheduleAssignment.objects.select_related("schedule__worship_service", "department_membership__person")
        .filter(department_membership__person=person)
        .exclude(schedule__status=Schedule.Status.CANCELLED)
        .exclude(schedule__worship_service__status=WorshipService.Status.CANCELLED)
        .filter(
            Q(schedule__worship_service=worship_service)
            | Q(
                schedule__worship_service__date=worship_service.date,
                schedule__worship_service__time=worship_service.time,
            )
        )
    )
    if exclude_schedule is not None:
        queryset = queryset.exclude(schedule=exclude_schedule)
    return queryset


def get_assignment_eligibility(schedule, department_membership):
    reasons = []

    if department_membership.department_id != schedule.department_id:
        reasons.append(_reason(DEPARTMENT_MEMBERSHIP_WRONG_DEPARTMENT))

    department_eligibility = get_department_membership_eligibility(department_membership)
    for reason in department_eligibility.reasons:
        reasons.append(_reason(reason.code, reason.message))

    person = department_membership.person
    worship_service = schedule.worship_service
    if not is_person_available(person, worship_service.date, worship_service.time):
        reasons.append(_reason(PERSON_UNAVAILABLE_FOR_WORSHIP_SERVICE))

    conflicts = get_person_schedule_conflicts(
        person=person,
        worship_service=worship_service,
        exclude_schedule=schedule,
    )
    for conflict in conflicts:
        if conflict.schedule.worship_service_id == worship_service.id:
            reasons.append(_reason(PERSON_ALREADY_ASSIGNED_TO_WORSHIP_SERVICE))
            break
    else:
        if conflicts.exists():
            reasons.append(_reason(PERSON_SCHEDULE_TIME_CONFLICT))

    return _result(reasons)


def can_assign_department_membership_to_schedule(schedule, department_membership):
    return get_assignment_eligibility(schedule, department_membership).eligible


def get_assignment_candidates(schedule):
    memberships = (
        DepartmentMembership.objects.filter(department=schedule.department)
        .select_related("person", "role", "department")
        .order_by("person__full_name", "id")
    )
    return [
        {
            "department_membership": membership,
            "eligibility": get_assignment_eligibility(schedule, membership),
        }
        for membership in memberships
    ]
