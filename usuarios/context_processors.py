from departamentos.permissions import (
    get_departamentos_do_usuario,
    get_departamentos_gerenciaveis,
    usuario_pode_criar_departamentos,
)
from eventos.permissions import usuario_pode_gerenciar_eventos
from financeiro.permissions import usuario_pode_gerenciar_financeiro
from governanca.permissions import (
    usuario_pode_acessar_painel_midia,
    usuario_pode_acessar_painel_secretaria,
)
from infantil.permissions import usuario_pode_visualizar_infantil
from ministros.permissions import usuario_pode_gerenciar_ministros
from verbo_no_lar.permissions import usuario_pode_acessar_verbo_no_lar


EMPTY_INTERNAL_PERMISSIONS = {
    "can_view_departamentos": False,
    "can_manage_departamentos": False,
    "can_manage_escalas": False,
    "can_view_infantil": False,
    "can_view_secretaria": False,
    "can_view_midia": False,
    "can_manage_eventos": False,
    "can_manage_ministros": False,
    "can_manage_verbo_no_lar": False,
    "can_manage_financeiro": False,
}


def internal_permissions(request):
    cached_permissions = getattr(request, "_internal_permissions_cache", None)
    if cached_permissions is not None:
        return cached_permissions

    if not request.user.is_authenticated:
        request._internal_permissions_cache = EMPTY_INTERNAL_PERMISSIONS.copy()
        return request._internal_permissions_cache

    departamentos_do_usuario = get_departamentos_do_usuario(request.user)
    departamentos_gerenciaveis = get_departamentos_gerenciaveis(request.user)
    pode_criar_departamentos = usuario_pode_criar_departamentos(request.user)
    possui_departamentos = departamentos_do_usuario.exists()
    possui_departamentos_gerenciaveis = departamentos_gerenciaveis.exists()

    request._internal_permissions_cache = {
        "can_view_departamentos": pode_criar_departamentos or possui_departamentos,
        "can_manage_departamentos": pode_criar_departamentos or possui_departamentos_gerenciaveis,
        "can_manage_escalas": possui_departamentos_gerenciaveis,
        "can_view_infantil": usuario_pode_visualizar_infantil(request.user),
        "can_view_secretaria": usuario_pode_acessar_painel_secretaria(request.user),
        "can_view_midia": usuario_pode_acessar_painel_midia(request.user),
        "can_manage_eventos": usuario_pode_gerenciar_eventos(request.user),
        "can_manage_ministros": usuario_pode_gerenciar_ministros(request.user),
        "can_manage_verbo_no_lar": usuario_pode_acessar_verbo_no_lar(request.user),
        "can_manage_financeiro": usuario_pode_gerenciar_financeiro(request.user),
    }
    return request._internal_permissions_cache
