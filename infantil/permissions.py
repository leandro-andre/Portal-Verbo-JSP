from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404

from departamentos.models import Departamento, DepartamentoMembro
from governanca.permissions import usuario_pode_acessar_painel_midia

from .models import AulaSala, ChamadaResponsavel, Crianca, SalaInfantil, SalaMembro


PAPEIS_GESTAO_SALA = SalaMembro.PAPEIS_GESTAO_SALA
PAPEIS_GESTAO_DEPARTAMENTO_INFANTIL = (DepartamentoMembro.Papel.LIDER,)


def _as_sala_id(sala):
    if isinstance(sala, SalaInfantil):
        return sala.pk
    return sala

def get_departamentos_infantis():
    return Departamento.objects.filter(
        codigo=Departamento.CodigoSistema.INFANTIL,
        ativo=True,
    )


def usuario_eh_admin_infantil(usuario):
    return bool(
        getattr(usuario, "is_authenticated", False)
        and (usuario.is_staff or usuario.is_superuser)
    )


def usuario_eh_lider_departamento_infantil(usuario):
    if not getattr(usuario, "is_authenticated", False):
        return False
    if usuario_eh_admin_infantil(usuario):
        return True

    return DepartamentoMembro.objects.filter(
        membro=usuario,
        ativo=True,
        papel__in=PAPEIS_GESTAO_DEPARTAMENTO_INFANTIL,
        departamento__in=get_departamentos_infantis(),
    ).exists()


def usuario_pertence_sala(usuario, sala, somente_ativo=True):
    if not getattr(usuario, "is_authenticated", False):
        return False
    if usuario_eh_admin_infantil(usuario) or usuario_eh_lider_departamento_infantil(usuario):
        return True

    filtros = {"membro": usuario, "sala_id": _as_sala_id(sala)}
    if somente_ativo:
        filtros["ativo"] = True
    return SalaMembro.objects.filter(**filtros).exists()


def usuario_tem_papel_na_sala(usuario, sala, papeis, somente_ativo=True):
    if not getattr(usuario, "is_authenticated", False):
        return False
    if usuario_eh_admin_infantil(usuario) or usuario_eh_lider_departamento_infantil(usuario):
        return True

    filtros = {
        "membro": usuario,
        "sala_id": _as_sala_id(sala),
        "papel__in": tuple(papeis),
    }
    if somente_ativo:
        filtros["ativo"] = True
    return SalaMembro.objects.filter(**filtros).exists()


def usuario_eh_lider_sala(usuario, sala):
    return usuario_tem_papel_na_sala(usuario, sala, PAPEIS_GESTAO_SALA)


def get_salas_do_usuario(usuario, somente_ativas=True):
    if not getattr(usuario, "is_authenticated", False):
        return SalaInfantil.objects.none()
    if usuario_eh_admin_infantil(usuario) or usuario_eh_lider_departamento_infantil(usuario):
        queryset = SalaInfantil.objects.all()
        return queryset.filter(ativa=True) if somente_ativas else queryset

    filtros = {"equipe__membro": usuario}
    if somente_ativas:
        filtros["equipe__ativo"] = True
        filtros["ativa"] = True
    return SalaInfantil.objects.filter(**filtros).distinct()


def get_salas_lideradas(usuario, somente_ativas=True):
    if not getattr(usuario, "is_authenticated", False):
        return SalaInfantil.objects.none()
    if usuario_eh_admin_infantil(usuario) or usuario_eh_lider_departamento_infantil(usuario):
        queryset = SalaInfantil.objects.all()
        return queryset.filter(ativa=True) if somente_ativas else queryset

    filtros = {
        "equipe__membro": usuario,
        "equipe__ativo": True,
        "equipe__papel__in": PAPEIS_GESTAO_SALA,
    }
    if somente_ativas:
        filtros["ativa"] = True
    return SalaInfantil.objects.filter(**filtros).distinct()


