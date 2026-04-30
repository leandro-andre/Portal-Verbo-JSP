from escalas.models import IndisponibilidadeMembro


def listar_indisponibilidades_do_membro(membro):
    return IndisponibilidadeMembro.objects.do_membro(membro).recentes_primeiro()


def criar_indisponibilidade(form, membro):
    indisponibilidade = form.save(commit=False)
    indisponibilidade.membro = membro
    indisponibilidade.save()
    return indisponibilidade


def atualizar_indisponibilidade(form):
    return form.save()


def cancelar_indisponibilidade(indisponibilidade):
    indisponibilidade.ativo = False
    indisponibilidade.save(update_fields=["ativo", "atualizado_em"])
    return indisponibilidade
