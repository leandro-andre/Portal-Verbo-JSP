from django.db import IntegrityError
from django.utils import timezone

from departamentos.selectors import is_department_membership_operationally_eligible
from worship.models import WorshipService

from .models import Schedule, ScheduleAssignment
from .selectors import get_assignment_eligibility


SCHEDULE_ALREADY_EXISTS = "SCHEDULE_ALREADY_EXISTS"
DEPARTMENT_NOT_ACTIVE = "DEPARTMENT_NOT_ACTIVE"
WORSHIP_SERVICE_NOT_SCHEDULED = "WORSHIP_SERVICE_NOT_SCHEDULED"
WORSHIP_SERVICE_IN_PAST = "WORSHIP_SERVICE_IN_PAST"
INVALID_SCHEDULE_TRANSITION = "INVALID_SCHEDULE_TRANSITION"
SCHEDULE_NOT_EDITABLE = "SCHEDULE_NOT_EDITABLE"
DEPARTMENT_MEMBERSHIP_NOT_ELIGIBLE = "DEPARTMENT_MEMBERSHIP_NOT_ELIGIBLE"
DEPARTMENT_MEMBERSHIP_WRONG_DEPARTMENT = "DEPARTMENT_MEMBERSHIP_WRONG_DEPARTMENT"
PERSON_UNAVAILABLE_FOR_WORSHIP_SERVICE = "PERSON_UNAVAILABLE_FOR_WORSHIP_SERVICE"
PERSON_ALREADY_ASSIGNED_TO_WORSHIP_SERVICE = "PERSON_ALREADY_ASSIGNED_TO_WORSHIP_SERVICE"
PERSON_SCHEDULE_TIME_CONFLICT = "PERSON_SCHEDULE_TIME_CONFLICT"
SCHEDULE_HAS_NO_ASSIGNMENTS = "SCHEDULE_HAS_NO_ASSIGNMENTS"


class SchedulingError(Exception):
    def __init__(self, code, message, reasons=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.reasons = reasons or []


def ensure_schedule_operational(schedule):
    if not schedule.department.ativo:
        raise SchedulingError(DEPARTMENT_NOT_ACTIVE, "O departamento desta escala esta inativo.")
    if schedule.worship_service.status != WorshipService.Status.SCHEDULED:
        raise SchedulingError(WORSHIP_SERVICE_NOT_SCHEDULED, "O culto desta escala esta cancelado.")


def ensure_schedule_editable(schedule):
    ensure_schedule_operational(schedule)
    if schedule.status != Schedule.Status.DRAFT:
        raise SchedulingError(SCHEDULE_NOT_EDITABLE, "Somente escalas em rascunho podem ser editadas.")


def create_schedule(*, department, worship_service, created_by=None):
    if not department.ativo:
        raise SchedulingError(DEPARTMENT_NOT_ACTIVE, "O departamento precisa estar ativo.")
    if worship_service.status != WorshipService.Status.SCHEDULED:
        raise SchedulingError(WORSHIP_SERVICE_NOT_SCHEDULED, "O culto precisa estar agendado.")
    if worship_service.date < timezone.localdate():
        raise SchedulingError(WORSHIP_SERVICE_IN_PAST, "Nao e permitido criar escala para culto passado.")

    try:
        return Schedule.objects.create(
            department=department,
            worship_service=worship_service,
            status=Schedule.Status.DRAFT,
            created_by=created_by,
        )
    except IntegrityError as exc:
        raise SchedulingError(
            SCHEDULE_ALREADY_EXISTS,
            "Ja existe uma escala deste departamento para este culto.",
        ) from exc


def publish_schedule(schedule):
    ensure_schedule_operational(schedule)
    if schedule.status == Schedule.Status.CANCELLED:
        raise SchedulingError(INVALID_SCHEDULE_TRANSITION, "Escala cancelada precisa voltar para rascunho antes de publicar.")
    if schedule.status == Schedule.Status.PUBLISHED:
        raise SchedulingError(INVALID_SCHEDULE_TRANSITION, "Esta escala ja esta publicada.")
    if not schedule.assignments.exists():
        raise SchedulingError(SCHEDULE_HAS_NO_ASSIGNMENTS, "Nao e permitido publicar escala sem pessoas.")
    schedule.status = Schedule.Status.PUBLISHED
    schedule.save(update_fields=["status", "updated_at"])
    return schedule


def reopen_schedule(schedule):
    ensure_schedule_operational(schedule)
    if schedule.status != Schedule.Status.PUBLISHED:
        raise SchedulingError(INVALID_SCHEDULE_TRANSITION, "Somente escala publicada pode voltar para rascunho.")
    schedule.status = Schedule.Status.DRAFT
    schedule.save(update_fields=["status", "updated_at"])
    return schedule


def cancel_schedule(schedule):
    if schedule.status == Schedule.Status.CANCELLED:
        raise SchedulingError(INVALID_SCHEDULE_TRANSITION, "Esta escala ja esta cancelada.")
    schedule.status = Schedule.Status.CANCELLED
    schedule.save(update_fields=["status", "updated_at"])
    return schedule


def reactivate_schedule(schedule):
    ensure_schedule_operational(schedule)
    if schedule.status != Schedule.Status.CANCELLED:
        raise SchedulingError(INVALID_SCHEDULE_TRANSITION, "Somente escala cancelada pode ser reativada.")
    schedule.status = Schedule.Status.DRAFT
    schedule.save(update_fields=["status", "updated_at"])
    return schedule


def create_schedule_assignment(*, schedule, department_membership, created_by=None):
    ensure_schedule_editable(schedule)
    if department_membership.department_id != schedule.department_id:
        raise SchedulingError(DEPARTMENT_MEMBERSHIP_WRONG_DEPARTMENT, "O vinculo nao pertence ao departamento desta escala.")
    if not is_department_membership_operationally_eligible(department_membership):
        raise SchedulingError(DEPARTMENT_MEMBERSHIP_NOT_ELIGIBLE, "O vinculo departamental nao esta elegivel.")

    eligibility = get_assignment_eligibility(schedule, department_membership)
    if not eligibility.eligible:
        reason = eligibility.reasons[0]
        raise SchedulingError(reason.code, reason.message, reasons=[item.as_dict() for item in eligibility.reasons])

    try:
        return ScheduleAssignment.objects.create(
            schedule=schedule,
            department_membership=department_membership,
            created_by=created_by,
        )
    except IntegrityError as exc:
        raise SchedulingError(
            PERSON_ALREADY_ASSIGNED_TO_WORSHIP_SERVICE,
            "Pessoa ja escalada nesta escala.",
        ) from exc


def delete_schedule_assignment(assignment):
    ensure_schedule_editable(assignment.schedule)
    assignment.delete()
