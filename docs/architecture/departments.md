# Department Foundation

`Departamento` representa a estrutura organizacional da igreja. A PVV-027
reaproveitou o model legado `departamentos.Departamento` e o expos na nova
arquitetura React + DRF. A PVV-028 adiciona cargos e vinculos departamentais
novos, baseados em `Person`, sem migrar automaticamente os vinculos legados.

## Modelo

O model `Departamento` foi mantido:

- `nome`: nome administrativo do departamento.
- `codigo`: identificador funcional/tecnico unico.
- `descricao`: texto administrativo opcional.
- `ativo`: lifecycle ativo/inativo.
- `criado_em`: data de criacao.

Nenhum novo model `Department` foi criado. `DepartamentoMembro` tambem nao foi
migrado.

## Cargos

`DepartmentRole` representa um cargo configuravel dentro de um `Departamento`.

- `department`: departamento dono do cargo.
- `name`: nome administrativo do cargo.
- `code`: identificador slug-like unico por departamento.
- `active`: lifecycle ativo/inativo.
- `can_manage_department`: permite gerenciar dados do proprio departamento no
  contexto daquele departamento.
- `can_manage_members`: permite gerenciar cargos e pessoas do proprio
  departamento.

O codigo do cargo e imutavel pela API depois da criacao. A regra de lideranca
nao depende do nome "Lider"; depende das flags do cargo.

## Pessoas No Departamento

`DepartmentMembership` representa o vinculo novo entre uma `Person`, um
`Departamento` e um `DepartmentRole`.

- Ha no maximo um registro por `Person + Departamento`.
- Troca de cargo atualiza o mesmo registro; nao ha historico de cargos nesta
  etapa.
- Criacao e reativacao exigem `Membership` eclesiastica ativa no dominio
  `church_journey`.
- Pessoa sem `Usuario` pode ser vinculada, desde que tenha `Membership ACTIVE`.
- Se a membresia eclesiastica ficar inativa depois, o vinculo departamental nao
  e alterado automaticamente; a API passa a marcar a elegibilidade operacional
  como falsa.

## Elegibilidade

Elegibilidade departamental e derivada. Nao existe campo persistido
`eligible`, `operationally_eligible` ou `eligibility_status` no banco.

O dominio separa dois conceitos:

- Entry eligibility: se uma pessoa pode entrar em um departamento.
- Operational eligibility: se uma pessoa ja vinculada esta apta a atuar.

Status do vinculo nao e a mesma coisa que elegibilidade. Uma
`DepartmentMembership` pode continuar `ACTIVE` e ainda assim estar
operacionalmente inelegivel porque a `Membership`, o cargo ou o departamento
ficaram inativos depois.

### Entry Eligibility

`get_department_entry_eligibility(person, department)` retorna um resultado
estruturado:

- `eligible`: booleano derivado.
- `reasons`: lista de motivos com `code` e `message`.

Regras atuais:

- `Membership ACTIVE` no dominio `church_journey`.
- `Departamento.ativo=True`.
- ausencia de `DepartmentMembership` existente para a mesma pessoa e
  departamento.

Motivos atuais:

- `MEMBERSHIP_NOT_ACTIVE`
- `DEPARTMENT_INACTIVE`
- `DEPARTMENT_MEMBERSHIP_ALREADY_EXISTS`

Pessoa sem `Usuario` pode ser elegivel, desde que tenha `Membership ACTIVE`.
Superuser, Admin ou Pastor nao ficam elegiveis por causa do papel global.

### Operational Eligibility

`get_department_membership_eligibility(department_membership)` retorna o mesmo
formato estruturado.

Regras atuais:

- `DepartmentMembership.status=ACTIVE`.
- `Departamento.ativo=True`.
- `DepartmentRole.active=True`.
- `Membership ACTIVE` da `Person`.

Motivos atuais:

- `DEPARTMENT_MEMBERSHIP_INACTIVE`
- `DEPARTMENT_INACTIVE`
- `DEPARTMENT_ROLE_INACTIVE`
- `MEMBERSHIP_NOT_ACTIVE`

Uma pessoa pode ter varios motivos simultaneamente; consultas de elegibilidade
nao param no primeiro erro.

`is_department_membership_operationally_eligible(...)` e apenas um atalho
booleano que delega para o resultado estruturado.

