import re
import unicodedata

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils import timezone

from pessoas.models import Person
from pessoas.validators import validate_brazilian_mobile

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


class InvalidAccessRequestWhatsappError(AccessRequestError):
    code = "INVALID_WHATSAPP"
    message = "O celular/WhatsApp informado na solicitacao e invalido."
    http_status = 400


class AccessRequestApprovalIntegrityError(AccessRequestError):
    code = "ACCESS_REQUEST_APPROVAL_INTEGRITY_ERROR"
    message = "Nao foi possivel aprovar a solicitacao com os dados informados."
    http_status = 409


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


class UserPersonLinkError(UserAccessError):
    code = "USER_PERSON_LINK_ERROR"
    message = "Nao foi possivel alterar o vinculo do usuario."


class UserPersonNotFoundError(UserPersonLinkError):
    code = "PERSON_NOT_FOUND"
    message = "A pessoa selecionada nao foi encontrada."


class UserPersonAlreadyHasUserError(UserPersonLinkError):
    code = "PERSON_ALREADY_HAS_USER"
    message = "Esta pessoa ja possui outro usuario vinculado."


class AccessStatus:
    PENDING_APPROVAL = "PENDING_APPROVAL"
    PENDING_ACTIVATION = "PENDING_ACTIVATION"
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"


def get_access_status(usuario):
    if usuario.is_active:
        return AccessStatus.ACTIVE
    if AccessRequest.objects.filter(usuario=usuario, status=AccessRequest.Status.PENDING).exists():
        return AccessStatus.PENDING_APPROVAL
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


def _ensure_valid_access_request_whatsapp(access_request):
    try:
        access_request.phone = validate_brazilian_mobile(access_request.phone)
    except DjangoValidationError as exc:
        raise InvalidAccessRequestWhatsappError from exc


def _get_or_create_person(access_request, *, person_id=None, create_new_person=False):
    if person_id:
        try:
            return Person.objects.get(pk=person_id)
        except Person.DoesNotExist as exc:
            raise PersonNotFoundError from exc
    if create_new_person:
        try:
            return Person.objects.create(
                full_name=access_request.full_name,
                birth_date=access_request.birth_date,
                email=access_request.email,
                phone=access_request.phone,
            )
        except DjangoValidationError as exc:
            if "phone" in getattr(exc, "message_dict", {}):
                raise InvalidAccessRequestWhatsappError from exc
            raise AccessRequestApprovalIntegrityError from exc
        except IntegrityError as exc:
            raise AccessRequestApprovalIntegrityError from exc
    raise ValueError("Resolva a identidade antes de aprovar a solicitacao.")


@transaction.atomic
def approve_access_request(access_request, *, reviewed_by, person_id=None, create_new_person=False):
    access_request = AccessRequest.objects.select_for_update().select_related("usuario").get(
        pk=access_request.pk
    )
    _ensure_pending(access_request)
    _ensure_valid_access_request_whatsapp(access_request)

    person = _get_or_create_person(
        access_request,
        person_id=person_id,
        create_new_person=create_new_person,
    )
    try:
        if hasattr(person, "user_account"):
            raise PersonAlreadyHasUserError

        usuario = access_request.usuario
        if usuario is None:
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
            access_request.usuario = usuario
        else:
            first_name, last_name = split_legacy_name(person.full_name)
            usuario.person = person
            usuario.first_name = first_name
            usuario.last_name = last_name
            usuario.email = person.email or access_request.email
            usuario.telefone = person.phone or access_request.phone
            usuario.is_active = True
            usuario.save(
                update_fields=[
                    "person",
                    "first_name",
                    "last_name",
                    "email",
                    "telefone",
                    "is_active",
                ]
            )
    except IntegrityError as exc:
        raise AccessRequestApprovalIntegrityError from exc

    access_request.person = person
    access_request.status = AccessRequest.Status.APPROVED
    access_request.reviewed_by = reviewed_by
    access_request.reviewed_at = timezone.now()
    access_request.rejection_reason = ""
    access_request.save(
        update_fields=[
            "person",
            "usuario",
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


@transaction.atomic
def link_user_to_person(usuario, *, person_id):
    user_model = get_user_model()
    usuario = user_model.objects.select_for_update().get(pk=usuario.pk)
    try:
        person = Person.objects.select_for_update().get(pk=person_id)
    except Person.DoesNotExist as exc:
        raise UserPersonNotFoundError from exc

    existing_user = getattr(person, "user_account", None)
    if existing_user is not None and existing_user.pk != usuario.pk:
        raise UserPersonAlreadyHasUserError

    usuario.person = person
    usuario.save(update_fields=["person"])
    return usuario


@transaction.atomic
def unlink_user_from_person(usuario):
    user_model = get_user_model()
    usuario = user_model.objects.select_for_update().get(pk=usuario.pk)
    usuario.person = None
    usuario.save(update_fields=["person"])
    return usuario
