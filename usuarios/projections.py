from pessoas.serializers import get_photo_url
from usuarios.roles import PEOPLE_VIEW, USER_DISABLE, USER_ENABLE
from usuarios.services import AccessStatus, get_access_status

from .models import AccessRequest


ACCESS_STATUS_LABELS = {
    AccessStatus.PENDING_APPROVAL: "Aguardando aprovacao",
    AccessStatus.PENDING_ACTIVATION: "Aguardando ativacao",
    AccessStatus.ACTIVE: "Conta ativa",
    AccessStatus.BLOCKED: "Conta bloqueada",
}


def _display_name_for(usuario):
    person = getattr(usuario, "person", None)
    if person is not None:
        return person.display_name
    return usuario.email or usuario.username


def _person_payload(person, request):
    if person is None:
        return None
    return {
        "id": person.id,
        "display_name": person.display_name,
        "full_name": person.full_name,
        "photo_url": get_photo_url(person, request),
        "status": person.status,
        "status_label": person.get_status_display(),
        "profile_url": f"/pessoas/{person.id}",
    }


def _access_request_payload(usuario):
    access_request = (
        AccessRequest.objects.filter(usuario=usuario)
        .only("id", "status", "created_at", "updated_at", "reviewed_at", "usuario_id")
        .first()
    )
    if access_request is None:
        return None
    return {
        "id": access_request.id,
        "status": access_request.status,
        "status_label": access_request.get_status_display(),
        "created_at": access_request.created_at,
        "updated_at": access_request.updated_at,
        "reviewed_at": access_request.reviewed_at,
        "detail_url": f"/solicitacoes-acesso/{access_request.id}",
    }


def build_user_admin_profile(usuario, viewer, request=None):
    person = getattr(usuario, "person", None)
    access_status = get_access_status(usuario)
    can_view_person_profile = bool(person and viewer.has_perm(PEOPLE_VIEW))
    has_email = bool((usuario.email or "").strip())
    can_block = bool(
        access_status == AccessStatus.ACTIVE
        and viewer.has_perm(USER_DISABLE)
        and usuario.pk != viewer.pk
        and not usuario.is_superuser
    )
    can_unblock = bool(access_status == AccessStatus.BLOCKED and viewer.has_perm(USER_ENABLE))
    can_resend_activation = bool(
        access_status == AccessStatus.PENDING_ACTIVATION
        and viewer.has_perm(USER_ENABLE)
        and has_email
    )
    can_send_password_reset = bool(
        access_status == AccessStatus.ACTIVE
        and usuario.has_usable_password()
        and viewer.has_perm(USER_ENABLE)
        and has_email
    )

    return {
        "id": usuario.id,
        "display_name": _display_name_for(usuario),
        "access_status": {
            "value": access_status,
            "label": ACCESS_STATUS_LABELS[access_status],
        },
        "account": {
            "id": usuario.id,
            "username": usuario.username,
            "email": usuario.email,
            "is_active": usuario.is_active,
            "is_superuser": usuario.is_superuser,
            "has_usable_password": usuario.has_usable_password(),
            "date_joined": usuario.date_joined,
            "last_login": usuario.last_login,
            "person_linked": person is not None,
        },
        "person": _person_payload(person, request),
        "activation": {
            "status": access_status,
            "label": ACCESS_STATUS_LABELS[access_status],
            "message": {
                AccessStatus.PENDING_APPROVAL: "Aguardando revisao da solicitacao de acesso.",
                AccessStatus.PENDING_ACTIVATION: "A conta ainda precisa concluir a ativacao.",
                AccessStatus.ACTIVE: "Conta ativada.",
                AccessStatus.BLOCKED: "Conta bloqueada.",
            }[access_status],
        },
        "security": {
            "has_usable_password": usuario.has_usable_password(),
            "is_active": usuario.is_active,
            "status": access_status,
            "status_label": ACCESS_STATUS_LABELS[access_status],
            "message": "Acoes sensiveis sao autorizadas pelo backend conforme estado da conta.",
        },
        "access_request": _access_request_payload(usuario),
        "actions": {
            "can_view_person_profile": can_view_person_profile,
            "person_profile_url": f"/pessoas/{person.id}" if can_view_person_profile else None,
            "can_block": can_block,
            "block_url": f"/api/users/{usuario.id}/disable/" if can_block else None,
            "can_unblock": can_unblock,
            "unblock_url": f"/api/users/{usuario.id}/enable/" if can_unblock else None,
            "can_resend_activation": can_resend_activation,
            "resend_activation_url": f"/api/users/{usuario.id}/resend-activation/" if can_resend_activation else None,
            "can_send_password_reset": can_send_password_reset,
            "password_reset_url": f"/api/users/{usuario.id}/password-reset/" if can_send_password_reset else None,
        },
    }
