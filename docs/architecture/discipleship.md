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

## Enrollment

`DiscipleshipEnrollment` representa a matricula de uma `Person` em uma
`DiscipleshipClass`.

Campos:

- `person`
- `discipleship_class`
- `status`
- `enrolled_at`
- `withdrawn_at`
- `created_at`
- `updated_at`

Somente `Person` com `ChurchJourney` real no novo dominio pode ser matriculada.
O fallback legado de `Usuario.status_eclesiastico` nao e suficiente para criar
matricula. Se a pessoa ainda nao possui jornada, o fluxo administrativo deve
iniciar a jornada explicitamente antes da matricula.

## Lifecycle Da Matricula

Estados:

- `ENROLLED`
- `WITHDRAWN`

`ENROLLED` significa pessoa atualmente matriculada na turma.

`WITHDRAWN` significa desistencia, preservando historico. A desistencia preenche
`withdrawn_at`, nao remove a matricula e nao altera `Person`, `ChurchJourney`,
`Usuario` ou a turma.

Nao existe `COMPLETED` na matricula nesta etapa. Conclusao individual sera
tratada em feature futura, depois de encontros e presenca.

## Regras De Matricula

Uma pessoa pode ser matriculada em turmas `PLANNED` ou `IN_PROGRESS`.

Turmas `COMPLETED` e `CANCELLED` nao aceitam novas matriculas.

A combinacao `person + discipleship_class` e unica. A mesma pessoa nao pode ter
duas matriculas na mesma turma, mesmo se uma delas estiver `WITHDRAWN`.

A mesma pessoa pode participar novamente do discipulado em outra turma futura.

Nao ha limite maximo de alunos nesta versao. Contadores de alunos sao derivados
das matriculas, nunca persistidos na turma.

## Permissoes De Matricula

Administrador do Portal e Secretaria podem visualizar, criar e marcar
desistencia.

Pastor pode visualizar.

Professor nao ganha permissao automaticamente por ser professor da turma. Essa
regra depende de autorizacao contextual futura do Departamento de Discipulado.

## Ausencias Intencionais

Matricula nao cria `ChurchJourney` automaticamente, nao altera `ChurchStatus`,
nao cria `Usuario` e nao escreve em `Usuario.discipulado_concluido` ou
`Usuario.discipulado_concluido_em`.

Esta feature tambem nao cria aulas reais, presenca, frequencia percentual,
completion individual, elegibilidade para Membership ou Membership.

## Lessons

`DiscipleshipLesson` representa uma Aula real dentro de uma
`DiscipleshipClass`.

A nomenclatura tecnica usa `DiscipleshipLesson`; na interface em portugues a
linguagem de negocio e "Aula" ou "Aulas", evitando "Session".

Campos:

- `discipleship_class`
- `title`
- `lesson_date`
- `status`
- `created_at`
- `updated_at`

Cada aula possui titulo e data. O titulo e obrigatorio, recebe normalizacao
simples com `strip` e nao pode conter apenas espacos.

## Unicidade De Aulas

Dentro da mesma turma, so pode existir uma aula por `lesson_date`.

A regra e protegida por servico de dominio e pela constraint de banco
`unique_discipleship_class_lesson_date`.

Essa unicidade tambem vale para aulas `CANCELLED`. Aula cancelada permanece no
historico e continua ocupando a data na turma. Turmas diferentes podem ter aula
na mesma data.

## Planned Sessions Como Previsao

`planned_sessions` continua sendo apenas previsao administrativa.

A quantidade real de aulas pode ser menor, igual ou maior que a previsao. Criar
uma aula nao altera `planned_sessions` e nao e bloqueado quando a quantidade
cadastrada ultrapassa esse valor.

## Lifecycle Da Aula

Estados:

- `SCHEDULED`
- `CANCELLED`

`SCHEDULED` significa aula valida/agendada.

`CANCELLED` significa aula cancelada e preservada para historico.

Nao existem `COMPLETED`, `HELD` ou `FINISHED` nesta etapa.

## Gerenciamento De Aulas

Aulas podem ser criadas e editadas somente em turmas `PLANNED` ou
`IN_PROGRESS`.

Turmas `COMPLETED` e `CANCELLED` preservam o historico e nao aceitam criacao ou
edicao de aulas nesta versao.

A edicao permite apenas `title` e `lesson_date`. Alterar a data valida
novamente a unicidade por turma/data, mas preserva a identidade da aula. Isso e
importante para a futura modelagem de presenca, que devera apontar para
`DiscipleshipLesson.id` em vez de apontar para uma data.

O cancelamento usa acao explicita `SCHEDULED -> CANCELLED`, sem exclusao fisica
e sem motivo de cancelamento nesta feature. Uma segunda tentativa de
cancelamento retorna erro de transicao invalida.

Nao ha reativacao `CANCELLED -> SCHEDULED` nesta etapa.

## Frequencia Futura

Quando Attendance for implementada, a presenca devera relacionar:

- `DiscipleshipLesson`
- `DiscipleshipEnrollment`

Exemplo futuro: Maria, Aula 1, `PRESENT`; Maria, Aula 2, `ABSENT`.

Aula `CANCELLED` nao devera entrar no denominador de frequencia futura. Esse
calculo ainda nao existe nesta feature.

## Permissoes De Aula

Administrador do Portal e Secretaria podem visualizar, criar, editar e cancelar
aulas.

Pastor pode visualizar.

Usuario comum nao possui acesso administrativo.

Professor nao ganha permissao automaticamente por ser professor da turma. Essa
autorizacao contextual fica para evolucao futura.

Capabilities:

- `DISCIPLESHIP_LESSON_VIEW`
- `DISCIPLESHIP_LESSON_CREATE`
- `DISCIPLESHIP_LESSON_CHANGE`
- `DISCIPLESHIP_LESSON_CANCEL`

## Ausencias Intencionais De Aula

Esta feature nao cria presenca, falta, frequencia, conclusao individual,
Completion de Enrollment, Membership, elegibilidade para Membership, professor
por aula, numero persistido da aula, reativacao de aula cancelada, exclusao de
aula ou dual-write em campos legados de `Usuario`.
