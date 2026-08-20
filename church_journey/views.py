from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from pessoas.models import Person

from .models import (
    ChurchJourney,
    DiscipleshipAttendance,
    DiscipleshipClass,
    DiscipleshipClassAssistant,
    DiscipleshipEnrollment,
    DiscipleshipLesson,
)
from .serializers import (
    ChurchJourneySerializer,
    DiscipleshipAttendanceBatchSerializer,
    DiscipleshipAttendanceRecordSerializer,
    DiscipleshipClassSerializer,
    DiscipleshipEnrollmentSerializer,
    DiscipleshipLessonSerializer,
)
from .services import (
    ChurchJourneyError,
    cancel_discipleship_class,
    cancel_discipleship_lesson,
    complete_discipleship_enrollment,
    complete_discipleship_class,
    create_discipleship_class,
    create_discipleship_lesson,
    enroll_person_in_discipleship_class,
    get_eligible_enrollments_for_lesson,
    record_discipleship_attendance_batch,
    start_church_journey,
    start_discipleship_class,
    update_discipleship_class,
    update_discipleship_lesson,
    withdraw_discipleship_enrollment,
)
from .selectors import (
    MINIMUM_DISCIPLESHIP_ATTENDANCE_PERCENTAGE,
    get_discipleship_completion_eligibility,
    is_eligible_for_membership,
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


def user_is_class_teacher(user, discipleship_class):
    return bool(
        getattr(user, "is_authenticated", False)
        and getattr(user, "person_id", None)
        and user.person_id == discipleship_class.teacher_id
    )


def user_is_class_assistant(user, discipleship_class):
    return bool(
        getattr(user, "is_authenticated", False)
        and getattr(user, "person_id", None)
        and DiscipleshipClassAssistant.objects.filter(
            discipleship_class=discipleship_class,
            person_id=user.person_id,
        ).exists()
    )


def can_view_attendance(user, discipleship_class):
    return bool(
        getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
        and (
            user.has_perm("church_journey.view_discipleshipattendance")
            or user_is_class_teacher(user, discipleship_class)
            or user_is_class_assistant(user, discipleship_class)
        )
    )


def can_manage_attendance(user, discipleship_class):
    return bool(
        getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
        and (
            user.has_perm("church_journey.change_discipleshipattendance")
            or user_is_class_teacher(user, discipleship_class)
            or user_is_class_assistant(user, discipleship_class)
        )
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


class DiscipleshipLessonAttendanceView(APIView):
    def get_lesson(self, class_id, lesson_id):
        return get_object_or_404(
            DiscipleshipLesson.objects.select_related("discipleship_class__teacher"),
            pk=lesson_id,
            discipleship_class_id=class_id,
        )

    def get_attendance_payload(self, request, lesson):
        eligible_enrollments = list(get_eligible_enrollments_for_lesson(lesson))
        attendance_by_enrollment = {
            attendance.enrollment_id: attendance
            for attendance in DiscipleshipAttendance.objects.filter(
                lesson=lesson,
                enrollment__in=eligible_enrollments,
            ).select_related("recorded_by")
        }
        students = []
        recorded_count = 0
        present_count = 0
        absent_count = 0
        justified_count = 0

        for enrollment in eligible_enrollments:
            attendance = attendance_by_enrollment.get(enrollment.pk)
            if attendance:
                recorded_count += 1
                if attendance.status == DiscipleshipAttendance.Status.PRESENT:
                    present_count += 1
                elif attendance.status == DiscipleshipAttendance.Status.ABSENT:
                    absent_count += 1
                elif attendance.status == DiscipleshipAttendance.Status.JUSTIFIED:
                    justified_count += 1

            students.append(
                {
                    "enrollment_id": enrollment.pk,
                    "person": {
                        "id": enrollment.person_id,
                        "display_name": enrollment.person.display_name,
                    },
                    "attendance": (
                        DiscipleshipAttendanceRecordSerializer(attendance).data
                        if attendance
                        else None
                    ),
                }
            )

        return {
            "lesson": {
                "id": lesson.pk,
                "title": lesson.title,
                "lesson_date": lesson.lesson_date,
                "status": lesson.status,
            },
            "summary": {
                "eligible": len(eligible_enrollments),
                "recorded": recorded_count,
                "not_recorded": len(eligible_enrollments) - recorded_count,
                "present": present_count,
                "absent": absent_count,
                "justified": justified_count,
            },
            "permissions": {
                "can_view_attendance": can_view_attendance(request.user, lesson.discipleship_class),
                "can_manage_attendance": can_manage_attendance(request.user, lesson.discipleship_class),
            },
            "students": students,
        }

    def get(self, request, class_id, lesson_id):
        lesson = self.get_lesson(class_id, lesson_id)
        if not can_view_attendance(request.user, lesson.discipleship_class):
            return Response(status=status.HTTP_403_FORBIDDEN)

        return Response(self.get_attendance_payload(request, lesson))

    def post(self, request, class_id, lesson_id):
        lesson = self.get_lesson(class_id, lesson_id)
        if not can_manage_attendance(request.user, lesson.discipleship_class):
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = DiscipleshipAttendanceBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        records = serializer.validated_data["records"]

        try:
            record_discipleship_attendance_batch(
                lesson=lesson,
                records=records,
                recorded_by=request.user,
            )
        except ChurchJourneyError as exc:
            return Response(
                {"code": exc.code, "message": exc.message},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(self.get_attendance_payload(request, lesson))


class DiscipleshipEnrollmentCompletionView(APIView):
    def get_object(self, class_id, enrollment_id):
        return get_object_or_404(
            DiscipleshipEnrollment.objects.select_related("person", "discipleship_class__teacher"),
            pk=enrollment_id,
            discipleship_class_id=class_id,
        )

    def get_payload(self, enrollment):
        eligibility = get_discipleship_completion_eligibility(enrollment)
        summary = eligibility["summary"]
        return {
            "enrollment_id": enrollment.pk,
            "status": enrollment.status,
            "completed_at": enrollment.completed_at,
            "frequency": {
                "eligible_lessons": summary["eligible_lessons"],
                "present": summary["present"],
                "absent": summary["absent"],
                "justified": summary["justified"],
                "not_recorded": summary["not_recorded"],
                "denominator": summary["denominator"],
                "percentage": (
                    round(summary["percentage"], 2)
                    if summary["percentage"] is not None
                    else None
                ),
                "attendance_complete": summary["attendance_complete"],
            },
            "completion": {
                "can_complete": eligibility["can_complete"],
                "minimum_percentage": MINIMUM_DISCIPLESHIP_ATTENDANCE_PERCENTAGE,
                "reason": eligibility["reason"],
            },
            "membership_eligibility": is_eligible_for_membership(enrollment.person),
        }

    def get(self, request, class_id, enrollment_id):
        enrollment = self.get_object(class_id, enrollment_id)
        if not can_view_attendance(request.user, enrollment.discipleship_class):
            return Response(status=status.HTTP_403_FORBIDDEN)

        return Response(self.get_payload(enrollment))

    def post(self, request, class_id, enrollment_id):
        enrollment = self.get_object(class_id, enrollment_id)
        if not (
            request.user.is_authenticated
            and request.user.is_active
            and request.user.has_perm("church_journey.complete_discipleshipenrollment")
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)

        try:
            enrollment = complete_discipleship_enrollment(enrollment)
        except ChurchJourneyError as exc:
            return Response(
                {"code": exc.code, "message": exc.message},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(self.get_payload(enrollment))
