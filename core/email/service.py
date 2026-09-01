from dataclasses import dataclass
import logging

from django.conf import settings

from resend.exceptions import ResendError

from .client import ResendEmailClient
from .exceptions import EmailConfigurationError, EmailDeliveryError


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailSendResult:
    provider: str
    message_id: str


def _message_id_from_response(response):
    if isinstance(response, dict):
        return str(response.get("id", ""))
    return str(getattr(response, "id", ""))


def _build_resend_params(*, to, subject, html, text=None):
    params = {
        "from": settings.EMAIL_FROM,
        "to": [to] if isinstance(to, str) else list(to),
        "subject": subject,
        "html": html,
    }
    if text is not None:
        params["text"] = text
    return params


def send_transactional_email(
    *,
    to,
    subject,
    html,
    text=None,
    idempotency_key=None,
    client=None,
):
    if not settings.EMAIL_PROVIDER_ENABLED:
        raise EmailConfigurationError("Envio transacional de e-mail nao configurado.")
    if not to:
        raise ValueError("Informe ao menos um destinatario.")
    if not subject:
        raise ValueError("Informe o assunto do e-mail.")
    if not html:
        raise ValueError("Informe o conteudo HTML do e-mail.")

    email_client = client or ResendEmailClient(settings.RESEND_API_KEY)
    params = _build_resend_params(to=to, subject=subject, html=html, text=text)

    try:
        response = email_client.send(params, idempotency_key=idempotency_key)
    except ResendError as exc:
        logger.warning("Falha ao enviar e-mail transacional via Resend: %s", exc.__class__.__name__)
        raise EmailDeliveryError("Falha ao enviar e-mail transacional via Resend.") from exc
    except Exception as exc:
        logger.exception("Erro inesperado ao enviar e-mail transacional via Resend.")
        raise EmailDeliveryError("Falha ao enviar e-mail transacional via Resend.") from exc

    message_id = _message_id_from_response(response)
    if not message_id:
        logger.warning("Resend retornou envio sem message_id.")
        raise EmailDeliveryError("Resend retornou envio sem message_id.")

    logger.info("E-mail transacional enviado.", extra={"provider": email_client.provider, "message_id": message_id})
    return EmailSendResult(provider=email_client.provider, message_id=message_id)
