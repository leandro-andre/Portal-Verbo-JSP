from church_journey.selectors import is_active_member

from .models import DepartmentMembership


def is_department_membership_operationally_eligible(department_membership):
    return bool(
        department_membership.status == DepartmentMembership.Status.ACTIVE
        and department_membership.department.ativo
        and department_membership.role.active
        and is_active_member(department_membership.person)
    )


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

    return {
        "can_manage_department": can_manage_department,
        "can_manage_roles": can_manage_roles,
        "can_manage_members": can_manage_members,
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
