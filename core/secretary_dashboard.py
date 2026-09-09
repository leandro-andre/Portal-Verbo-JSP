from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from church_journey.models import ChurchJourney, Membership
from church_journey.selectors import get_membership_eligible_people
from departamentos.models import DepartmentMembership
from departamentos.selectors import get_department_membership_eligibility
from pessoas.models import Person
from usuarios.models import AccessRequest
from usuarios.services import AccessStatus, get_access_status


PREVIEW_LIMIT = 5


def _date(value):
    return value.isoformat() if value else None


def _datetime(value):
    return value.isoformat() if value else None


def _person_summary(person):
    return {
        "id": person.id,
        "display_name": person.display_name,
        "full_name": person.full_name,
        "email": person.email,
        "phone": person.phone,
        "profile_url": f"/pessoas/{person.id}",
        "edit_url": f"/pessoas/{person.id}/editar",
    }


def _access_request_item(access_request):
    return {
        "id": access_request.id,
        "full_name": access_request.full_name,
        "email": access_request.email,
        "phone": access_request.phone,
        "created_at": _datetime(access_request.created_at),
        "review_url": f"/solicitacoes-acesso/{access_request.id}",
    }


def _access_requests_payload():
    queryset = AccessRequest.objects.filter(status=AccessRequest.Status.PENDING).order_by("created_at", "id")
    return {
        "count": queryset.count(),
        "items": [_access_request_item(item) for item in queryset[:PREVIEW_LIMIT]],
        "list_url": "/solicitacoes-acesso",
    }


def _membership_approval_item(enrollment):
    person = enrollment.person
    return {
        "person": _person_summary(person),
        "completed_at": _date(enrollment.completed_at),
        "detail": "Discipulado concluido",
        "resolution_url": f"/pessoas/{person.id}",
    }


def _membership_approvals_payload():
    queryset = get_membership_eligible_people()
    return {
        "count": queryset.count(),
        "items": [_membership_approval_item(item) for item in queryset[:PREVIEW_LIMIT]],
        "list_url": "/membresia",
    }


def _activation_item(usuario):
    person = usuario.person
    return {
        "user": {
            "id": usuario.id,
            "username": usuario.username,
            "email": usuario.email,
            "detail_url": f"/usuarios/{usuario.id}",
        },
        "person": _person_summary(person) if person else None,
        "date_joined": _datetime(usuario.date_joined),
        "resolution_url": f"/usuarios/{usuario.id}",
    }


def _pending_activation_payload():
    user_model = get_user_model()
    candidates = (
        user_model.objects.filter(is_active=False)
        .select_related("person")
        .order_by("date_joined", "id")
    )
    items = [usuario for usuario in candidates if get_access_status(usuario) == AccessStatus.PENDING_ACTIVATION]
    return {
        "count": len(items),
        "items": [_activation_item(usuario) for usuario in items[:PREVIEW_LIMIT]],
        "list_url": "/usuarios",
    }


def _incomplete_profile_item(person):
    missing = []
    if not person.email:
        missing.append("MISSING_EMAIL")
    if not person.phone:
        missing.append("MISSING_WHATSAPP")
    return {
        "person": _person_summary(person),
        "missing": missing,
        "resolution_url": f"/pessoas/{person.id}/editar",
    }


def _incomplete_profiles_payload():
    queryset = Person.objects.filter(Q(email="") | Q(phone="")).order_by("full_name", "id")
    return {
        "count": queryset.count(),
        "missing_email_count": Person.objects.filter(email="").count(),
        "missing_whatsapp_count": Person.objects.filter(phone="").count(),
        "items": [_incomplete_profile_item(person) for person in queryset[:PREVIEW_LIMIT]],
        "list_url": "/pessoas",
    }


def _department_eligibility_item(membership, eligibility):
    return {
        "id": membership.id,
        "person": _person_summary(membership.person),
        "department": {
            "id": membership.department_id,
            "name": membership.department.nome,
            "code": membership.department.codigo,
        },
        "role": {
            "id": membership.role_id,
            "name": membership.role.name,
            "code": membership.role.code,
        },
        "status": membership.status,
        "reasons": [reason.as_dict() for reason in eligibility.reasons],
        "resolution_url": f"/pessoas/{membership.person_id}",
    }


def _department_eligibility_payload():
    queryset = (
        DepartmentMembership.objects.filter(status=DepartmentMembership.Status.ACTIVE)
        .select_related("person", "department", "role")
        .order_by("person__full_name", "department__nome", "role__name", "id")
    )
    items = []
    for membership in queryset:
        eligibility = get_department_membership_eligibility(membership)
        if not eligibility.eligible:
            items.append(_department_eligibility_item(membership, eligibility))
    return {
        "count": len(items),
        "items": items[:PREVIEW_LIMIT],
        "list_url": "/departamentos",
    }


def _without_portal_access_payload():
    queryset = Person.objects.filter(user_account__isnull=True).order_by("full_name", "id")
    return {
        "count": queryset.count(),
        "items": [
            {
                "person": _person_summary(person),
                "resolution_url": f"/pessoas/{person.id}",
            }
            for person in queryset[:PREVIEW_LIMIT]
        ],
        "list_url": "/pessoas",
    }


def _inactive_memberships_payload():
    queryset = (
        Membership.objects.filter(status=Membership.Status.INACTIVE)
        .select_related("person")
        .order_by("person__full_name", "id")
    )
    return {
        "count": queryset.count(),
        "items": [
            {
                "person": _person_summary(membership.person),
                "member_since": _date(membership.member_since),
                "resolution_url": f"/pessoas/{membership.person_id}",
            }
            for membership in queryset[:PREVIEW_LIMIT]
        ],
        "list_url": "/membresia",
    }


def _overview_payload(*, pending_activation_count):
    user_model = get_user_model()
    return {
        "people_total": Person.objects.count(),
        "visitors": ChurchJourney.objects.filter(person__membership__isnull=True).count(),
        "active_members": Membership.objects.filter(status=Membership.Status.ACTIVE).count(),
        "inactive_members": Membership.objects.filter(status=Membership.Status.INACTIVE).count(),
        "active_portal_accounts": user_model.objects.filter(is_active=True).count(),
        "pending_activation_accounts": pending_activation_count,
        "generated_at": _datetime(timezone.now()),
    }


def build_secretary_dashboard(viewer=None):
    access_requests = _access_requests_payload()
    membership_approvals = _membership_approvals_payload()
    activation = _pending_activation_payload()
    incomplete_profiles = _incomplete_profiles_payload()
    department_eligibility = _department_eligibility_payload()
    without_portal_access = _without_portal_access_payload()
    inactive_memberships = _inactive_memberships_payload()
    action_required = access_requests["count"] + membership_approvals["count"]

    return {
        "summary": {
            "action_required": action_required,
            "pending_activation": activation["count"],
            "incomplete_profiles": incomplete_profiles["count"],
            "people_total": Person.objects.count(),
        },
        "action_required": {
            "access_requests": access_requests,
            "membership_approvals": membership_approvals,
        },
        "pending": {
            "activation": activation,
            "incomplete_profiles": incomplete_profiles,
            "department_eligibility": department_eligibility,
        },
        "monitoring": {
            "without_portal_access": without_portal_access,
            "inactive_memberships": inactive_memberships,
        },
        "overview": _overview_payload(pending_activation_count=activation["count"]),
        "meta": {
            "preview_limit": PREVIEW_LIMIT,
            "action_required_semantics": "items",
        },
    }
