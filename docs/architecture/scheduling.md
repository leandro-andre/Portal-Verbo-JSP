# Scheduling Foundation

PVV-032 cria o novo dominio de escalas em paralelo ao legado.

## Legado preservado

O app `escalas` continua funcional e nao foi removido. Ele possui:

- `CultoPadrao`, acoplado a geracao de escalas legadas
- `Escala`, ligada a `Departamento` e opcionalmente a `CultoPadrao`
- `EscalaItem`, ligado a `DepartamentoMembro`
- `IndisponibilidadeMembro`, ligada a `Usuario`

Esse legado tambem alimenta dashboard, views Django, templates internos e fluxos
de departamentos. Nao houve migracao, backfill, dual-write ou alteracao
destrutiva.

## Novo dominio

O app `scheduling` nasce sobre o novo nucleo:

`WorshipService -> Schedule -> ScheduleAssignment -> DepartmentMembership -> Person`

`Schedule` representa a escala de um departamento para um culto concreto.
Ela nao duplica data/horario como fonte de verdade; esses dados pertencem a
`WorshipService`.

`ScheduleAssignment` representa a pessoa escalada atraves de seu vinculo
departamental. Nao existe FK direta para `Person`.

## Constraints

- uma `Schedule` por `department + worship_service`
- um `ScheduleAssignment` por `schedule + department_membership`

O conflito operacional, porem, e por `Person`, pois uma pessoa pode possuir
vinculos em varios departamentos.

## Lifecycle

`Schedule.status`:

- `DRAFT`
- `PUBLISHED`
- `CANCELLED`

Transicoes:

- `DRAFT -> PUBLISHED`
- `PUBLISHED -> DRAFT`
- `DRAFT -> CANCELLED`
- `PUBLISHED -> CANCELLED`
- `CANCELLED -> DRAFT`

`CANCELLED -> PUBLISHED` e bloqueado; primeiro volta para `DRAFT`.
Publicar escala vazia e bloqueado.

Assignments podem ser adicionados/removidos apenas em `DRAFT`.

## Validacoes operacionais

Criar Schedule exige:

- departamento ativo
- culto `SCHEDULED`
- culto futuro
- combinacao ainda inexistente

Criar Assignment exige:

- Schedule em `DRAFT`
- culto da Schedule ainda `SCHEDULED`
- departamento da Schedule ativo
- DepartmentMembership do mesmo departamento
- DepartmentMembership operacionalmente elegivel
- Person disponivel para data/horario do culto
- Person sem conflito em mesmo `WorshipService`
- Person sem conflito em outro culto `SCHEDULED` na mesma data e horario

Schedules `CANCELLED` e cultos `CANCELLED` nao contam como conflito operacional.
Assignments em `DRAFT` e `PUBLISHED` contam como conflito.

## Elegibilidade

O selector `get_assignment_eligibility` retorna resultado estruturado:

- `eligible`
- `reasons`

Ele reutiliza a elegibilidade de `DepartmentMembership` e o selector oficial de
indisponibilidade `is_person_available`.

O endpoint de candidatos retorna todos os vinculos do departamento, inclusive os
inelegiveis, para permitir uma UI futura mais transparente.

## Privacidade

Indisponibilidade bloqueia novo assignment, mas a API nao retorna
`PersonUnavailability.reason`. O lider recebe apenas:

- `PERSON_UNAVAILABLE_FOR_WORSHIP_SERVICE`
- `Pessoa indisponivel para este culto.`

## Autorizacao

Admin e Secretaria possuem gestao global.

Pastor possui visualizacao global.

Lideranca contextual depende de:

- `request.user.person`
- `DepartmentMembership ACTIVE` no mesmo departamento
- `DepartmentRole ACTIVE`
- `can_manage_schedules=True`
- elegibilidade operacional atual do vinculo

Foi adicionada a flag `DepartmentRole.can_manage_schedules` porque as flags
anteriores falavam de dados/cargos/pessoas, nao de escala.

## Person sem Usuario

Assignment usa `DepartmentMembership`, entao a pessoa escalada nao precisa possuir
conta `Usuario`. Isso preserva o novo modelo baseado em `Person`.

## Mudancas posteriores

Se um culto for cancelado, departamento inativado, Membership ficar inativa ou
uma indisponibilidade for criada depois da escala, a Schedule/Assignment nao e
apagada automaticamente. O historico permanece. Novas operacoes passam pelas
validacoes atuais.

## Snapshot

Nao foram criados snapshots de nome, cargo, departamento ou culto. Consultas
leem os relacionamentos atuais. Isso pode fazer o cargo exibido refletir uma
mudanca posterior em `DepartmentMembership.role`; antes da migracao final, o
projeto deve decidir se precisa de snapshot historico.

## API

- `GET /api/scheduling/schedules/`
- `POST /api/scheduling/schedules/`
- `GET /api/scheduling/schedules/{id}/`
- `POST /api/scheduling/schedules/{id}/publish/`
- `POST /api/scheduling/schedules/{id}/reopen/`
- `POST /api/scheduling/schedules/{id}/cancel/`
- `POST /api/scheduling/schedules/{id}/reactivate/`
- `GET /api/scheduling/schedules/{id}/assignments/`
- `POST /api/scheduling/schedules/{id}/assignments/`
- `DELETE /api/scheduling/schedules/{id}/assignments/{assignment_id}/`
- `GET /api/scheduling/schedules/{id}/eligible-members/`

Filtros de listagem:

- `department_id`
- `worship_service_id`
- `year`
- `month`
- `status`

## UI minima

- `/escalas`: listagem, filtros simples e criacao minima
- `/escalas/:id`: detail, assignments, candidatos e lifecycle

PVV-033+ deve evoluir a experiencia de montagem, substituicao, publicacao em
lote, notificacoes e confirmacao/recusa.
