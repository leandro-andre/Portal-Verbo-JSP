import json

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from rest_framework import status
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
    build_account_activation_path,
    reject_access_request,
)


PENDING_ACCESS_REQUEST_EXISTS_CODE = "PENDING_ACCESS_REQUEST_EXISTS"


def _json_request_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return None


def _current_user_payload(user):
    if not user.is_authenticated:
        return {"is_authenticated": False, "user": None}

    return {
        "is_authenticated": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "email": user.email,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        },
    }


@require_GET
@ensure_csrf_cookie
def csrf_view(request):
    return JsonResponse({"detail": "CSRF cookie set."})


@require_GET
def current_user_view(request):
    return JsonResponse(_current_user_payload(request.user))


@require_POST
@csrf_protect
def login_view(request):
    data = _json_request_body(request)
    if data is None:
        return JsonResponse(
            {"code": "INVALID_JSON", "message": "Informe um JSON valido."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    identifier = (data.get("username") or data.get("email") or "").strip()
    password = data.get("password") or ""
    if not identifier or not password:
        return JsonResponse(
            {
                "code": "INVALID_CREDENTIALS",
                "message": "Informe usuario/e-mail e senha.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    username = identifier
    user_model = get_user_model()
    if "@" in identifier:
        user = user_model.objects.filter(email__iexact=identifier).first()
        if user is not None:
            username = user.get_username()

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse(
            {
                "code": "INVALID_CREDENTIALS",
                "message": "Usuario/e-mail ou senha invalidos.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    login(request, user)
    return JsonResponse(_current_user_payload(user))


@require_POST
@csrf_protect
def logout_view(request):
    logout(request)
    return JsonResponse({"detail": "Logout realizado."})


@require_POST
@csrf_protect
def activate_account_view(request):
    data = _json_request_body(request)
    if data is None:
        return JsonResponse(
            {"code": "INVALID_JSON", "message": "Informe um JSON valido."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    uid = (data.get("uid") or "").strip()
    token = (data.get("token") or "").strip()
    password = data.get("password") or ""
    password_confirm = data.get("password_confirm") or ""
    errors = {}

    if not uid:
        errors["uid"] = ["Link de ativacao invalido."]
    if not token:
        errors["token"] = ["Link de ativacao invalido."]
    if not password:
        errors["password"] = ["Informe a nova senha."]
    if password != password_confirm:
        errors["password_confirm"] = ["As senhas nao conferem."]

    usuario = None
    if uid and token:
        user_model = get_user_model()
        try:
            user_pk = force_str(urlsafe_base64_decode(uid))
            usuario = user_model.objects.get(pk=user_pk)
        except (TypeError, ValueError, OverflowError, user_model.DoesNotExist):
            errors["token"] = ["Link de ativacao invalido."]

    if usuario is not None:
        if usuario.is_active:
            errors["token"] = ["Esta conta ja foi ativada."]
        elif not default_token_generator.check_token(usuario, token):
            errors["token"] = ["Link de ativacao invalido ou expirado."]

    if usuario is not None and password:
        try:
            validate_password(password, usuario)
        except DjangoValidationError as exc:
            errors["password"] = list(exc.messages)

    if errors:
        return JsonResponse(errors, status=status.HTTP_400_BAD_REQUEST)

    usuario.set_password(password)
    usuario.is_active = True
    usuario.save(update_fields=["password", "is_active"])
    return JsonResponse({"detail": "Conta ativada com sucesso."})


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
            "activation_url": request.build_absolute_uri(
                build_account_activation_path(usuario),
            ),
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
