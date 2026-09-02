from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from .availability import (
    UnavailabilityError,
    create_person_unavailability,
    deactivate_unavailability,
    reactivate_unavailability,
    update_person_unavailability,
)
from .models import Person, PersonUnavailability
from .projections import build_person_360
from .serializers import PersonSerializer, PersonUnavailabilitySerializer


POSSIBLE_DUPLICATE_CODE = "POSSIBLE_DUPLICATE"
ACTION_PERMISSIONS = {
    "list": "pessoas.view_person",
    "retrieve": "pessoas.view_person",
    "create": "pessoas.add_person",
    "update": "pessoas.change_person",
    "partial_update": "pessoas.change_person",
}


class IsActiveAuthenticated(BasePermission):
    def has_permission(self, request, view):
        permission = ACTION_PERMISSIONS.get(getattr(view, "action", None))
        return bool(
            request.user.is_authenticated
            and request.user.is_active
            and (permission is None or request.user.has_perm(permission))
        )


class PersonViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsActiveAuthenticated]
    serializer_class = PersonSerializer
    queryset = Person.objects.all()
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        queryset = super().get_queryset()
        search = (self.request.query_params.get("q") or "").strip()
        if search:
            queryset = queryset.filter(
                models.Q(full_name__icontains=search)
                | models.Q(preferred_name__icontains=search)
                | models.Q(email__icontains=search)
            )
        return queryset

    def _possible_duplicate_response(self, duplicates):
        return Response(
            {
                "code": POSSIBLE_DUPLICATE_CODE,
                "message": (
                    "Encontramos uma pessoa com o mesmo nome completo "
                    "e data de nascimento."
                ),
                "candidates": [
                    {
                        "id": person.id,
                        "display_name": person.display_name,
                        "full_name": person.full_name,
                        "birth_date": person.birth_date.isoformat(),
                    }
                    for person in duplicates
                ],
            },
            status=status.HTTP_409_CONFLICT,
        )

    def _get_possible_duplicates(self, serializer):
        data = serializer.validated_data
        duplicates = Person.objects.possible_duplicates(
            full_name=data.get("full_name"),
            birth_date=data.get("birth_date"),
        )

        if serializer.instance is not None:
            duplicates = duplicates.exclude(pk=serializer.instance.pk)

        return duplicates

    def _requires_duplicate_confirmation(self, serializer):
        if serializer.instance is not None:
            submitted_fields = set(serializer.initial_data.keys())
            if not submitted_fields.intersection({"full_name", "birth_date"}):
                return None

        allow_possible_duplicate = serializer.validated_data.get(
            "allow_possible_duplicate",
            False,
        )
        duplicates = self._get_possible_duplicates(serializer)
        return duplicates if duplicates.exists() and not allow_possible_duplicate else None

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        duplicates = self._requires_duplicate_confirmation(serializer)

        if duplicates is not None:
            return self._possible_duplicate_response(duplicates)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        duplicates = self._requires_duplicate_confirmation(serializer)

        if duplicates is not None:
            return self._possible_duplicate_response(duplicates)

        self.perform_update(serializer)
        return Response(serializer.data)


class CanViewPerson360(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and request.user.is_active
            and request.user.has_perm("pessoas.view_person")
        )


class Person360View(APIView):
    permission_classes = [CanViewPerson360]

    def get(self, request, person_id):
        person = get_object_or_404(Person, pk=person_id)
        return Response(build_person_360(person, viewer=request.user, request=request))


class IsActiveUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.is_active)


def business_error_response(exc):
    return Response({"code": exc.code, "message": exc.message}, status=status.HTTP_409_CONFLICT)


def get_request_person_or_403(user):
    person = getattr(user, "person", None)
    if person is None:
        raise PermissionDenied("Sua conta nao esta vinculada a uma pessoa.")
    return person


def user_can_manage_any_unavailability(user):
    return bool(
        user.has_perm("pessoas.add_personunavailability")
        and user.has_perm("pessoas.change_personunavailability")
    )


def user_can_view_any_unavailability(user):
    return bool(user.has_perm("pessoas.view_personunavailability"))


