from core.models import Notification


def get_notifications_for_user(user):
    return Notification.objects.filter(recipient=user).order_by("-created_at", "-id")


def get_recent_notifications_for_user(user, *, limit=10):
    return list(get_notifications_for_user(user)[:limit])


def get_unread_count_for_user(user):
    return Notification.objects.filter(recipient=user, read_at__isnull=True).count()
