from usuarios.permissions import usuario_tem_acesso_secretaria


def usuario_pode_gerenciar_financeiro(usuario):
    return usuario_tem_acesso_secretaria(usuario)
