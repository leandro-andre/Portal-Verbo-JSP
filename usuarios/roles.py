from django.contrib.auth.models import Group, Permission


PORTAL_ADMIN_GROUP = "Administrador do Portal"
SECRETARY_GROUP = "Secretaria"
PASTOR_GROUP = "Pastor"

ROLE_CODES = {
    PORTAL_ADMIN_GROUP: "PORTAL_ADMIN",
    SECRETARY_GROUP: "SECRETARY",
    PASTOR_GROUP: "PASTOR",
}

ROLE_GROUPS = tuple(ROLE_CODES.keys())

PEOPLE_VIEW = "pessoas.view_person"
PEOPLE_CREATE = "pessoas.add_person"
PEOPLE_CHANGE = "pessoas.change_person"

ACCESS_REQUEST_VIEW = "usuarios.view_accessrequest"
ACCESS_REQUEST_APPROVE = "usuarios.approve_accessrequest"
ACCESS_REQUEST_REJECT = "usuarios.reject_accessrequest"

USER_VIEW = "usuarios.view_usuario"
USER_DISABLE = "usuarios.disable_usuario"
USER_ENABLE = "usuarios.enable_usuario"

CHURCH_JOURNEY_VIEW = "church_journey.view_churchjourney"
CHURCH_JOURNEY_CREATE = "church_journey.add_churchjourney"
CHURCH_JOURNEY_CHANGE = "church_journey.change_churchjourney"
MEMBERSHIP_VIEW = "church_journey.view_membership"
MEMBERSHIP_APPROVE = "church_journey.approve_membership"
MEMBERSHIP_DEACTIVATE = "church_journey.deactivate_membership"
MEMBERSHIP_REACTIVATE = "church_journey.reactivate_membership"

DEPARTMENT_VIEW = "departamentos.view_departamento"
DEPARTMENT_CREATE = "departamentos.add_departamento"
DEPARTMENT_CHANGE = "departamentos.change_departamento"
DEPARTMENT_DEACTIVATE = "departamentos.deactivate_departamento"
DEPARTMENT_REACTIVATE = "departamentos.reactivate_departamento"

DISCIPLESHIP_CLASS_VIEW = "church_journey.view_discipleshipclass"
DISCIPLESHIP_CLASS_CREATE = "church_journey.add_discipleshipclass"
DISCIPLESHIP_CLASS_CHANGE = "church_journey.change_discipleshipclass"
DISCIPLESHIP_CLASS_START = "church_journey.start_discipleshipclass"
DISCIPLESHIP_CLASS_COMPLETE = "church_journey.complete_discipleshipclass"
DISCIPLESHIP_CLASS_CANCEL = "church_journey.cancel_discipleshipclass"

DISCIPLESHIP_ENROLLMENT_VIEW = "church_journey.view_discipleshipenrollment"
DISCIPLESHIP_ENROLLMENT_CREATE = "church_journey.add_discipleshipenrollment"
DISCIPLESHIP_ENROLLMENT_WITHDRAW = "church_journey.withdraw_discipleshipenrollment"
DISCIPLESHIP_ENROLLMENT_COMPLETE = "church_journey.complete_discipleshipenrollment"

DISCIPLESHIP_LESSON_VIEW = "church_journey.view_discipleshiplesson"
DISCIPLESHIP_LESSON_CREATE = "church_journey.add_discipleshiplesson"
DISCIPLESHIP_LESSON_CHANGE = "church_journey.change_discipleshiplesson"
DISCIPLESHIP_LESSON_CANCEL = "church_journey.cancel_discipleshiplesson"

DISCIPLESHIP_ATTENDANCE_VIEW = "church_journey.view_discipleshipattendance"
DISCIPLESHIP_ATTENDANCE_CREATE = "church_journey.add_discipleshipattendance"
DISCIPLESHIP_ATTENDANCE_MANAGE = "church_journey.change_discipleshipattendance"

DISCIPLESHIP_COMPLETION_VIEW = "church_journey.view_discipleshipenrollment"
DISCIPLESHIP_COMPLETION_MANAGE = "church_journey.complete_discipleshipenrollment"

