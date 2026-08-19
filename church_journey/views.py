from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from pessoas.models import Person

from .models import ChurchJourney
from .serializers import ChurchJourneySerializer
from .services import ChurchJourneyError, start_church_journey


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
