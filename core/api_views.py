from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from usuarios.roles import ACCESS_REQUEST_VIEW, MEMBERSHIP_VIEW, PEOPLE_VIEW

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
