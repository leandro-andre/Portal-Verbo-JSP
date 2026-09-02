from datetime import date as date_type, datetime, time as datetime_time

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.utils import timezone

from church_journey.models import ChurchJourney, DiscipleshipEnrollment, Membership, MembershipStatusHistory
from church_journey.selectors import (
    can_create_membership,
    get_church_status,
    get_completed_discipleship,
    get_discipleship_completed_at,
    get_membership,
    is_eligible_for_membership,
)
from departamentos.models import DepartmentMembership
from departamentos.selectors import get_department_membership_eligibility
from scheduling.models import Schedule, ScheduleAssignment
from usuarios.models import AccessRequest
from usuarios.services import AccessStatus, get_access_status
from worship.models import WorshipService

from .models import PersonUnavailability
from .serializers import get_photo_url


CHURCH_STATUS_LABELS = {
    "UNKNOWN": "Indefinida",
    "VISITOR": "Visitante",
    "MEMBER": "Membro ativo",
    "INACTIVE_MEMBER": "Membro inativo",
}

DISCIPLESHIP_STATUS_LABELS = {
    "NOT_STARTED": "Nao iniciado",
    "IN_PROGRESS": "Em andamento",
    "COMPLETED": "Concluido",
    "WITHDRAWN": "Desistente",
}

MEMBERSHIP_STATUS_LABELS = {
    Membership.Status.ACTIVE: "Membresia ativa",
    Membership.Status.INACTIVE: "Membresia inativa",
}

ACCESS_STATUS_LABELS = {
    AccessStatus.PENDING_APPROVAL: "Aguardando aprovacao",
    AccessStatus.PENDING_ACTIVATION: "Aguardando ativacao",
    AccessStatus.ACTIVE: "Conta ativa",
    AccessStatus.BLOCKED: "Conta bloqueada",
}


def _date(value):
    return value.isoformat() if value else None


def _datetime(value):
    return value.isoformat() if value else None


def _time(value):
    return value.isoformat(timespec="minutes") if value else None


def _date_or_datetime(value):
    if isinstance(value, datetime):
        return _datetime(value)
    return _date(value)


def _sort_datetime(value):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            value = date_type.fromisoformat(value)
    if isinstance(value, datetime):
        if timezone.is_naive(value):
            return timezone.make_aware(value, timezone.get_current_timezone())
        return value
    return timezone.make_aware(datetime.combine(value, datetime_time.min), timezone.get_current_timezone())


def _age(birth_date):
    if not birth_date:
        return None
    today = timezone.localdate()
    years = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years


def _person_payload(person, request):
    return {
        "id": person.id,
        "full_name": person.full_name,
        "preferred_name": person.preferred_name,
        "display_name": person.display_name,
        "birth_date": _date(person.birth_date),
        "age": _age(person.birth_date),
        "email": person.email,
        "phone": person.phone,
        "photo_url": get_photo_url(person, request),
        "status": person.status,
        "created_at": _datetime(person.created_at),
        "updated_at": _datetime(person.updated_at),
    }


def _church_payload(person):
    status = get_church_status(person).value
    journey = ChurchJourney.objects.filter(person=person).first()
    return {
        "status": status,
        "label": CHURCH_STATUS_LABELS[status],
        "has_church_journey": journey is not None,
        "started_at": _date(journey.started_at) if journey else None,
    }


def _discipleship_payload(person):
    completed = get_completed_discipleship(person)
    if completed is not None:
        enrollment = completed
        status = "COMPLETED"
    else:
        enrollment = (
            DiscipleshipEnrollment.objects.filter(person=person)
            .select_related("discipleship_class")
            .order_by("-enrolled_at", "-id")
            .first()
        )
        if enrollment is None:
            status = "NOT_STARTED"
        elif enrollment.status == DiscipleshipEnrollment.Status.ENROLLED:
            status = "IN_PROGRESS"
        elif enrollment.status == DiscipleshipEnrollment.Status.WITHDRAWN:
            status = "WITHDRAWN"
        else:
            status = enrollment.status

    return {
        "status": status,
        "label": DISCIPLESHIP_STATUS_LABELS.get(status, status),
        "enrolled_at": _date(enrollment.enrolled_at) if enrollment else None,
        "completed_at": _date(get_discipleship_completed_at(person)),
        "withdrawn_at": _date(enrollment.withdrawn_at) if enrollment else None,
        "class": (
            {
                "id": enrollment.discipleship_class_id,
                "name": enrollment.discipleship_class.name,
                "status": enrollment.discipleship_class.status,
                "start_date": _date(enrollment.discipleship_class.start_date),
                "expected_end_date": _date(enrollment.discipleship_class.expected_end_date),
            }
            if enrollment
            else None
        ),
        "membership_eligible": is_eligible_for_membership(person),
        "membership_can_create": can_create_membership(person),
    }


