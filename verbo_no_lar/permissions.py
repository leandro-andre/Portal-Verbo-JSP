from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from governanca.permissions import usuario_eh_secretaria


def usuario_pode_gerenciar_verbo_no_lar(usuario):
    if not getattr(usuario, "is_authenticated", False):
        return False
    if usuario.is_superuser or usuario_eh_secretaria(usuario):
        return True
    if usuario.is_staff:
        return True
    return False


def usuario_pode_acessar_verbo_no_lar(usuario):
    if usuario_pode_gerenciar_verbo_no_lar(usuario):
        return True
    # Responsáveis de casa também acessam o módulo (lista filtrada).
    from .models import CasaVerboNoLar

    return CasaVerboNoLar.objects.filter(casal_responsavel=usuario, ativo=True).exists()


def usuario_pode_operar_casa_verbo_no_lar(usuario, casa):
    if usuario_pode_gerenciar_verbo_no_lar(usuario):
        return True
    if not getattr(usuario, "is_authenticated", False):
        return False
    return casa.casal_responsavel_id == usuario.id or casa.anfitriao_id == usuario.id


class VerboNoLarAccessRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return usuario_pode_acessar_verbo_no_lar(self.request.user)


class VerboNoLarManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return usuario_pode_gerenciar_verbo_no_lar(self.request.user)

