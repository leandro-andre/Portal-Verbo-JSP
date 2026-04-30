from infantil.models import ChamadaResponsavel


def criar_chamada_responsavel(form, sala, criado_por):
    chamada = form.save(commit=False)
    chamada.sala = sala
    chamada.criado_por = criado_por
    chamada.save()
    return chamada


def get_chamadas_da_sala(sala):
    return ChamadaResponsavel.objects.da_sala(sala).com_relacoes_basicas().ordenadas_por_solicitacao()


def cancelar_chamada(chamada):
    chamada.marcar_cancelado()
    return chamada


def resolver_chamada(chamada):
    chamada.marcar_resolvido()
    return chamada


def reenviar_chamada(chamada):
    chamada.marcar_reenviado()
    return chamada


def marcar_chamada_como_exibida(chamada):
    chamada.marcar_exibido()
    return chamada


def get_chamadas_ativas_para_midia():
    return ChamadaResponsavel.objects.ativas().com_relacoes_basicas().order_by("status", "-criado_em")


def get_chamadas_pendentes_para_midia():
    return get_chamadas_ativas_para_midia().pendentes()


def get_chamadas_exibidas_para_midia():
    return get_chamadas_ativas_para_midia().exibidas()


def get_chamadas_pendentes_payload():
    chamadas = (
        ChamadaResponsavel.objects.pendentes()
        .com_relacoes_basicas()
        .order_by("-criado_em")
        .values("id", "numero_ficha", "status", "sala__nome")
    )
    return [
        {
            "id": chamada["id"],
            "sala": chamada["sala__nome"],
            "numero_ficha": chamada["numero_ficha"],
            "status": chamada["status"],
        }
        for chamada in chamadas
    ]
