# Home / Dashboard Pessoal

## Natureza

A Home do Portal e uma projecao de leitura. Ela nao possui model proprio, nao persiste cards e nao cria preferencias de usuario nesta fase.

Endpoint agregador:

- `GET /api/me/dashboard/`

Rota React:

- `/`

## Personalizacao

A Home e unica e adaptativa:

- dados pessoais aparecem quando `Usuario.person` existe;
- estado sem pessoa vinculada aparece sem quebrar a pagina;
- atalhos administrativos sao derivados das capabilities do `current-user`;
- lideranca contextual vem de `DepartmentMembership` ativo com `DepartmentRole.can_manage_schedules=True`.

Usuario admin sem `Person` continua vendo a mensagem de vinculo pessoal pendente, mas suas capabilities globais continuam disponiveis no frontend via `current-user`.

## Fontes de Verdade

- Identidade e foto: `Person`
- Situacao eclesiastica: `Membership` novo e `ChurchJourney`
- Departamentos: `DepartmentMembership`
- Cargos: `DepartmentRole`
- Escalas: app `scheduling`
- Cultos da proxima escala: `WorshipService` via `Schedule`
- Indisponibilidades: `PersonUnavailability`
- Acessos administrativos: roles/capabilities globais
- Lideranca contextual: `DepartmentRole.can_manage_schedules`

Dados legados nao sao usados pela Home:

- `Escala`
- `EscalaItem`
- `DepartamentoMembro`
- `IndisponibilidadeMembro`
- `CultoPadrao`
- `Usuario.status_eclesiastico`

## Regras de Resumo

Proxima escala:

- `Schedule.PUBLISHED`
- `WorshipService.SCHEDULED`
- data maior ou igual a hoje
- primeira por data, horario, departamento e id

Contadores:

- `upcoming_count`: mesma regra de proximas escalas da tela `Minhas Escalas`
- `month_count`: escalas publicadas e cultos agendados no mes atual, incluindo passado do mesmo mes

Indisponibilidades:

- `PersonUnavailability.ACTIVE`
- `end_date >= hoje`
- ordenacao por `start_date`, `start_time`, `id`
- o motivo nao e exibido na Home

## Estados Vazios

A Home possui estados para:

- usuario sem `Person`;
- pessoa sem proxima escala;
- pessoa sem indisponibilidades futuras;
- pessoa sem departamento ativo.

## Responsividade

O layout usa cards em grade no desktop e empilha no mobile. A proxima escala mantem data e horario visiveis diretamente, sem depender de tooltip.

## Fora do Escopo

Nao foram implementados nesta feature:

- avisos;
- comunicados;
- notificacoes;
- inbox;
- versiculo;
- CMS;
- relatorios novos;
- graficos;
- analytics;
- preferencias ou widgets configuraveis.
