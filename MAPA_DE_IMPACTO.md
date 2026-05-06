# Mapa de Impacto entre Modulos

| Modulo | Depende de | Impacta | Risco | Observacoes |
| --- | --- | --- | --- | --- |
| `config` | Django, settings/env | Todo o projeto | Alto | Define apps instalados, URLs raiz, banco, auth e seguranca. |
| `core` | Nenhum dominio interno forte | Templates globais, secretaria, governanca | Medio | `SiteConfig` e injetado em todos os templates. |
| `usuarios` | Django auth, departamentos, escalas, eventos, noticias, infantil via dashboard/context | Todos os modulos internos | Alto | `AUTH_USER_MODEL` e permissoes centrais tornam este app estrutural. |
| `usuarios.permissions` | `departamentos`, `ministros` via `apps.get_model` | Departamentos, escalas, Verbo no Lar, financeiro, infantil, governanca | Alto | Centraliza identidade, acesso tecnico/pastoral e funcoes `usuario_tem_acesso_*`; evita misturar identidade com autorizacao. |
| `usuarios.context_processors` | `departamentos`, `eventos`, `infantil`, `ministros`, `verbo_no_lar`, `financeiro` | Sidebar e templates internos | Medio/Alto | Usa cache por request em `request._internal_permissions_cache`; ainda concentra dependencias de navegacao. |
| `governanca` | `core`, `departamentos`, `eventos`, `noticias`, `usuarios` | Admin, secretaria, midia, conteudo publico | Alto | Define permissoes editoriais consumindo identidade/acesso separados de `usuarios.permissions`. |
| `conteudo_interno` | `core`, `eventos`, `noticias`, `governanca`, `infantil`, `usuarios` | Site publico, agenda, noticias, midia | Alto | Painel interno altera conteudos de outros apps. |
| `departamentos` | `usuarios` | Escalas, governanca, eventos, infantil, ministros, sidebar | Alto | `DepartamentoMembro` e fonte de lideranca/papeis; `is_staff` nao define negocio. |
| `departamentos.permissions` | `usuarios.permissions`, `DepartamentoMembro` | Departamentos, escalas, eventos, ministros, sidebar | Alto | Centraliza acesso ao modulo, gestao de membros e gestao de escalas por departamento. |
| `escalas` | `departamentos`, `usuarios` | Dashboard, departamentos, rotina de servico | Alto | Escala depende de vinculo ativo, papel departamental, conflitos e indisponibilidades. |
| `eventos` | `usuarios`, `departamentos`, `governanca` | Site publico, secretaria, check-in | Medio | QR/check-in usa tokens e permissoes de equipe. |
| `noticias` | Poucas dependencias diretas | Site publico, secretaria, governanca | Baixo | Dominio simples, gerenciado por painel interno. |
| `infantil` | `usuarios`, `departamentos`, `governanca` | Midia, secretaria, responsaveis, dashboard | Alto | Tem dados sensiveis de criancas e fluxo operacional em tempo real. |
| `ministros` | `usuarios`, `departamentos`, `governanca` | Verbo no Lar, financeiro de ministros | Medio | Cadastro ministerial pode existir com ou sem usuario vinculado. |
| `verbo_no_lar` | `usuarios`, `ministros`, `governanca` | Relatorios, materiais, escalas ministeriais | Alto | Escalas e relatorios dependem de ministro e casa. |
| `financeiro` | `usuarios`, `governanca`, Mercado Pago externo | Contribuicoes, integracao externa, dados financeiros | Alto | Webhook publico, tokens sensiveis e status financeiro. |
| `templates/base.html` | `core.site_config`, `usuarios.context_processors` | Todas as telas | Medio | Qualquer erro de contexto pode afetar renderizacao geral. |
| `static/css/styles.css` | Templates | Experiencia de todo o sistema | Medio | Estilo compartilhado; mudancas podem impactar todos os modulos. |
| `admin` customizado | `core`, `governanca`, apps de dominio | Operacao tecnica/admin | Medio | Mistura acesso tecnico Django com regras editoriais em alguns pontos. |

## Impactos por model central

