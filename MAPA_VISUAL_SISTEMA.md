# Mapa Visual do Sistema - Portal Verbo JSP

Este documento complementa `ARQUITETURA.md`, `MAPA_DE_IMPACTO.md` e `FLUXOS.md` com diagramas Mermaid e uma leitura visual dos principais modulos, dependencias e riscos de impacto do sistema.

## Visao Macro do Sistema

```mermaid
flowchart TB
    visitante[Visitante / Publico] --> site[Site Publico]
    membro[Membro / Usuario logado] --> area[Area Interna]
    equipe[Equipe interna] --> area
    pastor[Pastor] --> area
    superuser[Superuser tecnico] --> admin[Django Admin]

    site --> core[core<br/>Home, Sobre, Contato, Ao vivo]
    site --> eventos_pub[eventos<br/>Agenda e inscricoes]
    site --> noticias[noticias<br/>Noticias]
    site --> ministros_pub[ministros<br/>Formulario externo]

    area --> usuarios[usuarios<br/>Login, perfil, dashboard]
    area --> conteudo[conteudo_interno<br/>Secretaria e Midia]
    area --> departamentos[departamentos<br/>Departamentos e membros]
    area --> escalas[escalas<br/>Cultos, escalas, indisponibilidades]
    area --> infantil[infantil<br/>Salas, criancas, chamadas]
    area --> verbo[verbo_no_lar<br/>Casas, escalas, relatorios]
    area --> ministros[ministros<br/>Gestao ministerial]
    area --> financeiro[financeiro<br/>Contribuicoes e Mercado Pago]

    usuarios --> permissoes[Permissoes globais<br/>usuarios.permissions]
    usuarios --> sidebar[Context processor<br/>cache por request]
    permissoes --> governanca[governanca<br/>Regras editoriais e auditoria]
    permissoes --> dep_perms[departamentos.permissions<br/>Acesso por departamento]
    dep_perms --> departamentos
    dep_perms --> escalas
    permissoes --> infantil
    permissoes --> verbo
    permissoes --> financeiro
    sidebar --> departamentos
    sidebar --> infantil
    sidebar --> financeiro

    conteudo --> core
    conteudo --> eventos_pub
    conteudo --> noticias
    conteudo --> infantil

    departamentos --> escalas
    departamentos --> governanca
    departamentos --> infantil
    departamentos --> eventos_pub
    departamentos --> ministros

    ministros --> verbo
    financeiro --> mp[Mercado Pago]
    mp --> webhook[Webhook publico]
    webhook --> financeiro
```

## Dependencia entre Modulos

```mermaid
flowchart LR
    config[config] --> core
    config --> usuarios
    config --> departamentos
    config --> escalas
    config --> eventos
    config --> noticias
    config --> infantil
    config --> ministros
    config --> verbo_no_lar
    config --> financeiro
    config --> governanca
    config --> conteudo_interno

    core --> templates[templates globais]
    usuarios --> templates

    usuarios --> permissoes_globais[usuarios.permissions]
    usuarios --> context_processor[usuarios.context_processors<br/>_internal_permissions_cache]
    permissoes_globais --> departamentos
    permissoes_globais --> governanca
    permissoes_globais --> financeiro
    permissoes_globais --> ministros
    permissoes_globais --> verbo_no_lar

    context_processor --> departamentos
    context_processor --> eventos
    context_processor --> infantil
    context_processor --> ministros
    context_processor --> verbo_no_lar
    context_processor --> financeiro

    departamentos --> dep_perms[departamentos.permissions]
    dep_perms --> escalas
    usuarios --> escalas
    usuarios --> eventos
    usuarios --> infantil
    usuarios --> ministros
    usuarios --> verbo_no_lar
    usuarios --> financeiro

    departamentos --> escalas
    departamentos --> governanca
    departamentos --> infantil
    departamentos --> eventos
    departamentos --> ministros

    governanca --> core
    governanca --> eventos
    governanca --> noticias
    governanca --> departamentos

    conteudo_interno --> core
    conteudo_interno --> eventos
    conteudo_interno --> noticias
    conteudo_interno --> governanca
    conteudo_interno --> infantil

    ministros --> verbo_no_lar
    financeiro --> mercado_pago[Mercado Pago API]

    classDef high fill:#fee2e2,stroke:#b91c1c,color:#7f1d1d
    classDef medium fill:#fef3c7,stroke:#b45309,color:#78350f
    classDef low fill:#dcfce7,stroke:#15803d,color:#14532d

    class usuarios,departamentos,governanca,financeiro,infantil,escalas high
    class conteudo_interno,verbo_no_lar,ministros,eventos,core medium
    class noticias low
```

