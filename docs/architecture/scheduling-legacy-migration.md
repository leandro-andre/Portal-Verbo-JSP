# Scheduling Legacy Migration Plan

Analise PVV-036 realizada em 2026-08-24.

Esta pagina documenta o estado operacional do legado de escalas e o plano de
migracao gradual para o novo dominio `scheduling`. A PVV-036 e somente uma
analise: nao altera models, migrations, rotas, templates, dashboards, dados ou
regras de dominio.

## Escopo

O legado analisado e formado por:

- `escalas.CultoPadrao`
- `escalas.Escala`
- `escalas.EscalaItem`
- `escalas.IndisponibilidadeMembro`
- `departamentos.DepartamentoMembro`

O novo dominio operacional e formado por:

- `worship.WorshipServiceTemplate`
- `worship.WorshipService`
- `scheduling.Schedule`
- `scheduling.ScheduleAssignment`
- `scheduling.DepartmentScheduleRequirement`
- `departamentos.DepartmentMembership`
- `availability.PersonUnavailability`
- `pessoas.Person`

## Inventario Do Legado

| Modelo legado | Papel atual | Principais vinculos | Tabela | Observacoes |
| --- | --- | --- | --- | --- |
| `CultoPadrao` | Modelo antigo de culto recorrente usado pela geracao mensal de `Escala`. | Nao aponta para `WorshipServiceTemplate`. | `departamentos_cultopadrao` | Possui `nome`, `dia_semana`, `horario`, `ativo` e unicidade condicional para template ativo por dia/horario. |
| `Escala` | Escala antiga por departamento, data e horario. | `Departamento`; opcionalmente `CultoPadrao`. | `departamentos_escala` | Duplica `data` e `horario`; a nova fonte deve ser `WorshipService`. |
| `EscalaItem` | Pessoa alocada na escala antiga. | `Escala`; `DepartamentoMembro`. | `departamentos_escalaitem` | Possui `funcao` textual e `confirmado`; a nova escala usa `ScheduleAssignment` e `DepartmentMembership`. |
| `IndisponibilidadeMembro` | Indisponibilidade antiga vinculada a usuario. | `Usuario`. | `departamentos_indisponibilidademembro` | O novo dominio usa `PersonUnavailability`, vinculado a `Person`. |
| `DepartamentoMembro` | Vinculo antigo entre usuario e departamento. | `Usuario`; `Departamento`. | modelo em `departamentos` | Ainda e usado por permissoes internas e telas Django antigas. |

## Mapeamento Legado Para Novo Dominio

| Legado | Novo destino | Condicao para migrar | Bloqueios conhecidos |
| --- | --- | --- | --- |
| `CultoPadrao` | `WorshipServiceTemplate` | Mesmo nome/dia/horario e status ativo/inativo equivalente. | Diferencas de semantica entre template antigo de escala e template novo de agenda de cultos. |
| `Escala` | `WorshipService` + `Schedule` | Localizar ou criar culto por data/horario/nome; criar `Schedule` por departamento + culto. | `Escala` antiga nao conhece status de culto, lifecycle novo nem `source_date`. |
| `EscalaItem` | `ScheduleAssignment` | `Escala` migrada, `Usuario.person` existente e `DepartmentMembership` equivalente no departamento. | Usuario sem `Person`; vinculo antigo sem `DepartmentMembership`; `funcao` textual sem `DepartmentRole`. |
| `IndisponibilidadeMembro` | `PersonUnavailability` | `Usuario.person` existente. | Usuario sem `Person`; diferenca de privacidade e escopo por pessoa. |
| `DepartamentoMembro` | `DepartmentMembership` | `Usuario.person` existente e departamento equivalente. | Permissoes antigas ainda dependem diretamente do modelo legado. |

## Diferencas Semanticas

- O legado e centrado em `Usuario`; o novo dominio e centrado em `Person`.
- `Escala` guarda `data` e `horario`; `Schedule` herda data/horario de
  `WorshipService`.
- `CultoPadrao` gera escalas legadas; `WorshipServiceTemplate` gera cultos da
  agenda.
- `EscalaItem.funcao` e texto livre; o novo caminho deve preferir
  `DepartmentRole`.