`get_person_department_eligibility(person, department)` localiza o vinculo
existente e retorna `NO_DEPARTMENT_MEMBERSHIP` quando nao houver vinculo.

## Codigo

`codigo` e usado por regras especiais e integracoes legadas, como:

- `secretaria`
- `midia`
- `infantil`

Por isso, na API React o codigo do departamento e obrigatorio na criacao e
imutavel na edicao. O backend normaliza para formato slug-like usando a regra
existente do model. Codigos existentes nao sao renomeados automaticamente.

## Lifecycle

O lifecycle de `Departamento` usa o campo existente `ativo`:

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

Tambem nao existe DELETE funcional para cargos ou vinculos departamentais. O
lifecycle usa endpoints explicitos:

- `POST /api/departments/{department_id}/roles/{role_id}/deactivate/`
- `POST /api/departments/{department_id}/roles/{role_id}/reactivate/`
- `POST /api/departments/{department_id}/members/{membership_id}/deactivate/`
- `POST /api/departments/{department_id}/members/{membership_id}/reactivate/`

## Permissoes

Capabilities:

- `DEPARTMENT_VIEW`
- `DEPARTMENT_CREATE`
- `DEPARTMENT_CHANGE`
- `DEPARTMENT_DEACTIVATE`
- `DEPARTMENT_REACTIVATE`
- `DEPARTMENT_ROLE_VIEW`
- `DEPARTMENT_ROLE_CREATE`
- `DEPARTMENT_ROLE_CHANGE`
- `DEPARTMENT_ROLE_DEACTIVATE`
- `DEPARTMENT_ROLE_REACTIVATE`
- `DEPARTMENT_MEMBERSHIP_VIEW`
- `DEPARTMENT_MEMBERSHIP_CREATE`
- `DEPARTMENT_MEMBERSHIP_CHANGE`
- `DEPARTMENT_MEMBERSHIP_DEACTIVATE`
- `DEPARTMENT_MEMBERSHIP_REACTIVATE`

Matriz:

- Administrador do Portal: visualizar, criar, editar, inativar e reativar.
- Secretaria: visualizar, criar, editar, inativar e reativar.
- Pastor: visualizar departamento, cargos e pessoas.
- Usuario comum: sem acesso administrativo.

A API nova usa permissoes Django e nao usa bypass legado de `eh_pastor` para
alteracao.

Permissoes contextuais nao criam Global Role. Um usuario com `person` vinculada
a uma `DepartmentMembership ACTIVE` no departamento pode receber acesso ao
proprio departamento conforme as flags do seu `DepartmentRole`.

A autorizacao contextual tambem exige elegibilidade operacional do proprio
gestor. Se a `Membership` do lider ficar `INACTIVE`, se seu cargo ficar
`INACTIVE` ou se o departamento ficar `INACTIVE`, o vinculo permanece, mas ele
perde gestao contextual. Administrador e Secretaria continuam administrando por
permissoes globais.

Elegibilidade nao e autorizacao. Secretaria pode administrar um membro
inelegivel; a inelegibilidade responde se a pessoa pode servir, nao quem pode
gerenciar o cadastro.

## Secretaria E Midia

Departamento Secretaria continua sendo uma estrutura operacional. Ele nao
concede automaticamente a Global Role Secretaria.

Departamento Midia continua sendo departamento. Midia nao foi promovida a
Global Role.

## Coexistencia Legada

As telas Django template de Departamentos continuam existindo. A API e UI React
novas convivem com a entidade `Departamento`.

`DepartamentoMembro` ainda aponta para `Usuario` e permanece como base de
Escalas, Infantil e qualquer rotina legada que ainda dependa dele.

PVV-028 nao executa dual-write, backfill ou migracao automatica de
`DepartamentoMembro` para `DepartmentMembership`.

## Futuro

Uma feature futura pode tratar migracao assistida do legado, historico de cargos
ou selectors especificos de elegibilidade para Escalas.

Criterios adicionais poderao surgir quando houver requisito real, como faixa
etaria, treinamento especifico, perfil ministerial ou requisitos do Infantil.
Nao ha rule engine, JSON arbitrario de criterios, DSL ou configuracao vazia de
regras nesta etapa.
