from django.utils.dateparse import parse_date, parse_time

from .models import IndisponibilidadeMembro


def get_indisponibilidades_ativas_do_membro(membro, data=None):
    if isinstance(data, str):
        data = parse_date(data) or data

    queryset = IndisponibilidadeMembro.objects.filter(
        membro=membro,
        ativo=True,
    )
    if data is not None:
        queryset = queryset.filter(
            data_inicio__lte=data,
            data_fim__gte=data,
        )
    return queryset


def membro_esta_indisponivel(membro, data, horario=None):
    if isinstance(data, str):
        data = parse_date(data) or data
    if isinstance(horario, str):
        horario = parse_time(horario) or horario

    indisponibilidades = get_indisponibilidades_ativas_do_membro(membro, data=data)

    if horario is None:
        return indisponibilidades.exists()

    for indisponibilidade in indisponibilidades:
        if not indisponibilidade.horario_inicio and not indisponibilidade.horario_fim:
            return True
        if (
            indisponibilidade.horario_inicio
            and indisponibilidade.horario_fim
            and indisponibilidade.horario_inicio <= horario <= indisponibilidade.horario_fim
        ):
            return True

    return False

