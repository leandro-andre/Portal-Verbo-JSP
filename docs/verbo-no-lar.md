# Verbo no Lar (módulo interno)

Este documento descreve o novo módulo **Verbo no Lar**, criado no app Django `verbo_no_lar`, com gestão interna de **casas**, **participantes**, **escala de ministros**, **materiais de apoio** e **relatórios**.

---

## 1. Onde fica no sistema (URLs)

O módulo é **interno** (área logada) e está sob:

- **Prefixo**: `/usuarios/verbo-no-lar/`
- **Namespace**: `usuarios:verbo_no_lar:*`

Rotas principais:

- **Casas**: `/usuarios/verbo-no-lar/casas/`
- **Materiais**: `/usuarios/verbo-no-lar/materiais/`
- **Participantes / Escalas / Relatórios**: sempre vinculados a uma casa.

O link aparece no menu lateral como **“Verbo no Lar”** quando o usuário tem permissão.

---

## 2. Permissões (backend)

As regras estão em `verbo_no_lar/permissions.py`.

### Quem tem acesso ao módulo

- **Acesso total**:
  - `superuser`
  - secretaria (via `governanca.permissions.usuario_eh_secretaria`)
  - `is_staff`
- **Acesso como responsável**:
  - Usuário que for **`casal_responsavel`** de alguma casa ativa (e também consegue operar a própria casa)

### Operação por casa

Para abrir/editar uma casa e suas telas vinculadas (participantes, escalas, relatórios):

- pode se for gestor total **ou**
- se for **responsável** (`casal_responsavel`) **ou anfitrião** (`anfitriao`) daquela casa.

---

## 3. Modelos (database)

### `CasaVerboNoLar`
Cadastro base do grupo/casa:

- nome, responsáveis (FK `usuarios.Usuario`), anfitrião opcional
- telefone/WhatsApp, endereço/bairro/ponto de referência
- link do Google Maps + latitude/longitude opcionais
- dia/horário padrão, capacidade aproximada, ativo, observações
- timestamps

### `ParticipanteVerboNoLar`
Participante pode ser:

- **membro** (FK `usuarios.Usuario`) **ou**
- **visitante** (apenas nome/telefone)

Regra de validação:
- se `tipo=membro` → precisa `membro`
- se `tipo=visitante` → precisa `nome_visitante`

### `EscalaVerboNoLar`
Escala de ministros por casa:

- casa, ministro (FK `ministros.Ministro`)
- data/horário, tema, status, observações

### `MaterialApoioVerboNoLar`
Material geral ou por casa:

- título, data, texto base, conteúdo (texto), anexo (arquivo)
- casa opcional (se vazio, é material **geral**)

### `RelatorioEncontroVerboNoLar`
Registro pós-encontro:

- casa, data, ministro, tema
- presentes / visitantes, pedidos de oração, observações
- criado_por (usuário) + criado_em

---

## 4. Telas

Templates em `templates/verbo_no_lar/` seguem o padrão do sistema interno (cards, tabelas, ações no topo).

- `casas_lista.html`: lista com botões “Participantes / Escala / Relatórios / Como chegar”
- `casa_detalhe.html`: dados completos + blocos com participantes, escalas e relatórios recentes
- `participantes_lista.html` + `participante_form.html`
- `escalas_lista.html` + `escala_form.html`
- `materiais_lista.html` + `material_form.html` + `material_detalhe.html`
- `relatorios_lista.html` + `relatorio_form.html` + `relatorio_detalhe.html`

---

## 5. Como testar (passo a passo)

1. Rode o servidor:
   - `venv\\Scripts\\python.exe manage.py runserver`

2. Entre com um usuário que tenha acesso:
   - `superuser` ou secretaria ou `is_staff`

3. Abra:
   - `/usuarios/verbo-no-lar/casas/`

4. Cadastre uma **Nova casa** (botão aparece apenas para gestores totais).

5. Dentro da casa:
   - cadastre participantes (membro e visitante)
   - crie escalas
   - crie relatórios
   - cadastre materiais em `/usuarios/verbo-no-lar/materiais/`

6. Teste permissão de responsável:
   - coloque um usuário como `casal_responsavel` de uma casa ativa
   - faça login com esse usuário
   - ele deve ver o menu “Verbo no Lar” e acessar apenas as casas onde é responsável/anfitrião

---

## 6. Observação importante sobre “Ministro”

O modelo `ministros.Ministro` **não está vinculado automaticamente** a um usuário (`usuarios.Usuario`).
Por isso, nesta primeira versão o “perfil Ministro” (usuário que só enxerga a própria escala) fica preparado para evoluir,
mas depende de uma estratégia de vínculo (ex.: FK opcional para usuário, ou tabela de associação).

