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

A partir da PVV-037, novas escalas nascem somente neste fluxo. A fonte de
verdade oficial fica:

- agenda oficial: `WorshipService`
- escalas novas: `Schedule`
- pessoas escaladas: `ScheduleAssignment`
- vinculo departamental: `DepartmentMembership`
- disponibilidade: `PersonUnavailability`

O legado `Escala`/`EscalaItem`/`CultoPadrao`/`IndisponibilidadeMembro` permanece
apenas para consulta historica e compatibilidade temporaria.

PVV-038 conclui o cutover dos dashboards e leituras operacionais atuais/futuras:

- dashboard pessoal usa `ScheduleAssignment` publicado e futuro via
  `Usuario.person`;
- dashboard admin usa `Schedule` publicado/futuro, rascunhos futuros e
  assignments futuros do novo dominio;
- nenhum dashboard operacional faz fallback para `Escala` ou `EscalaItem`
  legado quando nao ha `Schedule`;
- `DRAFT` pode aparecer apenas como contador administrativo separado;
- `PUBLISHED` e `WorshipService.SCHEDULED` sao a combinacao oficial para
  compromissos futuros ativos;
- `Schedule.CANCELLED` e `WorshipService.CANCELLED` nao aparecem como
  compromisso ativo.

`Schedule` representa a escala de um departamento para um culto concreto.
Ela nao duplica data/horario como fonte de verdade; esses dados pertencem a
`WorshipService`.

`ScheduleAssignment` representa a pessoa escalada atraves de seu vinculo
departamental. Nao existe FK direta para `Person`.

## Constraints

- uma `Schedule` por `department + worship_service`
- um `ScheduleAssignment` por `schedule + department_membership`
- um `DepartmentScheduleRequirement` por `department + role`

O conflito operacional, porem, e por `Person`, pois uma pessoa pode possuir
vinculos em varios departamentos.

## Composicao Por Departamento

PVV-034 adiciona `DepartmentScheduleRequirement` no app `scheduling`.

Ele pertence ao Departamento, usa um `DepartmentRole` daquele mesmo
Departamento e configura a composicao quantitativa esperada para escalas:

- `minimum_quantity`: minimo obrigatorio para publicacao.
- `recommended_quantity`: quantidade desejada, usada como aviso.
- `active`: lifecycle da configuracao.

`recommended_quantity` deve ser maior ou igual a `minimum_quantity`.
`minimum_quantity=0` e permitido e significa cargo nao obrigatorio.
`recommended_quantity=0` tambem e permitido e significa ausencia de
recomendacao quantitativa.

Cargo sem `DepartmentScheduleRequirement` nao cria requisito implicito. O
sistema nao inventa default 1.

Nao existe `maximum_quantity` nesta versao. A mesma configuracao vale para
todos os cultos do Departamento, incluindo extraordinarios; nao ha variacao por
template, tipo, horario ou culto especifico.

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

Antes de publicar, `publish_schedule` executa a validacao atual da composicao.
Minimos nao atendidos, escala sem pessoas, culto cancelado, departamento
inativo e assignments atualmente inelegiveis bloqueiam publicacao com
`SCHEDULE_VALIDATION_FAILED`.

Recomendado nao atingido gera aviso, mas nao bloqueia publicacao.

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

## Minhas Escalas

PVV-035 adiciona a experiencia self-service `Minhas Escalas`.

O fluxo de dados e:

`Usuario -> Usuario.person -> Person -> DepartmentMembership -> ScheduleAssignment -> Schedule -> WorshipService`

O endpoint publico para a propria pessoa e:

- `GET /api/me/schedules/`

Filtros opcionais:

- `scope=upcoming|history|all`
- `year`
- `month`

O endpoint nao aceita `person_id` ou `user_id`; ele sempre resolve a pessoa por
`request.user.person`. Se o Usuario nao possuir `Person` vinculada, retorna
estado claro com `person_linked=false` e lista vazia. Nao ha inferencia por
nome/e-mail e nenhuma `Person` e criada automaticamente.

`Person` sem `Usuario` continua podendo ter Membership, participar de
Departamento e ser escalada. Ela apenas nao possui acesso self-service ate
existir conta vinculada.

### Proximas Escalas

`scope=upcoming` retorna apenas assignments da propria pessoa quando:

- `Schedule.status=PUBLISHED`
- `Schedule.status` nao e `CANCELLED`
- `WorshipService.status=SCHEDULED`
- `WorshipService.date >= today`

Escalas de hoje aparecem como proximas. A hora atual nao e considerada nesta
feature.

`Schedule DRAFT` nunca aparece em Minhas Escalas. Quando o lider publica, a
escala passa a aparecer. Quando reabre para `DRAFT`, ela deixa de aparecer como
compromisso oficial.