## Fluxo de Usuarios e Qualificacoes

```mermaid
stateDiagram-v2
    [*] --> Visitante: cadastro publico
    Visitante --> Membro: Secretaria qualifica apos discipulado
    Membro --> Liderado: vinculo ativo em departamento
    Liderado --> Lider: papel departamental = lider
    Membro --> Ministro: vinculo com Ministro aprovado
    Lider --> Ministro: tambem pode ser ministro
    Ministro --> Pastor: autoridade pastoral marcada no usuario
    Membro --> Pastor: pode ser pastor sem ser ministro
    Pastor --> Superuser: acesso tecnico separado

    note right of Visitante
        Login, perfil, criancas,
        inscricoes e contribuicoes basicas.
    end note

    note right of Membro
        Pode servir em departamentos
        e ser escalado.
    end note

    note right of Lider
        Gerencia pessoas e escalas
        do departamento que lidera.
    end note

    note right of Ministro
        Pode ser escalado no
        Verbo no Lar.
    end note

    note right of Pastor
        Acesso amplo como regra
        de negocio da igreja.
    end note

    note right of Superuser
        Acesso tecnico/admin Django.
    end note
```

## Fluxo de Dizimos e Ofertas

```mermaid
sequenceDiagram
    participant U as Usuario
    participant F as financeiro
    participant MP as Mercado Pago
    participant WH as Webhook
    participant R as Relatorios/Listagem

    U->>F: Acessa Nova Contribuicao
    U->>F: Informa tipo, valor e descricao
    F->>F: Cria Contribuicao pendente
    F->>MP: Cria preferencia de pagamento
    MP-->>F: Retorna preference_id e link
    F-->>U: Redireciona para pagamento
    U->>MP: Conclui pagamento
    MP->>WH: Envia notificacao assinada
    WH->>F: Valida assinatura e extrai payment_id
    F->>MP: Consulta pagamento atualizado
    MP-->>F: Retorna status
    F->>F: Atualiza Contribuicao
    F->>R: Lista/relatorio mostra novo status
```

## Matriz de Impacto

