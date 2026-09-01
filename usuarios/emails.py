from dataclasses import dataclass
from html import escape
import logging
from urllib.parse import urlparse

from django.conf import settings

from core.email import send_transactional_email
from core.email.exceptions import EmailConfigurationError, EmailDeliveryError

from .services import build_account_activation_path


logger = logging.getLogger(__name__)


ACCESS_APPROVAL_SUBJECT = "Seu acesso ao Portal Verbo da Vida foi aprovado"


@dataclass(frozen=True)
class AccessApprovalEmailResult:
    sent: bool
    reason: str | None = None
    message_id: str | None = None
    type: str | None = None

    def as_api_payload(self):
        payload = {"email_sent": self.sent}
        if self.reason:
            payload["reason"] = self.reason
        if self.type:
            payload["type"] = self.type
        return payload


def _recipient_name(person, access_request):
    if person is not None:
        return person.display_name
    return (getattr(access_request, "full_name", "") or "").strip()


def _activation_link(usuario):
    base_url = _app_base_url()
    if not base_url:
        return ""
    return f"{base_url}{build_account_activation_path(usuario)}"


def _portal_link():
    return _app_base_url()


def _app_base_url():
    base_url = settings.APP_BASE_URL
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return base_url


def _build_activation_email(*, name, activation_link):
    safe_name = escape(name) if name else ""
    greeting_html = f"Ola, {safe_name}!" if safe_name else "Ola!"
    greeting_text = f"Ola, {name}!" if name else "Ola!"
    safe_link = escape(activation_link, quote=True)
    html = (
        f"<p>{greeting_html}</p>"
        "<p>Sua solicitacao de acesso ao Portal Verbo da Vida foi aprovada.</p>"
        "<p>Para concluir a configuracao da sua conta, use o link abaixo:</p>"
        f'<p><a href="{safe_link}">Ativar meu acesso</a></p>'
        "<p>Se o botao nao funcionar, copie e cole o link no navegador.</p>"
        f"<p>{safe_link}</p>"
        "<p>Portal Verbo da Vida</p>"
    )
    text = (
        f"{greeting_text}\n\n"
        "Sua solicitacao de acesso ao Portal Verbo da Vida foi aprovada.\n\n"
        "Para concluir a configuracao da sua conta, use o link abaixo:\n\n"
        f"{activation_link}\n\n"
        "Se o botao nao funcionar, copie e cole o link no navegador.\n\n"
        "Portal Verbo da Vida"
    )
    return html, text


def _build_active_account_email(*, name, portal_link):
    safe_name = escape(name) if name else ""
    greeting_html = f"Ola, {safe_name}!" if safe_name else "Ola!"
    greeting_text = f"Ola, {name}!" if name else "Ola!"
    safe_link = escape(portal_link, quote=True)
    html = (
        f"<p>{greeting_html}</p>"
        "<p>Sua solicitacao de acesso ao Portal Verbo da Vida foi aprovada.</p>"
        "<p>Voce ja pode acessar o Portal normalmente.</p>"
        f'<p><a href="{safe_link}">Acessar Portal</a></p>'
        "<p>Portal Verbo da Vida</p>"
    )
    text = (
        f"{greeting_text}\n\n"
        "Sua solicitacao de acesso ao Portal Verbo da Vida foi aprovada.\n\n"
        "Voce ja pode acessar o Portal normalmente.\n\n"
        f"{portal_link}\n\n"
        "Portal Verbo da Vida"
    )
    return html, text


def send_access_approval_email(access_request, usuario):
    recipient = (usuario.email or access_request.email or "").strip()
    if not recipient:
        logger.info("E-mail de aprovacao nao enviado: destinatario ausente.", extra={"access_request_id": access_request.id})
        return AccessApprovalEmailResult(sent=False, reason="missing_recipient")

    person = getattr(access_request, "person", None) or getattr(usuario, "person", None)
    name = _recipient_name(person, access_request)
    needs_activation = not usuario.is_active and not usuario.has_usable_password()

    if needs_activation:
        notification_type = "activation"
        link = _activation_link(usuario)
        if not link:
            logger.warning("E-mail de ativacao nao enviado: APP_BASE_URL ausente.", extra={"access_request_id": access_request.id})
            return AccessApprovalEmailResult(sent=False, reason="missing_app_base_url", type=notification_type)
        html, text = _build_activation_email(name=name, activation_link=link)
    else:
        notification_type = "approval-active-account"
        link = _portal_link()
        if not link:
            logger.warning("E-mail de aprovacao nao enviado: APP_BASE_URL ausente.", extra={"access_request_id": access_request.id})
            return AccessApprovalEmailResult(sent=False, reason="missing_app_base_url", type=notification_type)
        html, text = _build_active_account_email(name=name, portal_link=link)

    try:
        result = send_transactional_email(
            to=recipient,
            subject=ACCESS_APPROVAL_SUBJECT,
            html=html,
            text=text,
            idempotency_key=f"access-request-approved:{access_request.id}:{notification_type}",
        )
    except EmailConfigurationError:
        logger.warning(
            "E-mail de aprovacao nao enviado: provider desabilitado.",
            extra={"access_request_id": access_request.id, "email_type": notification_type},
        )
        return AccessApprovalEmailResult(sent=False, reason="provider_disabled", type=notification_type)
    except EmailDeliveryError:
        logger.warning(
            "E-mail de aprovacao nao enviado: falha de entrega.",
            extra={"access_request_id": access_request.id, "email_type": notification_type},
        )
        return AccessApprovalEmailResult(sent=False, reason="delivery_failed", type=notification_type)

    logger.info(
        "E-mail de aprovacao enviado.",
        extra={
            "access_request_id": access_request.id,
            "email_type": notification_type,
            "provider": result.provider,
            "message_id": result.message_id,
        },
    )
    return AccessApprovalEmailResult(
        sent=True,
        message_id=result.message_id,
        type=notification_type,
    )
