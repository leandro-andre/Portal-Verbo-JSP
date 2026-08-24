from django.db import IntegrityError
from django.utils import timezone

from .models import Departamento, DepartmentMembership, DepartmentRole
from .selectors import (
    DEPARTMENT_INACTIVE,
    DEPARTMENT_MEMBERSHIP_ALREADY_EXISTS as ELIGIBILITY_MEMBERSHIP_ALREADY_EXISTS,
    MEMBERSHIP_NOT_ACTIVE,
    get_department_entry_eligibility,
    person_has_active_membership,
)


INVALID_DEPARTMENT_TRANSITION = "INVALID_DEPARTMENT_TRANSITION"
PERSON_IS_NOT_ACTIVE_MEMBER = "PERSON_IS_NOT_ACTIVE_MEMBER"
DEPARTMENT_ROLE_MISMATCH = "DEPARTMENT_ROLE_MISMATCH"
DEPARTMENT_NOT_ACTIVE = "DEPARTMENT_NOT_ACTIVE"
DEPARTMENT_ROLE_NOT_ACTIVE = "DEPARTMENT_ROLE_NOT_ACTIVE"
DEPARTMENT_MEMBERSHIP_ALREADY_EXISTS = "DEPARTMENT_MEMBERSHIP_ALREADY_EXISTS"
INVALID_DEPARTMENT_ROLE_TRANSITION = "INVALID_DEPARTMENT_ROLE_TRANSITION"
INVALID_DEPARTMENT_MEMBERSHIP_TRANSITION = "INVALID_DEPARTMENT_MEMBERSHIP_TRANSITION"


class DepartmentError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)


def deactivate_department(department):
    if not department.ativo:
        raise DepartmentError(
            INVALID_DEPARTMENT_TRANSITION,
            "Somente departamentos ativos podem ser inativados.",
        )

    department.ativo = False
    department.save(update_fields=["ativo"])
    return department


def reactivate_department(department):
    if department.ativo:
        raise DepartmentError(
            INVALID_DEPARTMENT_TRANSITION,
            "Somente departamentos inativos podem ser reativados.",
        )

    department.ativo = True
    department.save(update_fields=["ativo"])
    return department


def ensure_department_active(department):
    if not department.ativo:
        raise DepartmentError(
            DEPARTMENT_NOT_ACTIVE,
            "O departamento precisa estar ativo.",
        )


def ensure_role_active(role):
    if not role.active:
        raise DepartmentError(
            DEPARTMENT_ROLE_NOT_ACTIVE,
            "O cargo precisa estar ativo.",
        )


def ensure_role_belongs_to_department(*, role, department):
    if role.department_id != department.id:
        raise DepartmentError(
            DEPARTMENT_ROLE_MISMATCH,
            "O cargo informado nao pertence a este departamento.",
        )


def ensure_person_is_active_member(person):
    if not person_has_active_membership(person):
        raise DepartmentError(
            PERSON_IS_NOT_ACTIVE_MEMBER,
            "A pessoa precisa ter membresia ativa.",
        )


def raise_entry_eligibility_error(eligibility):
    if eligibility.eligible:
        return

    reason_to_error = {
        MEMBERSHIP_NOT_ACTIVE: (
            PERSON_IS_NOT_ACTIVE_MEMBER,
            "A pessoa precisa ter membresia ativa.",
        ),
        DEPARTMENT_INACTIVE: (
            DEPARTMENT_NOT_ACTIVE,
            "O departamento precisa estar ativo.",
        ),
        ELIGIBILITY_MEMBERSHIP_ALREADY_EXISTS: (
            DEPARTMENT_MEMBERSHIP_ALREADY_EXISTS,
            "Esta pessoa ja esta vinculada a este departamento.",
        ),
    }
    reason = eligibility.reasons[0]
    code, message = reason_to_error.get(reason.code, (reason.code, reason.message))
    raise DepartmentError(code, message)


def ensure_person_can_enter_department(*, person, department):
    raise_entry_eligibility_error(get_department_entry_eligibility(person, department))