CAPABILITY_PERMISSIONS = {
    "PEOPLE_VIEW": PEOPLE_VIEW,
    "PEOPLE_CREATE": PEOPLE_CREATE,
    "PEOPLE_CHANGE": PEOPLE_CHANGE,
    "ACCESS_REQUEST_VIEW": ACCESS_REQUEST_VIEW,
    "ACCESS_REQUEST_APPROVE": ACCESS_REQUEST_APPROVE,
    "ACCESS_REQUEST_REJECT": ACCESS_REQUEST_REJECT,
    "USER_VIEW": USER_VIEW,
    "USER_DISABLE": USER_DISABLE,
    "USER_ENABLE": USER_ENABLE,
    "CHURCH_JOURNEY_VIEW": CHURCH_JOURNEY_VIEW,
    "CHURCH_JOURNEY_CREATE": CHURCH_JOURNEY_CREATE,
    "CHURCH_JOURNEY_CHANGE": CHURCH_JOURNEY_CHANGE,
    "MEMBERSHIP_VIEW": MEMBERSHIP_VIEW,
    "MEMBERSHIP_APPROVE": MEMBERSHIP_APPROVE,
    "MEMBERSHIP_DEACTIVATE": MEMBERSHIP_DEACTIVATE,
    "MEMBERSHIP_REACTIVATE": MEMBERSHIP_REACTIVATE,
    "DEPARTMENT_VIEW": DEPARTMENT_VIEW,
    "DEPARTMENT_CREATE": DEPARTMENT_CREATE,
    "DEPARTMENT_CHANGE": DEPARTMENT_CHANGE,
    "DEPARTMENT_DEACTIVATE": DEPARTMENT_DEACTIVATE,
    "DEPARTMENT_REACTIVATE": DEPARTMENT_REACTIVATE,
    "DISCIPLESHIP_CLASS_VIEW": DISCIPLESHIP_CLASS_VIEW,
    "DISCIPLESHIP_CLASS_CREATE": DISCIPLESHIP_CLASS_CREATE,
    "DISCIPLESHIP_CLASS_CHANGE": DISCIPLESHIP_CLASS_CHANGE,
    "DISCIPLESHIP_CLASS_START": DISCIPLESHIP_CLASS_START,
    "DISCIPLESHIP_CLASS_COMPLETE": DISCIPLESHIP_CLASS_COMPLETE,
    "DISCIPLESHIP_CLASS_CANCEL": DISCIPLESHIP_CLASS_CANCEL,
    "DISCIPLESHIP_ENROLLMENT_VIEW": DISCIPLESHIP_ENROLLMENT_VIEW,
    "DISCIPLESHIP_ENROLLMENT_CREATE": DISCIPLESHIP_ENROLLMENT_CREATE,
    "DISCIPLESHIP_ENROLLMENT_WITHDRAW": DISCIPLESHIP_ENROLLMENT_WITHDRAW,
    "DISCIPLESHIP_ENROLLMENT_COMPLETE": DISCIPLESHIP_ENROLLMENT_COMPLETE,
    "DISCIPLESHIP_LESSON_VIEW": DISCIPLESHIP_LESSON_VIEW,
    "DISCIPLESHIP_LESSON_CREATE": DISCIPLESHIP_LESSON_CREATE,
    "DISCIPLESHIP_LESSON_CHANGE": DISCIPLESHIP_LESSON_CHANGE,
    "DISCIPLESHIP_LESSON_CANCEL": DISCIPLESHIP_LESSON_CANCEL,
    "DISCIPLESHIP_ATTENDANCE_VIEW": DISCIPLESHIP_ATTENDANCE_VIEW,
    "DISCIPLESHIP_ATTENDANCE_MANAGE": DISCIPLESHIP_ATTENDANCE_MANAGE,
    "DISCIPLESHIP_COMPLETION_VIEW": DISCIPLESHIP_COMPLETION_VIEW,
    "DISCIPLESHIP_COMPLETION_MANAGE": DISCIPLESHIP_COMPLETION_MANAGE,
}

