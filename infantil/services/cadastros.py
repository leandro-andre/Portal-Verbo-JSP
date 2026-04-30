from infantil.models import Crianca


def criar_cadastro_responsavel(form, responsavel_usuario):
    crianca = form.save(commit=False)
    crianca.responsavel_usuario = responsavel_usuario
    crianca.status = Crianca.Status.PENDENTE
    crianca.sala = None
    crianca.ativo = False
    crianca.save()
    return crianca


def atualizar_cadastro_responsavel(form, crianca):
    reenviado_para_revisao = crianca.status == Crianca.Status.RECUSADO
    if reenviado_para_revisao:
        form.instance.status = Crianca.Status.PENDENTE
        form.instance.sala = None
        form.instance.ativo = False
    crianca_atualizada = form.save()
    return crianca_atualizada, reenviado_para_revisao


def revisar_cadastro_infantil(form):
    return form.save()


def cadastrar_crianca_na_sala(form, sala):
    crianca = form.save(commit=False)
    crianca.sala = sala
    crianca.status = Crianca.Status.APROVADO
    crianca.ativo = True
    crianca.save()
    return crianca