| Modulo | Depende de | Impacta | Nivel de risco | Observacoes |
| --- | --- | --- | --- | --- |
| `usuarios` | Django auth, departamentos, ministros | Todos os apps internos | Alto | Dono de identidade, status, acesso pastoral/tecnico e permissoes transversais. |
| `usuarios.context_processors` | `departamentos`, `eventos`, `infantil`, `ministros`, `verbo_no_lar`, `financeiro` | Sidebar e templates internos | Medio/Alto | Usa cache por request para reduzir recomputacao, mas segue acoplado a muitos dominios. |
| `departamentos` | `usuarios` | Escalas, governanca, infantil, eventos, ministros | Alto | `DepartamentoMembro` define papeis e lideranca; `departamentos.permissions` centraliza gestao por departamento. |
| `governanca` | `core`, `departamentos`, `usuarios`, `eventos`, `noticias` | Secretaria, Midia, admin editorial | Alto | Regras editoriais usam funcoes de identidade/acesso ja separadas em `usuarios.permissions`. |
| `financeiro` | `usuarios`, `governanca`, Mercado Pago | Contribuicoes, relatorios financeiros, integracao externa | Alto | Lida com tokens, webhook publico e status financeiro. |
| `infantil` | `usuarios`, `departamentos`, `governanca` | Midia, responsaveis, dashboard interno | Alto | Dados sensiveis de criancas e fluxo operacional de chamadas. |
| `escalas` | `departamentos`, `usuarios` | Departamentos, dashboard, rotina de servico | Alto | Depende de papeis departamentais, conflitos e indisponibilidades. |
| `conteudo_interno` | `core`, `governanca`, `eventos`, `noticias`, `infantil` | Site publico, Secretaria, Midia | Medio/Alto | Painel administrativo funcional que altera dados de varios dominios. |
| `verbo_no_lar` | `usuarios`, `ministros`, `governanca` | Relatorios, escalas ministeriais, materiais | Medio/Alto | Depende de ministro e responsaveis de casas. |
| `ministros` | `usuarios`, `departamentos`, `governanca` | Verbo no Lar, qualificacao ministerial | Medio | Pode representar ministro externo ou usuario vinculado. |
| `eventos` | `usuarios`, `departamentos`, `governanca` | Agenda, inscricoes, check-in | Medio | QR/check-in e inscricoes publicas/logadas. |
| `core` | Poucas dependencias internas | Todo o site via `SiteConfig` | Medio | Context processor injeta configuracao global em todos os templates. |
| `noticias` | `conteudo_interno`, `governanca` para gestao | Site publico | Baixo/Medio | Dominio simples, mas participa da governanca editorial. |

## Modulos Criticos

### `usuarios`

Modulo mais estrutural do sistema. Define `AUTH_USER_MODEL`, login, dashboard, perfil e permissoes centrais de negocio. Qualquer alteracao em `Usuario` afeta FKs, migrations, forms, testes, templates e regras de acesso.

Cuidados:

- Evitar adicionar regras especificas de um modulo diretamente no model.
- Manter permissoes transversais em `usuarios.permissions`.
- Separar acesso tecnico (`is_superuser`) de papel de negocio; `is_staff` fica restrito ao admin tecnico Django.
- Manter diferenca entre identidade (`usuario_eh_*`) e acesso (`usuario_tem_acesso_*`).
- Testar perfis: visitante, membro, liderado, lider, ministro, pastor e superuser.

### `departamentos`

Base organizacional do sistema. O model `DepartamentoMembro` e a principal fonte de lideranca, participacao e papeis departamentais.

Cuidados:

- Mudancas em papeis impactam escalas, governanca, infantil e eventos.
- Lideranca deve vir de `DepartamentoMembro`, nunca de `is_staff`.
- Evitar imports legados de escalas dentro de departamentos no longo prazo.
- Tratar departamentos reservados como infraestrutura de permissao com cuidado.

### `governanca`

Centraliza regras editoriais e permissoes para Secretaria/Midia. Tem impacto direto na administracao de conteudo publico e em varios paineis internos.

Cuidados:

- Usar `usuario_eh_secretaria`/`usuario_eh_midia` apenas para identidade real.
- Usar `usuario_tem_acesso_secretaria`/`usuario_tem_acesso_midia` para autorizacao de telas e acoes.
- Manter auditoria clara para alteracoes sensiveis.

### `financeiro`

Modulo sensivel por lidar com contribuicoes, credenciais e integracao externa.

Cuidados:

- Nao expor access token no frontend.
- Proteger e auditar credenciais armazenadas.
- Registrar logs de webhook, pagamento nao encontrado e falhas de API.
- Diferenciar erros temporarios de erros permanentes no webhook.

### `infantil`

Modulo sensivel por lidar com criancas, responsaveis, salas, aulas e chamadas para Midia.

Cuidados:

- Manter acesso minimo necessario por responsavel, equipe, lider e midia.
- Auditar acoes operacionais em chamadas, se o uso crescer.
- Preservar separacao entre exibir chamada e resolver atendimento.

