# Arquitetura do Portal Verbo JSP

## Visao geral

O Portal Verbo JSP e uma aplicacao Django para gestao de igreja. O sistema combina site publico, area logada de usuarios e modulos internos para secretaria, departamentos, escalas, infantil, eventos, ministros, Verbo no Lar, financeiro e governanca de conteudo.

A arquitetura atual segue uma divisao por apps de dominio. A area publica fica principalmente em `core`, `eventos`, `noticias` e `ministros`. A area interna fica sob `usuarios/` e inclui namespaces internos de outros apps, como `usuarios:departamentos`, `usuarios:eventos`, `usuarios:infantil`, `usuarios:conteudo`, `usuarios:ministros`, `usuarios:verbo_no_lar` e `usuarios:financeiro`.

O projeto usa um `Usuario` customizado como `AUTH_USER_MODEL`. As regras de permissao mais recentes caminham para separar:

- status eclesiastico: visitante ou membro;
- papel departamental: liderado, auxiliar, voluntario, lider;
- qualificacao ministerial: ministro vinculado ao usuario;
- autoridade pastoral: pastor como regra de negocio;
- superuser: acesso tecnico Django/admin.

## Configuracao base

- Projeto Django: `config`
- Settings por ambiente: `config/settings.py`, `settings_base.py`, `settings_dev.py`, `settings_prod.py`
- Banco padrao local: SQLite
- Templates globais: `templates/`
- Assets: `static/`
- Media local: `media/`
- Usuario customizado: `usuarios.Usuario`

## Modulos e dominios

### `core`

Responsavel pelas paginas publicas institucionais e configuracoes globais do site.

Models:

- `SiteConfig`
- `SobrePage`
- `Lider`
- `ContatoMensagem`

Views/telas principais:

- Home
- Sobre
- Contato
- Ao vivo

Dependencias relevantes:

- Usado por `conteudo_interno` para editar conteudo publico.
- Usado por `governanca` para regras editoriais.
- `core.context_processors.site_config` injeta `site` em todos os templates.

### `usuarios`

Responsavel por autenticacao, cadastro, perfil, dashboard e permissoes centrais de negocio.

Models:

- `Usuario`, herdando `AbstractUser`

Campos de negocio relevantes:

- `status_eclesiastico`
- `discipulado_concluido`
- `discipulado_concluido_em`
- `qualificado_por`
- `qualificado_em`
- `eh_pastor`

Views/telas principais:

- Login
- Logout
- Registro
- Dashboard
- Perfil

Permissoes centrais:

- `usuario_tem_acesso_tecnico_total`
- `usuario_tem_acesso_total_sistema`
- `usuario_eh_visitante`
- `usuario_eh_membro`
- `usuario_eh_secretaria`
- `usuario_eh_midia`
- `usuario_eh_lider_departamento`
- `usuario_eh_lider_em_algum_departamento`
- `usuario_eh_ministro`
- `usuario_eh_pastor`
- `usuario_tem_acesso_secretaria`
- `usuario_tem_acesso_midia`
- `usuario_pode_montar_escala`
- `usuario_pode_ser_escalado_departamento`
- `usuario_pode_ser_escalado_verbo_no_lar`
- `usuario_tem_acesso_total_pastoral`

Dependencias relevantes:

- `usuarios.permissions` centraliza identidade, acesso pastoral/tecnico e permissoes transversais.
- `usuarios.context_processors.internal_permissions` chama funcoes de diversos apps, com cache por request em `request._internal_permissions_cache`.
- Varios apps dependem de `AUTH_USER_MODEL`.

### `governanca`

Responsavel por regras editoriais e auditoria de conteudo.

Models:

- `ConteudoAuditLog`

Arquivos relevantes:

- `governanca/permissions.py`
- `governanca/admin_mixins.py`
- `governanca/audit.py`

Dependencias relevantes:

- Depende de `core`, `departamentos`, `eventos`, `noticias` e `usuarios`.
- Define acesso de Secretaria e Midia via cargos em departamentos reservados.

### `conteudo_interno`

Responsavel pelo painel interno da Secretaria e Midia.

Views/telas principais:

- Painel da Secretaria
- Qualificacao de Pessoas
- Configuracoes do site
- Contato/localizacao
- Pagina Sobre
- Gestao interna de eventos publicos
- Gestao interna de noticias
- Midia Ao Vivo
- Chamadas infantis pendentes para midia