- `EscalaItem.confirmado` existe no legado; PVV-032 a PVV-035 nao introduziram
  confirmacao operacional em `ScheduleAssignment`.
- O legado aceita fluxo template Django; o novo dominio e consumido por API e
  React.
- A indisponibilidade antiga pertence a usuario; a nova indisponibilidade
  pertence a pessoa e nao deve expor motivo para terceiros.

## Contadores Locais

Leitura local em 2026-08-24:

| Entidade | Total |
| --- | ---: |
| `CultoPadrao` | 3 |
| `Escala` | 15 |
| `EscalaItem` | 1 |
| `DepartamentoMembro` | 3 |
| `IndisponibilidadeMembro` | 0 |
| `WorshipServiceTemplate` | 3 |
| `WorshipService` | 31 |
| `Schedule` | 2 |
| `ScheduleAssignment` | 1 |
| `DepartmentMembership` | 1 |
| `PersonUnavailability` | 2 |

Recortes locais:

- Escalas legadas futuras: 0.
- Escalas legadas futuras ativas: 0.
- Itens legados em escalas futuras ativas: 0.
- `DepartamentoMembro` com usuario sem `Person`: 2.
- `EscalaItem` cujo usuario nao possui `Person`: 1.
- `DepartamentoMembro` sem `DepartmentMembership` equivalente: 1.
- `EscalaItem` sem `DepartmentMembership` equivalente: 0, considerando apenas os
  casos em que existe `Person`.
- Duplicidade futura entre escala legada e `Schedule` novo: 0.

Os dados locais de `Escala` estao concentrados entre 2026-04-26 e 2026-05-31,
todos no passado em relacao a 2026-08-24. Ha exemplos ligados ao departamento
Midia e aos cultos padrao Domingo Manha, Domingo Noite e Super Quinta. Isso
sugere dados historicos ou de teste local, mas nao autoriza exclusao automatica.

## Classificacao Dos Dados

Nao ha evidencia suficiente para classificar os registros locais como
descartaveis. A recomendacao e:

- tratar dados futuros do legado como operacionais ate prova contraria;
- tratar dados passados como historico consultavel ate decisao de produto;
- nao apagar dados de teste sem criterio explicito;
- gerar relatorio de producao antes de qualquer migracao real.

## Dependencias Atuais Do Legado

`usuarios/views.py` ainda importa `DepartamentoMembro` e `EscalaItem`. O
dashboard do usuario monta `minhas_participacoes` a partir de
`DepartamentoMembro` e `minhas_escalas` a partir de `EscalaItem`.

`core/templatetags/core_admin_tags.py` ainda importa `DepartamentoMembro` e
`Escala`. O dashboard admin calcula `membros_em_departamentos`,
`escalas_ativas` e `proximas_escalas` com modelos legados.

`departamentos/urls.py` inclui `escalas.urls` dentro do namespace
`usuarios:departamentos`. As rotas template antigas seguem ativas em:

- `/usuarios/departamentos/escalas/`
- `/usuarios/departamentos/escalas/gerar-mes/`
- `/usuarios/departamentos/escalas/nova/`
- `/usuarios/departamentos/escalas/<id>/editar/`
- `/usuarios/departamentos/escalas/<id>/itens/`
- `/usuarios/departamentos/escalas/cultos-padrao/`
- `/usuarios/departamentos/minhas-indisponibilidades/`

Templates antigos ainda apontam para essas rotas:

- `templates/usuarios/_sidebar.html`
- `templates/usuarios/dashboard.html`
- `templates/departamentos/escalas_lista.html`
- `templates/departamentos/escala_form.html`
- `templates/departamentos/escala_itens.html`
- `templates/departamentos/gerar_escalas_mes.html`
- `templates/departamentos/cultos_padrao_lista.html`
- `templates/departamentos/culto_padrao_form.html`
- `templates/departamentos/minhas_indisponibilidades.html`
- `templates/departamentos/indisponibilidade_form.html`

`templates/admin/index.html` tambem aponta para o admin legado de `Escala`.

## Dependencias De Permissao

As permissoes antigas de departamentos continuam baseadas em
`DepartamentoMembro` e em papeis legados. Isso afeta:

