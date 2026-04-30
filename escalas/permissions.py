from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404

from departamentos.permissions import (
    get_departamentos_gerenciaveis,
    usuario_pode_gerenciar_cultos_padrao,
    usuario_pode_gerenciar_escalas,
)

from .models import CultoPadrao, Escala, IndisponibilidadeMembro


def usuario_pode_acessar_indisponibilidades(usuario):
    return bool(getattr(usuario, "is_authenticated", False))


def usuario_pode_editar_propria_indisponibilidade(usuario, indisponibilidade):
    return bool(
        getattr(usuario, "is_authenticated", False)
        and (
            usuario.is_superuser
            or indisponibilidade.membro_id == getattr(usuario, "pk", None)
        )
    )


class EscalaLeaderRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    escala_kwarg = "pk"

    def get_permission_escala(self):
        if hasattr(self, "object") and self.object is not None:
            if isinstance(self.object, Escala):
                return self.object
        return get_object_or_404(
            Escala.objects.select_related("departamento"),
            pk=self.kwargs[self.escala_kwarg],
        )

    def get_permission_departamento(self):
        return self.get_permission_escala().departamento

    def test_func(self):
        return usuario_pode_gerenciar_escalas(
            self.request.user,
            self.get_permission_departamento(),
        )


class EscalaManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or get_departamentos_gerenciaveis(
            self.request.user
        ).exists()


class CultoPadraoManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    culto_kwarg = "pk"

    def get_permission_culto_padrao(self):
        if hasattr(self, "object") and self.object is not None:
            if isinstance(self.object, CultoPadrao):
                return self.object
        return get_object_or_404(CultoPadrao, pk=self.kwargs[self.culto_kwarg])

    def test_func(self):
        return usuario_pode_gerenciar_cultos_padrao(self.request.user)


class OwnIndisponibilidadeRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def get_permission_indisponibilidade(self):
        if hasattr(self, "object") and self.object is not None:
            if isinstance(self.object, IndisponibilidadeMembro):
                return self.object
        return get_object_or_404(IndisponibilidadeMembro, pk=self.kwargs["pk"])

    def test_func(self):
        return usuario_pode_editar_propria_indisponibilidade(
            self.request.user,
            self.get_permission_indisponibilidade(),
        )