def create_department_role(
    *,
    department,
    name,
    can_manage_department=False,
    can_manage_members=False,
    can_manage_schedules=False,
):
    ensure_department_active(department)
    code = generate_department_role_code(department=department, name=name)
    role = DepartmentRole(
        department=department,
        name=name,
        code=code,
        active=True,
        can_manage_department=can_manage_department,
        can_manage_members=can_manage_members,
        can_manage_schedules=can_manage_schedules,
    )
    try:
        role.save()
    except IntegrityError as exc:
        raise DepartmentError(
            "DEPARTMENT_ROLE_ALREADY_EXISTS",
            "Ja existe um cargo com este codigo neste departamento.",
        ) from exc
    return role


def generate_department_role_code(*, department, name):
    base_code = Departamento.normalizar_codigo(name)
    if not base_code:
        base_code = "cargo"

    code = base_code
    counter = 2
    while DepartmentRole.objects.filter(department=department, code__iexact=code).exists():
        code = f"{base_code}-{counter}"
        counter += 1
    return code


def update_department_role(
    role,
    *,
    name=None,
    can_manage_department=None,
    can_manage_members=None,
    can_manage_schedules=None,
):
    if name is not None:
        role.name = name
    if can_manage_department is not None:
        role.can_manage_department = can_manage_department
    if can_manage_members is not None:
        role.can_manage_members = can_manage_members
    if can_manage_schedules is not None:
        role.can_manage_schedules = can_manage_schedules
    role.save()
    return role


def deactivate_department_role(role):
    if not role.active:
        raise DepartmentError(
            INVALID_DEPARTMENT_ROLE_TRANSITION,
            "Somente cargos ativos podem ser inativados.",
        )
    role.active = False
    role.save(update_fields=["active", "updated_at"])
    return role


def reactivate_department_role(role):
    if role.active:
        raise DepartmentError(
            INVALID_DEPARTMENT_ROLE_TRANSITION,
            "Somente cargos inativos podem ser reativados.",
        )
    ensure_department_active(role.department)
    role.active = True
    role.save(update_fields=["active", "updated_at"])
    return role


def validate_membership_inputs(*, person, department, role):
    ensure_role_belongs_to_department(role=role, department=department)
    ensure_person_can_enter_department(person=person, department=department)
    ensure_role_active(role)


def create_department_membership(*, person, department, role, joined_at=None):
    validate_membership_inputs(person=person, department=department, role=role)
    try:
        return DepartmentMembership.objects.create(
            person=person,
            department=department,
            role=role,
            status=DepartmentMembership.Status.ACTIVE,
            joined_at=joined_at or timezone.localdate(),
            left_at=None,
        )
    except IntegrityError as exc:
        raise DepartmentError(
            DEPARTMENT_MEMBERSHIP_ALREADY_EXISTS,
            "Esta pessoa ja esta vinculada a este departamento.",
        ) from exc


def update_department_membership_role(department_membership, *, role):
    if department_membership.status != DepartmentMembership.Status.ACTIVE:
        raise DepartmentError(
            INVALID_DEPARTMENT_MEMBERSHIP_TRANSITION,
            "Somente vinculos ativos podem ser alterados.",
        )
    ensure_department_active(department_membership.department)
    ensure_person_is_active_member(department_membership.person)
    ensure_role_belongs_to_department(role=role, department=department_membership.department)
    ensure_role_active(role)
    department_membership.role = role
    department_membership.save(update_fields=["role", "updated_at"])
    return department_membership


def deactivate_department_membership(department_membership):
    if department_membership.status != DepartmentMembership.Status.ACTIVE:
        raise DepartmentError(
            INVALID_DEPARTMENT_MEMBERSHIP_TRANSITION,
            "Somente vinculos ativos podem ser inativados.",
        )
    department_membership.status = DepartmentMembership.Status.INACTIVE
    department_membership.left_at = timezone.localdate()
    department_membership.save(update_fields=["status", "left_at", "updated_at"])
    return department_membership


def reactivate_department_membership(department_membership):
    if department_membership.status != DepartmentMembership.Status.INACTIVE:
        raise DepartmentError(
            INVALID_DEPARTMENT_MEMBERSHIP_TRANSITION,
            "Somente vinculos inativos podem ser reativados.",
        )
    ensure_department_active(department_membership.department)
    ensure_person_is_active_member(department_membership.person)
    ensure_role_active(department_membership.role)
    department_membership.status = DepartmentMembership.Status.ACTIVE
    department_membership.left_at = None
    department_membership.save(update_fields=["status", "left_at", "updated_at"])
    return department_membership
