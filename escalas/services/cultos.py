from escalas.models import CultoPadrao


def listar_cultos_padrao(query="", status=""):
    return CultoPadrao.objects.all().por_nome(query).por_status(status).ordenados()


def criar_culto_padrao(form):
    return form.save()


def atualizar_culto_padrao(form):
    return form.save()


def alternar_status_culto_padrao(culto):
    culto.ativo = not culto.ativo
    culto.save(update_fields=["ativo", "atualizado_em"])
    return culto


def get_cultos_padrao_data(cultos_queryset):
    return [
        {
            "id": culto.id,
            "nome": culto.nome,
            "dia_semana": culto.dia_semana,
            "horario": culto.horario.strftime("%H:%M"),
        }
        for culto in cultos_queryset.order_by("dia_semana", "horario", "nome")
    ]
