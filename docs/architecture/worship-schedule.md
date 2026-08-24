# Worship Schedule

PVV-031 cria a Agenda de Cultos como dominio institucional separado de Escalas.

## Decisao de dominio

O projeto ja possui `escalas.CultoPadrao`, atualmente persistido na tabela legada
`departamentos_cultopadrao` e acoplado a `Escala`/`EscalaItem`. Esse modelo serve
ao fluxo legado de escalas departamentais: sugere titulo, valida dia/horario e
gera bases de escala por departamento.

Por isso a agenda oficial foi criada no app `worship`, em paralelo. Nao houve
remocao, backfill, dual-write ou alteracao destrutiva no legado.

## Template vs ocorrencia

`WorshipServiceTemplate` representa a regra semanal simples:

- `name`
- `weekday`
- `time`
- `active`
- `created_at`
- `updated_at`

Template nao e uma ocorrencia concreta. Alterar um template afeta apenas novas
geracoes; ocorrencias ja materializadas permanecem com seus proprios dados.

`WorshipService` representa um culto concreto em uma data:

- `template`, opcional e `SET_NULL`
- `name`
- `date`
- `source_date`
- `time`
- `status`
- `kind`
- `notes`
- `created_at`
- `updated_at`

`REGULAR` nasce de um template e preserva `source_date`. `EXTRAORDINARY` nao
precisa de template e fica com `template=null` e `source_date=null`.

## Weekday

O dia da semana usa representacao numerica estavel compatibilizada com
`date.weekday()`:

- 0: Segunda-feira
- 1: Terca-feira
- 2: Quarta-feira
- 3: Quinta-feira
- 4: Sexta-feira
- 5: Sabado
- 6: Domingo

A API retorna tambem `weekday_label`.

## Geracao mensal

`generate_worship_services_for_month(year, month)` percorre todos os templates
ativos e calcula as datas daquele `weekday` dentro do mes. A operacao e explicita:
GET nunca cria dados.

A geracao so cria o que falta:

- templates inativos nao geram novas ocorrencias
- cultos extraordinarios nao sao alterados
- ocorrencias existentes nao sao removidas
- alteracoes pontuais existentes sao preservadas

## Idempotencia e source_date

A identidade de geracao e `template + source_date`.

Exemplo: template Domingo 10h gera `source_date=2026-09-06`. Se a Secretaria
mover essa ocorrencia para 2026-09-07 ou alterar o horario para 11h,
`source_date` continua 2026-09-06. Uma nova geracao do mes reconhece a origem e
nao recria 2026-09-06 10h.

Existe constraint unica condicional para `template + source_date` quando
`template` nao e nulo. Cultos extraordinarios nao entram nessa constraint.

Nao existe constraint global `date + time`, pois atividades simultaneas podem ser
legitimas.

## Lifecycles

Template:

- ativo
- inativo

Inativar template impede novas geracoes futuras, mas nao cancela nem apaga
ocorrencias existentes.

Ocorrencia:

- `SCHEDULED`
- `CANCELLED`

Cancelamento preserva historico. Reativacao permite corrigir cancelamento por
engano. Nao existe status `COMPLETED` nesta feature; culto passado pode continuar
`SCHEDULED` historicamente.

## Permissions

Administrador e Secretaria administram a agenda:

- visualizar
- criar/alterar templates
- inativar/reativar templates
- gerar mes
- criar extraordinario
- alterar ocorrencia
- cancelar/reativar ocorrencia

Pastor e view-only.

Lider de departamento nao administra agenda, mesmo quando possui permissao
contextual sobre um departamento. Agenda de Cultos e institucional, nao
departamental.

Capabilities de frontend:

- `WORSHIP_SCHEDULE_VIEW`
- `WORSHIP_SCHEDULE_MANAGE`

## APIs

Templates:

- `GET /api/worship/templates/`
- `POST /api/worship/templates/`
- `GET /api/worship/templates/{id}/`
- `PATCH /api/worship/templates/{id}/`
- `POST /api/worship/templates/{id}/deactivate/`
- `POST /api/worship/templates/{id}/reactivate/`

Agenda:

- `GET /api/worship/services/?year=2026&month=9`
- `POST /api/worship/services/generate/`
- `POST /api/worship/services/extraordinary/`
- `GET /api/worship/services/{id}/`
- `PATCH /api/worship/services/{id}/`
- `POST /api/worship/services/{id}/cancel/`
- `POST /api/worship/services/{id}/reactivate/`

DELETE nao e operacao funcional.

## Frontend

A rota `/agenda-cultos` mostra a agenda mensal agrupada por data, com navegacao
mes anterior/proximo. A geracao mensal e acionada por botao explicito.

A rota `/agenda-cultos/padroes` gerencia templates. A edicao mostra a regra de
que cultos ja gerados nao sao reescritos.

Cultos cancelados continuam visiveis na agenda.

## Integracao futura com Escalas

Escalas futuras devem possuir FK para `WorshipService`. Elas nao devem duplicar
data/horario como fonte primaria da agenda.

Um `WorshipService` cancelado nao devera receber nova escala. Quando o novo
scheduling existir, o cancelamento devera afetar a elegibilidade operacional das
escalas relacionadas sem apagar historico.

Nada disso foi implementado nesta feature.