def _membership_payload(person):
    membership = get_membership(person)
    if membership is None:
        return {
            "has_membership": False,
            "status": None,
            "label": "Sem membresia",
            "member_since": None,
            "approved_at": None,
            "approved_by": None,
            "created_at": None,
            "updated_at": None,
        }

    return {
        "has_membership": True,
        "status": membership.status,
        "label": MEMBERSHIP_STATUS_LABELS[membership.status],
        "member_since": _date(membership.member_since),
        "approved_at": _datetime(membership.approved_at),
        "approved_by": (
            {
                "id": membership.approved_by_id,
                "display_name": membership.approved_by.display_name,
            }
            if membership.approved_by_id
            else None
        ),
        "created_at": _datetime(membership.created_at),
        "updated_at": _datetime(membership.updated_at),
    }


def _access_payload(person):
    try:
        usuario = person.user_account
    except ObjectDoesNotExist:
        usuario = None
    if usuario is None:
        return {
            "has_user": False,
            "id": None,
            "username": None,
            "email": None,
            "status": "NO_ACCESS",
            "label": "Sem acesso ao Portal",
            "is_active": False,
            "last_login": None,
            "date_joined": None,
        }

    status = get_access_status(usuario)
    return {
        "has_user": True,
        "id": usuario.id,
        "username": usuario.username,
        "email": usuario.email,
        "status": status,
        "label": ACCESS_STATUS_LABELS[status],
        "is_active": usuario.is_active,
        "last_login": _datetime(usuario.last_login),
        "date_joined": _datetime(usuario.date_joined),
    }


def _department_payload(department_membership):
    eligibility = get_department_membership_eligibility(department_membership)
    role = department_membership.role
    department = department_membership.department
    return {
        "id": department_membership.id,
        "status": department_membership.status,
        "joined_at": _date(department_membership.joined_at),
        "left_at": _date(department_membership.left_at),
        "department": {
            "id": department.id,
            "name": department.nome,
            "code": department.codigo,
            "active": department.ativo,
        },
        "role": {
            "id": role.id,
            "name": role.name,
            "code": role.code,
            "active": role.active,
            "can_manage_department": role.can_manage_department,
            "can_manage_members": role.can_manage_members,
            "can_manage_schedules": role.can_manage_schedules,
        },
        "operationally_eligible": eligibility.eligible,
        "eligibility": eligibility.as_dict(),
    }


def _departments_payload(person):
    memberships = (
        DepartmentMembership.objects.filter(person=person)
        .select_related("person", "department", "role")
        .order_by("department__nome", "role__name", "id")
    )
    active = []
    inactive = []
    for membership in memberships:
        payload = _department_payload(membership)
        if membership.status == DepartmentMembership.Status.ACTIVE:
            active.append(payload)
        else:
            inactive.append(payload)
    return {"active": active, "inactive": inactive}


def _schedule_assignment_payload(assignment):
    schedule = assignment.schedule
    worship_service = schedule.worship_service
    department = schedule.department
    department_membership = assignment.department_membership
    role = department_membership.role

    return {
        "id": assignment.id,
        "schedule_id": schedule.id,
        "schedule_status": schedule.status,
        "worship_service": {
            "id": worship_service.id,
            "name": worship_service.name,
            "date": _date(worship_service.date),
            "time": _time(worship_service.time),
            "status": worship_service.status,
            "kind": worship_service.kind,
        },
        "department": {
            "id": department.id,
            "name": department.nome,
            "code": department.codigo,
        },
        "role": {
            "id": role.id,
            "name": role.name,
            "code": role.code,
        },
        "assigned_at": _datetime(assignment.created_at),
    }


def _schedule_assignments_queryset(person):
    return (
        ScheduleAssignment.objects.filter(
            department_membership__person=person,
            schedule__status=Schedule.Status.PUBLISHED,
        )
        .exclude(schedule__worship_service__status=WorshipService.Status.CANCELLED)
        .select_related(
            "schedule",
            "schedule__department",
            "schedule__worship_service",
            "department_membership",
            "department_membership__role",
        )
    )