- `departamentos/permissions.py`
- `escalas/permissions.py`
- `usuarios/permissions.py`
- `infantil/permissions.py`
- `governanca/permissions.py`
- `eventos/permissions.py`
- `ministros/permissions.py`

Impactos por area:

- Infantil usa `DepartamentoMembro.Papel.LIDER` para identificar lideranca do
  Departamento Infantil.
- Governanca usa papeis `LIDER` e `VICE_LIDER` de `DepartamentoMembro` para
  permissao contextual em conteudo publico.
- Eventos usa lideranca de `DepartamentoMembro` para gestao contextual.
- Ministros usa departamentos gerenciaveis, que ainda dependem do vinculo
  legado.
- Midia aparece nos dados locais legados de escala; nenhuma dependencia nova de
  Midia deve assumir que os dados antigos ja foram migrados.

Antes de remover `DepartamentoMembro`, essas permissoes precisam ser reescritas
para `DepartmentMembership` e `DepartmentRole` sem quebrar acessos ja
homologados.

## Dashboards E Falha Temporal

Existe risco temporal nos testes e dashboards que dependem de escalas futuras.
Como a data atual da analise e 2026-08-24, dados fixos de maio de 2026 deixam de
ser futuros. O caso conhecido e o teste de dashboard de departamentos que espera
conteudo de uma escala com data fixa no passado.

A correcao recomendada para PVV futura e usar datas relativas a
`timezone.localdate()` ou congelamento explicito de tempo nos testes. Essa
correcao deve ser feita junto com a troca dos dashboards para a nova fonte de
verdade.

## Fonte De Verdade Proposta

| Area | Fonte atual | Fonte alvo | Momento de troca |
| --- | --- | --- | --- |
| Agenda de cultos | `WorshipServiceTemplate`, `WorshipService` | Ja e fonte de verdade | Mantida. |
| Escalas operacionais | `Escala`, `EscalaItem` em telas Django antigas; `Schedule`, `ScheduleAssignment` em React/API | `Schedule`, `ScheduleAssignment` | Apos congelar escrita legada e migrar/arquivar dados futuros. |
| Minhas escalas React | `ScheduleAssignment` | Ja e fonte de verdade nova | Mantida. |
| Dashboard usuario Django | `EscalaItem` | `ScheduleAssignment` ou link para React | PVV-037. |
| Dashboard admin Django | `Escala` | `Schedule` + `WorshipService` | PVV-037. |
| Indisponibilidade | `IndisponibilidadeMembro` em templates antigos; `PersonUnavailability` em React/API | `PersonUnavailability` | Apos migrar usuarios com `Person`. |
| Participacao em departamentos | `DepartamentoMembro` em permissoes antigas; `DepartmentMembership` no novo dominio | `DepartmentMembership` | Somente apos reescrever permissoes consumidoras. |

## Estrategia De Migracao

Nenhuma migracao foi implementada nesta PVV. A estrategia recomendada e:

1. Gerar relatorio de producao com os mesmos contadores e bloqueios locais.
2. Congelar escrita no legado de escalas: esconder ou desabilitar criar, editar,
   gerar e remover em telas antigas, mantendo leitura quando necessario.
3. Resolver identidades: todo `Usuario` relevante em `DepartamentoMembro`,
   `EscalaItem` e `IndisponibilidadeMembro` precisa ter `Person`.
4. Criar ou validar `DepartmentMembership` equivalente para os vinculos
   legados ainda operacionais.
5. Migrar somente dados futuros ou definidos como historico necessario.
6. Criar `WorshipService` alvo para cada `Escala` migrada quando ainda nao
   existir culto equivalente.
7. Criar `Schedule` por `department + worship_service`.
8. Criar `ScheduleAssignment` apenas quando houver `Person`,
   `DepartmentMembership` equivalente e cargo mapeavel.
9. Manter relatorio de rejeicoes para casos sem pessoa, sem vinculo novo ou sem
   culto alvo.
10. Trocar dashboards e navegacao para as fontes novas.
11. Manter legado read-only por uma janela de homologacao.
12. Remover rotas/templates/admin legado apenas quando nao houver dependencia
   funcional, dado operacional pendente ou teste exercitando o caminho antigo.

## Casos Que Exigem Revisao Manual

Usuario sem `Person`:

