from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from departamentos.models import DepartamentoMembro
from departamentos.permissions import get_departamentos_gerenciaveis
from usuarios.permissions import usuario_tem_acesso_secretaria


def usuario_pode_gerenciar_eventos(usuario):
    if not getattr(usuario, "is_authenticated", False):
        return False
    if usuario_tem_acesso_secretaria(usuario):
        return True
    return get_departamentos_gerenciaveis(
        usuario,
        papeis=(DepartamentoMembro.Papel.LIDER,),
    ).exists()


def usuario_pode_operar_evento(usuario):
    return usuario_pode_gerenciar_eventos(usuario)


class EventoManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return usuario_pode_gerenciar_eventos(self.request.user)


class EventoTeamRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return usuario_pode_operar_evento(self.request.user)
