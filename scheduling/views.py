from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from departamentos.models import DepartmentMembership
from departamentos.selectors import can_manage_department_schedules
from .models import Schedule, ScheduleAssignment
from .serializers import (
    MonthlyScheduleSerializer,
    MyScheduleAssignmentSerializer,
    ScheduleAssignmentCreateSerializer,
    ScheduleAssignmentSerializer,
    ScheduleCreateSerializer,
    ScheduleDetailSerializer,
    ScheduleSerializer,
    ScheduleValidationSerializer,
    serialize_assignment_candidates,
)
from .selectors import (
    get_department_monthly_schedule,
    get_person_schedule_assignments,
    get_schedule_composition_validation,
    get_schedule_departments_for_user,
)
from .services import (
    SchedulingError,
    cancel_schedule,
    create_schedule,
    create_schedule_assignment,
    delete_schedule_assignment,
    publish_schedule,
    reactivate_schedule,
    reopen_schedule,
)


def ensure_authenticated(user):
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        raise PermissionDenied("Autenticacao obrigatoria.")


def is_global_schedule_manager(user):
    return bool(
        user.has_perm("scheduling.add_schedule")
        and user.has_perm("scheduling.change_schedule")
        and user.has_perm("scheduling.add_scheduleassignment")
    )


def can_view_schedules(user):
    return bool(user.has_perm("scheduling.view_schedule") or user.has_perm("scheduling.view_scheduleassignment"))


def can_manage_schedule(user, department):
    if is_global_schedule_manager(user):
        return True
    return can_manage_department_schedules(user, department)


def get_contextual_schedule_department_ids(user):
    person_id = getattr(user, "person_id", None)
    if not person_id:
        return []
    return list(
        DepartmentMembership.objects.filter(
            person_id=person_id,
            status=DepartmentMembership.Status.ACTIVE,
            role__active=True,
            role__can_manage_schedules=True,
            department__ativo=True,
        ).values_list("department_id", flat=True)
    )


def business_error_response(error):
    payload = {"code": error.code, "message": error.message}
    if error.reasons:
        payload["reasons"] = error.reasons
    if error.details:
        payload.update(error.details)
    return Response(payload, status=status.HTTP_409_CONFLICT)


def get_schedule_or_404(pk):
    return get_object_or_404(
        Schedule.objects.select_related("department", "worship_service", "created_by").annotate(
            assignments_count=Count("assignments", distinct=True)
        ),
        pk=pk,
    )


