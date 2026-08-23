# Department Foundation

`Departamento` representa a estrutura organizacional da igreja. A PVV-027
reaproveita o model legado `departamentos.Departamento` e o expõe na nova
arquitetura React + DRF.

## Modelo

O model atual foi mantido:

- `nome`: nome administrativo do departamento.
- `codigo`: identificador funcional/tecnico unico.
- `descricao`: texto administrativo opcional.
- `ativo`: lifecycle ativo/inativo.
- `criado_em`: data de criacao.

Nenhum novo model `Department` foi criado. `DepartamentoMembro` tambem nao foi
migrado nesta etapa.

## Codigo

`codigo` e usado por regras especiais e integracoes legadas, como:

- `secretaria`
- `midia`
- `infantil`

Por isso, na API React o codigo e obrigatorio na criacao e imutavel na edicao.
O backend normaliza para formato slug-like usando a regra existente do model.
Codigos existentes nao sao renomeados automaticamente.

## Lifecycle

O lifecycle usa o campo existente `ativo`:

- `ACTIVE`: `ativo=True`
- `INACTIVE`: `ativo=False`

Endpoints explicitos:

- `POST /api/departments/{id}/deactivate/`
- `POST /api/departments/{id}/reactivate/`

Transicoes repetidas retornam `INVALID_DEPARTMENT_TRANSITION`.

Inativar departamento nao exclui nem altera:

- `DepartamentoMembro`
- `Escala`
- `EscalaItem`
- Infantil
- dados historicos

DELETE funcional nao existe para Departamento.

## Permissoes

Capabilities novas:

- `DEPARTMENT_VIEW`
- `DEPARTMENT_CREATE`
- `DEPARTMENT_CHANGE`
- `DEPARTMENT_DEACTIVATE`
- `DEPARTMENT_REACTIVATE`

Matriz:

- Administrador do Portal: visualizar, criar, editar, inativar e reativar.
- Secretaria: visualizar, criar, editar, inativar e reativar.
- Pastor: visualizar.
- Usuario comum: sem acesso administrativo.

A API nova usa permissoes Django e nao usa bypass legado de `eh_pastor` para
alteracao.

## Secretaria E Midia

Departamento Secretaria continua sendo uma estrutura operacional. Ele nao
concede automaticamente a Global Role Secretaria.

Departamento Midia continua sendo departamento. Midia nao foi promovida a
Global Role.

## Coexistencia Legada

As telas Django template de Departamentos continuam existindo. A PVV-027 apenas
adiciona a nova API e UI React para a entidade `Departamento`.

`DepartamentoMembro` ainda aponta para `Usuario` e permanece como base de
Escalas e Infantil ate a futura PVV-028.

## Futuro

PVV-028 deve tratar `DepartmentMembership` com `Person`, `Membership ACTIVE`,
papel contextual e lideranca. Lideranca nao deve ser campo direto em
`Departamento`.
