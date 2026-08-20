# Discipleship Class

O discipulado passa a ter uma fundacao propria dentro de `church_journey` por
meio de `DiscipleshipClass`.

Nesta etapa, a turma representa apenas o container administrativo do
discipulado. Ela ainda nao possui alunos, encontros/aulas reais, presencas,
conclusao individual ou relacao com Membership.

## Professor

Cada turma possui um unico professor em `teacher`, apontando para `Person`.
Professor e papel de negocio, nao conta de acesso, por isso nao aponta para
`Usuario` e nao e armazenado como texto.

Futuramente, o professor devera ter um vinculo valido com o Departamento de
Discipulado, provavelmente por `DepartmentMembership`. Essa autorizacao
contextual nao faz parte desta feature.

## Campos

- `name`
- `teacher`
- `start_date`
- `expected_end_date`
- `planned_sessions`
- `status`
- `created_at`
- `updated_at`

`planned_sessions` pertence a turma. A quantidade de aulas nao fica hardcoded,
mesmo que hoje as turmas usem a mesma quantidade.

`expected_end_date` pode ser igual a `start_date`, mas nao pode ser anterior.
O termino previsto nao e calculado automaticamente a partir da quantidade de
aulas.

## Lifecycle

Estados:

- `PLANNED`
- `IN_PROGRESS`
- `COMPLETED`
- `CANCELLED`

Transicoes permitidas:

- `PLANNED -> IN_PROGRESS`
- `PLANNED -> CANCELLED`
- `IN_PROGRESS -> COMPLETED`
- `IN_PROGRESS -> CANCELLED`

Turmas `COMPLETED` e `CANCELLED` ficam preservadas para historico e nao sao
editaveis nesta primeira versao.

## Uma Turma Em Andamento

Pode existir no maximo uma turma com status `IN_PROGRESS`.

A regra e protegida por servico de dominio e por constraint parcial de banco:
`unique_discipleship_class_in_progress`.

Essa constraint e compativel com SQLite atual e com PostgreSQL.

## Permissoes

Administrador do Portal e Secretaria podem visualizar, criar, alterar, iniciar,
concluir e cancelar turmas.

Pastor pode visualizar.

Usuario comum nao possui acesso administrativo.

No futuro, o Departamento de Discipulado podera receber permissoes contextuais
sem transformar isso em role global.

## Fora Desta Feature

Esta feature nao cria:

- `DiscipleshipEnrollment`
- alunos
- `DiscipleshipSession`
- presenca
- conclusao individual
- elegibilidade para Membership
- Membership
- vinculo real com Departamento de Discipulado
- dual-write em `Usuario.discipulado_concluido`

Concluir uma turma encerra a turma, mas nao conclui automaticamente o
discipulado dos alunos.