`Schedule CANCELLED` e `WorshipService CANCELLED` nao aparecem como proximas
ativas.

### Historico

`scope=history` retorna registros da propria pessoa quando o culto esta no
passado, a Schedule foi cancelada ou o WorshipService foi cancelado. Isso
preserva visibilidade historica sem apagar `ScheduleAssignment`.

Nao existe status `REALIZADA`; evento passado e tratado como historico derivado
pela data do culto.

### Warnings Pessoais

Minhas Escalas pode retornar `warnings` por item, voltados somente a pessoa
autenticada. Exemplos:

- indisponibilidade pessoal registrada para o horario da escala
- situacao operacional atual que pode impedir a escala

Esses warnings nao removem o assignment e nao expõem detalhes de terceiros. O
motivo privado de `PersonUnavailability.reason` continua oculto.

Nao ha confirmacao, recusa, solicitacao de troca, notificacoes, lembretes,
contato automatico do lider, check-in ou presenca nesta etapa. A publicacao do
lider e a etapa que torna a escala vigente no processo atual.

## Mudancas posteriores

Se um culto for cancelado, departamento inativado, Membership ficar inativa ou
uma indisponibilidade for criada depois da escala, a Schedule/Assignment nao e
apagada automaticamente. O historico permanece. Novas operacoes passam pelas
validacoes atuais.

PVV-034 tambem usa essa validacao para revisar escalas existentes. Se uma
Schedule publicada se tornar invalida depois por mudanca de requirement,
Membership, cargo, departamento ou indisponibilidade, o status `PUBLISHED` nao
muda automaticamente. O endpoint de validacao passa a mostrar a pendencia
atual.

Assignments atualmente inelegiveis continuam no banco, mas nao contam para
`assigned_quantity` da composicao. O motivo privado de uma indisponibilidade
continua oculto; a validacao informa apenas que a pessoa esta indisponivel para
o culto.

## Snapshot

Nao foram criados snapshots de nome, cargo, departamento ou culto. Consultas
leem os relacionamentos atuais. Isso pode fazer o cargo exibido refletir uma
mudanca posterior em `DepartmentMembership.role`; antes da migracao final, o
projeto deve decidir se precisa de snapshot historico.

## API

- `GET /api/scheduling/departments/`
- `GET /api/scheduling/monthly/`
- `GET /api/me/schedules/`
- `GET /api/scheduling/schedules/`
- `POST /api/scheduling/schedules/`
- `GET /api/scheduling/schedules/{id}/`
- `GET /api/scheduling/schedules/{id}/validation/`
- `POST /api/scheduling/schedules/{id}/publish/`
- `POST /api/scheduling/schedules/{id}/reopen/`
- `POST /api/scheduling/schedules/{id}/cancel/`
- `POST /api/scheduling/schedules/{id}/reactivate/`
- `GET /api/scheduling/schedules/{id}/assignments/`
- `POST /api/scheduling/schedules/{id}/assignments/`
- `DELETE /api/scheduling/schedules/{id}/assignments/{assignment_id}/`
- `GET /api/scheduling/schedules/{id}/eligible-members/`

`GET /api/scheduling/monthly/?year=YYYY&month=M&department_id=ID` retorna a
projecao mensal para montagem: todos os `WorshipService` do mes, a `Schedule`
do departamento quando existir e um resumo operacional. Esse GET nao cria
Schedule e nao executa backfill. Cultos sem Schedule aparecem como pendentes
para criacao explicita via `POST /api/scheduling/schedules/`.

Resumo mensal:

- `services`
- `cancelled_services`
- `operational_services`
- `published`
- `draft`
- `cancelled_schedules`
- `without_schedule`

Quando uma Schedule existe, a projecao mensal tambem pode indicar
`validation_status`:

- `OK`
- `WARNING`
- `BLOCKED`

`GET /api/scheduling/schedules/{id}/validation/` retorna:

- `valid`
- `can_publish`
- `blocking_issues`
- `warnings`
- `requirements`

Cada requisito validado inclui cargo, minimo, recomendado, quantidade atribuida
operacionalmente valida, `minimum_met` e `recommended_met`.

Filtros de listagem:

- `department_id`
- `worship_service_id`
- `year`
- `month`
- `status`

## UI minima

- `/escalas`: montagem mensal por ano, mes e departamento, baseada na Agenda
  de Cultos. Cultos cancelados permanecem visiveis, mas nao editaveis.
- `/escalas/:id`: detail agrupado pelos cargos ativos do departamento,
  assignments, candidatos filtraveis por cargo, lifecycle, composicao da escala
  e pendencias/avisos de validacao.

Nao ha autoescala, drag and drop, publicacao em lote, slots fixos,
substituicao, notificacoes ou confirmacao/recusa nesta etapa.
