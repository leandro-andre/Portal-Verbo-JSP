from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404

from .models import Departamento, DepartamentoMembro
from usuarios.permissions import (
    usuario_eh_lider_departamento,
    usuario_tem_acesso_total_sistema,
)


PAPEIS_GESTAO_DEPARTAMENTO = (DepartamentoMembro.Papel.LIDER,)
PAPEIS_GESTAO_ESCALA = (DepartamentoMembro.Papel.LIDER,)


def _as_departamento_id(departamento):
    if isinstance(departamento, Departamento):
        return departamento.pk
    return departamento


def get_departamentos_do_usuario(usuario, somente_ativos=True):
    if not getattr(usuario, "is_authenticated", False):
        return Departamento.objects.none()
    if usuario_tem_acesso_total_sistema(usuario):
        return Departamento.objects.all()

    filtros = {"participacoes__membro": usuario}
    if somente_ativos:
        filtros["participacoes__ativo"] = True
    return Departamento.objects.filter(**filtros).distinct()


def usuario_pertence_departamento(usuario, departamento, somente_ativo=True):
    if not getattr(usuario, "is_authenticated", False):
        return False
    if usuario_tem_acesso_total_sistema(usuario):
        return True

    filtros = {
        "membro": usuario,
        "departamento_id": _as_departamento_id(departamento),
    }
    if somente_ativo:
        filtros["ativo"] = True
    return DepartamentoMembro.objects.filter(**filtros).exists()


def usuario_tem_cargo_no_departamento(usuario, departamento, papeis, somente_ativo=True):
    if not getattr(usuario, "is_authenticated", False):
        return False
    if usuario_tem_acesso_total_sistema(usuario):
        return True

    filtros = {
        "membro": usuario,
        "departamento_id": _as_departamento_id(departamento),
        "papel__in": tuple(papeis),
    }
    if somente_ativo:
        filtros["ativo"] = True
    return DepartamentoMembro.objects.filter(**filtros).exists()


def usuario_eh_lider(usuario, departamento):
    return usuario_eh_lider_departamento(usuario, departamento)


def get_departamentos_gerenciaveis(usuario, papeis=None):
    if not getattr(usuario, "is_authenticated", False):
        return Departamento.objects.none()
    if usuario_tem_acesso_total_sistema(usuario):
        return Departamento.objects.all()

    papeis = tuple(papeis or PAPEIS_GESTAO_DEPARTAMENTO)
    return Departamento.objects.filter(
        participacoes__membro=usuario,
        participacoes__ativo=True,
        participacoes__papel__in=papeis,
    ).distinct()


def usuario_pode_acessar_departamentos(usuario):
    return bool(
        getattr(usuario, "is_authenticated", False)
        and (
            usuario_pode_criar_departamentos(usuario)
            or get_departamentos_do_usuario(usuario).exists()
        )
    )


def usuario_pode_criar_departamentos(usuario):
    return bool(
        getattr(usuario, "is_authenticated", False)
        and usuario_tem_acesso_total_sistema(usuario)
    )


def usuario_pode_gerenciar_cultos_padrao(usuario):
    return bool(
        getattr(usuario, "is_authenticated", False)
        and usuario_tem_acesso_total_sistema(usuario)
    )


def usuario_pode_gerenciar_membros(usuario, departamento):
    return usuario_tem_cargo_no_departamento(
        usuario,
        departamento,
        PAPEIS_GESTAO_DEPARTAMENTO,
    )


def usuario_pode_gerenciar_escalas(usuario, departamento):
    return usuario_tem_cargo_no_departamento(
        usuario,
        departamento,
        PAPEIS_GESTAO_ESCALA,
    )


class DepartmentCreatorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return usuario_pode_criar_departamentos(self.request.user)


class DepartmentMemberRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    department_kwarg = "pk"

    def get_permission_departamento(self):
        if hasattr(self, "object") and self.object is not None:
            if isinstance(self.object, Departamento):
                return self.object
        return get_object_or_404(Departamento, pk=self.kwargs[self.department_kwarg])

    def test_func(self):
        return usuario_pertence_departamento(
            self.request.user,
            self.get_permission_departamento(),
        )


class DepartmentLeaderRequiredMixin(DepartmentMemberRequiredMixin):
    def test_func(self):
        return usuario_pode_gerenciar_membros(
            self.request.user,
            self.get_permission_departamento(),
        )


# Compatibilidade para imports legados enquanto as chamadas migram para o app escalas.
from escalas.permissions import (  # noqa: E402
    CultoPadraoManagerRequiredMixin,
    EscalaLeaderRequiredMixin,
    EscalaManagerRequiredMixin,
    OwnIndisponibilidadeRequiredMixin,
    usuario_pode_acessar_indisponibilidades,
    usuario_pode_editar_propria_indisponibilidade,
)