Dependencias relevantes:

- Edita models de `core`, `eventos` e `noticias`.
- Usa permissoes de `governanca`.
- Usa servicos de `infantil` para chamadas na midia.

### `departamentos`

Responsavel por departamentos e vinculos de usuarios aos departamentos.

Models:

- `Departamento`
- `DepartamentoMembro`

Papeis departamentais:

- `lider`
- `vice_lider`
- `liderado`
- `auxiliar`
- `voluntario`
- `membro` como legado

Views/telas principais:

- Lista de departamentos
- Criar/editar departamento
- Gerenciar membros do departamento
- Ativar/desativar vinculo departamental

Dependencias relevantes:

- `departamentos.permissions` concentra regras de acesso a departamentos, gestao de membros e gestao de escalas por departamento.
- Usa `AUTH_USER_MODEL`.
- E base para `escalas`, `governanca`, `eventos`, `infantil`, `ministros` e navegacao interna.
- Mantem imports de compatibilidade para models migrados para `escalas`.

### `escalas`

Responsavel por indisponibilidades, cultos padrao, escalas e itens de escala.

Models:

- `IndisponibilidadeMembro`
- `CultoPadrao`
- `Escala`
- `EscalaItem`

Views/telas principais:

- Minhas indisponibilidades
- Criar/editar/cancelar indisponibilidade
- Cultos padrao
- Lista de escalas
- Gerar escalas do mes
- Criar/editar escala
- Itens da escala

Dependencias relevantes:

- Depende fortemente de `departamentos.Departamento` e `DepartamentoMembro`.
- Usa regras de `usuarios.permissions` para acesso pastoral e escalabilidade.
- E consumido pelo dashboard de `usuarios`.

### `eventos`

Responsavel por agenda publica, inscricoes, check-in e gestao interna de eventos.

Models:

- `Evento`
- `InscricaoEvento`

Views/telas principais:

- Agenda publica
- Inscricao em evento
- Minhas inscricoes
- Detalhe da inscricao
- QR Code/check-in por token
- Gestao interna de eventos
- Lista de inscricoes
- Leitor QR

Dependencias relevantes:

- Usa `AUTH_USER_MODEL`.
- Permissoes dependem de Secretaria e lideranca departamental.
- Tambem e manipulado por `conteudo_interno`.

### `noticias`

Responsavel pela area publica de noticias.

Models:

- `Noticia`

Views/telas principais:

- Lista publica de noticias
- Detalhe da noticia

Dependencias relevantes:

- Gestao interna feita por `conteudo_interno`.
- Governanca editorial aplicada via `governanca`.

### `infantil`

Responsavel por salas infantis, equipe, criancas, aulas e chamadas de responsavel.

Models:

- `SalaInfantil`
- `SalaMembro`
- `Crianca`
- `AulaSala`
- `ChamadaResponsavel`

Views/telas principais:

- Minhas criancas
- Cadastro/revisao de criancas
- Lista de salas
- Criar/editar sala
- Equipe da sala
- Criancas da sala
- Aulas da sala
- Chamadas da sala
- Fluxo de chamada para midia

Dependencias relevantes:

- Usa `AUTH_USER_MODEL`.
- Usa `departamentos` para lideranca do departamento Infantil.
- Usa `governanca` para permissao da Midia.
- E consumido por `conteudo_interno` no painel de Midia.

### `ministros`

Responsavel por cadastro de ministros, formulario externo, dados ministeriais, galeria e dados financeiros de ministro.

Models:

- `Ministro`
- `FotoMinistro`

Views/telas principais:

- Lista de ministros
- Criar/editar ministro
- Detalhe do ministro
- Galeria
- Formulario externo por token
- Regenerar token do formulario

Dependencias relevantes:

- Pode vincular `Ministro.usuario` a `usuarios.Usuario`.
- Permissoes dependem de Secretaria, lideranca departamental e acesso pastoral.
- `verbo_no_lar` depende de `Ministro`.

### `verbo_no_lar`

Responsavel por casas, participantes, escalas, materiais e relatorios do Verbo no Lar.

Models:

- `CasaVerboNoLar`
- `ParticipanteVerboNoLar`
- `EscalaVerboNoLar`
- `MaterialApoioVerboNoLar`
- `RelatorioEncontroVerboNoLar`

