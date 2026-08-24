from escalas.models import IndisponibilidadeMembro


def listar_indisponibilidades_do_membro(membro):
    return IndisponibilidadeMembro.objects.do_membro(membro).recentes_primeiro()