- Nao migrar automaticamente para `ScheduleAssignment`.
- Nao criar `Person` por inferencia fraca de nome/e-mail.
- Exigir vinculacao manual ou rotina de identidade aprovada.

`DepartamentoMembro` sem `DepartmentMembership`:

- Nao converter `EscalaItem` ate existir vinculo novo.
- Revisar se o vinculo ainda e valido, se a pessoa e membro do departamento e
  qual `DepartmentRole` deve representar a funcao.

`Escala` sem `WorshipService` equivalente:

- Criar culto alvo apenas em migracao controlada e idempotente.
- Preservar data/horario do registro legado.
- Marcar origem em relatorio, nao em campos inexistentes.

`EscalaItem.funcao` sem `DepartmentRole`:

- Mapear por tabela aprovada por departamento.
- Quando nao houver correspondencia segura, migrar para revisao manual.

## Historico

O historico legado nao deve ser apagado como efeito colateral da transicao. Ha
duas alternativas aceitaveis:

- manter telas antigas em modo leitura para consulta historica por tempo
  determinado;
- exportar historico validado e arquivar antes de remover o app legado.

Como `ScheduleAssignment` nao possui confirmacao equivalente a
`EscalaItem.confirmado`, uma migracao historica completa exigiria decisao de
produto sobre preservacao ou descarte desse estado.

## Duplicidade Operacional

Enquanto os dois dominios coexistirem:

- nao deve haver geracao futura simultanea nos dois fluxos;
- o legado deve ser congelado antes da migracao de dados futuros;
- relatorios devem comparar departamento, data e horario;
- o novo dominio deve ser tratado como fonte de verdade para novas escalas apos
  PVV-035.

Na base local nao foram encontradas escalas legadas futuras nem duplicidade
futura com `Schedule`.

## Plano PVV-037+

PVV-037A: congelar escrita legada.

- Remover acoes de criar, editar, gerar, remover e alterar status nas telas
  antigas, ou proteger por feature flag local.
- Manter leitura onde ainda houver dependencia.

PVV-037B: relatorio de migracao.

- Produzir comando read-only para listar dados migraveis, bloqueados e
  duplicados.
- Rodar primeiro em ambiente local e depois em homologacao/producao.

PVV-037C: migracao controlada de dados futuros.

- Implementar comando idempotente.
- Migrar somente registros aprovados.
- Gerar log de rejeicoes.

PVV-037D: dashboards na nova fonte.

- Trocar dashboard do usuario e admin para `Schedule` e
  `ScheduleAssignment`.
- Corrigir testes temporais com datas relativas.

PVV-037E: indisponibilidades antigas.

- Redirecionar navegacao para o fluxo React de `PersonUnavailability`.
- Migrar registros apenas quando houver `Person`.

PVV-037F: permissoes por `DepartmentMembership`.

- Reescrever consumidores de `DepartamentoMembro`.
- Homologar Infantil, Governanca, Eventos, Ministros e Departamentos.

PVV-037G: remocao do legado.

- Remover rotas, templates, admin e modelos legados somente quando todos os
  criterios abaixo forem atendidos.

## Criterios Para Desabilitar Ou Remover Legado

O legado pode ser desabilitado quando:

- nao houver escrita futura necessaria em `Escala`, `EscalaItem`,
  `CultoPadrao` ou `IndisponibilidadeMembro`;
- dashboards nao dependerem mais de `Escala` ou `EscalaItem`;
- sidebar e templates internos apontarem para React/API novos;
- usuarios operacionais relevantes tiverem `Person`;
- vinculos relevantes tiverem `DepartmentMembership`;
- permissao contextual nao depender mais de `DepartamentoMembro`;
- houver decisao formal sobre historico e confirmacao antiga.

O legado pode ser removido quando, alem dos criterios acima:

- nao existirem imports funcionais dos modelos antigos;
- nao existirem URLs ativas para views antigas;
- nao existirem templates referenciando namespaces antigos;
- testes nao dependerem do fluxo antigo;
- migracao ou arquivamento de dados tiver sido homologado;
- backup e rollback estiverem definidos.

## Resultado Da PVV-036

Esta PVV produziu somente documentacao de arquitetura e plano operacional.
Nenhum model foi alterado, nenhuma migration foi criada, nenhuma rota foi
removida, nenhum template foi alterado e nenhum dado legado foi apagado ou
migrado.

