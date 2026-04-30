import calendar

from django.utils.dateparse import parse_date, parse_time

from .models import CultoPadrao, Escala, IndisponibilidadeMembro


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


def get_datas_do_culto_no_mes(ano, mes, dia_semana):
    calendario = calendar.Calendar()
    datas = []

    for data in calendario.itermonthdates(ano, mes):
        if data.month != mes:
            continue
        if data.weekday() == dia_semana:
            datas.append(data)

    return datas


def gerar_escalas_do_mes_para_departamento(departamento, ano, mes, cultos_padroes):
    criadas = []
    ignoradas = []

    for culto in cultos_padroes:
        if not isinstance(culto, CultoPadrao):
            continue

        for data in get_datas_do_culto_no_mes(ano, mes, culto.dia_semana):
            escala, created = Escala.objects.get_or_create(
                departamento=departamento,
                data=data,
                horario=culto.horario,
                defaults={
                    "titulo": culto.nome,
                    "culto_padrao": culto,
                    "ativa": True,
                    "observacoes": "",
                },
            )
            if created:
                criadas.append(escala)
            else:
                ignoradas.append(escala)

    return {
        "criadas": criadas,
        "ignoradas": ignoradas,
    }
