from departamentos.models import DepartamentoMembro

from escalas.models import CultoPadrao, Escala, EscalaItem
from escalas.utils import gerar_escalas_do_mes_para_departamento, membro_esta_indisponivel


def listar_escalas_gerenciaveis(*, user, departamentos_queryset, query="", status="", departamento_id=""):
    return (
        Escala.objects.com_relacoes_basicas()
        .com_totais_itens()
        .gerenciaveis_por_usuario(user, departamentos_queryset)
        .por_titulo(query)
        .por_status(status)
        .por_departamento_id(departamento_id)
        .order_by("data", "horario", "titulo")
    )


def gerar_escalas_do_mes(*, departamento, ano, mes, cultos_padroes):
    return gerar_escalas_do_mes_para_departamento(
        departamento=departamento,
        ano=ano,
        mes=mes,
        cultos_padroes=cultos_padroes,
    )


def criar_escala(form):
    return form.save()


def atualizar_escala(form):
    return form.save()


def get_itens_da_escala(escala):
    return EscalaItem.objects.da_escala(escala).com_relacoes_basicas().ordenados_para_exibicao()


def get_item_escala_or_none(escala, item_id):
    try:
        return EscalaItem.objects.select_related("participacao__membro").get(
            pk=item_id,
            escala=escala,
        )
    except (EscalaItem.DoesNotExist, ValueError):
        return None


def get_indisponiveis_da_escala(escala):
    participacoes_departamento = DepartamentoMembro.objects.filter(
        departamento=escala.departamento,
        ativo=True,
    ).select_related("membro")
    return [
        participacao
        for participacao in participacoes_departamento
        if membro_esta_indisponivel(
            participacao.membro,
            escala.data,
            escala.horario,
        )
    ]


def salvar_item_escala(form):
    return form.save()


def remover_item_da_escala(item):
    item.delete()


def get_cultos_queryset_para_escala(escala=None):
    queryset = CultoPadrao.objects.filter(ativo=True)
    if escala and escala.culto_padrao_id:
        queryset = (queryset | CultoPadrao.objects.filter(pk=escala.culto_padrao_id)).distinct()
    return queryset