class BaseUnavailabilityView(APIView):
    permission_classes = [IsActiveUser]

    def serialize(self, unavailability):
        return PersonUnavailabilitySerializer(unavailability).data

    def list_for_person(self, person):
        queryset = person.unavailabilities.order_by("-start_date", "-id")
        return Response(PersonUnavailabilitySerializer(queryset, many=True).data)

    def create_for_person(self, request, person):
        serializer = PersonUnavailabilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            unavailability = create_person_unavailability(person=person, **serializer.validated_data)
        except UnavailabilityError as exc:
            return business_error_response(exc)
        return Response(self.serialize(unavailability), status=status.HTTP_201_CREATED)

    def update_unavailability(self, request, unavailability):
        serializer = PersonUnavailabilitySerializer(unavailability, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            unavailability = update_person_unavailability(unavailability, **serializer.validated_data)
        except UnavailabilityError as exc:
            return business_error_response(exc)
        return Response(self.serialize(unavailability))

    def deactivate(self, unavailability):
        try:
            unavailability = deactivate_unavailability(unavailability)
        except UnavailabilityError as exc:
            return business_error_response(exc)
        return Response(self.serialize(unavailability))

    def reactivate(self, unavailability):
        try:
            unavailability = reactivate_unavailability(unavailability)
        except UnavailabilityError as exc:
            return business_error_response(exc)
        return Response(self.serialize(unavailability))


class MyUnavailabilityListCreateView(BaseUnavailabilityView):
    def get(self, request):
        return self.list_for_person(get_request_person_or_403(request.user))

    def post(self, request):
        return self.create_for_person(request, get_request_person_or_403(request.user))


class MyUnavailabilityDetailView(BaseUnavailabilityView):
    def get_object(self, request, pk):
        person = get_request_person_or_403(request.user)
        return get_object_or_404(PersonUnavailability, pk=pk, person=person)

    def get(self, request, pk):
        return Response(self.serialize(self.get_object(request, pk)))

    def patch(self, request, pk):
        return self.update_unavailability(request, self.get_object(request, pk))


class MyUnavailabilityDeactivateView(BaseUnavailabilityView):
    def post(self, request, pk):
        return self.deactivate(get_object_or_404(PersonUnavailability, pk=pk, person=get_request_person_or_403(request.user)))


class MyUnavailabilityReactivateView(BaseUnavailabilityView):
    def post(self, request, pk):
        return self.reactivate(get_object_or_404(PersonUnavailability, pk=pk, person=get_request_person_or_403(request.user)))


class PersonUnavailabilityListCreateView(BaseUnavailabilityView):
    def get_person(self, person_id):
        return get_object_or_404(Person, pk=person_id)

    def get(self, request, person_id):
        if not user_can_view_any_unavailability(request.user):
            raise PermissionDenied("Sua sessao atual nao possui permissao para visualizar indisponibilidades.")
        return self.list_for_person(self.get_person(person_id))

    def post(self, request, person_id):
        if not user_can_manage_any_unavailability(request.user):
            raise PermissionDenied("Sua sessao atual nao possui permissao para gerenciar indisponibilidades.")
        return self.create_for_person(request, self.get_person(person_id))


class PersonUnavailabilityDetailView(BaseUnavailabilityView):
    def get_object(self, person_id, pk):
        return get_object_or_404(PersonUnavailability, pk=pk, person_id=person_id)

    def get(self, request, person_id, pk):
        if not user_can_view_any_unavailability(request.user):
            raise PermissionDenied("Sua sessao atual nao possui permissao para visualizar indisponibilidades.")
        return Response(self.serialize(self.get_object(person_id, pk)))

    def patch(self, request, person_id, pk):
        if not user_can_manage_any_unavailability(request.user):
            raise PermissionDenied("Sua sessao atual nao possui permissao para gerenciar indisponibilidades.")
        return self.update_unavailability(request, self.get_object(person_id, pk))


class PersonUnavailabilityDeactivateView(BaseUnavailabilityView):
    def post(self, request, person_id, pk):
        if not request.user.has_perm("pessoas.deactivate_personunavailability"):
            raise PermissionDenied("Sua sessao atual nao possui permissao para inativar indisponibilidades.")
        return self.deactivate(get_object_or_404(PersonUnavailability, pk=pk, person_id=person_id))


class PersonUnavailabilityReactivateView(BaseUnavailabilityView):
    def post(self, request, person_id, pk):
        if not request.user.has_perm("pessoas.reactivate_personunavailability"):
            raise PermissionDenied("Sua sessao atual nao possui permissao para reativar indisponibilidades.")
        return self.reactivate(get_object_or_404(PersonUnavailability, pk=pk, person_id=person_id))
