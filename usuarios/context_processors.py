from departamentos.permissions import (
    get_departamentos_do_usuario,
    get_departamentos_gerenciaveis,
    usuario_pode_criar_departamentos,
)
from eventos.permissions import usuario_pode_gerenciar_eventos
from governanca.permissions import (
    usuario_pode_acessar_painel_midia,
    usuario_pode_acessar_painel_secretaria,
)
from infantil.permissions import usuario_pode_visualizar_infantil


def internal_permissions(request):
    if not request.user.is_authenticated:
        return {
            "can_view_departamentos": False,
            "can_manage_departamentos": False,
            "can_manage_escalas": False,
            "can_view_infantil": False,
            "can_view_secretaria": False,
            "can_view_midia": False,
            "can_manage_eventos": False,
        }

    departamentos_do_usuario = get_departamentos_do_usuario(request.user)
    departamentos_gerenciaveis = get_departamentos_gerenciaveis(request.user)
    pode_criar_departamentos = usuario_pode_criar_departamentos(request.user)

    return {
        "can_view_departamentos": pode_criar_departamentos or departamentos_do_usuario.exists(),
        "can_manage_departamentos": pode_criar_departamentos or departamentos_gerenciaveis.exists(),
        "can_manage_escalas": departamentos_gerenciaveis.exists(),
        "can_view_infantil": usuario_pode_visualizar_infantil(request.user),
        "can_view_secretaria": usuario_pode_acessar_painel_secretaria(request.user),
        "can_view_midia": usuario_pode_acessar_painel_midia(request.user),
        "can_manage_eventos": usuario_pode_gerenciar_eventos(request.user),
    }