def usuario_pode_visualizar_infantil(usuario):
    return (
        usuario_eh_admin_infantil(usuario)
        or usuario_eh_lider_departamento_infantil(usuario)
        or get_salas_do_usuario(usuario).exists()
    )


def usuario_pode_acessar_minhas_criancas(usuario):
    return bool(getattr(usuario, "is_authenticated", False))


def usuario_pode_ver_crianca_do_responsavel(usuario, crianca):
    return bool(
        getattr(usuario, "is_authenticated", False)
        and crianca.responsavel_usuario_id == getattr(usuario, "pk", None)
    )


def usuario_pode_editar_crianca_do_responsavel(usuario, crianca):
    return (
        usuario_pode_ver_crianca_do_responsavel(usuario, crianca)
        and crianca.pode_ser_editada_pelo_responsavel
    )


def usuario_pode_revisar_cadastros_infantis(usuario):
    return usuario_pode_visualizar_infantil(usuario)


def usuario_pode_ver_cadastro_crianca(usuario, crianca):
    return usuario_pode_revisar_cadastros_infantis(usuario) or usuario_pode_ver_crianca_do_responsavel(
        usuario,
        crianca,
    )


def usuario_pode_criar_salas_infantis(usuario):
    return usuario_eh_admin_infantil(usuario) or usuario_eh_lider_departamento_infantil(usuario)


def usuario_pode_ver_sala(usuario, sala):
    return usuario_pertence_sala(usuario, sala)


def usuario_pode_editar_sala(usuario, sala):
    return usuario_eh_admin_infantil(usuario) or usuario_eh_lider_departamento_infantil(
        usuario
    )


def usuario_pode_ver_equipe_sala(usuario, sala):
    if usuario_eh_admin_infantil(usuario) or usuario_eh_lider_departamento_infantil(usuario):
        return True
    return usuario_eh_lider_sala(usuario, sala)


def usuario_pode_gerenciar_equipe_sala(usuario, sala):
    return usuario_eh_admin_infantil(usuario) or usuario_eh_lider_departamento_infantil(
        usuario
    )


def usuario_pode_ver_criancas(usuario, sala):
    return usuario_pode_ver_sala(usuario, sala)


def usuario_pode_gerenciar_criancas(usuario, sala):
    return (
        usuario_eh_admin_infantil(usuario)
        or usuario_eh_lider_departamento_infantil(usuario)
        or usuario_eh_lider_sala(usuario, sala)
    )


def usuario_pode_ver_aulas(usuario, sala):
    return usuario_pode_ver_sala(usuario, sala)


def usuario_pode_gerenciar_aulas(usuario, sala):
    return (
        usuario_eh_admin_infantil(usuario)
        or usuario_eh_lider_departamento_infantil(usuario)
        or usuario_eh_lider_sala(usuario, sala)
    )


def usuario_pode_acessar_anexos(usuario, sala):
    return usuario_pode_ver_aulas(usuario, sala)


def usuario_pode_criar_chamada_responsavel(usuario, sala):
    return usuario_pode_ver_sala(usuario, sala)


def usuario_pode_ver_chamadas_sala(usuario, sala):
    return usuario_pode_ver_sala(usuario, sala)


def usuario_pode_cancelar_chamada(usuario, chamada):
    if not getattr(usuario, "is_authenticated", False):
        return False
    if chamada.status != ChamadaResponsavel.Status.PENDENTE:
        return False
    return (
        usuario_eh_admin_infantil(usuario)
        or usuario_eh_lider_departamento_infantil(usuario)
        or usuario_pertence_sala(usuario, chamada.sala)
    )


def usuario_pode_operar_chamadas_na_midia(usuario):
    return usuario_pode_acessar_painel_midia(usuario)


def usuario_pode_marcar_chamada_exibida(usuario, chamada):
    return (
        chamada.status == ChamadaResponsavel.Status.PENDENTE
        and usuario_pode_operar_chamadas_na_midia(usuario)
    )