class ScheduleListCreateView(APIView):
    def get(self, request):
        ensure_authenticated(request.user)
        contextual_department_ids = get_contextual_schedule_department_ids(request.user)
        if not can_view_schedules(request.user) and not contextual_department_ids:
            raise PermissionDenied("Sem permissao para visualizar escalas.")
        queryset = (
            Schedule.objects.select_related("department", "worship_service", "created_by")
            .annotate(assignments_count=Count("assignments", distinct=True))
            .order_by("worship_service__date", "worship_service__time", "department__nome")
        )
        department_id = request.query_params.get("department_id")
        worship_service_id = request.query_params.get("worship_service_id")
        year = request.query_params.get("year")
        month = request.query_params.get("month")
        status_filter = (request.query_params.get("status") or "").upper()
        if not can_view_schedules(request.user):
            queryset = queryset.filter(department_id__in=contextual_department_ids)
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if worship_service_id:
            queryset = queryset.filter(worship_service_id=worship_service_id)
        if year and month:
            queryset = queryset.filter(worship_service__date__year=year, worship_service__date__month=month)
        if status_filter in Schedule.Status.values:
            queryset = queryset.filter(status=status_filter)
        return Response(ScheduleSerializer(queryset, many=True, context={"request": request}).data)

    def post(self, request):
        ensure_authenticated(request.user)
        serializer = ScheduleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        department = serializer.validated_data["department"]
        if not can_manage_schedule(request.user, department):
            raise PermissionDenied("Sem permissao para criar escala neste departamento.")
        try:
            schedule = create_schedule(
                department=department,
                worship_service=serializer.validated_data["worship_service"],
                created_by=request.user,
            )
        except SchedulingError as error:
            return business_error_response(error)
        schedule.assignments_count = 0
        return Response(ScheduleSerializer(schedule, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ScheduleDepartmentListView(APIView):
    def get(self, request):
        ensure_authenticated(request.user)
        departments = get_schedule_departments_for_user(request.user)
        from .serializers import ScheduleDepartmentSerializer

        return Response(ScheduleDepartmentSerializer(departments, many=True).data)


class MySchedulesView(APIView):
    def get(self, request):
        ensure_authenticated(request.user)
        person = getattr(request.user, "person", None)
        scope = (request.query_params.get("scope") or "upcoming").lower()
        year = request.query_params.get("year")
        month = request.query_params.get("month")
        try:
            parsed_year = int(year) if year else None
            parsed_month = int(month) if month else None
        except ValueError:
            return Response({"message": "Informe ano e mes validos."}, status=status.HTTP_400_BAD_REQUEST)
        if parsed_month is not None and not 1 <= parsed_month <= 12:
            return Response({"message": "Informe um mes entre 1 e 12."}, status=status.HTTP_400_BAD_REQUEST)
        normalized_scope = scope if scope in {"upcoming", "history", "all"} else "upcoming"
        if person is None:
            return Response(
                {
                    "person_linked": False,
                    "scope": normalized_scope,
                    "items": [],
                }
            )
        assignments = get_person_schedule_assignments(
            person,
            scope=normalized_scope,
            year=parsed_year,
            month=parsed_month,
        )
        return Response(
            {
                "person_linked": True,
                "scope": normalized_scope,
                "items": MyScheduleAssignmentSerializer(assignments, many=True).data,
            }
        )


class MonthlyScheduleView(APIView):
    def get(self, request):
        ensure_authenticated(request.user)
        try:
            year = int(request.query_params.get("year", ""))
            month = int(request.query_params.get("month", ""))
        except ValueError:
            return Response({"message": "Informe ano e mes validos."}, status=status.HTTP_400_BAD_REQUEST)
        if not 1 <= month <= 12:
            return Response({"message": "Informe um mes entre 1 e 12."}, status=status.HTTP_400_BAD_REQUEST)
        department_id = request.query_params.get("department_id")
        from departamentos.models import Departamento

        department = get_object_or_404(Departamento, pk=department_id)
        if not can_view_schedules(request.user) and not can_manage_schedule(request.user, department):
            raise PermissionDenied("Sem permissao para visualizar escalas deste departamento.")
        projection = get_department_monthly_schedule(department=department, year=year, month=month, user=request.user)
        projection["permissions"] = {"can_manage": can_manage_schedule(request.user, department)}
        return Response(MonthlyScheduleSerializer(projection, context={"request": request}).data)


class ScheduleDetailView(APIView):
    def get(self, request, pk):
        ensure_authenticated(request.user)
        schedule = get_schedule_or_404(pk)
        if not can_view_schedules(request.user) and not can_manage_schedule(request.user, schedule.department):
            raise PermissionDenied("Sem permissao para visualizar escala.")
        return Response(ScheduleDetailSerializer(schedule, context={"request": request}).data)


class ScheduleValidationView(APIView):
    def get(self, request, pk):
        ensure_authenticated(request.user)
        schedule = get_schedule_or_404(pk)
        if not can_view_schedules(request.user) and not can_manage_schedule(request.user, schedule.department):
            raise PermissionDenied("Sem permissao para visualizar validacao da escala.")
        return Response(ScheduleValidationSerializer(get_schedule_composition_validation(schedule)).data)


class ScheduleLifecycleView(APIView):
    action = None

    def post(self, request, pk):
        ensure_authenticated(request.user)
        schedule = get_schedule_or_404(pk)
        if not can_manage_schedule(request.user, schedule.department):
            raise PermissionDenied("Sem permissao para administrar esta escala.")
        action_map = {
            "publish": publish_schedule,
            "reopen": reopen_schedule,
            "cancel": cancel_schedule,
            "reactivate": reactivate_schedule,
        }
        try:
            schedule = action_map[self.action](schedule)
        except SchedulingError as error:
            return business_error_response(error)
        schedule = get_schedule_or_404(schedule.pk)
        return Response(ScheduleDetailSerializer(schedule, context={"request": request}).data)


class SchedulePublishView(ScheduleLifecycleView):
    action = "publish"


class ScheduleReopenView(ScheduleLifecycleView):
    action = "reopen"


class ScheduleCancelView(ScheduleLifecycleView):
    action = "cancel"


class ScheduleReactivateView(ScheduleLifecycleView):
    action = "reactivate"


class ScheduleAssignmentListCreateView(APIView):
    def get_schedule(self, schedule_id):
        return get_schedule_or_404(schedule_id)

    def get(self, request, schedule_id):
        ensure_authenticated(request.user)
        schedule = self.get_schedule(schedule_id)
        if not can_view_schedules(request.user) and not can_manage_schedule(request.user, schedule.department):
            raise PermissionDenied("Sem permissao para visualizar escala.")
        return Response(ScheduleAssignmentSerializer(schedule.assignments.select_related("department_membership__person", "department_membership__role", "created_by"), many=True).data)

    def post(self, request, schedule_id):
        ensure_authenticated(request.user)
        schedule = self.get_schedule(schedule_id)
        if not can_manage_schedule(request.user, schedule.department):
            raise PermissionDenied("Sem permissao para administrar esta escala.")
        serializer = ScheduleAssignmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            assignment = create_schedule_assignment(
                schedule=schedule,
                department_membership=serializer.validated_data["department_membership"],
                created_by=request.user,
            )
        except SchedulingError as error:
            return business_error_response(error)
        return Response(ScheduleAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)


class ScheduleAssignmentDeleteView(APIView):
    def delete(self, request, schedule_id, assignment_id):
        ensure_authenticated(request.user)
        schedule = get_schedule_or_404(schedule_id)
        if not can_manage_schedule(request.user, schedule.department):
            raise PermissionDenied("Sem permissao para administrar esta escala.")
        assignment = get_object_or_404(ScheduleAssignment, pk=assignment_id, schedule=schedule)
        try:
            delete_schedule_assignment(assignment)
        except SchedulingError as error:
            return business_error_response(error)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ScheduleEligibleMembersView(APIView):
    def get(self, request, schedule_id):
        ensure_authenticated(request.user)
        schedule = get_schedule_or_404(schedule_id)
        if not can_view_schedules(request.user) and not can_manage_schedule(request.user, schedule.department):
            raise PermissionDenied("Sem permissao para visualizar candidatos.")
        candidates = serialize_assignment_candidates(schedule)
        role_id = request.query_params.get("role_id")
        if role_id:
            candidates = [
                candidate
                for candidate in candidates
                if str(candidate["department_membership"]["role"]["id"]) == str(role_id)
            ]
        return Response(candidates)