### `escalas`

Modulo operacional central para departamentos. Depende de `DepartamentoMembro`, indisponibilidades e regras de conflito.

Cuidados:

- Validar sempre departamento, vinculo ativo, conflito e indisponibilidade.
- Evitar duplicar regras em forms, models e services sem uma fonte clara.
- Garantir testes para lider de um departamento tentando agir em outro.

## Recomendacoes de Arquitetura

### Onde evitar acoplamento

- Evitar que `usuarios.context_processors.internal_permissions` continue crescendo indefinidamente com consultas a todos os apps. O cache por request ja reduz recomputacao, mas um servico de navegacao ainda pode isolar melhor esse acoplamento.
- Evitar que novas views usem funcoes de identidade como autorizacao. Pastor deve ter acesso pastoral, nao virar semanticamente Secretaria, Midia, Lider ou Ministro.
- Evitar que `departamentos` importe models de `escalas` como compatibilidade permanente.
- Evitar que regras de permissao fiquem duplicadas em views, forms e templates.
- Evitar que credenciais e segredos sejam tratados como campos administrativos comuns sem politica de seguranca.

### Quais apps devem continuar separados

- `usuarios`: identidade, qualificacao e permissoes transversais.
- `departamentos`: estrutura organizacional e papeis por departamento.
- `escalas`: regras de culto, escala, itens e indisponibilidade.
- `infantil`: dados e operacao infantil, por sensibilidade e regras proprias.
- `financeiro`: contribuicoes e integracao Mercado Pago.
- `verbo_no_lar`: casas, materiais, relatorios e escalas ministeriais.
- `ministros`: cadastro ministerial, inclusive externo.
- `conteudo_interno`: operacao de Secretaria/Midia sobre conteudo.
- `governanca`: regras editoriais e auditoria.

### Quais integracoes devem ir para services

- Mercado Pago: manter em `financeiro/services/mercado_pago.py`.
- Chamadas infantis para Midia: manter operacoes em `infantil/services/chamadas.py`.
- Cadastro/revisao infantil: manter em `infantil/services/cadastros.py`.
- Escalas e geracao mensal: manter em `escalas/services/`.
- Conteudo editorial: manter em `conteudo_interno/services/`.
- Futuras integracoes: WhatsApp, e-mail transacional, YouTube, relatorios exportaveis e BI devem entrar por services dedicados.

### Onde usar permissoes centralizadas

- `usuarios.permissions`: regras transversais de perfil de pessoa:
  - visitante;
  - membro;
  - secretaria/midia como identidade departamental reservada;
  - acesso secretaria/midia;
  - lider departamental;
  - ministro;
  - pastor;
  - superuser/acesso tecnico total;
  - acesso pastoral;
  - pode ser escalado.

- `departamentos.permissions`: regras especificas de departamento:
  - pertence ao departamento;
  - pode acessar departamentos;
  - pode gerenciar membros;
  - pode gerenciar escalas do departamento.

- `governanca.permissions`: regras editoriais e de paineis Secretaria/Midia.

- `infantil.permissions`: regras especificas de sala, equipe, crianca, aula e chamada.

- `verbo_no_lar.permissions`: regras especificas de casa, responsavel, anfitriao e administracao do modulo.

- `financeiro.permissions`: regras administrativas financeiras.

## Leitura recomendada do sistema

Para entender impacto antes de alterar qualquer parte:

1. Ler `usuarios/models.py` e `usuarios/permissions.py`.
2. Ler `departamentos/models.py` e `departamentos/permissions.py`.
3. Ler `governanca/permissions.py`.
4. Ler o app que sera alterado.
5. Revisar `usuarios/context_processors.py` para impacto na sidebar.
6. Revisar templates relacionados.
7. Rodar `python manage.py check`.
8. Rodar testes do app e dos apps dependentes.
