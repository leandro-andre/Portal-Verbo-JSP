# Availability / Indisponibilidades

`PersonUnavailability` representa um periodo em que uma `Person` nao esta
disponivel para servir. A indisponibilidade pertence a pessoa, nao a `Usuario`,
`Departamento` ou `DepartmentMembership`.

## Local Do Dominio

O model fica no app `pessoas`, porque indisponibilidade e um fato operacional da
`Person`. O app legado `escalas` continua com `IndisponibilidadeMembro` para as
telas e regras antigas ate a futura migracao de Scheduling.

## Campos

- `person`: FK obrigatoria para `Person`.
- `start_date`: data inicial obrigatoria.
- `end_date`: data final obrigatoria.
- `start_time`: hora inicial opcional.
- `end_time`: hora final opcional.
- `reason`: motivo opcional.
- `status`: `ACTIVE` ou `INACTIVE`.
- `created_at` e `updated_at`.

Nao existe campo de departamento. Uma indisponibilidade ativa vale globalmente
para todos os departamentos em que a pessoa servir.

## Datas E Horarios

Regras atuais:

- `end_date >= start_date`.
- Se um horario for informado, o outro tambem deve ser informado.
- Faixa horaria so e permitida quando `start_date == end_date`.
- Em faixa horaria de um dia, `end_time > start_time`.
- Periodos de varios dias representam dias inteiros.

Exemplos validos:

- `10/09/2026` ate `15/09/2026`, sem horario.
- `10/09/2026`, `18:00` ate `22:00`.

Exemplo invalido nesta versao:

- `10/09/2026` ate `15/09/2026`, `18:00` ate `22:00`.

Nao ha recorrencia semanal, calendario externo ou regra implicita por horario
em multiplos dias.

## Sobreposicao

Sobreposicoes entre indisponibilidades `ACTIVE` da mesma pessoa sao bloqueadas.

- Periodo integral conflita com outro periodo que toque as mesmas datas.
- Dia inteiro conflita com qualquer faixa horaria no mesmo dia.
- Faixas horarias no mesmo dia conflitam apenas quando se intersectam.
- Faixas adjacentes, como `18:00-20:00` e `20:00-22:00`, sao permitidas.
- Indisponibilidades `INACTIVE` nao bloqueiam nova criacao.
- Indisponibilidades de outra `Person` nao conflitam.

## Lifecycle

Nao existe DELETE funcional. O historico e preservado via lifecycle:

- `ACTIVE -> INACTIVE`
- `INACTIVE -> ACTIVE`

Indisponibilidade `INACTIVE` e ignorada por selectors operacionais. Periodos
passados nao sao inativados automaticamente; nao ha cron job.

## Selectors

Selectors principais em `pessoas.availability`:

- `get_person_unavailability_conflicts(person, date, time=None)`
- `get_person_availability(person, date, time=None)`
- `is_person_available(person, date, time=None)`

Consulta sem horario responde se existe qualquer indisponibilidade ativa no dia,
mesmo parcial. Consulta com horario diferencia faixas parciais. Se uma futura
Escala nao tiver horario, deve usar a consulta conservadora sem horario.

## APIs

Self-service:

- `GET /api/people/me/unavailability/`
- `POST /api/people/me/unavailability/`
- `GET /api/people/me/unavailability/{id}/`
- `PATCH /api/people/me/unavailability/{id}/`
- `POST /api/people/me/unavailability/{id}/deactivate/`
- `POST /api/people/me/unavailability/{id}/reactivate/`

Administrativo:

- `GET /api/people/{person_id}/unavailability/`
- `POST /api/people/{person_id}/unavailability/`
- `GET /api/people/{person_id}/unavailability/{id}/`
- `PATCH /api/people/{person_id}/unavailability/{id}/`
- `POST /api/people/{person_id}/unavailability/{id}/deactivate/`
- `POST /api/people/{person_id}/unavailability/{id}/reactivate/`

## Autorizacao E Privacidade

Self-service exige `request.user.person` e opera apenas sobre a propria pessoa.

Administrador do Portal e Secretaria possuem gestao global. Pastor possui
visualizacao global. Usuario comum sem permissao global nao administra outras
pessoas.

`reason` pode conter informacao pessoal. Nesta feature, ele aparece para a
propria pessoa e para leitura administrativa autorizada. Nao foi criado endpoint
operacional para lider contextual; quando esse endpoint existir, deve retornar
apenas disponibilidade/datas/horarios, sem `reason`.

## Coexistencia Legada

`IndisponibilidadeMembro` continua intacta, ligada a `Usuario`, para o fluxo
legado. Nao ha dual-write, backfill ou data migration. O diagnostico local
indicou ausencia de dados legados a migrar, e a migracao futura deve ser tratada
junto da nova feature de Scheduling.

Escalas, `EscalaItem`, confirmacao de escala e indisponibilidade por
departamento nao foram implementadas nesta etapa.
