# Área do usuário — como funciona

Este documento descreve a parte relacionada ao **usuário logado** no Portal: cadastro, autenticação, modelo de dados, painel, perfil, navegação e como as permissões controlam o que aparece no menu.

Toda a área interna que você vê com sidebar (“Área do usuário”) começa em URLs sob o prefixo **`/usuarios/`**, definido em `usuarios/urls.py`.

---

## 1. Modelo de usuário

O projeto usa um modelo customizado **`usuarios.Usuario`**, herdando de `AbstractUser`:

| Campo | Função |
|--------|--------|
| Campos do Django (`username`, `password`, `first_name`, `last_name`, `email`, …) | Identidade e autenticação padrão |
| `telefone` | Contato opcional |
| `foto` | Foto de perfil (upload em `media/perfil/`) |
| `data_nascimento` | Opcional |
| `is_membro` | Exibido na sidebar como “Membro” ou “Visitante” |

Configuração global:

- **`AUTH_USER_MODEL`** aponta para `"usuarios.Usuario"` (`config/settings_base.py`).
- **`LOGIN_URL`**: `usuarios:login` — qualquer view com `LoginRequiredMixin` redireciona para `/usuarios/login/` se não houver sessão.
- **`LOGIN_REDIRECT_URL`**: `usuarios:dashboard` — destino após login quando não há `next` na query string.
- **`LOGOUT_REDIRECT_URL`**: `core:home` — após logout (a view de logout também usa `next_page` para a home).

---

## 2. Rotas principais (`usuarios`)

Namespace da app: **`usuarios`** (`app_name = "usuarios"`).

| URL | Nome | Quem acessa | O que faz |
|-----|------|-------------|-----------|
| `/usuarios/login/` | `usuarios:login` | Público | Login com `LoginForm`; usuário já logado é redirecionado ao painel |
| `/usuarios/logout/` | `usuarios:logout` | Logado | Encerra sessão (POST com CSRF) |
| `/usuarios/registro/` | `usuarios:registro` | Público | Cadastro com `RegistroForm`; ao salvar, **faz login automático** e redireciona ao painel |
| `/usuarios/dashboard/` | `usuarios:dashboard` | **Login obrigatório** | Painel com resumos reais do banco |
| `/usuarios/perfil/` | `usuarios:perfil` | **Login obrigatório** | Edição do próprio usuário (`PerfilForm`) |

### Módulos incluídos em `/usuarios/`

Além das rotas acima, `usuarios/urls.py` **inclui** outros apps com **namespace**, todos sob `/usuarios/…`:

| Prefixo | Namespace | Conteúdo típico |
|---------|-----------|-----------------|
| `departamentos/` | `usuarios:departamentos` | Departamentos, escalas, indisponibilidades |
| `eventos/` | `usuarios:eventos` | Gestão de eventos, inscrições, check-in, minhas inscrições |
| `infantil/` | `usuarios:infantil` | Infantil (ex.: minhas crianças) |
| `conteudo/` | `usuarios:conteudo` | Secretaria, mídia (conforme permissão) |
| `ministros/` | `usuarios:ministros` | Gestão de ministros (conforme permissão) |

Exemplo de URL nomeada na template: `{% url 'usuarios:eventos:minhas_inscricoes' %}`.

---

## 3. Fluxos de autenticação

### Login (`UsuarioLoginView`)

- Usa o template `templates/usuarios/login.html`.
- Formulário: `LoginForm` (extensão de `AuthenticationForm` com classes CSS nos campos).
- `redirect_authenticated_user = True`: quem já está logado não vê o formulário de login de novo (vai ao fluxo padrão de redirect).

### Registro (`RegistroView`)

- Template: `templates/usuarios/registro.html`.
- Formulário: `RegistroForm` (`UserCreationForm` + nome, sobrenome, e-mail, telefone).
- Se o visitante **já está autenticado**, é redirecionado ao dashboard.
- Após cadastro válido: **`login(request, user)`** e mensagem de sucesso; redirect para `usuarios:dashboard`.

### Logout (`UsuarioLogoutView`)

- `next_page` aponta para `core:home` (alinhado ao `LOGOUT_REDIRECT_URL`).
- Na sidebar, o logout é um **POST** para evitar CSRF em GET acidental.

---

## 4. Painel (`DashboardView`)

