from core.models import SiteConfig, SobrePage
from departamentos.models import Departamento, DepartamentoMembro
from eventos.models import Evento
from noticias.models import Noticia


PAPEIS_GOVERNANCA_PUBLICA = (
    DepartamentoMembro.Papel.LIDER,
    DepartamentoMembro.Papel.VICE_LIDER,
)

ROLE_SUPERUSER = "superuser"
ROLE_SECRETARIA = "secretaria"
ROLE_MIDIA = "midia"

CONTENT_GOVERNANCE_POLICY = {
    SiteConfig._meta.label_lower: {
        "view": (ROLE_SUPERUSER, ROLE_SECRETARIA, ROLE_MIDIA),
        "add": (ROLE_SUPERUSER, ROLE_SECRETARIA),
        "change": (ROLE_SUPERUSER, ROLE_SECRETARIA, ROLE_MIDIA),
        "delete": (ROLE_SUPERUSER,),
        "publish": (ROLE_SUPERUSER, ROLE_SECRETARIA),
        "field_roles": {
            "__default__": (ROLE_SUPERUSER, ROLE_SECRETARIA),
            "youtube_embed_url": (ROLE_SUPERUSER, ROLE_SECRETARIA, ROLE_MIDIA),
        },
    },
    SobrePage._meta.label_lower: {
        "view": (ROLE_SUPERUSER, ROLE_SECRETARIA),
        "add": (ROLE_SUPERUSER, ROLE_SECRETARIA),
        "change": (ROLE_SUPERUSER, ROLE_SECRETARIA),
        "delete": (ROLE_SUPERUSER,),
        "publish": (ROLE_SUPERUSER, ROLE_SECRETARIA),
    },
    Evento._meta.label_lower: {
        "view": (ROLE_SUPERUSER, ROLE_SECRETARIA),
        "add": (ROLE_SUPERUSER, ROLE_SECRETARIA),
        "change": (ROLE_SUPERUSER, ROLE_SECRETARIA),
        "delete": (ROLE_SUPERUSER, ROLE_SECRETARIA),
        "publish": (ROLE_SUPERUSER, ROLE_SECRETARIA),
    },
    Noticia._meta.label_lower: {
        "view": (ROLE_SUPERUSER, ROLE_SECRETARIA),
        "add": (ROLE_SUPERUSER, ROLE_SECRETARIA),
        "change": (ROLE_SUPERUSER, ROLE_SECRETARIA),
        "delete": (ROLE_SUPERUSER, ROLE_SECRETARIA),
        "publish": (ROLE_SUPERUSER, ROLE_SECRETARIA),
    },
}


def _resolve_model_label(model_or_instance):
    if hasattr(model_or_instance, "_meta"):
        return model_or_instance._meta.label_lower
    raise TypeError("Informe uma classe de model ou uma instancia de model.")


def _resolve_model_class(model_or_instance):
    if hasattr(model_or_instance, "_meta") and hasattr(model_or_instance, "_default_manager"):
        return model_or_instance
    if hasattr(model_or_instance, "_meta"):
        return model_or_instance.__class__
    raise TypeError("Informe uma classe de model ou uma instancia de model.")


def usuario_tem_cargo_em_departamentos(usuario, codigos_departamento, papeis=None, somente_ativo=True):
    if not getattr(usuario, "is_authenticated", False):
        return False
    if usuario.is_superuser:
        return True

    filtros = {
        "membro": usuario,
        "departamento__codigo__in": tuple(codigos_departamento),
        "departamento__ativo": True,
    }
    if somente_ativo:
        filtros["ativo"] = True

    papeis = tuple(papeis or PAPEIS_GOVERNANCA_PUBLICA)
    if papeis:
        filtros["papel__in"] = papeis

    return DepartamentoMembro.objects.filter(**filtros).exists()


def usuario_eh_secretaria(usuario):
    return usuario_tem_cargo_em_departamentos(
        usuario,
        (Departamento.CodigoSistema.SECRETARIA,),
    )


def usuario_eh_midia(usuario):
    return usuario_tem_cargo_em_departamentos(
        usuario,
        (Departamento.CodigoSistema.MIDIA,),
    )


def usuario_pode_gerenciar_site_publico(usuario):
    return bool(getattr(usuario, "is_authenticated", False) and (usuario.is_superuser or usuario_eh_secretaria(usuario)))


def usuario_pode_gerenciar_ao_vivo(usuario):
    return bool(
        getattr(usuario, "is_authenticated", False)
        and (usuario.is_superuser or usuario_eh_secretaria(usuario) or usuario_eh_midia(usuario))
    )


def usuario_pode_acessar_painel_secretaria(usuario):
    return usuario_pode_gerenciar_site_publico(usuario)


def usuario_pode_acessar_painel_midia(usuario):
    return bool(
        getattr(usuario, "is_authenticated", False)
        and (usuario.is_superuser or usuario_eh_midia(usuario))
    )


def _usuario_tem_role(usuario, role_name):
    if role_name == ROLE_SUPERUSER:
        return bool(getattr(usuario, "is_authenticated", False) and usuario.is_superuser)
    if role_name == ROLE_SECRETARIA:
        return usuario_eh_secretaria(usuario)
    if role_name == ROLE_MIDIA:
        return usuario_eh_midia(usuario)
    return False


def get_content_governance_policy(model_or_instance):
    return CONTENT_GOVERNANCE_POLICY.get(_resolve_model_label(model_or_instance), {})


def usuario_pode_executar_acao_conteudo(usuario, model_or_instance, acao):
    if not getattr(usuario, "is_authenticated", False):
        return False
    if usuario.is_superuser:
        return True

    policy = get_content_governance_policy(model_or_instance)
    allowed_roles = policy.get(acao, ())
    return any(_usuario_tem_role(usuario, role_name) for role_name in allowed_roles)


def usuario_pode_publicar_conteudo(usuario, model_or_instance):
    return usuario_pode_executar_acao_conteudo(usuario, model_or_instance, "publish")


def usuario_pode_editar_campo(usuario, model_or_instance, campo, obj=None):
    if not getattr(usuario, "is_authenticated", False):
        return False
    if usuario.is_superuser:
        return True

    model_class = _resolve_model_class(model_or_instance)
    if not any(field.name == campo for field in model_class._meta.get_fields() if hasattr(field, "name")):
        return False

    policy = get_content_governance_policy(obj or model_or_instance)
    if not policy:
        return False

    field_roles = policy.get("field_roles", {})
    if not field_roles:
        return usuario_pode_executar_acao_conteudo(usuario, obj or model_or_instance, "change")

    allowed_roles = field_roles.get(campo, field_roles.get("__default__", ()))
    return any(_usuario_tem_role(usuario, role_name) for role_name in allowed_roles)


def get_campos_editaveis_por_usuario(usuario, model_or_instance, obj=None):
    model_class = _resolve_model_class(model_or_instance)
    editable_fields = []
    for field in model_class._meta.concrete_fields:
        if not getattr(field, "editable", False):
            continue
        if usuario_pode_editar_campo(usuario, model_class, field.name, obj=obj):
            editable_fields.append(field.name)
    return editable_fields


def get_campos_bloqueados_por_usuario(usuario, model_or_instance, obj=None):
    model_class = _resolve_model_class(model_or_instance)
    editable_fields = {
        field.name
        for field in model_class._meta.concrete_fields
        if getattr(field, "editable", False)
    }
    return sorted(editable_fields.difference(get_campos_editaveis_por_usuario(usuario, model_class, obj=obj)))
