# Autorizacao funcional

## Principios

Autenticacao responde quem e o usuario. Autorizacao responde o que esse usuario pode fazer.

O Portal usa Django Groups e Permissions para as roles globais funcionais. O backend continua sendo a fonte de verdade; capabilities no frontend servem apenas para adaptar navegacao e botoes.

## Global Roles

As roles globais iniciais sao:

- `PORTAL_ADMIN`: Administrador do Portal
- `SECRETARY`: Secretaria
- `PASTOR`: Pastor

Os nomes tecnicos ficam centralizados em `usuarios.roles`.

Superuser e uma conta tecnica do Django. Administrador do Portal e uma role funcional baseada em Group. Um superuser sem o Group "Administrador do Portal" nao e apresentado como administrador funcional no frontend.

## Matriz inicial

Administrador do Portal:

- visualizar, criar e alterar Pessoas
- visualizar, aprovar e rejeitar solicitacoes de acesso
- visualizar, bloquear e reativar usuarios

Secretaria:

- visualizar, criar e alterar Pessoas
- visualizar, aprovar e rejeitar solicitacoes de acesso
- visualizar usuarios
- nao bloqueia nem reativa usuarios nesta fase

Pastor:

- visualizar Pessoas
- visualizar solicitacoes de acesso
- visualizar usuarios
- nao cria/edita Pessoas, nao aprova/rejeita solicitacoes e nao bloqueia/reativa usuarios nesta fase

## Permissions

Permissions padrao Django sao usadas quando expressam a acao:

- `pessoas.view_person`
- `pessoas.add_person`
- `pessoas.change_person`
- `usuarios.view_accessrequest`
- `usuarios.view_usuario`

Permissions customizadas cobrem acoes de negocio:

- `usuarios.approve_accessrequest`
- `usuarios.reject_accessrequest`
- `usuarios.disable_usuario`
- `usuarios.enable_usuario`

## Bootstrap

Execute:

```powershell
python manage.py setup_portal_roles
```

O comando e idempotente: cria os Groups, atribui as permissions esperadas e corrige a matriz ao ser reexecutado.

Para atribuir uma role em desenvolvimento:

```powershell
python manage.py assign_portal_role <username> SECRETARY
```

Roles aceitas: `PORTAL_ADMIN`, `SECRETARY`, `PASTOR`.

## Frontend

`/api/auth/current-user/` retorna roles e capabilities estaveis. O React usa essas capabilities para:

- exibir itens da sidebar
- proteger paginas com rota autorizada
- esconder botoes de acao sem permissao

Isso nao substitui a seguranca backend. Chamadas diretas continuam recebendo `403` quando o usuario nao possui a permission real.

## Legado e proximos passos

O campo legado `Usuario.eh_pastor` permanece. O Departamento Secretaria tambem permanece, mas nao concede automaticamente a Global Role Secretaria.

Midia nao e Global Role. Lider, vice-lider, professor, auxiliar, voluntario e ministro tambem nao sao Global Roles. Esses casos pertencem a autorizacao contextual futura baseada em departamentos e dominios especificos.
