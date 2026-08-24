from dataclasses import dataclass

from church_journey.models import Membership
from church_journey.selectors import get_membership

from .models import DepartmentMembership


DEPARTMENT_MEMBERSHIP_INACTIVE = "DEPARTMENT_MEMBERSHIP_INACTIVE"
DEPARTMENT_INACTIVE = "DEPARTMENT_INACTIVE"
DEPARTMENT_ROLE_INACTIVE = "DEPARTMENT_ROLE_INACTIVE"
MEMBERSHIP_NOT_ACTIVE = "MEMBERSHIP_NOT_ACTIVE"
NO_DEPARTMENT_MEMBERSHIP = "NO_DEPARTMENT_MEMBERSHIP"
DEPARTMENT_MEMBERSHIP_ALREADY_EXISTS = "DEPARTMENT_MEMBERSHIP_ALREADY_EXISTS"

REASON_MESSAGES = {
    DEPARTMENT_MEMBERSHIP_INACTIVE: "O vinculo da pessoa com o departamento esta inativo.",
    DEPARTMENT_INACTIVE: "O departamento esta inativo.",
    DEPARTMENT_ROLE_INACTIVE: "O cargo no departamento esta inativo.",
    MEMBERSHIP_NOT_ACTIVE: "A membresia da pessoa nao esta ativa.",
    NO_DEPARTMENT_MEMBERSHIP: "A pessoa nao possui vinculo com este departamento.",
    DEPARTMENT_MEMBERSHIP_ALREADY_EXISTS: "A pessoa ja possui vinculo com este departamento.",
}


@dataclass(frozen=True)
class DepartmentEligibilityReason:
    code: str
    message: str

    def as_dict(self):
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True)
class DepartmentEligibilityResult:
    eligible: bool
    reasons: tuple[DepartmentEligibilityReason, ...]

    def as_dict(self):
        return {
            "eligible": self.eligible,
            "reasons": [reason.as_dict() for reason in self.reasons],
        }


def _reason(code):
    return DepartmentEligibilityReason(code=code, message=REASON_MESSAGES[code])


def _result(reason_codes):
    reasons = tuple(_reason(code) for code in reason_codes)
    return DepartmentEligibilityResult(eligible=not reasons, reasons=reasons)


def person_has_active_membership(person):
    membership = get_membership(person)
    return bool(membership is not None and membership.status == Membership.Status.ACTIVE)


def get_department_membership_eligibility(department_membership):
    reason_codes = []

    if department_membership.status != DepartmentMembership.Status.ACTIVE:
        reason_codes.append(DEPARTMENT_MEMBERSHIP_INACTIVE)
    if not department_membership.department.ativo:
        reason_codes.append(DEPARTMENT_INACTIVE)
    if not department_membership.role.active:
        reason_codes.append(DEPARTMENT_ROLE_INACTIVE)
    if not person_has_active_membership(department_membership.person):
        reason_codes.append(MEMBERSHIP_NOT_ACTIVE)

    return _result(reason_codes)


def is_department_membership_operationally_eligible(department_membership):
    return get_department_membership_eligibility(department_membership).eligible


def get_person_department_eligibility(person, department):
    department_membership = (
        DepartmentMembership.objects.filter(person=person, department=department)
        .select_related("person", "department", "role")
        .first()
    )
    if department_membership is None:
        return _result([NO_DEPARTMENT_MEMBERSHIP])
    return get_department_membership_eligibility(department_membership)


def get_department_entry_eligibility(person, department):
    reason_codes = []

    if not person_has_active_membership(person):
        reason_codes.append(MEMBERSHIP_NOT_ACTIVE)
    if not department.ativo:
        reason_codes.append(DEPARTMENT_INACTIVE)
    if DepartmentMembership.objects.filter(person=person, department=department).exists():
        reason_codes.append(DEPARTMENT_MEMBERSHIP_ALREADY_EXISTS)

    return _result(reason_codes)


def get_contextual_department_membership(user, department):
    person_id = getattr(user, "person_id", None)
    if not person_id:
        return None

    membership = (
        DepartmentMembership.objects.filter(
            department=department,
            person_id=person_id,
            status=DepartmentMembership.Status.ACTIVE,
        )
        .select_related("person", "department", "role")
        .first()
    )
    if membership is None or not is_department_membership_operationally_eligible(membership):
        return None
    return membership


def get_department_context_permissions(user, department):
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        return {
            "can_manage_department": False,
            "can_manage_roles": False,
            "can_manage_members": False,
            "can_manage_schedules": False,
        }

    contextual_membership = get_contextual_department_membership(user, department)
    contextual_role = contextual_membership.role if contextual_membership else None

    can_manage_department = bool(
        user.has_perm("departamentos.change_departamento")
        or (contextual_role and contextual_role.can_manage_department)
    )
    can_manage_members = bool(
        user.has_perm("departamentos.add_departmentmembership")
        or user.has_perm("departamentos.change_departmentmembership")
        or user.has_perm("departamentos.deactivate_departmentmembership")
        or user.has_perm("departamentos.reactivate_departmentmembership")
        or (contextual_role and contextual_role.can_manage_members)
    )
    can_manage_roles = bool(
        user.has_perm("departamentos.add_departmentrole")
        or user.has_perm("departamentos.change_departmentrole")
        or user.has_perm("departamentos.deactivate_departmentrole")
        or user.has_perm("departamentos.reactivate_departmentrole")
        or (contextual_role and contextual_role.can_manage_members)
    )
    can_manage_schedules = bool(contextual_role and contextual_role.can_manage_schedules)

    return {
        "can_manage_department": can_manage_department,
        "can_manage_roles": can_manage_roles,
        "can_manage_members": can_manage_members,
        "can_manage_schedules": can_manage_schedules,
    }


def can_view_department(user, department):
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        return False
    if user.has_perm("departamentos.view_departamento"):
        return True
    permissions = get_department_context_permissions(user, department)
    return any(permissions.values())


def can_manage_department(user, department):
    return get_department_context_permissions(user, department)["can_manage_department"]


def can_manage_department_roles(user, department):
    return get_department_context_permissions(user, department)["can_manage_roles"]


def can_manage_department_members(user, department):
    return get_department_context_permissions(user, department)["can_manage_members"]


def can_manage_department_schedules(user, department):
    return get_department_context_permissions(user, department)["can_manage_schedules"]
