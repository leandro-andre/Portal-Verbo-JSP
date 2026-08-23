from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Departamento
from .serializers import DepartmentSerializer, DepartmentUpdateSerializer
from .services import DepartmentError, deactivate_department, reactivate_department


class HasDepartmentPermission(BasePermission):
    method_permissions = {
        "GET": "departamentos.view_departamento",
        "POST": "departamentos.add_departamento",
        "PATCH": "departamentos.change_departamento",
    }

    def has_permission(self, request, view):
        permission = getattr(view, "permission_required", None)
        if permission is None:
            permission = self.method_permissions.get(request.method)
        if permission is None:
            return bool(request.user.is_authenticated and request.user.is_active)
        return bool(
            request.user.is_authenticated
            and request.user.is_active
            and permission
            and request.user.has_perm(permission)
        )


class DepartmentListCreateView(APIView):
    permission_classes = [HasDepartmentPermission]

    def get(self, request):
        queryset = Departamento.objects.order_by("nome", "id")
        status_filter = (request.query_params.get("status") or "").upper()
        if status_filter == "ACTIVE":
            queryset = queryset.filter(ativo=True)
        elif status_filter == "INACTIVE":
            queryset = queryset.filter(ativo=False)
        return Response(DepartmentSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = DepartmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        department = serializer.save()
        return Response(DepartmentSerializer(department).data, status=status.HTTP_201_CREATED)


class DepartmentDetailView(APIView):
    permission_classes = [HasDepartmentPermission]

    def get_object(self, pk):
        return get_object_or_404(Departamento, pk=pk)

    def get(self, request, pk):
        return Response(DepartmentSerializer(self.get_object(pk)).data)

    def patch(self, request, pk):
        department = self.get_object(pk)
        serializer = DepartmentUpdateSerializer(department, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        department = serializer.save()
        return Response(DepartmentSerializer(department).data)


class DepartmentDeactivateView(APIView):
    permission_classes = [HasDepartmentPermission]
    permission_required = "departamentos.deactivate_departamento"

    def post(self, request, pk):
        department = get_object_or_404(Departamento, pk=pk)
        try:
            department = deactivate_department(department)
        except DepartmentError as exc:
            return Response(
                {"code": exc.code, "message": exc.message},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(DepartmentSerializer(department).data)


class DepartmentReactivateView(APIView):
    permission_classes = [HasDepartmentPermission]
    permission_required = "departamentos.reactivate_departamento"

    def post(self, request, pk):
        department = get_object_or_404(Departamento, pk=pk)
        try:
            department = reactivate_department(department)
        except DepartmentError as exc:
            return Response(
                {"code": exc.code, "message": exc.message},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(DepartmentSerializer(department).data)
