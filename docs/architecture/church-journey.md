# Church Journey Foundation

`Person` representa identidade humana. `Usuario` representa acesso ao Portal.
`ChurchJourney` representa a entrada explicita de uma pessoa na jornada da igreja.

Uma pessoa pode existir sem jornada eclesiastica. Isso preserva cadastros criados
por motivos administrativos, responsaveis de criancas, participantes ocasionais
de eventos e visitantes textuais do Verbo no Lar.

## Entrada Explicita

A jornada e iniciada por um caso de uso explicito:

`start_church_journey(person, started_at=None)`

Se `started_at` nao for informado, a data atual e usada. Essa data significa o
momento em que a igreja passou a considerar a pessoa dentro da jornada
eclesiastica; nao significa necessariamente primeira presenca, primeiro evento
ou primeiro contato.

Cada `Person` pode possuir no maximo uma `ChurchJourney`.

## Visitor Derivado

Nesta fundacao, `ChurchJourney` nao persiste um campo de status. Enquanto
`Membership` ainda nao existe, uma `Person` com `ChurchJourney` e interpretada
como `ChurchStatus.VISITOR`.

`Visitor` nao e model separado.

## Prioridade Novo Dominio vs Legado

Os selectors de `church_journey` priorizam o novo dominio:

1. `Person` com `ChurchJourney` retorna `VISITOR`.
2. Sem `ChurchJourney`, usa fallback legado em `Usuario.status_eclesiastico`.
3. Sem `ChurchJourney` e sem `Usuario`, retorna `UNKNOWN`.

Isso permite que membros legados sem `ChurchJourney` continuem aparecendo como
`MEMBER` ate uma migracao futura.

## O Que Nao Inicia Jornada

Os fluxos abaixo nao criam `ChurchJourney` automaticamente:

- aprovacao de `AccessRequest`
- inscricao em evento
- participante textual de Verbo no Lar
- responsavel ou crianca no Infantil
- existencia de `Person`
- existencia de `Usuario`

## Sem Dual Write

Esta etapa nao escreve em campos legados quando cria `ChurchJourney` e nao cria
dados futuros. `Usuario.status_eclesiastico`, `Usuario.discipulado_concluido` e
`Usuario.qualificar_como_membro(...)` permanecem como fluxo legado.

## Futuro

Features futuras poderao adicionar `Discipleship` e `Membership`. A intencao e
manter consumidores consultando selectors de `church_journey`, trocando a fonte
interna sem espalhar regras pelos modulos.
