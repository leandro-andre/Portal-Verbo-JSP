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

DISCIPLESHIP_CLASS_VIEW = "church_journey.view_discipleshipclass"
DISCIPLESHIP_CLASS_CREATE = "church_journey.add_discipleshipclass"
DISCIPLESHIP_CLASS_CHANGE = "church_journey.change_discipleshipclass"
DISCIPLESHIP_CLASS_START = "church_journey.start_discipleshipclass"
DISCIPLESHIP_CLASS_COMPLETE = "church_journey.complete_discipleshipclass"
DISCIPLESHIP_CLASS_CANCEL = "church_journey.cancel_discipleshipclass"

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
    "DISCIPLESHIP_CLASS_VIEW": DISCIPLESHIP_CLASS_VIEW,
    "DISCIPLESHIP_CLASS_CREATE": DISCIPLESHIP_CLASS_CREATE,
    "DISCIPLESHIP_CLASS_CHANGE": DISCIPLESHIP_CLASS_CHANGE,
    "DISCIPLESHIP_CLASS_START": DISCIPLESHIP_CLASS_START,
    "DISCIPLESHIP_CLASS_COMPLETE": DISCIPLESHIP_CLASS_COMPLETE,
    "DISCIPLESHIP_CLASS_CANCEL": DISCIPLESHIP_CLASS_CANCEL,
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
        DISCIPLESHIP_CLASS_VIEW,
        DISCIPLESHIP_CLASS_CREATE,
        DISCIPLESHIP_CLASS_CHANGE,
        DISCIPLESHIP_CLASS_START,
        DISCIPLESHIP_CLASS_COMPLETE,
        DISCIPLESHIP_CLASS_CANCEL,
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
        DISCIPLESHIP_CLASS_VIEW,
        DISCIPLESHIP_CLASS_CREATE,
        DISCIPLESHIP_CLASS_CHANGE,
        DISCIPLESHIP_CLASS_START,
        DISCIPLESHIP_CLASS_COMPLETE,
        DISCIPLESHIP_CLASS_CANCEL,
    ),
    PASTOR_GROUP: (
        PEOPLE_VIEW,
        ACCESS_REQUEST_VIEW,
        USER_VIEW,
        CHURCH_JOURNEY_VIEW,
        DISCIPLESHIP_CLASS_VIEW,
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
