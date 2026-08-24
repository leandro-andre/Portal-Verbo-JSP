# Portal Verbo JSP

Portal Django para igreja/comunidade, com site publico, area de usuarios, eventos, noticias, departamentos, escalas, infantil e governanca de conteudo.

## Requisitos

- Python 3.13
- Node 24.14.1 para build do frontend React
- Git
- SQLite para desenvolvimento local

## Configuracao local

Crie e ative o ambiente virtual:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Instale as dependencias:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Crie um arquivo `.env` na raiz do projeto:

```env
DJANGO_ENV=dev
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=django-insecure-dev-only-key-change-me
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,testserver
DJANGO_CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DJANGO_SERVE_REACT_APP=False
DATABASE_URL=
```

Prepare o banco local:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

Rode o servidor:

```powershell
python manage.py runserver
```

Acesse:

- Site: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Testes

Rode a suite completa:

```powershell
python manage.py test
```

Para rodar um app especifico:

```powershell
python manage.py test governanca
```

## Solicitacao de acesso

O fluxo publico em `/pedir-acesso` cria uma `AccessRequest` pendente e um `Usuario`
inativo na mesma transacao. A senha escolhida pelo solicitante e salva apenas como
hash via Django; ela nao e persistida na solicitacao nem retornada pela API.

Na aprovacao, a Secretaria resolve a `Person` e o mesmo `Usuario` pendente e
vinculado a ela, ficando ativo para login. Solicitacoes antigas sem `Usuario`
relacionado continuam suportadas temporariamente pelo fluxo legado de activation
URL. Solicitacoes rejeitadas preservam o `Usuario` tecnico inativo vinculado a
request ate uma politica futura de retencao/limpeza ser definida.

## Estrutura

- `core`: paginas publicas, contato, ao vivo e configuracao global do site.
- `usuarios`: autenticacao, cadastro, dashboard e perfil.
- `eventos`: agenda publica, inscricoes, check-in e gestao interna.
- `noticias`: listagem e detalhe de noticias.
- `departamentos`: departamentos, membros e papeis.
- `escalas`: cultos padrao, escalas e indisponibilidades.
- `infantil`: salas, equipe, criancas, aulas e chamadas de responsavel.
- `conteudo_interno`: paineis internos de secretaria e midia.
- `governanca`: permissoes editoriais e auditoria.

## Ambientes

O arquivo `config/settings.py` escolhe a configuracao usando `DJANGO_ENV`:

- `DJANGO_ENV=dev`: usa `config/settings_dev.py`.
- `DJANGO_ENV=prod` ou `production`: usa `config/settings_prod.py`.

Em producao, defina pelo menos:

```env
DJANGO_ENV=production
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=uma-chave-segura
DJANGO_ALLOWED_HOSTS=seudominio.com,.up.railway.app
DJANGO_CSRF_TRUSTED_ORIGINS=https://seudominio.com,https://app.up.railway.app
DJANGO_SERVE_REACT_APP=True
DATABASE_URL=postgresql://...
DJANGO_USE_X_FORWARDED_PROTO=True
```

Sem `DATABASE_URL`, o desenvolvimento local continua usando SQLite. Em producao,
`DATABASE_URL` e obrigatorio para evitar fallback acidental para SQLite.

Build/execucao esperados para producao:

```powershell
cd frontend
npm ci
npm run build
cd ..
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

Mais detalhes: `docs/deployment/production-readiness.md`.

## Arquivos locais

O reposititorio ignora arquivos gerados localmente, como:

- `venv/`
- `.env`
- `db.sqlite3`
- `media/`
- `staticfiles/`
- `__pycache__/` e `*.pyc`

Esses arquivos devem ser recriados ou providos pelo ambiente onde o projeto estiver rodando.
