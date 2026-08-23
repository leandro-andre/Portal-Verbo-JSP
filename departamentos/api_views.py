from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from pessoas.models import Person

from .models import Departamento, DepartmentMembership, DepartmentRole
from .selectors import (
    can_manage_department,
    can_manage_department_members,
    can_manage_department_roles,
    can_view_department,
    get_department_entry_eligibility,
)
from .serializers import (
    DepartmentDetailSerializer,
    DepartmentMembershipCreateSerializer,
    DepartmentMembershipSerializer,
    DepartmentMembershipUpdateSerializer,
    DepartmentPersonSerializer,
    DepartmentRoleCreateSerializer,
    DepartmentRoleSerializer,
    DepartmentRoleUpdateSerializer,
    DepartmentSerializer,
    DepartmentUpdateSerializer,
)
from .services import (
    DepartmentError,
    create_department_membership,
    create_department_role,
    deactivate_department,
    deactivate_department_membership,
    deactivate_department_role,
    reactivate_department,
    reactivate_department_membership,
    reactivate_department_role,
    update_department_membership_role,
    update_department_role,
)


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


class IsActiveAuthenticated(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.is_active)


def business_error_response(exc):
    return Response(
        {"code": exc.code, "message": exc.message},
        status=status.HTTP_409_CONFLICT,
    )


def ensure_or_403(condition):
    if not condition:
        raise PermissionDenied("Sua sessao atual nao possui permissao para acessar esta area.")


def can_manage_with_global_or_context(user, department, permission, context_checker):
    return bool(user.has_perm(permission) or context_checker(user, department))


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
    permission_classes = [IsActiveAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Departamento, pk=pk)

    def get(self, request, pk):
        department = self.get_object(pk)
        ensure_or_403(can_view_department(request.user, department))
        return Response(DepartmentDetailSerializer(department, context={"request": request}).data)

    def patch(self, request, pk):
        department = self.get_object(pk)
        ensure_or_403(
            can_manage_with_global_or_context(
                request.user,
                department,
                "departamentos.change_departamento",
                can_manage_department,
            )
        )
        serializer = DepartmentUpdateSerializer(department, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        department = serializer.save()
        return Response(DepartmentDetailSerializer(department, context={"request": request}).data)


class DepartmentDeactivateView(APIView):
    permission_classes = [HasDepartmentPermission]
    permission_required = "departamentos.deactivate_departamento"

    def post(self, request, pk):
        department = get_object_or_404(Departamento, pk=pk)
        try:
            department = deactivate_department(department)
        except DepartmentError as exc:
            return business_error_response(exc)
        return Response(DepartmentDetailSerializer(department, context={"request": request}).data)


class DepartmentReactivateView(APIView):
    permission_classes = [HasDepartmentPermission]
    permission_required = "departamentos.reactivate_departamento"

    def post(self, request, pk):
        department = get_object_or_404(Departamento, pk=pk)
        try:
            department = reactivate_department(department)
        except DepartmentError as exc:
            return business_error_response(exc)
        return Response(DepartmentDetailSerializer(department, context={"request": request}).data)


class DepartmentRoleListCreateView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get_department(self, department_id):
        return get_object_or_404(Departamento, pk=department_id)

    def get(self, request, department_id):
        department = self.get_department(department_id)
        ensure_or_403(
            request.user.has_perm("departamentos.view_departmentrole")
            or can_manage_department_roles(request.user, department)
        )
        roles = DepartmentRole.objects.filter(department=department).order_by("name", "id")
        return Response(DepartmentRoleSerializer(roles, many=True).data)

    def post(self, request, department_id):
        department = self.get_department(department_id)
        ensure_or_403(
            can_manage_with_global_or_context(
                request.user,
                department,
                "departamentos.add_departmentrole",
                can_manage_department_roles,
            )
        )
        serializer = DepartmentRoleCreateSerializer(data=request.data, context={"department": department})
        serializer.is_valid(raise_exception=True)
        try:
            role = create_department_role(department=department, **serializer.validated_data)
        except DepartmentError as exc:
            return business_error_response(exc)
        return Response(DepartmentRoleSerializer(role).data, status=status.HTTP_201_CREATED)


class DepartmentRoleDetailView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get_objects(self, department_id, role_id):
        department = get_object_or_404(Departamento, pk=department_id)
        role = get_object_or_404(DepartmentRole, pk=role_id, department=department)
        return department, role

    def get(self, request, department_id, role_id):
        department, role = self.get_objects(department_id, role_id)
        ensure_or_403(
            request.user.has_perm("departamentos.view_departmentrole")
            or can_manage_department_roles(request.user, department)
        )
        return Response(DepartmentRoleSerializer(role).data)

    def patch(self, request, department_id, role_id):
        department, role = self.get_objects(department_id, role_id)
        ensure_or_403(
            can_manage_with_global_or_context(
                request.user,
                department,
                "departamentos.change_departmentrole",
                can_manage_department_roles,
            )
        )
        serializer = DepartmentRoleUpdateSerializer(role, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            role = update_department_role(role, **serializer.validated_data)
        except DepartmentError as exc:
            return business_error_response(exc)
        return Response(DepartmentRoleSerializer(role).data)


class DepartmentRoleDeactivateView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request, department_id, role_id):
        department = get_object_or_404(Departamento, pk=department_id)
        role = get_object_or_404(DepartmentRole, pk=role_id, department=department)
        ensure_or_403(
            can_manage_with_global_or_context(
                request.user,
                department,
                "departamentos.deactivate_departmentrole",
                can_manage_department_roles,
            )
        )
        try:
            role = deactivate_department_role(role)
        except DepartmentError as exc:
            return business_error_response(exc)
        return Response(DepartmentRoleSerializer(role).data)


class DepartmentRoleReactivateView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request, department_id, role_id):
        department = get_object_or_404(Departamento, pk=department_id)
        role = get_object_or_404(DepartmentRole, pk=role_id, department=department)
        ensure_or_403(
            can_manage_with_global_or_context(
                request.user,
                department,
                "departamentos.reactivate_departmentrole",
                can_manage_department_roles,
            )
        )
        try:
            role = reactivate_department_role(role)
        except DepartmentError as exc:
            return business_error_response(exc)
        return Response(DepartmentRoleSerializer(role).data)