def _schedules_payload(person):
    today = timezone.localdate()
    upcoming = (
        _schedule_assignments_queryset(person)
        .filter(schedule__worship_service__date__gte=today)
        .order_by(
            "schedule__worship_service__date",
            "schedule__worship_service__time",
            "schedule__department__nome",
            "department_membership__role__name",
            "id",
        )[:20]
    )
    recent = (
        _schedule_assignments_queryset(person)
        .filter(schedule__worship_service__date__lt=today)
        .order_by(
            "-schedule__worship_service__date",
            "-schedule__worship_service__time",
            "schedule__department__nome",
            "department_membership__role__name",
            "id",
        )[:20]
    )

    return {
        "upcoming": [_schedule_assignment_payload(assignment) for assignment in upcoming],
        "recent": [_schedule_assignment_payload(assignment) for assignment in recent],
    }


def _unavailability_payload(unavailability):
    return {
        "id": unavailability.id,
        "start_date": _date(unavailability.start_date),
        "end_date": _date(unavailability.end_date),
        "start_time": _time(unavailability.start_time),
        "end_time": _time(unavailability.end_time),
        "is_full_day": unavailability.is_full_day,
        "status": unavailability.status,
        "created_at": _datetime(unavailability.created_at),
        "updated_at": _datetime(unavailability.updated_at),
    }


def _unavailabilities_payload(person):
    today = timezone.localdate()
    upcoming = (
        PersonUnavailability.objects.filter(
            person=person,
            status=PersonUnavailability.Status.ACTIVE,
            end_date__gte=today,
        )
        .order_by("start_date", "start_time", "end_date", "id")[:20]
    )
    return {"upcoming": [_unavailability_payload(unavailability) for unavailability in upcoming]}


def _timeline_item(code, label, occurred_at, source, description=""):
    return {
        "code": code,
        "label": label,
        "description": description,
        "occurred_at": _date_or_datetime(occurred_at),
        "date_only": not isinstance(occurred_at, datetime),
        "source": source,
    }


def _timeline_payload(person):
    items = []

    if person.created_at:
        items.append(_timeline_item("PERSON_CREATED", "Pessoa cadastrada", person.created_at, "pessoas.Person"))

    journey = ChurchJourney.objects.filter(person=person).first()
    if journey is not None:
        items.append(
            _timeline_item(
                "CHURCH_JOURNEY_STARTED",
                "Jornada eclesiastica iniciada",
                journey.started_at,
                "church_journey.ChurchJourney",
            )
        )

    enrollments = (
        DiscipleshipEnrollment.objects.filter(person=person)
        .select_related("discipleship_class")
        .order_by("-enrolled_at", "-id")[:10]
    )
    for enrollment in enrollments:
        items.append(
            _timeline_item(
                "DISCIPLESHIP_ENROLLED",
                "Discipulado iniciado",
                enrollment.enrolled_at,
                "church_journey.DiscipleshipEnrollment",
                enrollment.discipleship_class.name,
            )
        )
        if enrollment.completed_at:
            items.append(
                _timeline_item(
                    "DISCIPLESHIP_COMPLETED",
                    "Discipulado concluido",
                    enrollment.completed_at,
                    "church_journey.DiscipleshipEnrollment",
                    enrollment.discipleship_class.name,
                )
            )
        if enrollment.withdrawn_at:
            items.append(
                _timeline_item(
                    "DISCIPLESHIP_WITHDRAWN",
                    "Discipulado encerrado",
                    enrollment.withdrawn_at,
                    "church_journey.DiscipleshipEnrollment",
                    enrollment.discipleship_class.name,
                )
            )

    membership = get_membership(person)
    if membership is not None:
        items.append(_timeline_item("MEMBERSHIP_STARTED", "Membresia iniciada", membership.member_since, "church_journey.Membership"))
        if membership.approved_at:
            items.append(_timeline_item("MEMBERSHIP_APPROVED", "Membresia aprovada", membership.approved_at, "church_journey.Membership"))
        histories = MembershipStatusHistory.objects.filter(membership=membership).order_by("-changed_at", "-id")[:10]
        for history in histories:
            items.append(
                _timeline_item(
                    "MEMBERSHIP_STATUS_CHANGED",
                    "Status de membresia alterado",
                    history.changed_at,
                    "church_journey.MembershipStatusHistory",
                    f"{history.from_status} para {history.to_status}",
                )
            )

    for department_membership in (
        DepartmentMembership.objects.filter(person=person)
        .select_related("department", "role")
        .order_by("-joined_at", "-id")[:20]
    ):
        items.append(
            _timeline_item(
                "DEPARTMENT_JOINED",
                "Entrada em departamento",
                department_membership.joined_at,
                "departamentos.DepartmentMembership",
                f"{department_membership.department.nome} - {department_membership.role.name}",
            )
        )
        if department_membership.left_at:
            items.append(
                _timeline_item(
                    "DEPARTMENT_LEFT",
                    "Saida de departamento",
                    department_membership.left_at,
                    "departamentos.DepartmentMembership",
                    f"{department_membership.department.nome} - {department_membership.role.name}",
                )
            )

    try:
        usuario = person.user_account
    except ObjectDoesNotExist:
        usuario = None
    if usuario is not None and usuario.date_joined:
        items.append(_timeline_item("USER_CREATED", "Usuario do Portal criado", usuario.date_joined, "usuarios.Usuario"))

    access_request_filter = Q(person=person)
    if usuario is not None:
        access_request_filter |= Q(usuario=usuario)
    for access_request in (
        AccessRequest.objects.filter(access_request_filter)
        .select_related("reviewed_by")
        .distinct()
        .order_by("-created_at", "-id")[:10]
    ):
        items.append(_timeline_item("ACCESS_REQUESTED", "Solicitacao de acesso criada", access_request.created_at, "usuarios.AccessRequest"))
        if access_request.reviewed_at:
            label = "Solicitacao de acesso aprovada" if access_request.status == AccessRequest.Status.APPROVED else "Solicitacao de acesso revisada"
            items.append(_timeline_item("ACCESS_REQUEST_REVIEWED", label, access_request.reviewed_at, "usuarios.AccessRequest"))

    items = sorted(items, key=lambda item: _sort_datetime(item["occurred_at"]), reverse=True)
    return items[:30]


