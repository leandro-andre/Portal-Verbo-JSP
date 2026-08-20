from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from pessoas.models import Person

from .models import ChurchJourney, DiscipleshipClass
from .serializers import ChurchJourneySerializer, DiscipleshipClassSerializer
from .services import (
    ChurchJourneyError,
    cancel_discipleship_class,
    complete_discipleship_class,
    create_discipleship_class,
    start_church_journey,
    start_discipleship_class,
    update_discipleship_class,
)


ACTION_PERMISSIONS = {
    "GET": "church_journey.view_churchjourney",
    "POST": "church_journey.add_churchjourney",
}


class CanUseChurchJourney(BasePermission):
    def has_permission(self, request, view):
        permission = ACTION_PERMISSIONS.get(request.method)
        return bool(
            request.user.is_authenticated
            and request.user.is_active
            and permission is not None
            and request.user.has_perm(permission)
        )


class PersonChurchJourneyView(APIView):
    permission_classes = [CanUseChurchJourney]

    def get_person(self, person_id):
        return get_object_or_404(Person, pk=person_id)

    def get(self, request, person_id):
        person = self.get_person(person_id)
        journey = get_object_or_404(ChurchJourney, person=person)
        return Response(ChurchJourneySerializer(journey).data)

    def post(self, request, person_id):
        person = self.get_person(person_id)
        serializer = ChurchJourneySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            journey = start_church_journey(
                person,
                started_at=serializer.validated_data.get("started_at"),
            )
        except ChurchJourneyError as exc:
            return Response(
                {"code": exc.code, "message": exc.message},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(ChurchJourneySerializer(journey).data, status=status.HTTP_201_CREATED)


class HasDjangoPermission(BasePermission):
    permission_required = None

    def has_permission(self, request, view):
        permission = getattr(view, "permission_required", None)
        if permission is None:
            permission = getattr(view, "method_permissions", {}).get(request.method)
        return bool(
            request.user.is_authenticated
            and request.user.is_active
            and permission
            and request.user.has_perm(permission)
        )


class DiscipleshipClassListCreateView(APIView):
    permission_classes = [HasDjangoPermission]
    method_permissions = {
        "GET": "church_journey.view_discipleshipclass",
        "POST": "church_journey.add_discipleshipclass",
    }

    def get_queryset(self):
        return DiscipleshipClass.objects.select_related("teacher")

    def get(self, request):
        serializer = DiscipleshipClassSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = DiscipleshipClassSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        discipleship_class = create_discipleship_class(
            name=data["name"],
            teacher=data["teacher"],
            start_date=data["start_date"],
            expected_end_date=data["expected_end_date"],
            planned_sessions=data["planned_sessions"],
        )
        return Response(
            DiscipleshipClassSerializer(discipleship_class).data,
            status=status.HTTP_201_CREATED,
        )


class DiscipleshipClassDetailView(APIView):
    permission_classes = [HasDjangoPermission]
    method_permissions = {
        "GET": "church_journey.view_discipleshipclass",
        "PATCH": "church_journey.change_discipleshipclass",
        "DELETE": "church_journey.view_discipleshipclass",
    }

    def get_object(self, pk):
        return get_object_or_404(
            DiscipleshipClass.objects.select_related("teacher"),
            pk=pk,
        )

    def get(self, request, pk):
        return Response(DiscipleshipClassSerializer(self.get_object(pk)).data)

    def patch(self, request, pk):
        discipleship_class = self.get_object(pk)
        serializer = DiscipleshipClassSerializer(
            discipleship_class,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        try:
            discipleship_class = update_discipleship_class(
                discipleship_class,
                **serializer.validated_data,
            )
        except ChurchJourneyError as exc:
            return Response(
                {"code": exc.code, "message": exc.message},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(DiscipleshipClassSerializer(discipleship_class).data)


class DiscipleshipClassLifecycleView(APIView):
    permission_classes = [HasDjangoPermission]
    action = None
    permission_required = None

    def get_object(self, pk):
        return get_object_or_404(
            DiscipleshipClass.objects.select_related("teacher"),
            pk=pk,
        )

    def post(self, request, pk):
        discipleship_class = self.get_object(pk)

        try:
            if self.action == "start":
                discipleship_class = start_discipleship_class(discipleship_class)
            elif self.action == "complete":
                discipleship_class = complete_discipleship_class(discipleship_class)
            elif self.action == "cancel":
                discipleship_class = cancel_discipleship_class(discipleship_class)
            else:
                return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        except ChurchJourneyError as exc:
            return Response(
                {"code": exc.code, "message": exc.message},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(DiscipleshipClassSerializer(discipleship_class).data)
