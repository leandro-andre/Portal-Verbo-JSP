from django.utils import timezone

from church_journey.enums import ChurchStatus
from church_journey.models import Membership
from church_journey.selectors import (
    get_discipleship_completed_at,
    has_church_journey,
    has_completed_discipleship,
)
from departamentos.models import DepartmentMembership
from pessoas.models import PersonUnavailability
from pessoas.serializers import get_photo_url
from scheduling.models import Schedule, ScheduleAssignment
from scheduling.selectors import get_my_schedule_assignment_warnings, get_upcoming_assignments_for_person
from worship.models import WorshipService


def _date(value):
    return value.isoformat() if value else None


def _time(value):
    return value.strftime("%H:%M") if value else None


def _membership_for(person):
    return getattr(person, "membership", None)


def _church_status_for(person):
    membership = _membership_for(person)
    if membership is not None:
        if membership.status == Membership.Status.ACTIVE:
            return ChurchStatus.MEMBER
        return ChurchStatus.INACTIVE_MEMBER
    if has_church_journey(person):
        return ChurchStatus.VISITOR
    return ChurchStatus.UNKNOWN


def _department_payload(membership):
    return {
        "id": membership.id,
        "status": membership.status,
        "joined_at": _date(membership.joined_at),
        "department": {
            "id": membership.department_id,
            "name": membership.department.nome,
            "code": membership.department.codigo,
        },
        "role": {
            "id": membership.role_id,
            "name": membership.role.name,
            "code": membership.role.code,
            "can_manage_schedules": membership.role.can_manage_schedules,
        },
    }


def _active_department_memberships(person):
    return (
        DepartmentMembership.objects.filter(
            person=person,
            status=DepartmentMembership.Status.ACTIVE,
            department__ativo=True,
        )
        .select_related("department", "role")
        .order_by("department__nome", "role__name", "id")
    )


def _next_schedule_payload(assignment):
    if assignment is None:
        return None
    schedule = assignment.schedule
    worship_service = schedule.worship_service
    membership = assignment.department_membership
    return {
        "assignment_id": assignment.id,
        "schedule_id": schedule.id,
        "date": _date(worship_service.date),
        "time": _time(worship_service.time),
        "worship_service": {
            "id": worship_service.id,
            "name": worship_service.name,
            "kind": worship_service.kind,
        },
        "department": {
            "id": schedule.department_id,
            "name": schedule.department.nome,
        },
        "role": {
            "id": membership.role_id,
            "name": membership.role.name,
        },
        "warnings": get_my_schedule_assignment_warnings(assignment),
    }


def _month_assignments_count(person, today):
    return ScheduleAssignment.objects.filter(
        department_membership__person=person,
        schedule__status=Schedule.Status.PUBLISHED,
        schedule__worship_service__status=WorshipService.Status.SCHEDULED,
        schedule__worship_service__date__year=today.year,
        schedule__worship_service__date__month=today.month,
    ).count()


def _unavailability_payload(person, today):
    queryset = (
        PersonUnavailability.objects.filter(
            person=person,
            status=PersonUnavailability.Status.ACTIVE,
            end_date__gte=today,
        )
        .order_by("start_date", "start_time", "id")
    )
    next_unavailability = queryset.first()
    return {
        "future_count": queryset.count(),
        "next": (
            {
                "id": next_unavailability.id,
                "start_date": _date(next_unavailability.start_date),
                "end_date": _date(next_unavailability.end_date),
                "start_time": _time(next_unavailability.start_time),
                "end_time": _time(next_unavailability.end_time),
                "is_full_day": next_unavailability.is_full_day,
            }
            if next_unavailability is not None
            else None
        ),
    }


def _profile_payload(person, request):
    membership = _membership_for(person)
    return {
        "id": person.id,
        "name": person.display_name,
        "full_name": person.full_name,
        "photo_url": get_photo_url(person, request),
        "church_status": _church_status_for(person).value,
        "member_since": _date(membership.member_since) if membership else None,
    }


def _journey_payload(person, departments):
    completed_at = get_discipleship_completed_at(person)
    return {
        "church_status": _church_status_for(person).value,
        "discipleship_completed": has_completed_discipleship(person),
        "discipleship_completed_at": _date(completed_at),
        "departments": departments,
    }


def _contextual_access_payload(departments):
    manageable = [
        item
        for item in departments
        if item["role"]["can_manage_schedules"]
    ]
    return {
        "can_manage_schedules": bool(manageable),
        "schedule_departments": [
            {
                "id": item["department"]["id"],
                "name": item["department"]["name"],
                "role": item["role"]["name"],
            }
            for item in manageable
        ],
    }


def get_user_dashboard(user, request=None, *, today=None):
    current_date = today or timezone.localdate()
    display_name = getattr(user, "display_name", "") or user.get_username()
    account = {
        "id": user.id,
        "username": user.get_username(),
        "display_name": display_name,
    }
    person = getattr(user, "person", None)
    if person is None:
        return {
            "person_linked": False,
            "account": account,
            "profile": None,
            "next_schedule": None,
            "schedules_summary": {"upcoming_count": 0, "month_count": 0},
            "unavailability": {"future_count": 0, "next": None},
            "journey": {"church_status": ChurchStatus.UNKNOWN.value, "discipleship_completed": False, "discipleship_completed_at": None, "departments": []},
            "contextual_access": {"can_manage_schedules": False, "schedule_departments": []},
            "message": "Seu acesso ainda nao esta vinculado a uma pessoa. Procure a Secretaria para revisar seu cadastro.",
        }

    person = (
        person.__class__.objects.select_related("membership", "church_journey")
        .filter(pk=person.pk)
        .first()
    ) or person
    departments = [_department_payload(membership) for membership in _active_department_memberships(person)]
    upcoming_assignments = get_upcoming_assignments_for_person(person, today=current_date)
    next_assignment = upcoming_assignments.first()
    return {
        "person_linked": True,
        "account": account,
        "profile": _profile_payload(person, request),
        "next_schedule": _next_schedule_payload(next_assignment),
        "schedules_summary": {
            "upcoming_count": upcoming_assignments.count(),
            "month_count": _month_assignments_count(person, current_date),
        },
        "unavailability": _unavailability_payload(person, current_date),
        "journey": _journey_payload(person, departments),
        "contextual_access": _contextual_access_payload(departments),
        "message": "",
    }