ROLE_PERMISSIONS = {
    PORTAL_ADMIN_GROUP: (
        PEOPLE_VIEW,
        PEOPLE_CREATE,
        PEOPLE_CHANGE,
        ACCESS_REQUEST_VIEW,
        ACCESS_REQUEST_APPROVE,
        ACCESS_REQUEST_REJECT,
        USER_VIEW,
        USER_DISABLE,
        USER_ENABLE,
        CHURCH_JOURNEY_VIEW,
        CHURCH_JOURNEY_CREATE,
        CHURCH_JOURNEY_CHANGE,
        MEMBERSHIP_VIEW,
        MEMBERSHIP_APPROVE,
        MEMBERSHIP_DEACTIVATE,
        MEMBERSHIP_REACTIVATE,
        DEPARTMENT_VIEW,
        DEPARTMENT_CREATE,
        DEPARTMENT_CHANGE,
        DEPARTMENT_DEACTIVATE,
        DEPARTMENT_REACTIVATE,
        DISCIPLESHIP_CLASS_VIEW,
        DISCIPLESHIP_CLASS_CREATE,
        DISCIPLESHIP_CLASS_CHANGE,
        DISCIPLESHIP_CLASS_START,
        DISCIPLESHIP_CLASS_COMPLETE,
        DISCIPLESHIP_CLASS_CANCEL,
        DISCIPLESHIP_ENROLLMENT_VIEW,
        DISCIPLESHIP_ENROLLMENT_CREATE,
        DISCIPLESHIP_ENROLLMENT_WITHDRAW,
        DISCIPLESHIP_ENROLLMENT_COMPLETE,
        DISCIPLESHIP_LESSON_VIEW,
        DISCIPLESHIP_LESSON_CREATE,
        DISCIPLESHIP_LESSON_CHANGE,
        DISCIPLESHIP_LESSON_CANCEL,
        DISCIPLESHIP_ATTENDANCE_VIEW,
        DISCIPLESHIP_ATTENDANCE_CREATE,
        DISCIPLESHIP_ATTENDANCE_MANAGE,
    ),
    SECRETARY_GROUP: (
        PEOPLE_VIEW,
        PEOPLE_CREATE,
        PEOPLE_CHANGE,
        ACCESS_REQUEST_VIEW,
        ACCESS_REQUEST_APPROVE,
        ACCESS_REQUEST_REJECT,
        USER_VIEW,
        CHURCH_JOURNEY_VIEW,
        CHURCH_JOURNEY_CREATE,
        CHURCH_JOURNEY_CHANGE,
        MEMBERSHIP_VIEW,
        MEMBERSHIP_APPROVE,
        MEMBERSHIP_DEACTIVATE,
        MEMBERSHIP_REACTIVATE,
        DEPARTMENT_VIEW,
        DEPARTMENT_CREATE,
        DEPARTMENT_CHANGE,
        DEPARTMENT_DEACTIVATE,
        DEPARTMENT_REACTIVATE,
        DISCIPLESHIP_CLASS_VIEW,
        DISCIPLESHIP_CLASS_CREATE,
        DISCIPLESHIP_CLASS_CHANGE,
        DISCIPLESHIP_CLASS_START,
        DISCIPLESHIP_CLASS_COMPLETE,
        DISCIPLESHIP_CLASS_CANCEL,
        DISCIPLESHIP_ENROLLMENT_VIEW,
        DISCIPLESHIP_ENROLLMENT_CREATE,
        DISCIPLESHIP_ENROLLMENT_WITHDRAW,
        DISCIPLESHIP_ENROLLMENT_COMPLETE,
        DISCIPLESHIP_LESSON_VIEW,
        DISCIPLESHIP_LESSON_CREATE,
        DISCIPLESHIP_LESSON_CHANGE,
        DISCIPLESHIP_LESSON_CANCEL,
        DISCIPLESHIP_ATTENDANCE_VIEW,
        DISCIPLESHIP_ATTENDANCE_CREATE,
        DISCIPLESHIP_ATTENDANCE_MANAGE,
    ),
    PASTOR_GROUP: (
        PEOPLE_VIEW,
        ACCESS_REQUEST_VIEW,
        USER_VIEW,
        CHURCH_JOURNEY_VIEW,
        MEMBERSHIP_VIEW,
        DEPARTMENT_VIEW,
        DISCIPLESHIP_CLASS_VIEW,
        DISCIPLESHIP_ENROLLMENT_VIEW,
        DISCIPLESHIP_LESSON_VIEW,
        DISCIPLESHIP_ATTENDANCE_VIEW,
    ),
}


def split_permission_codename(permission_path):
    app_label, codename = permission_path.split(".", 1)
    return app_label, codename


def setup_portal_roles():
    configured_groups = []
    for group_name, permission_paths in ROLE_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=group_name)
        permissions = []
        for permission_path in permission_paths:
            app_label, codename = split_permission_codename(permission_path)
            permissions.append(
                Permission.objects.get(
                    content_type__app_label=app_label,
                    codename=codename,
                )
            )
        group.permissions.set(permissions)
        configured_groups.append(group)
    return configured_groups


def get_role_codes(usuario):
    if not getattr(usuario, "is_authenticated", False):
        return []

    group_names = set(usuario.groups.values_list("name", flat=True))
    return [
        role_code
        for group_name, role_code in ROLE_CODES.items()
        if group_name in group_names
    ]


def get_capabilities(usuario):
    if not getattr(usuario, "is_authenticated", False):
        return []

    return [
        capability
        for capability, permission_path in CAPABILITY_PERMISSIONS.items()
        if usuario.has_perm(permission_path)
    ]