Views/telas principais:

- Lista/detalhe de casas
- Criar/editar casa
- Participantes
- Escalas do Verbo no Lar
- Materiais de apoio
- Relatorios de encontro

Dependencias relevantes:

- Usa `AUTH_USER_MODEL`.
- Usa `ministros.Ministro` para escalas e relatorios.
- Permissoes dependem de Secretaria, pastor e responsaveis/anfitrioes de casa.

### `financeiro`

Responsavel por configuracao financeira, contribuicoes e integracao com Mercado Pago.

Models:

- `ConfiguracaoFinanceira`
- `Contribuicao`

Views/telas principais:

- Nova contribuicao
- Retorno do pagamento
- Webhook Mercado Pago
- Configuracoes financeiras
- Lista administrativa de contribuicoes

Dependencias relevantes:

- Usa `AUTH_USER_MODEL`.
- Usa `governanca`/Secretaria e pastor para permissao administrativa.
- Integra API externa Mercado Pago via `financeiro/services/mercado_pago.py`.

## Mapa de dependencias por dominio

```text
core
  <- conteudo_interno
  <- governanca

usuarios
  <- quase todos os apps via AUTH_USER_MODEL
  <- usuarios.context_processors agrega permissoes de apps internos

departamentos
  <- escalas
  <- governanca
  <- infantil
  <- eventos
  <- ministros
  <- usuarios.context_processors

escalas
  <- usuarios.dashboard
  <- departamentos via imports legados
  <- escalas.permissions define acesso ao modulo e indisponibilidades

ministros
  <- verbo_no_lar

infantil
  <- conteudo_interno/midia

eventos/noticias/core
  <- conteudo_interno
  <- governanca

financeiro
  <- usuarios.urls
  <- Mercado Pago externo
```

## Models que impactam outros modulos

| Model | Impacta | Motivo |
| --- | --- | --- |
| `usuarios.Usuario` | Todos os apps internos | `AUTH_USER_MODEL`, permissoes, dashboard, vinculos |
| `departamentos.Departamento` | Governanca, escalas, infantil, eventos, ministros | Departamentos reservados e liderancas |
| `departamentos.DepartamentoMembro` | Escalas, governanca, eventos, infantil, usuarios | Fonte de papel departamental |
| `escalas.Escala` | Usuarios, departamentos | Dashboard e gestao interna |
| `escalas.EscalaItem` | Usuarios, escalas | Proximas escalas do membro |
| `infantil.Crianca` | Usuarios, infantil, secretaria | Cadastro/responsavel/revisao |
| `infantil.ChamadaResponsavel` | Infantil, conteudo_interno, midia | Chamadas para exibicao |
| `ministros.Ministro` | Verbo no Lar, usuarios | Escala ministerial e qualificacao ministerial |
| `verbo_no_lar.CasaVerboNoLar` | Verbo no Lar, permissoes | Responsavel/anfitriao definem acesso |
| `financeiro.ConfiguracaoFinanceira` | Financeiro, Mercado Pago | Credenciais e estado da integracao |
| `financeiro.Contribuicao` | Financeiro, usuarios | Registro financeiro do usuario |
| `core.SiteConfig` | Todos os templates | Context processor global |
| `core.SobrePage` e `core.Lider` | Site publico, secretaria | Conteudo institucional |
| `eventos.Evento` | Publico, secretaria, check-in | Agenda e inscricoes |
| `eventos.InscricaoEvento` | Eventos, usuarios | Inscricoes e QR/check-in |
| `noticias.Noticia` | Publico, secretaria | Conteudo editorial |

## Telas existentes

Publicas:

- Home
- Sobre
- Agenda
- Noticias
- Detalhe da noticia
- Ao vivo
- Contato
- Formulario externo de ministro
- Check-in por token de evento

Usuario:

- Login
- Registro
- Dashboard
- Perfil
- Minhas inscricoes
- Minhas criancas
- Contribuir

Secretaria/Midia:

- Dashboard da Secretaria
- Qualificacao de Pessoas
- Configuracoes do site
- Contato/localizacao
- Pagina Sobre
- Eventos internos
- Noticias internas
- Midia Ao Vivo
- Chamadas pendentes da midia

Departamentos/Escalas:

