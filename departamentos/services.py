from django.db import IntegrityError
from django.utils import timezone

from church_journey.selectors import is_active_member

from .models import Departamento, DepartmentMembership, DepartmentRole


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
    if not is_active_member(person):
        raise DepartmentError(
            PERSON_IS_NOT_ACTIVE_MEMBER,
            "A pessoa precisa ter membresia ativa.",
        )


def create_department_role(
    *,
    department,
    name,
    code,
    can_manage_department=False,
    can_manage_members=False,
):
    ensure_department_active(department)
    code = Departamento.normalizar_codigo(code or name)
    if DepartmentRole.objects.filter(department=department, code__iexact=code).exists():
        raise DepartmentError(
            "DEPARTMENT_ROLE_ALREADY_EXISTS",
            "Ja existe um cargo com este codigo neste departamento.",
        )
    role = DepartmentRole(
        department=department,
        name=name,
        code=code,
        active=True,
        can_manage_department=can_manage_department,
        can_manage_members=can_manage_members,
    )
    try:
        role.save()
    except IntegrityError as exc:
        raise DepartmentError(
            "DEPARTMENT_ROLE_ALREADY_EXISTS",
            "Ja existe um cargo com este codigo neste departamento.",
        ) from exc
    return role


def update_department_role(
    role,
    *,
    name=None,
    can_manage_department=None,
    can_manage_members=None,
):
    if name is not None:
        role.name = name
    if can_manage_department is not None:
        role.can_manage_department = can_manage_department
    if can_manage_members is not None:
        role.can_manage_members = can_manage_members
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
    ensure_person_is_active_member(person)
    ensure_department_active(department)
    ensure_role_belongs_to_department(role=role, department=department)
    ensure_role_active(role)


def create_department_membership(*, person, department, role, joined_at=None):
    validate_membership_inputs(person=person, department=department, role=role)
    if DepartmentMembership.objects.filter(person=person, department=department).exists():
        raise DepartmentError(
            DEPARTMENT_MEMBERSHIP_ALREADY_EXISTS,
            "Esta pessoa ja esta vinculada a este departamento.",
        )
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
    validate_membership_inputs(
        person=department_membership.person,
        department=department_membership.department,
        role=role,
    )
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
    validate_membership_inputs(
        person=department_membership.person,
        department=department_membership.department,
        role=department_membership.role,
    )
    department_membership.status = DepartmentMembership.Status.ACTIVE
    department_membership.left_at = None
    department_membership.save(update_fields=["status", "left_at", "updated_at"])
    return department_membership
