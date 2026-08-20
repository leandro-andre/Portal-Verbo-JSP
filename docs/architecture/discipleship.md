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

## Attendance

`DiscipleshipAttendance` representa o lancamento de chamada de uma matricula em
uma aula.

Relacionamentos:

- `DiscipleshipEnrollment`
- `DiscipleshipLesson`
- `recorded_by`, apontando para `Usuario`

`recorded_by` registra o ultimo usuario que criou ou corrigiu o lancamento. O
historico completo de alteracoes nao faz parte desta etapa e podera ser criado
futuramente se houver necessidade de auditoria detalhada.

## Status De Presenca

Estados:

- `PRESENT`
- `ABSENT`
- `JUSTIFIED`

`PRESENT` significa presente.

`ABSENT` significa ausente, registrado explicitamente.

`JUSTIFIED` significa ausencia justificada. Nao significa presenca e nao deve
ser convertida em `PRESENT`.

Nao existe `PENDING` persistido. A ausencia de `DiscipleshipAttendance`
significa "Nao lancado", nao falta automatica.

## Unicidade E Correcao

A combinacao `enrollment + lesson` e unica.

Correcoes atualizam a mesma linha de `DiscipleshipAttendance`; nao sao criadas
linhas duplicadas para representar mudancas entre `PRESENT`, `ABSENT` e
`JUSTIFIED`.

DELETE funcional nao e disponibilizado. Uma chamada registrada deve ser
corrigida, nao apagada.

## Integridade Da Chamada

A matricula e a aula precisam pertencer a mesma `DiscipleshipClass`.

Aula futura nao aceita chamada. A regra usa `timezone.localdate()`; aula na data
local atual aceita chamada, assim como aula passada.

Aula `CANCELLED` nao aceita chamada e tambem sera retirada do denominador da
frequencia futura.

## Janela Da Matricula

Uma matricula e elegivel para uma aula quando:

- `lesson.lesson_date >= enrollment.enrolled_at`
- se `withdrawn_at` existir, `lesson.lesson_date <= enrollment.withdrawn_at`
- a aula nao esta cancelada
- a aula nao e futura para fins de lancamento

Alunos matriculados depois da aula nao aparecem como faltas pendentes naquela
aula. Alunos desistentes nao recebem faltas posteriores a `withdrawn_at`.

Na data exata de `enrolled_at` ou `withdrawn_at`, a matricula ainda e elegivel.

## Chamada Parcial

A chamada pode ser salva parcialmente. Se a aula possui 12 alunos elegiveis e o
usuario envia 8 registros, apenas esses 8 sao criados ou corrigidos; os demais
continuam como "Nao lancado".

Quando a API recebe um lote com algum registro invalido, o lote inteiro falha
em transacao atomica. Isso evita persistir metade de um lote enviado com erro.

## Autorizacao Contextual

Administrador do Portal e Secretaria podem visualizar e gerenciar chamadas por
permissoes globais.

Pastor pode visualizar.

Professor pode visualizar e gerenciar somente a propria turma, quando
`request.user.person == discipleship_class.teacher`.

O dominio de Departamentos possui papel de auxiliar por departamento, mas nao
identifica auxiliar de uma turma especifica de discipulado. Por isso a PVV-020
cria `DiscipleshipClassAssistant`, um vinculo minimo entre turma e `Person`.
Auxiliar so gerencia chamada quando estiver vinculado aquela turma.

Usuario comum, professor de outra turma e auxiliar nao relacionado nao possuem
acesso.

Capabilities globais:

- `DISCIPLESHIP_ATTENDANCE_VIEW`
- `DISCIPLESHIP_ATTENDANCE_MANAGE`

O React nao tenta carregar todas as turmas permitidas no `current-user`; o
endpoint de chamada retorna permissoes contextualizadas para a aula.

## Frequencia Futura

PVV-021 devera calcular frequencia usando:

- `PRESENT`: numerador e denominador
- `ABSENT`: denominador
- `JUSTIFIED`: fora do numerador e fora do denominador
- aula `CANCELLED`: fora do denominador
- aulas fora da janela da matricula: fora do denominador
- ausencia de `DiscipleshipAttendance`: tratar como chamada nao lancada, nao
  automaticamente como `ABSENT`

Esta feature nao implementa percentual de frequencia, criterio de conclusao,
Completion, elegibilidade para Membership, Membership ou dual-write legado.

## Completion E Eligibility

