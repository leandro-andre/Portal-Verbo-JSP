from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from pessoas.models import Person
from usuarios.permissions import usuario_tem_acesso_secretaria

from .models import AccessRequest
from .serializers import (
    AdminAccessRequestSerializer,
    ApproveAccessRequestSerializer,
    PublicAccessRequestCreateSerializer,
    RejectAccessRequestSerializer,
)
from .services import (
    AccessRequestError,
    approve_access_request,
    reject_access_request,
)


PENDING_ACCESS_REQUEST_EXISTS_CODE = "PENDING_ACCESS_REQUEST_EXISTS"


class CanReviewAccessRequests(BasePermission):
    def has_permission(self, request, view):
        return bool(usuario_tem_acesso_secretaria(request.user))


class PublicAccessRequestCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PublicAccessRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        pending_requests = AccessRequest.objects.pending_for_contact(
            email=data.get("email"),
            phone=data.get("phone"),
        )
        if pending_requests.exists():
            return Response(
                {
                    "code": PENDING_ACCESS_REQUEST_EXISTS_CODE,
                    "message": (
                        "Ja existe uma solicitacao de acesso pendente "
                        "para este e-mail ou telefone."
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AdminAccessRequestListView(APIView):
    permission_classes = [CanReviewAccessRequests]

    def get(self, request):
        status_filter = (request.query_params.get("status") or AccessRequest.Status.PENDING).upper()
        if status_filter not in AccessRequest.Status.values:
            status_filter = AccessRequest.Status.PENDING

        queryset = AccessRequest.objects.filter(status=status_filter).select_related(
            "person",
            "reviewed_by",
        )
        if status_filter == AccessRequest.Status.PENDING:
            queryset = queryset.order_by("created_at", "id")

        serializer = AdminAccessRequestSerializer(queryset, many=True)
        return Response(serializer.data)


class AdminAccessRequestDetailView(APIView):
    permission_classes = [CanReviewAccessRequests]

    def get_object(self, pk):
        return get_object_or_404(
            AccessRequest.objects.select_related("person", "reviewed_by"),
            pk=pk,
        )

    def get(self, request, pk):
        access_request = self.get_object(pk)
        access_request.candidate_people = list(
            Person.objects.possible_duplicates(
                full_name=access_request.full_name,
                birth_date=access_request.birth_date,
            )
        )
        serializer = AdminAccessRequestSerializer(access_request)
        return Response(serializer.data)


class AdminAccessRequestApproveView(APIView):
    permission_classes = [CanReviewAccessRequests]

    def post(self, request, pk):
        serializer = ApproveAccessRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        access_request = get_object_or_404(AccessRequest, pk=pk)

        try:
            approved_request, usuario = approve_access_request(
                access_request,
                reviewed_by=request.user,
                person_id=serializer.validated_data.get("person_id"),
                create_new_person=serializer.validated_data.get("create_new_person", False),
            )
        except AccessRequestError as exc:
            return Response(
                {"code": exc.code, "message": exc.message},
                status=status.HTTP_409_CONFLICT,
            )

        response_data = AdminAccessRequestSerializer(approved_request).data
        response_data["created_user"] = {
            "id": usuario.id,
            "username": usuario.username,
            "is_active": usuario.is_active,
        }
        return Response(response_data)


class AdminAccessRequestRejectView(APIView):
    permission_classes = [CanReviewAccessRequests]

    def post(self, request, pk):
        serializer = RejectAccessRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        access_request = get_object_or_404(AccessRequest, pk=pk)

        try:
            rejected_request = reject_access_request(
                access_request,
                reviewed_by=request.user,
                rejection_reason=serializer.validated_data.get("rejection_reason", ""),
            )
        except AccessRequestError as exc:
            return Response(
                {"code": exc.code, "message": exc.message},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(AdminAccessRequestSerializer(rejected_request).data)
