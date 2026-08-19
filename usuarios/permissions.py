from django.apps import apps

from church_journey.selectors import is_legacy_department_eligible_for_user_account


def _is_authenticated(usuario):
    return bool(getattr(usuario, "is_authenticated", False))


def usuario_tem_acesso_tecnico_total(usuario):
    return bool(_is_authenticated(usuario) and getattr(usuario, "is_superuser", False))


def usuario_eh_visitante(usuario):
    return bool(_is_authenticated(usuario) and getattr(usuario, "is_visitante", False))


def usuario_eh_membro(usuario):
    return bool(_is_authenticated(usuario) and getattr(usuario, "is_membro", False))


def usuario_eh_pastor(usuario):
    return bool(_is_authenticated(usuario) and getattr(usuario, "eh_pastor", False))


def usuario_tem_acesso_total_pastoral(usuario):
    return usuario_eh_pastor(usuario)


def usuario_tem_acesso_total_sistema(usuario):
    return usuario_tem_acesso_tecnico_total(usuario) or usuario_tem_acesso_total_pastoral(usuario)


def usuario_tem_cargo_departamental(usuario, codigos_departamento, papeis=None, somente_ativo=True):
    """Identidade departamental real, sem atalhos de acesso tecnico ou pastoral."""
    if not _is_authenticated(usuario):
        return False

    DepartamentoMembro = apps.get_model("departamentos", "DepartamentoMembro")
    filtros = {
        "membro": usuario,
        "departamento__codigo__in": tuple(codigos_departamento),
        "departamento__ativo": True,
    }
    if somente_ativo:
        filtros["ativo"] = True
    if papeis is None:
        papeis = (DepartamentoMembro.Papel.LIDER, DepartamentoMembro.Papel.VICE_LIDER)
    if papeis:
        filtros["papel__in"] = tuple(papeis)

    return DepartamentoMembro.objects.filter(**filtros).exists()


def usuario_eh_secretaria(usuario):
    Departamento = apps.get_model("departamentos", "Departamento")
    return usuario_tem_cargo_departamental(usuario, (Departamento.CodigoSistema.SECRETARIA,))


def usuario_eh_midia(usuario):
    Departamento = apps.get_model("departamentos", "Departamento")
    return usuario_tem_cargo_departamental(usuario, (Departamento.CodigoSistema.MIDIA,))


def usuario_tem_acesso_secretaria(usuario):
    return bool(
        _is_authenticated(usuario)
        and (
            usuario_tem_acesso_total_sistema(usuario)
            or usuario_eh_secretaria(usuario)
        )
    )


def usuario_tem_acesso_midia(usuario):
    return bool(
        _is_authenticated(usuario)
        and (
            usuario_tem_acesso_total_sistema(usuario)
            or usuario_eh_midia(usuario)
        )
    )


def usuario_eh_lider_departamento(usuario, departamento):
    if not _is_authenticated(usuario):
        return False

    DepartamentoMembro = apps.get_model("departamentos", "DepartamentoMembro")
    departamento_id = getattr(departamento, "pk", departamento)
    return DepartamentoMembro.objects.filter(
        membro=usuario,
        departamento_id=departamento_id,
        ativo=True,
        papel__in=DepartamentoMembro.PAPEIS_LIDERANCA,
    ).exists()


def usuario_eh_lider_em_algum_departamento(usuario):
    if not _is_authenticated(usuario):
        return False

    DepartamentoMembro = apps.get_model("departamentos", "DepartamentoMembro")
    return DepartamentoMembro.objects.filter(
        membro=usuario,
        ativo=True,
        departamento__ativo=True,
        papel__in=DepartamentoMembro.PAPEIS_LIDERANCA,
    ).exists()


def usuario_eh_ministro(usuario):
    if not _is_authenticated(usuario):
        return False

    Ministro = apps.get_model("ministros", "Ministro")
    return Ministro.objects.filter(
        usuario=usuario,
        ativo=True,
        status__in=(Ministro.Status.APROVADO, Ministro.Status.ATUALIZADO),
    ).exists()


def usuario_pode_montar_escala(usuario, departamento):
    return (
        usuario_tem_acesso_total_sistema(usuario)
        or usuario_eh_lider_departamento(usuario, departamento)
    )


def usuario_pode_ser_escalado_departamento(usuario):
    return is_legacy_department_eligible_for_user_account(usuario)


def usuario_pode_ser_escalado_verbo_no_lar(usuario):
    return (
        usuario_tem_acesso_total_sistema(usuario)
        or usuario_eh_ministro(usuario)
    )