| Model | Depende de | Impacta | Risco | Observacoes |
| --- | --- | --- | --- | --- |
| `Usuario` | Django auth | Todos os apps | Alto | Alteracoes exigem cuidado com migrations e fixtures. |
| `Departamento` | `usuarios` via M2M through | Governanca, escalas, infantil | Alto | Codigos reservados definem Secretaria/Midia/Infantil. |
| `DepartamentoMembro` | `Usuario`, `Departamento` | Permissoes, escalas, eventos, infantil | Alto | Mudanca em papeis quebra regras e testes. |
| `Escala` | `Departamento`, `CultoPadrao` | Dashboard, gestao de escalas | Medio | Validacoes por data/horario/departamento. |
| `EscalaItem` | `Escala`, `DepartamentoMembro` | Dashboard, conflito de agenda | Alto | Bloqueia conflito e indisponibilidade. |
| `IndisponibilidadeMembro` | `Usuario` | Escalas | Medio | Afeta montagem de escala. |
| `Evento` | Nenhum forte | Agenda, inscricoes, secretaria | Medio | Conteudo publico e capacidade. |
| `InscricaoEvento` | `Evento`, `Usuario` | Check-in, minhas inscricoes | Medio | Tokens/QR exigem rastreabilidade. |
| `SalaInfantil` | Nenhum forte | Infantil | Medio | Unidade operacional do departamento infantil. |
| `SalaMembro` | `SalaInfantil`, `Usuario` | Permissoes infantis | Alto | Lideranca/professor/auxiliar da sala. |
| `Crianca` | `Usuario`, `SalaInfantil` | Responsavel, secretaria, infantil | Alto | Dados sensiveis. |
| `ChamadaResponsavel` | `SalaInfantil`, `Crianca` | Midia, sala infantil | Alto | Fluxo operacional em tempo real. |
| `Ministro` | `Usuario` opcional | Verbo no Lar, ministros | Medio | Pode representar ministro externo ou da casa. |
| `CasaVerboNoLar` | `Usuario` | Participantes, escalas, relatorios | Alto | Responsavel/anfitriao definem acesso operacional. |
| `EscalaVerboNoLar` | `CasaVerboNoLar`, `Ministro` | Materiais/relatorios ministeriais | Medio | Fonte da agenda ministerial do modulo. |
| `RelatorioEncontroVerboNoLar` | `CasaVerboNoLar`, `Ministro`, `Usuario` | Relatorios | Medio | Dados operacionais e historicos. |
| `ConfiguracaoFinanceira` | Nenhum forte | Mercado Pago, financeiro | Alto | Armazena credenciais e estado da integracao. |
| `Contribuicao` | `Usuario` opcional | Financeiro, Mercado Pago | Alto | Status depende de webhook/consulta externa. |
| `SiteConfig` | Nenhum forte | Todos os templates | Medio | Registro unico usado globalmente. |
| `ConteudoAuditLog` | `ContentType`, `Usuario` | Governanca | Baixo | Auditoria editorial. |

## Relacoes criticas

```text
Usuario
  -> DepartamentoMembro
  -> SalaMembro
  -> Crianca.responsavel_usuario
  -> Ministro.usuario
  -> CasaVerboNoLar responsavel/anfitriao
  -> Contribuicao.usuario
  -> InscricaoEvento.usuario

DepartamentoMembro
  -> EscalaItem
  -> permissoes de lideranca
  -> Secretaria/Midia via departamentos reservados

usuarios.permissions
  -> identidade: visitante, membro, secretaria, midia, lider, ministro, pastor
  -> acesso: secretaria, midia, pastoral, tecnico total
  -> regras transversais de escala e acesso amplo

departamentos.permissions
  -> pertence ao departamento
  -> gerencia membros
  -> gerencia escalas
  -> acesso ao modulo de departamentos

Ministro
  -> EscalaVerboNoLar
  -> RelatorioEncontroVerboNoLar

ChamadaResponsavel
  -> conteudo_interno/midia

ConfiguracaoFinanceira
  -> Mercado Pago API
  -> Webhook publico
```

## Riscos por nivel

Alto:

- Mudancas em `Usuario`, `DepartamentoMembro`, permissoes e financeiro.
- Webhooks financeiros sem logging estruturado.
- Dados infantis e chamadas de responsavel.
- Context processor de permissoes segue acoplado a varios dominios, embora tenha cache por request.

Medio:

- Acoplamento entre `conteudo_interno` e apps de conteudo.
- Verbo no Lar depender de ministro.
- Imports legados de `departamentos` para `escalas`.
- Fixtures antigas com nomes historicos como `staff` podem confundir leitura, mesmo quando a regra atual usa pastor/superuser/acesso departamental.

Baixo:

- Noticias publicas.
- Templates estaticos de conteudo simples.
- Admins basicos.

## Observacoes de manutencao

- Antes de alterar `DepartamentoMembro.Papel`, revisar `governanca`, `eventos`, `infantil`, `escalas`, `ministros`, sidebar e testes.
- Antes de alterar `Usuario`, revisar todas as FKs para `AUTH_USER_MODEL`.
- Antes de alterar `usuarios.permissions`, revisar `governanca.permissions`, `departamentos.permissions`, `escalas.permissions`, financeiro, ministros, Verbo no Lar e context processor.
- Antes de alterar `usuarios.context_processors`, revisar sidebar, templates internos e custo de queries por request.
- Antes de alterar `Ministro`, revisar `verbo_no_lar`.
- Antes de alterar `SiteConfig`, revisar templates globais e `conteudo_interno`.
- Antes de alterar `financeiro`, revisar o ciclo completo Mercado Pago: preferencia, retorno, webhook e consulta.
