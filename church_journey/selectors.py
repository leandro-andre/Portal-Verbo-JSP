from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from .enums import ChurchStatus
from .models import DiscipleshipAttendance, DiscipleshipEnrollment, DiscipleshipLesson, Membership


MINIMUM_DISCIPLESHIP_ATTENDANCE_PERCENTAGE = 75


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
    membership = get_membership(person)
    if membership is not None:
        if membership.status == Membership.Status.ACTIVE:
            return ChurchStatus.MEMBER
        if membership.status == Membership.Status.INACTIVE:
            return ChurchStatus.INACTIVE_MEMBER
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


def is_inactive_church_member(person):
    return get_church_status(person) == ChurchStatus.INACTIVE_MEMBER


def is_visitor(person):
    return get_church_status(person) == ChurchStatus.VISITOR


def get_membership(person):
    if person is None or person.pk is None:
        return None

    return Membership.objects.filter(person=person).first()


def has_membership(person):
    return get_membership(person) is not None


def is_active_member(person):
    membership = get_membership(person)
    return bool(membership is not None and membership.status == Membership.Status.ACTIVE)


def is_inactive_member(person):
    membership = get_membership(person)
    return bool(membership is not None and membership.status == Membership.Status.INACTIVE)


def get_membership_status(person):
    membership = get_membership(person)
    return membership.status if membership is not None else None


def get_member_since(person):
    membership = get_membership(person)
    return membership.member_since if membership is not None else None


def has_completed_discipleship(person):
    if get_completed_discipleship(person) is not None:
        return True

    usuario = get_legacy_user_account(person)
    return bool(getattr(usuario, "discipulado_concluido", False))


def get_discipleship_completed_at(person):
    completed_enrollment = get_completed_discipleship(person)
    if completed_enrollment is not None:
        return completed_enrollment.completed_at

    usuario = get_legacy_user_account(person)
    return getattr(usuario, "discipulado_concluido_em", None)


def get_completed_discipleship(person):
    if person is None:
        return None

    return (
        DiscipleshipEnrollment.objects.filter(
            person=person,
            status=DiscipleshipEnrollment.Status.COMPLETED,
        )
        .order_by("-completed_at", "-id")
        .first()
    )


def get_first_completed_discipleship(person):
    if person is None:
        return None

    return (
        DiscipleshipEnrollment.objects.filter(
            person=person,
            status=DiscipleshipEnrollment.Status.COMPLETED,
            completed_at__isnull=False,
        )
        .order_by("completed_at", "id")
        .first()
    )


def is_eligible_for_membership(person):
    return get_completed_discipleship(person) is not None


def can_create_membership(person):
    return is_eligible_for_membership(person) and not has_membership(person)


def get_membership_eligible_people():
    return (
        DiscipleshipEnrollment.objects.filter(
            status=DiscipleshipEnrollment.Status.COMPLETED,
            person__church_journey__isnull=False,
            person__membership__isnull=True,
        )
        .select_related("person")
        .order_by("completed_at", "person__full_name", "person_id")
    )


def get_frequency_eligible_lessons(enrollment):
    filters = Q(
        discipleship_class=enrollment.discipleship_class,
        lesson_date__gte=enrollment.enrolled_at,
    ) & ~Q(status=DiscipleshipLesson.Status.CANCELLED)

    if enrollment.withdrawn_at:
        filters &= Q(lesson_date__lte=enrollment.withdrawn_at)

    return DiscipleshipLesson.objects.filter(filters).order_by("lesson_date", "id")


def get_discipleship_attendance_summary(enrollment):
    eligible_lessons = list(get_frequency_eligible_lessons(enrollment))
    attendances = {
        attendance.lesson_id: attendance
        for attendance in DiscipleshipAttendance.objects.filter(
            enrollment=enrollment,
            lesson__in=eligible_lessons,
        )
    }
    present = 0
    absent = 0
    justified = 0
    not_recorded = 0

    for lesson in eligible_lessons:
        attendance = attendances.get(lesson.pk)
        if attendance is None:
            not_recorded += 1
        elif attendance.status == DiscipleshipAttendance.Status.PRESENT:
            present += 1
        elif attendance.status == DiscipleshipAttendance.Status.ABSENT:
            absent += 1
        elif attendance.status == DiscipleshipAttendance.Status.JUSTIFIED:
            justified += 1

    denominator = present + absent
    percentage = None
    if denominator:
        percentage = (present * 100) / denominator

    return {
        "eligible_lessons": len(eligible_lessons),
        "present": present,
        "absent": absent,
        "justified": justified,
        "not_recorded": not_recorded,
        "denominator": denominator,
        "percentage": percentage,
        "attendance_complete": not_recorded == 0,
    }


def get_discipleship_completion_eligibility(enrollment):
    summary = get_discipleship_attendance_summary(enrollment)

    if enrollment.status == DiscipleshipEnrollment.Status.COMPLETED:
        return {"can_complete": False, "reason": "ALREADY_COMPLETED", "summary": summary}
    if enrollment.status == DiscipleshipEnrollment.Status.WITHDRAWN:
        return {"can_complete": False, "reason": "ENROLLMENT_WITHDRAWN", "summary": summary}
    if enrollment.discipleship_class.status != "COMPLETED":
        return {"can_complete": False, "reason": "CLASS_NOT_COMPLETED", "summary": summary}
    if not summary["attendance_complete"]:
        return {"can_complete": False, "reason": "ATTENDANCE_INCOMPLETE", "summary": summary}
    if summary["denominator"] == 0:
        return {"can_complete": False, "reason": "NO_FREQUENCY_DENOMINATOR", "summary": summary}
    if summary["present"] * 100 < summary["denominator"] * MINIMUM_DISCIPLESHIP_ATTENDANCE_PERCENTAGE:
        return {"can_complete": False, "reason": "MINIMUM_ATTENDANCE_NOT_REACHED", "summary": summary}

    return {"can_complete": True, "reason": None, "summary": summary}


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
