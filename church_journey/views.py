from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from pessoas.models import Person

from .models import ChurchJourney, DiscipleshipClass, DiscipleshipEnrollment, DiscipleshipLesson
from .serializers import (
    ChurchJourneySerializer,
    DiscipleshipClassSerializer,
    DiscipleshipEnrollmentSerializer,
    DiscipleshipLessonSerializer,
)
from .services import (
    ChurchJourneyError,
    cancel_discipleship_class,
    cancel_discipleship_lesson,
    complete_discipleship_class,
    create_discipleship_class,
    create_discipleship_lesson,
    enroll_person_in_discipleship_class,
    start_church_journey,
    start_discipleship_class,
    update_discipleship_class,
    update_discipleship_lesson,
    withdraw_discipleship_enrollment,
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


class DiscipleshipEnrollmentListCreateView(APIView):
    permission_classes = [HasDjangoPermission]
    method_permissions = {
        "GET": "church_journey.view_discipleshipenrollment",
        "POST": "church_journey.add_discipleshipenrollment",
    }

    def get_class(self, class_id):
        return get_object_or_404(DiscipleshipClass, pk=class_id)

    def get_queryset(self, class_id):
        return (
            DiscipleshipEnrollment.objects.filter(discipleship_class_id=class_id)
            .select_related("person", "discipleship_class")
            .order_by("person__full_name", "id")
        )

    def get(self, request, class_id):
        self.get_class(class_id)
        serializer = DiscipleshipEnrollmentSerializer(self.get_queryset(class_id), many=True)
        return Response(serializer.data)

    def post(self, request, class_id):
        discipleship_class = self.get_class(class_id)
        serializer = DiscipleshipEnrollmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            enrollment = enroll_person_in_discipleship_class(
                person=serializer.validated_data["person"],
                discipleship_class=discipleship_class,
            )
        except ChurchJourneyError as exc:
            return Response(
                {"code": exc.code, "message": exc.message},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            DiscipleshipEnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED,
        )


class DiscipleshipEnrollmentDetailView(APIView):
    permission_classes = [HasDjangoPermission]
    method_permissions = {
        "GET": "church_journey.view_discipleshipenrollment",
        "DELETE": "church_journey.view_discipleshipenrollment",
    }

    def get_object(self, class_id, pk):
        return get_object_or_404(
            DiscipleshipEnrollment.objects.select_related("person", "discipleship_class"),
            pk=pk,
            discipleship_class_id=class_id,
        )

    def get(self, request, class_id, pk):
        return Response(DiscipleshipEnrollmentSerializer(self.get_object(class_id, pk)).data)


class DiscipleshipEnrollmentWithdrawView(APIView):
    permission_classes = [HasDjangoPermission]
    permission_required = "church_journey.withdraw_discipleshipenrollment"

    def get_object(self, class_id, pk):
        return get_object_or_404(
            DiscipleshipEnrollment.objects.select_related("person", "discipleship_class"),
            pk=pk,
            discipleship_class_id=class_id,
        )

    def post(self, request, class_id, pk):
        try:
            enrollment = withdraw_discipleship_enrollment(self.get_object(class_id, pk))
        except ChurchJourneyError as exc:
            return Response(
                {"code": exc.code, "message": exc.message},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(DiscipleshipEnrollmentSerializer(enrollment).data)


class DiscipleshipLessonListCreateView(APIView):
    permission_classes = [HasDjangoPermission]
    method_permissions = {
        "GET": "church_journey.view_discipleshiplesson",
        "POST": "church_journey.add_discipleshiplesson",
    }

    def get_class(self, class_id):
        return get_object_or_404(DiscipleshipClass, pk=class_id)

    def get_queryset(self, class_id):
        return DiscipleshipLesson.objects.filter(discipleship_class_id=class_id).order_by(
            "lesson_date",
            "id",
        )

    def get(self, request, class_id):
        self.get_class(class_id)
        serializer = DiscipleshipLessonSerializer(self.get_queryset(class_id), many=True)
        return Response(serializer.data)

    def post(self, request, class_id):
        discipleship_class = self.get_class(class_id)
        serializer = DiscipleshipLessonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            lesson = create_discipleship_lesson(
                discipleship_class=discipleship_class,
                title=serializer.validated_data["title"],
                lesson_date=serializer.validated_data["lesson_date"],
            )
        except ChurchJourneyError as exc:
            return Response(
                {"code": exc.code, "message": exc.message},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            DiscipleshipLessonSerializer(lesson).data,
            status=status.HTTP_201_CREATED,
        )


class DiscipleshipLessonDetailView(APIView):
    permission_classes = [HasDjangoPermission]
    method_permissions = {
        "GET": "church_journey.view_discipleshiplesson",
        "PATCH": "church_journey.change_discipleshiplesson",
        "DELETE": "church_journey.view_discipleshiplesson",
    }

    def get_object(self, class_id, pk):
        return get_object_or_404(
            DiscipleshipLesson,
            pk=pk,
            discipleship_class_id=class_id,
        )

    def get(self, request, class_id, pk):
        return Response(DiscipleshipLessonSerializer(self.get_object(class_id, pk)).data)

    def patch(self, request, class_id, pk):
        lesson = self.get_object(class_id, pk)
        serializer = DiscipleshipLessonSerializer(lesson, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            lesson = update_discipleship_lesson(lesson, **serializer.validated_data)
        except ChurchJourneyError as exc:
            return Response(
                {"code": exc.code, "message": exc.message},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(DiscipleshipLessonSerializer(lesson).data)


class DiscipleshipLessonCancelView(APIView):
    permission_classes = [HasDjangoPermission]
    permission_required = "church_journey.cancel_discipleshiplesson"

    def get_object(self, class_id, pk):
        return get_object_or_404(
            DiscipleshipLesson,
            pk=pk,
            discipleship_class_id=class_id,
        )

    def post(self, request, class_id, pk):
        try:
            lesson = cancel_discipleship_lesson(self.get_object(class_id, pk))
        except ChurchJourneyError as exc:
            return Response(
                {"code": exc.code, "message": exc.message},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(DiscipleshipLessonSerializer(lesson).data)
