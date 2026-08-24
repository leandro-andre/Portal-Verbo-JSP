from departamentos.models import DepartamentoMembro

from escalas.models import Escala, EscalaItem
from escalas.utils import membro_esta_indisponivel


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


def get_itens_da_escala(escala):
    return EscalaItem.objects.da_escala(escala).com_relacoes_basicas().ordenados_para_exibicao()


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