- Lista de departamentos
- Formulario de departamento
- Membros do departamento
- Minhas indisponibilidades
- Cultos padrao
- Lista de escalas
- Gerar escalas do mes
- Formulario de escala
- Itens da escala

Infantil:

- Lista de salas
- Formulario de sala
- Equipe da sala
- Criancas da sala
- Aulas da sala
- Chamadas da sala
- Revisao de cadastros infantis

Ministros:

- Lista
- Formulario
- Detalhe
- Galeria
- Formulario externo

Verbo no Lar:

- Casas
- Detalhe da casa
- Participantes
- Escalas
- Materiais
- Relatorios

Financeiro:

- Nova contribuicao
- Retorno de pagamento
- Configuracao financeira
- Lista de contribuicoes
- Webhook

## Telas que deveriam existir ou evoluir

- Gestao central de usuarios e permissoes de negocio, separada do admin tecnico.
- Perfil administrativo de pessoa, consolidando status eclesiastico, pastor, vinculos departamentais, ministro e historico.
- Tela de matriz de acessos por modulo.
- Relatorios consolidados por departamento, escala, infantil, financeiro e Verbo no Lar.
- Painel de auditoria operacional, alem da auditoria editorial.
- Tela de saude de integracoes externas: Mercado Pago, YouTube/Ao Vivo, QR/check-in.
- Historico de qualificacao e alteracoes de status de usuario.

## Riscos de acoplamento

1. `usuarios.context_processors.internal_permissions` consulta varios apps em todos os templates. O cache por request reduz recomputacao durante a mesma renderizacao, mas o acoplamento da sidebar com muitos dominios ainda existe.

2. `departamentos` e a base de muitas permissoes. Mudancas em `DepartamentoMembro.Papel` impactam escalas, governanca, infantil, eventos e ministros.

3. A separacao identidade/acesso foi padronizada: `usuario_eh_secretaria` e `usuario_eh_midia` representam cargo real; `usuario_tem_acesso_secretaria` e `usuario_tem_acesso_midia` concedem acesso para Secretaria/Midia, pastor e superuser. O risco remanescente e manter novas views usando funcoes de acesso, nao identidade.

4. `departamentos.models` ainda expoe imports de compatibilidade para models que foram movidos para `escalas`. Isso evita quebra, mas conserva acoplamento legado.

5. `financeiro` guarda tokens em banco e depende de webhook publico. Requer cuidado com logs, backups, segredo do webhook e tratamento de retentativas.

6. Templates globais dependem de `SiteConfig.objects.get_or_create(id=1)` em todas as paginas. E pratico, mas pode gerar consulta em toda renderizacao.

7. Verbo no Lar depende diretamente de `ministros.Ministro`; qualquer remodelagem ministerial impacta escalas e relatorios do modulo.

8. Testes de permissao foram atualizados para cobrir visitante, membro, liderado, lider, ministro, pastor e superuser. O risco remanescente e fixtures antigas com nomes historicos como `staff`, mesmo quando representam acesso pastoral.

## Sugestoes de separacao por apps

- Manter `usuarios` como dono da identidade e permissoes transversais de negocio.
- Criar, no futuro, um app `pessoas` ou `membresia` se a jornada eclesiastica crescer muito. Ele poderia conter qualificacao, discipulado, historico de status, pastorado e relacoes familiares.
- Manter `departamentos` como estrutura organizacional, sem importar escalas no longo prazo.
- Manter `escalas` como dominio proprio, consumindo `DepartamentoMembro` por interface clara.
- Criar um modulo `integracoes` se Mercado Pago, YouTube, QR, WhatsApp ou outras integracoes crescerem.
- Criar app `relatorios` para consultas cruzadas e dashboards executivos.
- Criar app `auditoria` se a auditoria sair do escopo editorial e passar a cobrir usuarios, financeiro, escalas e infantil.

## Recomendacoes imediatas

1. Adicionar logs estruturados para webhooks financeiros.
2. Definir politica de armazenamento de credenciais sensiveis.
3. Medir queries do context processor com testes de performance e `assertNumQueries`.
4. Criar factories simples para perfis de permissao: visitante, membro, liderado, lider, ministro, pastor e superuser.
5. Renomear fixtures antigas que usam `staff` como nome quando o papel real e pastor/acesso pastoral.
6. Evoluir `usuarios.context_processors.internal_permissions` para um service de navegacao se a sidebar continuar crescendo.