def _pending(code, severity, label):
    return {"code": code, "severity": severity, "label": label}


def _pending_items(*, person, access, membership, discipleship, departments):
    items = []
    if not access["has_user"]:
        items.append(_pending("NO_PORTAL_USER", "info", "Pessoa sem usuario vinculado ao Portal"))
    elif access["status"] == AccessStatus.PENDING_ACTIVATION:
        items.append(_pending("ACCOUNT_PENDING_ACTIVATION", "warning", "Conta aguardando ativacao"))
    elif access["status"] == AccessStatus.BLOCKED:
        items.append(_pending("ACCOUNT_BLOCKED", "danger", "Conta bloqueada"))

    if not (person.email or access["email"]):
        items.append(_pending("MISSING_EMAIL", "warning", "Cadastro sem e-mail"))
    if not person.phone:
        items.append(_pending("MISSING_PHONE", "warning", "Cadastro sem celular/WhatsApp"))
    if discipleship["membership_can_create"]:
        items.append(_pending("MEMBERSHIP_ELIGIBLE_PENDING_APPROVAL", "warning", "Elegivel para membresia aguardando aprovacao"))
    if membership["status"] == Membership.Status.INACTIVE:
        items.append(_pending("MEMBERSHIP_INACTIVE", "warning", "Membership inativa"))

    for department_membership in departments["active"]:
        if not department_membership["operationally_eligible"]:
            items.append(
                _pending(
                    "DEPARTMENT_MEMBERSHIP_OPERATIONALLY_INELIGIBLE",
                    "warning",
                    f"{department_membership['department']['name']}: vinculo ativo, mas inelegivel para escala",
                )
            )
    return items


def build_person_360(person, viewer=None, request=None):
    church = _church_payload(person)
    discipleship = _discipleship_payload(person)
    membership = _membership_payload(person)
    access = _access_payload(person)
    departments = _departments_payload(person)
    schedules = _schedules_payload(person)
    unavailability = _unavailabilities_payload(person)
    timeline = _timeline_payload(person)
    pending_items = _pending_items(
        person=person,
        access=access,
        membership=membership,
        discipleship=discipleship,
        departments=departments,
    )
    active_departments_count = len(departments["active"])

    return {
        "person": _person_payload(person, request),
        "church": church,
        "discipleship": discipleship,
        "membership": membership,
        "access": access,
        "departments": departments,
        "schedules": schedules,
        "unavailability": unavailability,
        "timeline": timeline,
        "pending_items": pending_items,
        "summary": {
            "church_label": church["label"],
            "discipleship_label": discipleship["label"],
            "membership_label": membership["label"],
            "access_label": access["label"],
            "active_departments_count": active_departments_count,
            "upcoming_schedules_count": len(schedules["upcoming"]),
            "next_schedule": schedules["upcoming"][0] if schedules["upcoming"] else None,
            "upcoming_unavailability_count": len(unavailability["upcoming"]),
            "next_unavailability": unavailability["upcoming"][0] if unavailability["upcoming"] else None,
        },
        "actions": {
            "edit_person_url": f"/pessoas/{person.id}/editar",
            "manage_access_url": f"/usuarios/{access['id']}" if access["has_user"] else None,
        },
    }