- **Exige login** (`LoginRequiredMixin`).
- Template: `templates/usuarios/dashboard.html`.
- Cada view que usa a sidebar deve passar no contexto algo como **`active_section`** (ex.: `'dashboard'`) para marcar o item ativo no menu.

O painel agrega dados reais, entre eles:

- **Completude do perfil** (`get_profile_status`): percentual com base em nome, sobrenome, e-mail, telefone e data de nascimento.
- **Participações em departamentos** ativas (`DepartamentoMembro`).
- **Próximas escalas** (itens de escala futuros ligados ao usuário).
- **Próximos eventos** publicados (`Evento`).
- **Últimas notícias** publicadas.
- **Mensagens de contato** associadas ao usuário (`ContatoMensagem`).

Ou seja: o dashboard é um **hub** de leitura, não um “menu fake”.

---

## 5. Perfil (`PerfilView`)

- **Exige login**.
- `UpdateView` com `get_object()` retornando `request.user` — o usuário só edita **a si mesmo**.
- Campos editáveis: `first_name`, `last_name`, `email`, `telefone`, `data_nascimento`, `foto` (`PerfilForm`).
- Após salvar: mensagem de sucesso e permanece em `usuarios:perfil`.
- Também mostra `profile_status` (mesma lógica do dashboard).

---

## 6. Sidebar e permissões do menu

O arquivo `templates/usuarios/_sidebar.html` monta a navegação da área logada.

### Sempre (usuário autenticado)

- Painel
- Meu perfil
- Minhas crianças (`usuarios:infantil:minhas_criancas`)
- Minhas inscrições (`usuarios:eventos:minhas_inscricoes`)

### Escalas

- **Escalas** (gestão/listagem): só se `can_manage_escalas` for verdadeiro.
- **Minhas indisponibilidades**: qualquer usuário logado.

### Bloco “Departamentos” (título agrupador)

Só aparece se **alguma** destas permissões for verdadeira:

- `can_view_departamentos`
- `can_view_infantil`
- `can_view_secretaria`
- `can_view_midia`
- `can_manage_eventos`
- `can_manage_ministros`

Dentro dele, cada link depende da respectiva flag (departamentos, infantil, secretaria, eventos, ministros, mídia).

### Origem das flags

O context processor **`usuarios.context_processors.internal_permissions`** roda em **todas** as templates e define essas variáveis booleanas com base em funções de cada domínio (departamentos, governança/secretaria, infantil, eventos, ministros, etc.).

Se o usuário **não** está autenticado, todas as flags vêm como `False`.

---

## 7. Integração com outras áreas (visão rápida)

- **Eventos (público)**: a agenda em `/eventos/agenda/` usa o namespace `eventos:` da app pública (`eventos/urls.py`), não o `usuarios:eventos`.
- **Eventos (área logada / gestão)**: rotas em `usuarios/eventos/...` via `usuarios:eventos:...` (`eventos/internal_urls.py`).
- Views que precisam de equipe (ex.: gestão de eventos, check-in) usam mixins em `eventos/permissions.py` e podem redirecionar para login ou negar acesso conforme o papel do usuário.

---

## 8. Onde mexer no código (referência)

| Objetivo | Arquivo usual |
|----------|----------------|
| Novas rotas “da área do usuário” | `usuarios/urls.py` (ou include de outro app) |
| Login / registro / dashboard / perfil | `usuarios/views.py` |
| Campos do usuário | `usuarios/models.py` + migrações |
| Formulários | `usuarios/forms.py` |
| Menu lateral | `templates/usuarios/_sidebar.html` |
| Flags do menu | `usuarios/context_processors.py` |
| URLs de login e modelo auth | `config/settings_base.py` |

---

## 9. Teste rápido manual

1. Acesse `/usuarios/registro/`, crie uma conta → deve ir ao **painel** já logado.
2. Acesse `/usuarios/perfil/`, altere telefone/foto → salvar → mensagem de sucesso.
3. Faça logout pela sidebar → deve voltar à **home** do site.
4. Acesse `/usuarios/dashboard/` sem estar logado → redirect para `/usuarios/login/?next=...`.

---

*Documento gerado com base na estrutura do repositório (app `usuarios`, templates e settings). Se novos módulos forem incluídos em `usuarios/urls.py`, atualize a seção 2 e a sidebar conforme necessário.*
