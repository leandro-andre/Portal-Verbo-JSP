from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from church_journey.models import ChurchJourney, DiscipleshipEnrollment, Membership
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
from usuarios.services import AccessStatus, get_access_status

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
        "pending_items": pending_items,
        "summary": {
            "church_label": church["label"],
            "discipleship_label": discipleship["label"],
            "membership_label": membership["label"],
            "access_label": access["label"],
            "active_departments_count": active_departments_count,
        },
        "actions": {
            "edit_person_url": f"/pessoas/{person.id}/editar",
            "manage_access_url": f"/usuarios/{access['id']}" if access["has_user"] else None,
        },
    }