def usuario_pode_resolver_chamada(usuario, chamada):
    if chamada.status != ChamadaResponsavel.Status.EXIBIDO:
        return False
    return (
        usuario_eh_admin_infantil(usuario)
        or usuario_eh_lider_departamento_infantil(usuario)
        or usuario_pertence_sala(usuario, chamada.sala)
    )


def usuario_pode_reenviar_chamada(usuario, chamada):
    if chamada.status != ChamadaResponsavel.Status.EXIBIDO:
        return False
    return (
        usuario_eh_admin_infantil(usuario)
        or usuario_eh_lider_departamento_infantil(usuario)
        or usuario_pertence_sala(usuario, chamada.sala)
    )


class InfantilAccessRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return usuario_pode_visualizar_infantil(self.request.user)


class SalaPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    sala_kwarg = "pk"

    def get_permission_sala(self):
        if hasattr(self, "object") and self.object is not None:
            if isinstance(self.object, SalaInfantil):
                return self.object
            if isinstance(self.object, Crianca):
                return self.object.sala
            if isinstance(self.object, AulaSala):
                return self.object.sala
            if isinstance(self.object, ChamadaResponsavel):
                return self.object.sala
        model = getattr(self, "model", None)
        if model in {Crianca, AulaSala, ChamadaResponsavel} and hasattr(self, "get_object"):
            self.object = self.get_object()
            return self.object.sala
        if "sala_pk" in self.kwargs:
            return get_object_or_404(SalaInfantil, pk=self.kwargs["sala_pk"])
        return get_object_or_404(SalaInfantil, pk=self.kwargs[self.sala_kwarg])


class SalaViewRequiredMixin(SalaPermissionMixin):
    def test_func(self):
        return usuario_pode_ver_sala(self.request.user, self.get_permission_sala())


class SalaEditRequiredMixin(SalaPermissionMixin):
    def test_func(self):
        return usuario_pode_editar_sala(self.request.user, self.get_permission_sala())


class SalaTeamViewRequiredMixin(SalaPermissionMixin):
    def test_func(self):
        return usuario_pode_ver_equipe_sala(self.request.user, self.get_permission_sala())


class SalaTeamManageRequiredMixin(SalaPermissionMixin):
    def test_func(self):
        return usuario_pode_gerenciar_equipe_sala(
            self.request.user,
            self.get_permission_sala(),
        )


class SalaChildrenViewRequiredMixin(SalaPermissionMixin):
    def test_func(self):
        return usuario_pode_ver_criancas(self.request.user, self.get_permission_sala())


class SalaChildrenManageRequiredMixin(SalaPermissionMixin):
    def test_func(self):
        return usuario_pode_gerenciar_criancas(
            self.request.user,
            self.get_permission_sala(),
        )


class SalaLessonsViewRequiredMixin(SalaPermissionMixin):
    def test_func(self):
        return usuario_pode_ver_aulas(self.request.user, self.get_permission_sala())


class SalaLessonsManageRequiredMixin(SalaPermissionMixin):
    def test_func(self):
        return usuario_pode_gerenciar_aulas(
            self.request.user,
            self.get_permission_sala(),
        )


class SalaCreatorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return usuario_pode_criar_salas_infantis(self.request.user)


class SalaCallsManageRequiredMixin(SalaPermissionMixin):
    def test_func(self):
        return usuario_pode_criar_chamada_responsavel(
            self.request.user,
            self.get_permission_sala(),
        )


class CadastroCriancaResponsavelRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return usuario_pode_ver_crianca_do_responsavel(self.request.user, self.get_object())


class CadastroCriancaResponsavelEditRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return usuario_pode_editar_crianca_do_responsavel(self.request.user, self.get_object())


class CadastroCriancaReviewRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return usuario_pode_revisar_cadastros_infantis(self.request.user)
