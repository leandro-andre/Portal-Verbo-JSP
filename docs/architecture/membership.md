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
dual-write ou backfill nesta fundacao. A aprovacao explicita pela Secretaria
fica para PVV-024.

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

## Futuro

PVV-024 deve implementar aprovacao da Secretaria como caso de uso explicito.
Lifecycle ACTIVE/INACTIVE, reativacao e historico tambem ficam fora desta
fundacao.

Departamentos e escalas ainda nao mudam nesta fase. Regra futura: apenas
`Membership ACTIVE` deve permitir novos vinculos departamentais e novas
elegibilidades de escala; historicos existentes devem ser preservados.
