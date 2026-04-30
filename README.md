# Portal Verbo JSP

Portal Django para igreja/comunidade, com site publico, area de usuarios, eventos, noticias, departamentos, escalas, infantil e governanca de conteudo.

## Requisitos

- Python 3.13
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
DJANGO_ENV=prod
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=uma-chave-segura
DJANGO_ALLOWED_HOSTS=seudominio.com,www.seudominio.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://seudominio.com,https://www.seudominio.com
```

Se usar proxy/reverse proxy com HTTPS:

```env
DJANGO_USE_X_FORWARDED_PROTO=True
```

## Arquivos locais

O reposititorio ignora arquivos gerados localmente, como:

- `venv/`
- `.env`
- `db.sqlite3`
- `media/`
- `staticfiles/`
- `__pycache__/` e `*.pyc`

Esses arquivos devem ser recriados ou providos pelo ambiente onde o projeto estiver rodando.
