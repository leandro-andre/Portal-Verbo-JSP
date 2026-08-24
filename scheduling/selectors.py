from dataclasses import dataclass

from django.db.models import Count, Q

from departamentos.models import DepartmentMembership
from departamentos.models import Departamento, DepartmentRole
from departamentos.selectors import get_department_membership_eligibility
from pessoas.availability import is_person_available
from worship.models import WorshipService

from .models import DepartmentScheduleRequirement, Schedule, ScheduleAssignment


DEPARTMENT_MEMBERSHIP_WRONG_DEPARTMENT = "DEPARTMENT_MEMBERSHIP_WRONG_DEPARTMENT"
PERSON_UNAVAILABLE_FOR_WORSHIP_SERVICE = "PERSON_UNAVAILABLE_FOR_WORSHIP_SERVICE"
PERSON_ALREADY_ASSIGNED_TO_WORSHIP_SERVICE = "PERSON_ALREADY_ASSIGNED_TO_WORSHIP_SERVICE"
PERSON_SCHEDULE_TIME_CONFLICT = "PERSON_SCHEDULE_TIME_CONFLICT"
SCHEDULE_HAS_NO_ASSIGNMENTS = "SCHEDULE_HAS_NO_ASSIGNMENTS"
SCHEDULE_REQUIREMENT_MINIMUM_NOT_MET = "SCHEDULE_REQUIREMENT_MINIMUM_NOT_MET"
SCHEDULE_REQUIREMENT_RECOMMENDED_NOT_MET = "SCHEDULE_REQUIREMENT_RECOMMENDED_NOT_MET"

