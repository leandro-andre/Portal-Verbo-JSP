from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from departamentos.permissions import get_departamentos_gerenciaveis
from governanca.permissions import usuario_eh_secretaria


def usuario_pode_gerenciar_ministros(usuario):
    if not getattr(usuario, "is_authenticated", False):
        return False
    if usuario.is_superuser or usuario_eh_secretaria(usuario):
        return True
    if usuario.is_staff:
        return True
    return get_departamentos_gerenciaveis(usuario).exists()


def usuario_pode_ver_dados_financeiros_ministro(usuario):
    return usuario_pode_gerenciar_ministros(usuario)


class MinistroManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return usuario_pode_gerenciar_ministros(self.request.user)
