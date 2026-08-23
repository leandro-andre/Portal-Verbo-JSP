# Membership Foundation

Membership representa a relacao formal de uma `Person` com a igreja como membro.
Ela pertence ao dominio de jornada eclesiastica, mas nao substitui `ChurchJourney`
nem depende de `Usuario`.

## Modelo

`Membership` fica no app `church_journey` e possui relacao `OneToOneField` com
`Person`.

Campos iniciais:

- `person`: pessoa membro. Uma pessoa possui no maximo uma Membership.
- `status`: `ACTIVE` ou `INACTIVE`.
- `member_since`: data oficial de membresia.
- `approved_by`: usuario que aprovou tecnicamente a membresia, opcional nesta fundacao.
- `approved_at`: data/hora de aprovacao, opcional nesta fundacao.
- `created_at` e `updated_at`.

`person` usa `CASCADE` porque Membership nao deve sobreviver sem a pessoa. O
portal nao possui exclusao funcional de `Person`; se um registro tecnico de
Membership for removido, a `Person` permanece.

`approved_by` usa `SET_NULL` para preservar a Membership se um usuario tecnico
for removido.

## Regras

Membership depende de `Person`, nao de `Usuario`. Uma pessoa pode ser membro da
igreja sem login no Portal.

Membership nao duplica campos de `ChurchJourney`, como data de entrada na
jornada ou status de visitante. Ela so pode existir para pessoa com
`ChurchJourney` e discipulado concluido.

`member_since` deve ser a data de conclusao do discipulado, nao a data da
aprovacao nem a data de criacao do registro.

Discipulado concluido nao cria Membership automaticamente. Nao ha signal,
dual-write ou backfill.

Pastor nao implica Membership. Role pastoral e membresia sao conceitos separados.

## ChurchStatus

`ChurchStatus` continua derivado, sem persistencia no banco:

- sem `ChurchJourney` e sem `Membership`: `UNKNOWN`
- `ChurchJourney` sem `Membership`: `VISITOR`
- `Membership ACTIVE`: `MEMBER`
- `Membership INACTIVE`: `INACTIVE_MEMBER`

Membership tem prioridade sobre compatibilidade legada de `Usuario`. Membro
inativo nao volta a ser visitante.

## Eligibility

`is_eligible_for_membership(person)` indica elegibilidade de discipulado:
existe enrollment concluido.

`can_create_membership(person)` indica possibilidade de criar Membership:
discipulado concluido e nenhuma Membership existente.

## Aprovacao

A aprovacao de Membership e um caso de uso explicito executado pela Secretaria
ou pelo Administrador do Portal. Pastor visualiza, mas nao aprova nesta versao.

Endpoint:

`POST /api/people/{person_id}/membership/approve/`

O payload nao define `status`, `member_since`, `approved_by` ou `approved_at`.
O backend deriva todos os dados.

Pre-condicoes:

- a pessoa possui `ChurchJourney`;
- a pessoa possui `DiscipleshipEnrollment` com status `COMPLETED`;
- a pessoa ainda nao possui `Membership`.

Somente o novo dominio de discipulado vale para aprovar nova Membership.
Campos legados em `Usuario`, como `discipulado_concluido`, podem existir para
compatibilidade de leitura, mas nao aprovam Membership nova.

Quando ha mais de uma conclusao, `member_since` usa a primeira conclusao valida
por `completed_at` e depois `id`. Isso preserva a data da primeira entrada
possivel como membro.

`approved_by` e o `Usuario` autenticado que executou a aprovacao.
`approved_at` e o momento da aprovacao via `timezone.now()`.

Membership nasce `ACTIVE`, o que faz `ChurchStatus` derivado passar a `MEMBER`.
A aprovacao nao altera `Person.status`, `Usuario`, roles, groups, enrollments,
attendance, lessons ou dados legados.

## Futuro

Lifecycle ACTIVE/INACTIVE, reativacao e historico ficam fora desta etapa.

Departamentos e escalas ainda nao mudam nesta fase. Regra futura: apenas
`Membership ACTIVE` deve permitir novos vinculos departamentais e novas
elegibilidades de escala; historicos existentes devem ser preservados.
