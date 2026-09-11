from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from core.notifications.selectors import (
    get_notifications_for_user,
    get_recent_notifications_for_user,
    get_unread_count_for_user,
)
from core.notifications.serializers import NotificationSerializer
from core.notifications.services import mark_all_notifications_read, mark_notification_read
from usuarios.roles import ACCESS_REQUEST_VIEW, MEMBERSHIP_VIEW, PEOPLE_VIEW

from .global_search import search_global
from .models import Notification
from .secretary_dashboard import build_secretary_dashboard


class CanViewSecretaryDashboard(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and request.user.is_active
            and request.user.has_perm(PEOPLE_VIEW)
            and request.user.has_perm(ACCESS_REQUEST_VIEW)
            and request.user.has_perm(MEMBERSHIP_VIEW)
        )


class SecretaryDashboardView(APIView):
    permission_classes = [CanViewSecretaryDashboard]

    def get(self, request):
        return Response(build_secretary_dashboard(viewer=request.user))


class IsActiveAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.is_active)


class GlobalSearchView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        return Response(
            search_global(
                viewer=request.user,
                query=request.query_params.get("q"),
                request=request,
            )
        )


class NotificationListView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", "0"))
        except ValueError:
            limit = 0
        queryset = get_notifications_for_user(request.user)
        if limit > 0:
            queryset = queryset[: min(limit, 100)]
        return Response(NotificationSerializer(queryset, many=True).data)


class NotificationRecentView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request):
        return Response(
            {
                "unread_count": get_unread_count_for_user(request.user),
                "items": NotificationSerializer(
                    get_recent_notifications_for_user(request.user, limit=10),
                    many=True,
                ).data,
            }
        )


class NotificationReadView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        mark_notification_read(notification=notification)
        return Response(NotificationSerializer(notification).data)


class NotificationReadAllView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request):
        updated = mark_all_notifications_read(recipient=request.user)
        return Response({"marked_count": updated, "unread_count": 0})
