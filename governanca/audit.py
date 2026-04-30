import json
from datetime import date, datetime, time

from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str

from .models import ConteudoAuditLog


def serialize_audit_value(value):
    if value is None:
        return ""
    if hasattr(value, "name"):
        return force_str(value.name or "")
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, bool):
        return "true" if value else "false"
    if hasattr(value, "_meta") and hasattr(value, "pk"):
        return f"{value.pk}:{force_str(value)}"
    return force_str(value)


def get_auditable_field_names(instance):
    return [
        field.name
        for field in instance._meta.concrete_fields
        if getattr(field, "editable", False)
    ]


def get_field_snapshot(instance, field_names=None):
    field_names = field_names or get_auditable_field_names(instance)
    return {
        field_name: serialize_audit_value(getattr(instance, field_name, None))
        for field_name in field_names
    }


def _build_common_kwargs(usuario, instance):
    content_type = ContentType.objects.get_for_model(instance.__class__)
    return {
        "usuario": usuario if getattr(usuario, "is_authenticated", False) else None,
        "content_type": content_type,
        "object_id": force_str(instance.pk),
        "object_repr": force_str(instance),
    }


def log_model_create(usuario, instance, changed_fields=None):
    common_kwargs = _build_common_kwargs(usuario, instance)
    snapshot = get_field_snapshot(instance, changed_fields)
    logs = [
        ConteudoAuditLog(
            **common_kwargs,
            acao=ConteudoAuditLog.Acao.CREATE,
            campo=campo,
            valor_novo=valor_novo,
        )
        for campo, valor_novo in snapshot.items()
    ]
    ConteudoAuditLog.objects.bulk_create(logs)


def log_model_update(usuario, old_instance, new_instance, changed_fields=None):
    common_kwargs = _build_common_kwargs(usuario, new_instance)
    old_snapshot = get_field_snapshot(old_instance, changed_fields)
    new_snapshot = get_field_snapshot(new_instance, changed_fields)

    logs = []
    for campo, valor_novo in new_snapshot.items():
        valor_anterior = old_snapshot.get(campo, "")
        if valor_anterior == valor_novo:
            continue

        acao = ConteudoAuditLog.Acao.UPDATE
        if campo == "publicado":
            acao = (
                ConteudoAuditLog.Acao.PUBLISH
                if valor_novo == "true"
                else ConteudoAuditLog.Acao.UNPUBLISH
            )

        logs.append(
            ConteudoAuditLog(
                **common_kwargs,
                acao=acao,
                campo=campo,
                valor_anterior=valor_anterior,
                valor_novo=valor_novo,
            )
        )

    if logs:
        ConteudoAuditLog.objects.bulk_create(logs)


def log_model_delete(usuario, instance):
    common_kwargs = _build_common_kwargs(usuario, instance)
    snapshot = json.dumps(
        get_field_snapshot(instance),
        ensure_ascii=True,
        sort_keys=True,
    )
    ConteudoAuditLog.objects.create(
        **common_kwargs,
        acao=ConteudoAuditLog.Acao.DELETE,
        valor_anterior=snapshot,
    )