PVV-021 introduz conclusao individual do discipulado por matricula.

A conclusao minima aprovada pela regra DSC-002 exige frequencia de 75%.

Formula:

`present / (present + absent) * 100`

`PRESENT` entra no numerador e no denominador.

`ABSENT` entra apenas no denominador.

`JUSTIFIED` nao entra no numerador nem no denominador. Justificada e ausencia
aceita, nao presenca.

Aulas `CANCELLED` nao entram no calculo. Aulas fora da janela da matricula
tambem nao entram.

`planned_sessions` nao participa do calculo. A frequencia usa somente
`DiscipleshipLesson` reais, nao canceladas, elegiveis para aquela matricula.

## Janela E Chamada Completa

Uma aula entra na frequencia da matricula quando:

- `lesson.lesson_date >= enrollment.enrolled_at`
- se `withdrawn_at` existir, `lesson.lesson_date <= enrollment.withdrawn_at`
- `lesson.status != CANCELLED`

Ausencia de `DiscipleshipAttendance` nao significa `ABSENT`. Significa chamada
nao lancada.

Se existir aula elegivel sem Attendance, a frequencia pode ser exibida como
parcial, mas a matricula nao pode ser concluida.

Se o denominador for zero, por exemplo todas as aulas elegiveis forem
`JUSTIFIED` ou nao houver aula valida, `frequency_percentage` e nulo e a
matricula nao pode ser concluida. Nunca se assume 100% automaticamente.

## Enrollment Completed

`DiscipleshipEnrollment` passa a aceitar:

- `ENROLLED`
- `WITHDRAWN`
- `COMPLETED`

`COMPLETED` significa que aquela pessoa concluiu individualmente o discipulado
naquela turma. A conclusao da turma nao conclui automaticamente os alunos.

A conclusao e um caso de uso explicito:

- turma precisa estar `COMPLETED`
- matricula precisa estar `ENROLLED`
- chamadas elegiveis precisam estar completas
- denominador precisa ser valido
- frequencia precisa ser `>= 75%`

Ao concluir:

- `status = COMPLETED`
- `completed_at = timezone.localdate()`

`completed_at` e `DateField` porque a regra pastoral/administrativa atual
trabalha com data de conclusao, nao instante de auditoria detalhada.

Nao ha signal de conclusao. Nao ha conclusao automatica ao fechar turma. Nao ha
revogacao de conclusao nesta feature.

Matricula `WITHDRAWN` nao pode virar `COMPLETED`, mesmo com frequencia historica
alta antes da desistencia.

## Membership Eligibility

Elegibilidade para futura Membership e derivada:

uma `Person` e elegivel quando possui ao menos uma `DiscipleshipEnrollment` com
`status = COMPLETED`.

Nao existe campo persistido de eligibility em `Person` e nao existe tabela
`MembershipEligibility`.

Elegivel para Membership nao significa membro. A pessoa continua com
`ChurchStatus.VISITOR` ate uma futura feature de Membership aprovar e registrar
a membresia.

Nao criar `Membership`, nao promover para `MEMBER`, nao alterar
`Usuario.status_eclesiastico` e nao fazer dual-write em
`Usuario.discipulado_concluido`.

## Compatibility Layer Apos Completion

`has_completed_discipleship(person)` prioriza o novo dominio:

1. existe `DiscipleshipEnrollment.COMPLETED`: `True`
2. caso contrario, usa fallback legado `Usuario.discipulado_concluido`

`get_discipleship_completed_at(person)` segue a mesma prioridade. Quando houver
mais de uma conclusao no novo dominio, retorna a conclusao mais recente.

## Permissoes De Completion

Administrador do Portal e Secretaria podem visualizar frequencia e concluir
matriculas.

Pastor pode visualizar frequencia.

Professor da turma e auxiliar contextual podem visualizar acompanhamento da
propria turma, reutilizando a autorizacao contextual da chamada. Eles nao
concluem formalmente nesta versao.

Capabilities:

- `DISCIPLESHIP_COMPLETION_VIEW`
- `DISCIPLESHIP_COMPLETION_MANAGE`

## Checkpoint Apos PVV-021

Apos PVV-021 o desenvolvimento deve parar para o CHECKPOINT 01 de homologacao
end-to-end:

`Person -> ChurchJourney -> Visitor -> DiscipleshipClass -> Enrollment ->
Lessons -> Attendance -> Completion -> Membership Eligibility`

Membership so deve ser implementada depois dessa homologacao.