REASON_MESSAGES = {
    DEPARTMENT_MEMBERSHIP_WRONG_DEPARTMENT: "O vinculo nao pertence ao departamento desta escala.",
    PERSON_UNAVAILABLE_FOR_WORSHIP_SERVICE: "Pessoa indisponivel para este culto.",
    PERSON_ALREADY_ASSIGNED_TO_WORSHIP_SERVICE: "Pessoa ja escalada para este culto.",
    PERSON_SCHEDULE_TIME_CONFLICT: "Pessoa ja escalada em outro culto no mesmo horario.",
    SCHEDULE_HAS_NO_ASSIGNMENTS: "Nao e permitido publicar escala sem pessoas.",
    SCHEDULE_REQUIREMENT_MINIMUM_NOT_MET: "Minimo obrigatorio do cargo nao atendido.",
    SCHEDULE_REQUIREMENT_RECOMMENDED_NOT_MET: "Quantidade recomendada do cargo nao atingida.",
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


@dataclass(frozen=True)
class ScheduleValidationIssue:
    code: str
    message: str
    role_id: int | None = None
    assignment_id: int | None = None

    def as_dict(self):
        payload = {"code": self.code, "message": self.message}
        if self.role_id is not None:
            payload["role_id"] = self.role_id
        if self.assignment_id is not None:
            payload["assignment_id"] = self.assignment_id
        return payload


@dataclass(frozen=True)
class ScheduleRequirementValidation:
    role: DepartmentRole
    minimum_quantity: int
    recommended_quantity: int
    assigned_quantity: int
    minimum_met: bool
    recommended_met: bool

    def as_dict(self):
        return {
            "role": {"id": self.role_id, "name": self.role.name, "code": self.role.code},
            "minimum_quantity": self.minimum_quantity,
            "recommended_quantity": self.recommended_quantity,
            "assigned_quantity": self.assigned_quantity,
            "minimum_met": self.minimum_met,
            "recommended_met": self.recommended_met,
        }

    @property
    def role_id(self):
        return self.role.id


@dataclass(frozen=True)
class ScheduleValidationResult:
    valid: bool
    can_publish: bool
    blocking_issues: tuple[ScheduleValidationIssue, ...]
    warnings: tuple[ScheduleValidationIssue, ...]
    requirements: tuple[ScheduleRequirementValidation, ...]

    def as_dict(self):
        return {
            "valid": self.valid,
            "can_publish": self.can_publish,
            "blocking_issues": [issue.as_dict() for issue in self.blocking_issues],
            "warnings": [issue.as_dict() for issue in self.warnings],
            "requirements": [requirement.as_dict() for requirement in self.requirements],
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


def get_department_schedule_requirements(department, *, include_inactive=True):
    queryset = (
        DepartmentScheduleRequirement.objects.filter(department=department)
        .select_related("department", "role")
        .order_by("role__name", "id")
    )
    if not include_inactive:
        queryset = queryset.filter(active=True, role__active=True)
    return queryset


def get_schedule_composition_validation(schedule):
    schedule = (
        Schedule.objects.select_related("department", "worship_service")
        .prefetch_related("assignments__department_membership__person", "assignments__department_membership__role")
        .get(pk=schedule.pk)
    )
    assignments = list(get_schedule_assignments(schedule))
    valid_assignment_counts = {}
    blocking_issues = []
    warnings = []

    if not assignments:
        blocking_issues.append(ScheduleValidationIssue(SCHEDULE_HAS_NO_ASSIGNMENTS, REASON_MESSAGES[SCHEDULE_HAS_NO_ASSIGNMENTS]))

    if not schedule.department.ativo:
        blocking_issues.append(ScheduleValidationIssue("DEPARTMENT_NOT_ACTIVE", "O departamento desta escala esta inativo."))

    if schedule.worship_service.status != WorshipService.Status.SCHEDULED:
        blocking_issues.append(ScheduleValidationIssue("WORSHIP_SERVICE_NOT_SCHEDULED", "O culto desta escala esta cancelado."))

    for assignment in assignments:
        eligibility = get_assignment_eligibility(schedule, assignment.department_membership)
        if eligibility.eligible:
            role_id = assignment.department_membership.role_id
            valid_assignment_counts[role_id] = valid_assignment_counts.get(role_id, 0) + 1
            continue
        for reason in eligibility.reasons:
            blocking_issues.append(
                ScheduleValidationIssue(
                    code=reason.code,
                    message=f"{assignment.department_membership.person.display_name}: {reason.message}",
                    role_id=assignment.department_membership.role_id,
                    assignment_id=assignment.id,
                )
            )

    requirements = []
    for requirement in get_department_schedule_requirements(schedule.department, include_inactive=False):
        assigned_quantity = valid_assignment_counts.get(requirement.role_id, 0)
        minimum_met = assigned_quantity >= requirement.minimum_quantity
        recommended_met = assigned_quantity >= requirement.recommended_quantity
        requirement_validation = ScheduleRequirementValidation(
            role=requirement.role,
            minimum_quantity=requirement.minimum_quantity,
            recommended_quantity=requirement.recommended_quantity,
            assigned_quantity=assigned_quantity,
            minimum_met=minimum_met,
            recommended_met=recommended_met,
        )
        requirements.append(requirement_validation)
        if not minimum_met:
            blocking_issues.append(
                ScheduleValidationIssue(
                    code=SCHEDULE_REQUIREMENT_MINIMUM_NOT_MET,
                    message=f"{requirement.role.name}: minimo de {requirement.minimum_quantity} nao atendido.",
                    role_id=requirement.role_id,
                )
            )
        elif not recommended_met:
            warnings.append(
                ScheduleValidationIssue(
                    code=SCHEDULE_REQUIREMENT_RECOMMENDED_NOT_MET,
                    message=f"{requirement.role.name}: {assigned_quantity} de {requirement.recommended_quantity} recomendados.",
                    role_id=requirement.role_id,
                )
            )

    return ScheduleValidationResult(
        valid=not blocking_issues and not warnings,
        can_publish=not blocking_issues,
        blocking_issues=tuple(blocking_issues),
        warnings=tuple(warnings),
        requirements=tuple(requirements),
    )


def get_schedule_departments_for_user(user):
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        return Departamento.objects.none()
    if user.has_perm("scheduling.view_schedule"):
        return Departamento.objects.filter(ativo=True).order_by("nome", "id")
    person_id = getattr(user, "person_id", None)
    if not person_id:
        return Departamento.objects.none()
    return (
        Departamento.objects.filter(
            ativo=True,
            department_memberships__person_id=person_id,
            department_memberships__status=DepartmentMembership.Status.ACTIVE,
            department_memberships__role__active=True,
            department_memberships__role__can_manage_schedules=True,
        )
        .distinct()
        .order_by("nome", "id")
    )


def get_department_monthly_schedule(*, department, year, month, user):
    services = list(
        WorshipService.objects.filter(date__year=year, date__month=month)
        .select_related("template")
        .order_by("date", "time", "id")
    )
    schedules_by_service = {
        schedule.worship_service_id: schedule
        for schedule in Schedule.objects.filter(department=department, worship_service__in=services)
        .select_related("department", "worship_service", "created_by")
        .annotate(assignments_count=Count("assignments", distinct=True))
        .prefetch_related("assignments")
    }

    items = []
    summary = {
        "services": len(services),
        "cancelled_services": 0,
        "operational_services": 0,
        "published": 0,
        "draft": 0,
        "cancelled_schedules": 0,
        "without_schedule": 0,
    }
    for service in services:
        schedule = schedules_by_service.get(service.id)
        if service.status == WorshipService.Status.CANCELLED:
            summary["cancelled_services"] += 1
        else:
            summary["operational_services"] += 1
            if schedule is None:
                summary["without_schedule"] += 1
            elif schedule.status == Schedule.Status.PUBLISHED:
                summary["published"] += 1
            elif schedule.status == Schedule.Status.DRAFT:
                summary["draft"] += 1
        if schedule is not None and schedule.status == Schedule.Status.CANCELLED:
            summary["cancelled_schedules"] += 1
        validation_status = None
        if schedule is not None:
            validation = get_schedule_composition_validation(schedule)
            validation_status = "BLOCKED" if validation.blocking_issues else "WARNING" if validation.warnings else "OK"
        items.append({"worship_service": service, "schedule": schedule, "validation_status": validation_status})

    return {
        "year": year,
        "month": month,
        "department": department,
        "summary": summary,
        "items": items,
    }


def get_active_schedule_roles(schedule):
    return DepartmentRole.objects.filter(department=schedule.department, active=True).order_by("name", "id")
