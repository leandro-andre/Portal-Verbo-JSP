import hashlib
import hmac
import json
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs
from urllib.request import Request, urlopen

from django.urls import reverse
from django.utils import timezone

from financeiro.models import ConfiguracaoFinanceira, Contribuicao


API_BASE_URL = "https://api.mercadopago.com"
TIMEOUT_SECONDS = 20


class MercadoPagoError(Exception):
    pass


def get_configuracao_financeira():
    return ConfiguracaoFinanceira.load()


def _request_mercado_pago(method, path, access_token, payload=None):
    if not access_token:
        raise MercadoPagoError("Access token do Mercado Pago nao configurado.")

    data = None
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload, default=_json_default).encode("utf-8")

    request = Request(
        f"{API_BASE_URL}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise MercadoPagoError(f"Mercado Pago retornou HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise MercadoPagoError(f"Falha ao conectar ao Mercado Pago: {exc.reason}") from exc


def _json_default(value):
    if isinstance(value, Decimal):
        return float(value)
    raise TypeError(f"Tipo nao serializavel: {type(value)!r}")


def criar_preferencia_pagamento(contribuicao, request):
    config = get_configuracao_financeira()
    notification_url = config.webhook_url or request.build_absolute_uri(
        reverse("financeiro:webhook")
    )
    retorno_url = request.build_absolute_uri(reverse("financeiro:retorno"))
    descricao = contribuicao.descricao or contribuicao.get_tipo_display()

    payload = {
        "items": [
            {
                "title": f"{contribuicao.get_tipo_display()} - Igreja",
                "description": descricao,
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": contribuicao.valor,
            }
        ],
        "external_reference": str(contribuicao.pk),
        "notification_url": notification_url,
        "back_urls": {
            "success": retorno_url,
            "failure": retorno_url,
            "pending": retorno_url,
        },
        "metadata": {
            "contribuicao_id": contribuicao.pk,
            "tipo": contribuicao.tipo,
        },
    }
    data = _request_mercado_pago(
        "POST",
        "/checkout/preferences",
        config.mercado_pago_access_token,
        payload,
    )

    preference_id = data.get("id") or ""
    link = data.get("sandbox_init_point") if config.ambiente == config.Ambiente.TESTE else data.get("init_point")
    link = link or data.get("init_point") or data.get("sandbox_init_point") or ""

    if not preference_id or not link:
        raise MercadoPagoError("Resposta do Mercado Pago nao trouxe preference_id ou link de pagamento.")

    contribuicao.mercado_pago_preference_id = preference_id
    contribuicao.link_pagamento = link
    contribuicao.save(
        update_fields=[
            "mercado_pago_preference_id",
            "link_pagamento",
            "atualizado_em",
        ]
    )
    return contribuicao


def testar_conexao():
    config = get_configuracao_financeira()
    try:
        data = _request_mercado_pago("GET", "/users/me", config.mercado_pago_access_token)
    except MercadoPagoError as exc:
        config.conectado = False
        config.ultima_verificacao = timezone.now()
        config.mensagem_status = str(exc)
        config.save(
            update_fields=[
                "conectado",
                "ultima_verificacao",
                "mensagem_status",
                "atualizado_em",
            ]
        )
        return False, str(exc)

    nickname = data.get("nickname") or data.get("email") or data.get("id") or "conta Mercado Pago"
    mensagem = f"Conexao realizada com sucesso: {nickname}."
    config.conectado = True
    config.ultima_verificacao = timezone.now()
    config.mensagem_status = mensagem
    config.save(
        update_fields=[
            "conectado",
            "ultima_verificacao",
            "mensagem_status",
            "atualizado_em",
        ]
    )
    return True, mensagem


def consultar_pagamento(payment_id):
    config = get_configuracao_financeira()
    return _request_mercado_pago(
        "GET",
        f"/v1/payments/{payment_id}",
        config.mercado_pago_access_token,
    )


def atualizar_contribuicao_por_pagamento(payment_data):
    payment_id = str(payment_data.get("id") or "")
    external_reference = str(payment_data.get("external_reference") or "")
    preference_id = str(
        payment_data.get("preference_id")
        or payment_data.get("order", {}).get("id")
        or ""
    )

    contribuicao = None
    if external_reference:
        contribuicao = Contribuicao.objects.filter(pk=external_reference).first()
    if not contribuicao and payment_id:
        contribuicao = Contribuicao.objects.filter(mercado_pago_payment_id=payment_id).first()
    if not contribuicao and preference_id:
        contribuicao = Contribuicao.objects.filter(mercado_pago_preference_id=preference_id).first()
    if not contribuicao:
        raise MercadoPagoError("Contribuicao correspondente ao pagamento nao encontrada.")

    contribuicao.mercado_pago_payment_id = payment_id
    contribuicao.status = mapear_status_pagamento(payment_data.get("status"))
    contribuicao.save(
        update_fields=[
            "mercado_pago_payment_id",
            "status",
            "atualizado_em",
        ]
    )
    return contribuicao


def mapear_status_pagamento(status_mercado_pago):
    status = (status_mercado_pago or "").lower()
    if status == "approved":
        return Contribuicao.Status.APROVADO
    if status in {"rejected"}:
        return Contribuicao.Status.RECUSADO
    if status in {"cancelled", "refunded", "charged_back"}:
        return Contribuicao.Status.CANCELADO
    if status in {"pending", "in_process", "authorized"}:
        return Contribuicao.Status.PENDENTE
    return Contribuicao.Status.ERRO


def extrair_payment_id(request):
    data = {}
    if request.body:
        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            data = parse_qs(request.body.decode("utf-8"))

    payment_id = (
        _get_nested(data, "data", "id")
        or request.GET.get("data.id")
        or request.GET.get("id")
        or request.POST.get("data.id")
        or request.POST.get("id")
    )
    topic = (
        data.get("type")
        if isinstance(data, dict)
        else None
    ) or request.GET.get("type") or request.GET.get("topic") or request.POST.get("type")
    if topic and topic != "payment":
        return None
    return str(payment_id) if payment_id else None


def validar_assinatura_webhook(request, payment_id):
    config = get_configuracao_financeira()
    secret = config.mercado_pago_webhook_secret
    if not secret:
        return False, "Segredo de webhook nao configurado."

    x_signature = request.headers.get("x-signature", "")
    x_request_id = request.headers.get("x-request-id", "")
    if not x_signature or not x_request_id or not payment_id:
        return False, "Headers de assinatura ausentes."

    parts = {}
    for item in x_signature.split(","):
        if "=" in item:
            key, value = item.split("=", 1)
            parts[key.strip()] = value.strip()

    timestamp = parts.get("ts")
    signature = parts.get("v1")
    if not timestamp or not signature:
        return False, "Formato de assinatura invalido."

    manifest = f"id:{payment_id};request-id:{x_request_id};ts:{timestamp};"
    expected = hmac.new(
        secret.encode("utf-8"),
        manifest.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return False, "Assinatura do webhook invalida."
    return True, "Assinatura validada."


def _get_nested(data, *keys):
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current
