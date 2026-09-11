from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone

from core.models import Notification

from . import types

MY_SCHEDULES_URL = "/minhas-escalas"


def create_notification(
    *,
    recipient,
    type,
    title,
    message,
    target_url="",
    source_app="",
    source_type="",
    source_id="",
    metadata=None,
):
    return Notification.objects.create(
        recipient=recipient,
        type=type,
        title=title,
        message=message,
        target_url=target_url or "",
        source_app=source_app or "",
        source_type=source_type or "",
        source_id=str(source_id or ""),
        metadata=metadata or {},
    )


def mark_notification_read(*, notification):
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
    return notification


def mark_all_notifications_read(*, recipient):
    return Notification.objects.filter(recipient=recipient, read_at__isnull=True).update(read_at=timezone.now())


def get_portal_user_for_person(person):
    try:
        return person.user_account
    except ObjectDoesNotExist:
        return None


def schedule_message(schedule, *, prefix):
    worship_service = schedule.worship_service
    return (
        f"{prefix} {schedule.department.nome} para "
        f"{worship_service.date:%d/%m/%Y} as {worship_service.time:%H:%M}."
    )


def _assignment_context(assignment):
    return {
        "recipient": get_portal_user_for_person(assignment.department_membership.person),
        "schedule": assignment.schedule,
        "source_id": assignment.id,
    }


def _notify_schedule_assignment(*, assignment, type, title, prefix):
    context = _assignment_context(assignment)
    recipient = context["recipient"]
    if recipient is None:
        return None
    schedule = context["schedule"]
    return create_notification(
        recipient=recipient,
        type=type,
        title=title,
        message=schedule_message(schedule, prefix=prefix),
        target_url=MY_SCHEDULES_URL,
        source_app="scheduling",
        source_type="ScheduleAssignment",
        source_id=context["source_id"],
    )


def notify_schedule_published(schedule):
    assignments = schedule.assignments.select_related(
        "department_membership__person__user_account",
        "schedule__department",
        "schedule__worship_service",
    )
    seen_recipients = set()
    created = []
    with transaction.atomic():
        for assignment in assignments:
            recipient = get_portal_user_for_person(assignment.department_membership.person)
            if recipient is None or recipient.pk in seen_recipients:
                continue
            seen_recipients.add(recipient.pk)
            created.append(
                create_notification(
                    recipient=recipient,
                    type=types.SCHEDULE_PUBLISHED,
                    title="Nova escala publicada",
                    message=schedule_message(schedule, prefix="Voce foi escalado em"),
                    target_url=MY_SCHEDULES_URL,
                    source_app="scheduling",
                    source_type="Schedule",
                    source_id=schedule.pk,
                )
            )
    return created


def notify_schedule_assignment_added(assignment):
    return _notify_schedule_assignment(
        assignment=assignment,
        type=types.SCHEDULE_ASSIGNMENT_ADDED,
        title="Voce foi incluido em uma escala",
        prefix="Voce foi adicionado a escala de",
    )


def notify_schedule_assignment_removed(assignment):
    return _notify_schedule_assignment(
        assignment=assignment,
        type=types.SCHEDULE_ASSIGNMENT_REMOVED,
        title="Alteracao na sua escala",
        prefix="Voce foi removido da escala de",
    )


def notify_schedule_cancelled(schedule):
    assignments = schedule.assignments.select_related(
        "department_membership__person__user_account",
        "schedule__department",
        "schedule__worship_service",
    )
    seen_recipients = set()
    created = []
    with transaction.atomic():
        for assignment in assignments:
            recipient = get_portal_user_for_person(assignment.department_membership.person)
            if recipient is None or recipient.pk in seen_recipients:
                continue
            seen_recipients.add(recipient.pk)
            created.append(
                create_notification(
                    recipient=recipient,
                    type=types.SCHEDULE_CANCELLED,
                    title="Escala cancelada",
                    message=schedule_message(schedule, prefix="A escala de"),
                    target_url=MY_SCHEDULES_URL,
                    source_app="scheduling",
                    source_type="Schedule",
                    source_id=schedule.pk,
                )
            )
    return created