class DepartmentMembershipListCreateView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get_department(self, department_id):
        return get_object_or_404(Departamento, pk=department_id)

    def get(self, request, department_id):
        department = self.get_department(department_id)
        ensure_or_403(
            request.user.has_perm("departamentos.view_departmentmembership")
            or can_manage_department_members(request.user, department)
        )
        memberships = (
            DepartmentMembership.objects.filter(department=department)
            .select_related("person", "department", "role")
            .order_by("person__full_name", "id")
        )
        return Response(DepartmentMembershipSerializer(memberships, many=True).data)

    def post(self, request, department_id):
        department = self.get_department(department_id)
        ensure_or_403(
            can_manage_with_global_or_context(
                request.user,
                department,
                "departamentos.add_departmentmembership",
                can_manage_department_members,
            )
        )
        serializer = DepartmentMembershipCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            membership = create_department_membership(
                department=department,
                person=serializer.validated_data["person"],
                role=serializer.validated_data["role"],
                joined_at=serializer.validated_data.get("joined_at"),
            )
        except DepartmentError as exc:
            return business_error_response(exc)
        return Response(DepartmentMembershipSerializer(membership).data, status=status.HTTP_201_CREATED)


class DepartmentEligiblePeopleView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get(self, request, department_id):
        department = get_object_or_404(Departamento, pk=department_id)
        ensure_or_403(
            request.user.has_perm("departamentos.add_departmentmembership")
            or can_manage_department_members(request.user, department)
        )
        candidates = (
            Person.objects.filter(membership__status="ACTIVE")
            .exclude(department_memberships__department=department)
            .order_by("full_name", "id")
        )
        eligible_people = [
            person
            for person in candidates
            if get_department_entry_eligibility(person, department).eligible
        ]
        return Response(DepartmentPersonSerializer(eligible_people, many=True).data)


class DepartmentMembershipDetailView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def get_objects(self, department_id, membership_id):
        department = get_object_or_404(Departamento, pk=department_id)
        membership = get_object_or_404(
            DepartmentMembership.objects.select_related("person", "department", "role"),
            pk=membership_id,
            department=department,
        )
        return department, membership

    def get(self, request, department_id, membership_id):
        department, membership = self.get_objects(department_id, membership_id)
        ensure_or_403(
            request.user.has_perm("departamentos.view_departmentmembership")
            or can_manage_department_members(request.user, department)
        )
        return Response(DepartmentMembershipSerializer(membership).data)

    def patch(self, request, department_id, membership_id):
        department, membership = self.get_objects(department_id, membership_id)
        ensure_or_403(
            can_manage_with_global_or_context(
                request.user,
                department,
                "departamentos.change_departmentmembership",
                can_manage_department_members,
            )
        )
        serializer = DepartmentMembershipUpdateSerializer(membership, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            membership = update_department_membership_role(
                membership,
                role=serializer.validated_data["role"],
            )
        except DepartmentError as exc:
            return business_error_response(exc)
        return Response(DepartmentMembershipSerializer(membership).data)


class DepartmentMembershipDeactivateView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request, department_id, membership_id):
        department = get_object_or_404(Departamento, pk=department_id)
        membership = get_object_or_404(
            DepartmentMembership.objects.select_related("person", "department", "role"),
            pk=membership_id,
            department=department,
        )
        ensure_or_403(
            can_manage_with_global_or_context(
                request.user,
                department,
                "departamentos.deactivate_departmentmembership",
                can_manage_department_members,
            )
        )
        try:
            membership = deactivate_department_membership(membership)
        except DepartmentError as exc:
            return business_error_response(exc)
        return Response(DepartmentMembershipSerializer(membership).data)


class DepartmentMembershipReactivateView(APIView):
    permission_classes = [IsActiveAuthenticated]

    def post(self, request, department_id, membership_id):
        department = get_object_or_404(Departamento, pk=department_id)
        membership = get_object_or_404(
            DepartmentMembership.objects.select_related("person", "department", "role"),
            pk=membership_id,
            department=department,
        )
        ensure_or_403(
            can_manage_with_global_or_context(
                request.user,
                department,
                "departamentos.reactivate_departmentmembership",
                can_manage_department_members,
            )
        )
        try:
            membership = reactivate_department_membership(membership)
        except DepartmentError as exc:
            return business_error_response(exc)
        return Response(DepartmentMembershipSerializer(membership).data)