## PVV-037 - Freeze Implementado

A PVV-037 iniciou a primeira fase de corte operacional. A partir desta fase,
novas escalas devem ser criadas somente no dominio novo:

`WorshipService -> Schedule -> ScheduleAssignment -> DepartmentMembership -> Person`

Fonte oficial apos o freeze:

- agenda oficial: `WorshipService`
- escalas novas: `Schedule`
- pessoas escaladas: `ScheduleAssignment`
- vinculo departamental: `DepartmentMembership`
- disponibilidade: `PersonUnavailability`

Rotas legadas congeladas para escrita:

- `usuarios:departamentos:escala_nova`
- `usuarios:departamentos:escala_editar`
- `usuarios:departamentos:escala_gerar_mes`
- `usuarios:departamentos:escala_itens` via `POST`
- `usuarios:departamentos:escala_item_remover`
- `usuarios:departamentos:culto_padrao_novo`
- `usuarios:departamentos:culto_padrao_editar`
- `usuarios:departamentos:culto_padrao_status`
- `usuarios:departamentos:indisponibilidade_nova`
- `usuarios:departamentos:indisponibilidade_editar`
- `usuarios:departamentos:indisponibilidade_cancelar`

Comportamento adotado:

- `GET` em rotas antigas de gestao mostra orientacao de transicao e link para
  `/escalas`.
- `POST` em rotas antigas de escrita retorna `403` com
  `LEGACY_SCHEDULING_READ_ONLY`.
- listagem antiga de escalas continua consultavel em modo historico.
- detalhe antigo de itens de escala continua consultavel em modo historico, sem
  formulario de adicionar/editar/remover pessoas.
- listagem antiga de `CultoPadrao` continua consultavel, sem acoes de criar,
  editar, inativar ou reativar.
- listagem antiga de `IndisponibilidadeMembro` continua consultavel, sem acoes
  de criar, editar ou cancelar.

Navegacao:

- o item operacional "Escalas" da sidebar interna aponta para `/escalas`.
- o item "Minhas indisponibilidades" aponta para `/minhas-indisponibilidades`.
- telas legadas preservadas exibem linguagem de historico legado.

Django Admin:

- `Escala`, `EscalaItem`, `CultoPadrao` e `IndisponibilidadeMembro` ficaram
  read-only no Admin.
- superuser ainda pode consultar listas/detalhes pelo Admin.
- add/change/delete foram bloqueados para esses modelos legados.
- `DepartamentoMembro` nao foi congelado nesta fase, pois ainda sustenta
  permissoes e gestao de outros modulos.

Relatorio read-only:

- foi criado o comando `python manage.py legacy_scheduling_report`.
- o comando nao altera banco.
- a saida inclui contagens legadas, escalas futuras, dados passados,
  `DepartamentoMembro` sem `Person`, vinculos sem `DepartmentMembership` novo,
  possiveis duplicidades com `Schedule`, match com `WorshipService` e match
  `Usuario -> Person -> DepartmentMembership`.

Resultado local do relatorio em 2026-08-24:

- `CultosPadrao` legado: 3.
- `Escalas` legado totais: 15.
- Escalas futuras: 0.
- Escalas passadas: 15.
- `EscalaItem`: 1.
- `IndisponibilidadeMembro`: 0.
- `DepartamentoMembro` sem `Person`: 2.
- vinculos sem `DepartmentMembership` novo: 1.
- duplicidades futuras com Scheduling novo: 0.
- matches futuros com `WorshipService`: nenhum item futuro a avaliar.

Excecoes e proximos passos:

- dashboards Django ainda podem ler dados legados temporariamente.
- permissoes antigas baseadas em `DepartamentoMembro` permanecem para nao
  quebrar Infantil, Governanca, Eventos, Ministros e Departamentos.
- PVV-038 deve usar o relatorio para decidir migracao ou arquivamento de dados
  futuros em ambiente real.

Nenhuma migracao de dados, backfill, dual-write, remocao de model ou remocao de
tabela foi executada na PVV-037.

## PVV-038 - Dashboard Cutover Implementado

A PVV-038 migrou leituras operacionais de dashboards para o novo dominio de
Scheduling. O principio adotado e:

