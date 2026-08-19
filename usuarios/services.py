import re
import unicodedata

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils import timezone

from pessoas.models import Person

from .models import AccessRequest


class AccessRequestError(Exception):
    code = "ACCESS_REQUEST_ERROR"
    message = "Nao foi possivel processar a solicitacao de acesso."


class AccessRequestNotPendingError(AccessRequestError):
    code = "ACCESS_REQUEST_NOT_PENDING"
    message = "Somente solicitacoes pendentes podem ser revisadas."


class PersonAlreadyHasUserError(AccessRequestError):
    code = "PERSON_ALREADY_HAS_USER"
    message = "Esta pessoa ja possui acesso ao Portal."


class PersonNotFoundError(AccessRequestError):
    code = "PERSON_NOT_FOUND"
    message = "A pessoa selecionada nao foi encontrada."


class UserAccessError(Exception):
    code = "USER_ACCESS_ERROR"
    message = "Nao foi possivel alterar o acesso do usuario."


class CannotDisableOwnAccountError(UserAccessError):
    code = "CANNOT_DISABLE_OWN_ACCOUNT"
    message = "Voce nao pode bloquear sua propria conta por este fluxo."


class CannotDisableSuperuserError(UserAccessError):
    code = "CANNOT_DISABLE_SUPERUSER"
    message = "Contas superuser nao podem ser bloqueadas por este fluxo."


class UserAccessNotActiveError(UserAccessError):
    code = "USER_ACCESS_NOT_ACTIVE"
    message = "Somente acessos ativos podem ser bloqueados."


class UserAccessNotBlockedError(UserAccessError):
    code = "USER_ACCESS_NOT_BLOCKED"
    message = "Somente acessos bloqueados podem ser reativados."


class AccessStatus:
    PENDING_ACTIVATION = "PENDING_ACTIVATION"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"


def get_access_status(usuario):
    if usuario.is_active:
        return AccessStatus.ACTIVE
    if not usuario.has_usable_password():
        return AccessStatus.PENDING_ACTIVATION
    return AccessStatus.BLOCKED


def normalize_username_part(value):
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", ".", ascii_value.lower()).strip(".")


def generate_username(full_name):
    user_model = get_user_model()
    parts = [part for part in normalize_username_part(full_name).split(".") if part]
    if not parts:
        base_username = "usuario"
    elif len(parts) == 1:
        base_username = parts[0]
    else:
        base_username = f"{parts[0]}.{parts[-1]}"

    username = base_username
    suffix = 2
    while user_model.objects.filter(username=username).exists():
        username = f"{base_username}{suffix}"
        suffix += 1
    return username


def split_legacy_name(full_name):
    parts = (full_name or "").strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def build_account_activation_path(usuario):
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    token = default_token_generator.make_token(usuario)
    return f"/ativar-conta/{uid}/{token}"


def _ensure_pending(access_request):
    if access_request.status != AccessRequest.Status.PENDING:
        raise AccessRequestNotPendingError


def _get_or_create_person(access_request, *, person_id=None, create_new_person=False):
    if person_id:
        try:
            return Person.objects.get(pk=person_id)
        except Person.DoesNotExist as exc:
            raise PersonNotFoundError from exc
    if create_new_person:
        return Person.objects.create(
            full_name=access_request.full_name,
            birth_date=access_request.birth_date,
            email=access_request.email,
            phone=access_request.phone,
        )
    raise ValueError("Resolva a identidade antes de aprovar a solicitacao.")


@transaction.atomic
def approve_access_request(access_request, *, reviewed_by, person_id=None, create_new_person=False):
    access_request = AccessRequest.objects.select_for_update().get(pk=access_request.pk)
    _ensure_pending(access_request)

    person = _get_or_create_person(
        access_request,
        person_id=person_id,
        create_new_person=create_new_person,
    )
    if hasattr(person, "user_account"):
        raise PersonAlreadyHasUserError

    first_name, last_name = split_legacy_name(person.full_name)
    user_model = get_user_model()
    usuario = user_model(
        username=generate_username(person.full_name),
        person=person,
        first_name=first_name,
        last_name=last_name,
        email=person.email,
        telefone=person.phone,
        is_active=False,
    )
    usuario.set_unusable_password()
    usuario.save()

    access_request.person = person
    access_request.status = AccessRequest.Status.APPROVED
    access_request.reviewed_by = reviewed_by
    access_request.reviewed_at = timezone.now()
    access_request.rejection_reason = ""
    access_request.save(
        update_fields=[
            "person",
            "status",
            "reviewed_by",
            "reviewed_at",
            "rejection_reason",
            "updated_at",
        ]
    )
    return access_request, usuario


@transaction.atomic
def reject_access_request(access_request, *, reviewed_by, rejection_reason=""):
    access_request = AccessRequest.objects.select_for_update().get(pk=access_request.pk)
    _ensure_pending(access_request)
    access_request.status = AccessRequest.Status.REJECTED
    access_request.reviewed_by = reviewed_by
    access_request.reviewed_at = timezone.now()
    access_request.rejection_reason = (rejection_reason or "").strip()
    access_request.save(
        update_fields=[
            "status",
            "reviewed_by",
            "reviewed_at",
            "rejection_reason",
            "updated_at",
        ]
    )
    return access_request


@transaction.atomic
def disable_user_access(usuario, *, acting_user):
    user_model = get_user_model()
    usuario = user_model.objects.select_for_update().get(pk=usuario.pk)

    if usuario.pk == acting_user.pk:
        raise CannotDisableOwnAccountError
    if usuario.is_superuser:
        raise CannotDisableSuperuserError
    if get_access_status(usuario) != AccessStatus.ACTIVE:
        raise UserAccessNotActiveError

    usuario.is_active = False
    usuario.save(update_fields=["is_active"])
    return usuario


@transaction.atomic
def enable_user_access(usuario):
    user_model = get_user_model()
    usuario = user_model.objects.select_for_update().get(pk=usuario.pk)

    if get_access_status(usuario) != AccessStatus.BLOCKED:
        raise UserAccessNotBlockedError

    usuario.is_active = True
    usuario.save(update_fields=["is_active"])
    return usuario
