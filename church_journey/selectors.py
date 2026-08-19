from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from .enums import ChurchStatus


LEGACY_VISITOR_STATUS = "visitante"
LEGACY_MEMBER_STATUS = "membro"


def get_legacy_user_account(person):
    if person is None:
        return None

    try:
        return person.user_account
    except ObjectDoesNotExist:
        return None


def get_church_status(person):
    if has_church_journey(person):
        return ChurchStatus.VISITOR
    return get_church_status_for_user_account(get_legacy_user_account(person))


def has_church_journey(person):
    if person is None:
        return False

    try:
        person.church_journey
    except ObjectDoesNotExist:
        return False
    return True


def get_church_status_for_user_account(usuario):
    status = getattr(usuario, "status_eclesiastico", None)
    if status == LEGACY_MEMBER_STATUS:
        return ChurchStatus.MEMBER
    if status == LEGACY_VISITOR_STATUS:
        return ChurchStatus.VISITOR
    return ChurchStatus.UNKNOWN


def is_member(person):
    return get_church_status(person) == ChurchStatus.MEMBER


def is_visitor(person):
    return get_church_status(person) == ChurchStatus.VISITOR


def has_completed_discipleship(person):
    usuario = get_legacy_user_account(person)
    return bool(getattr(usuario, "discipulado_concluido", False))


def get_discipleship_completed_at(person):
    usuario = get_legacy_user_account(person)
    return getattr(usuario, "discipulado_concluido_em", None)


def is_legacy_department_eligible(person):
    return is_legacy_department_eligible_for_user_account(get_legacy_user_account(person))


def is_legacy_department_eligible_for_user_account(usuario):
    if not getattr(usuario, "is_authenticated", False):
        return False

    return bool(
        get_church_status_for_user_account(usuario) == ChurchStatus.MEMBER
        or getattr(usuario, "eh_pastor", False)
        or getattr(usuario, "is_superuser", False)
    )


def get_legacy_department_eligible_user_filter(prefix=""):
    field_prefix = f"{prefix}__" if prefix else ""
    return (
        Q(**{f"{field_prefix}status_eclesiastico": LEGACY_MEMBER_STATUS})
        | Q(**{f"{field_prefix}eh_pastor": True})
        | Q(**{f"{field_prefix}is_superuser": True})
    )