- atual/futuro operacional usa `WorshipService`, `Schedule` e
  `ScheduleAssignment`;
- historico legado continua preservado em telas legadas read-only;
- vazio no novo dominio significa vazio operacional, sem fallback para
  `Escala`/`EscalaItem`.

Consumers migrados:

- `usuarios.views.DashboardView`: deixou de consultar `EscalaItem` para
  proximas escalas pessoais. Agora usa `get_upcoming_assignments_for_person`,
  que retorna apenas `ScheduleAssignment` de `Schedule.PUBLISHED`,
  `WorshipService.SCHEDULED` e data maior ou igual a `timezone.localdate()`.
- `usuarios.views.DashboardView`: deixou de montar "Meus departamentos" por
  `DepartamentoMembro`; agora usa `DepartmentMembership.ACTIVE` quando o usuario
  possui `Person`.
- `core.templatetags.core_admin_tags.get_dashboard_stats`: deixou de contar
  `Escala` legado para escalas ativas e proximas escalas. Agora usa
  `get_operational_schedule_dashboard_counts` e
  `get_upcoming_published_schedules`.
- `templates/usuarios/dashboard.html`: renderiza os dados de
  `ScheduleAssignment -> Schedule -> WorshipService` e aponta "Ver todas" para
  `/minhas-escalas`.
- `templates/admin/index.html`: card e painel de escalas apontam para
  `scheduling.Schedule`/`/escalas`, nao para `escalas.Escala`.

Selectors novos/reutilizados:

- `get_person_schedule_assignments`: selector da PVV-035 reutilizado para
  Minhas Escalas.
- `get_upcoming_assignments_for_person`: alias operacional para dashboard
  pessoal.
- `get_upcoming_published_schedules`: schedules publicados, cultos agendados e
  data futura/atual.
- `get_next_published_schedule_for_department`: proxima escala oficial por
  departamento.
- `get_operational_schedule_dashboard_counts`: contadores separados de
  publicadas futuras, rascunhos futuros e pessoas escaladas.

Sem `Person`:

- dashboard pessoal mostra estado neutro;
- nao busca por username, e-mail ou `DepartamentoMembro`;
- nao consulta `EscalaItem` legado como fallback.

Status no dashboard operacional:

- `DRAFT`: nao aparece como escala oficial/proxima escala pessoal; pode aparecer
  apenas em contador administrativo separado.
- `PUBLISHED`: fonte oficial de proximas escalas e compromissos ativos.
- `Schedule.CANCELLED`: nao aparece como compromisso ativo.
- `WorshipService.CANCELLED`: nao aparece como compromisso ativo, mesmo que a
  `Schedule` esteja publicada.

Referencias legadas restantes apos o cutover:

| Categoria | Referencias | Classificacao |
| --- | --- | --- |
| App `escalas` | models, forms, services, views, admin e comando de relatorio | LEGADO READ-ONLY / HISTORICO |
| Templates `templates/departamentos/*` de escalas antigas | listagem, detalhe, cultos padrao e indisponibilidades | LEGITIMO HISTORICO |
| `departamentos/tests.py`, `core/tests.py`, `escalas/tests.py` | fixtures e provas de que legado futuro e ignorado | TESTE |
| migrations antigas | snapshots historicos do schema | MIGRATION |
| docs de arquitetura | inventario e historico de decisao | DOCUMENTACAO |
| `templates/admin/index.html` | usa apenas admin do novo `scheduling.Schedule` para operacao | CUTOVER CONCLUIDO |

Bloqueadores restantes:

- permissoes antigas de outros modulos ainda podem depender de
  `DepartamentoMembro`; isso nao e parte do cutover de dashboards.
- telas historicas legadas continuam existindo propositalmente em modo
  read-only.
- dados passados legados continuam preservados ate decisao de arquivamento ou
  remocao futura.

Proximo passo recomendado:

- PVV-039 ou PVV-038B: limpar documentacao antiga de area do usuario, revisar
  permissoes legadas por modulo e preparar estrategia de arquivamento/remocao
  depois que nao houver consumers reais.

Nenhuma migracao de dados, backfill, dual-write, remocao de model ou remocao de
tabela foi executada na PVV-038.
