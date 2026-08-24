from escalas.models import CultoPadrao


def listar_cultos_padrao(query="", status=""):
    return CultoPadrao.objects.all().por_nome(query).por_status(status).ordenados()
