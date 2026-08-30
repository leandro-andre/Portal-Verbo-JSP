# Production Readiness

## Arquitetura Alvo

Primeiro ambiente online planejado:

- Railway para Django + React no mesmo servico.
- Railway PostgreSQL para banco de producao.
- Cloudflare R2 para media/fotos em producao.
- GitHub como origem do deploy.
- HTTPS via Railway/dominio configurado.
- Same-origin sempre que possivel:
  - `/` e rotas React: SPA
  - `/api/`: Django API
  - `/admin/`: Django Admin
  - `/static/`: static files
  - `/media/`: local apenas em desenvolvimento; producao retorna URLs assinadas do R2

Esta etapa nao executa deploy, nao cria Railway, nao cria PostgreSQL online, nao altera recursos Cloudflare/R2 e nao migra dados.

## Ambientes

O projeto usa `DJANGO_ENV`:

- `dev`: `config.settings_dev`
- `prod` ou `production`: `config.settings_prod`

Desenvolvimento continua simples:

- sem `DATABASE_URL`, usa SQLite local;
- `DJANGO_SERVE_REACT_APP=False`, React roda via Vite;
- Vite usa proxy `/api` para `http://localhost:8000`.

Producao:

- `DJANGO_DEBUG=False`;
- `DJANGO_SECRET_KEY` obrigatoria;
- `DATABASE_URL` ou `DJANGO_DATABASE_URL` obrigatorio;
- `DJANGO_ALLOWED_HOSTS` obrigatorio e sem `*`;
- cookies seguros habilitados;
- `DJANGO_SERVE_REACT_APP=True` por padrao.

## Variaveis

Variaveis principais:

- `DJANGO_ENV`
- `DJANGO_DEBUG`
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DJANGO_SERVE_REACT_APP`
- `DATABASE_URL`
- `DJANGO_DATABASE_URL`
- `DJANGO_DB_CONN_MAX_AGE`
- `DJANGO_DB_SSL_REQUIRE`
- `DJANGO_USE_X_FORWARDED_PROTO`
- `DJANGO_SECURE_SSL_REDIRECT`
- `DJANGO_SECURE_HSTS_SECONDS`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `R2_ENDPOINT_URL`
- `R2_QUERYSTRING_EXPIRE`

`DJANGO_SECRET_KEY` nunca deve ser versionada com valor real.

## Banco

Sem `DATABASE_URL`, o projeto usa SQLite local.

Com `DATABASE_URL`, o projeto usa `dj-database-url`. Para Railway PostgreSQL, a variavel esperada e `DATABASE_URL`.

Em producao, a ausencia de `DATABASE_URL` falha cedo para evitar fallback acidental para SQLite.

## Static Files

WhiteNoise foi configurado para servir static files sem Nginx separado.

`collectstatic` deve ser executado depois do build do React, para incluir:

- Django admin static;
- static local em `static/`;
- assets gerados por Vite em `frontend/dist`.

WhiteNoise nao serve media de usuarios como solucao persistente.

## React

Build esperado:

```bash
npm run build
python manage.py collectstatic --noinput
```

Com `DJANGO_SERVE_REACT_APP=True`, Django serve `frontend/dist/index.html` para `/` e para rotas SPA como:

- `/meu-perfil`
- `/minhas-escalas`
- `/departamentos`
- `/escalas`
- `/agenda-cultos`

O fallback nao captura:

- `/api/`
- `/admin/`
- `/static/`
- `/media/`

## Auth, CSRF e Cookies

A arquitetura continua:

- Django session;
- cookies;
- CSRF;
- chamadas relativas `/api/...`;
- sem JWT;
- sem token em localStorage.

Em producao:

- `SESSION_COOKIE_SECURE=True`;
- `CSRF_COOKIE_SECURE=True`;
- `SECURE_PROXY_SSL_HEADER` usa `HTTP_X_FORWARDED_PROTO=https` por padrao.

`SECURE_SSL_REDIRECT` fica desligado por padrao para evitar redirect loop antes de validar o proxy. Pode ser ligado depois por variavel.

HSTS fica com `0` por padrao. Deve ser ativado somente depois do dominio e HTTPS finais estarem validados.

## Health Check

Endpoint:

- `GET /api/health/`

Resposta:

```json
{"status": "ok"}
```

Nao exige autenticacao e nao expoe detalhes internos. Nesta fase ele valida a aplicacao, sem consulta pesada ao banco.

## Logging

Django continua emitindo logs para stdout/stderr, que Railway captura. Nao foi adicionada stack externa de observabilidade.

Nao logar:

- senhas;
- `SECRET_KEY`;
- tokens CSRF;
- cookies;
- dados sensiveis desnecessarios.

## Gunicorn

Servidor WSGI de producao:

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

Nao usar `python manage.py runserver` em producao.

## Sequencia De Deploy Futuro

Sequencia esperada para PVV-043:

1. Instalar dependencias Python.
2. Instalar dependencias Node.
3. Build React via `npm run build` na raiz, que executa `npm ci` dentro de `frontend/`.
4. `python manage.py collectstatic --noinput`.
5. `python manage.py migrate`.
6. Iniciar Gunicorn.

Migrations devem rodar como etapa controlada de deploy/release, antes de servir trafego.

## Media E R2

PVV-040 adicionou foto em `Person`.

MEDIA usa o storage default do Django:

- sem variaveis R2: `FileSystemStorage`, adequado para desenvolvimento local;
- com `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME` e `R2_ENDPOINT_URL`: `storages.backends.s3.S3Storage` apontando para Cloudflare R2.

Se qualquer variavel R2 obrigatoria estiver presente sem as demais, o Django falha cedo com mensagem de configuracao incompleta. Credenciais reais devem existir apenas como variaveis de ambiente no Railway/ambiente de execucao.

STATIC continua no WhiteNoise e nao deve ser enviado para R2.

O bucket R2 permanece privado. URLs de `photo_url` sao temporarias e assinadas pelo `django-storages`, com expiracao padrao de 3600 segundos ajustavel por `R2_QUERYSTRING_EXPIRE`. Nao depender de `r2.dev` nem tornar o bucket publico sem decisao explicita.

Confirmacao segura do storage ativo, sem imprimir segredos:

```bash
python manage.py shell -c "from django.core.files.storage import storages; print(storages['default'].__class__.__module__ + '.' + storages['default'].__class__.__name__)"
```

Em producao/R2 o resultado esperado contem `storages.backends.s3.S3Storage`.

## Checklist PVV-043 Railway

- Criar projeto Railway.
- Conectar GitHub.
- Criar Railway PostgreSQL.
- Configurar variables.
- Configurar build do frontend.
- Configurar `collectstatic`.
- Configurar `migrate` como etapa segura.
- Configurar start command com Gunicorn.
- Configurar health check `/api/health/`.
- Gerar dominio temporario Railway.
- Testar `/admin/`.
- Testar `/api/health/`.
- Testar React em `/`.
- Testar refresh de rota SPA.
- Testar login e CSRF.

## Checklist PVV-044 R2

- Criar bucket R2.
- Criar credenciais.
- Adicionar backend de storage compativel.
- Configurar media storage.
- Validar URLs.
- Testar upload de foto.
- Testar substituicao e delete.
- Testar persistencia entre deploys.

## Checklist PVV-045 Dominio

- Definir dominio/subdominio.
- Configurar DNS.
- Validar HTTPS.
- Atualizar `DJANGO_ALLOWED_HOSTS`.
- Atualizar `DJANGO_CSRF_TRUSTED_ORIGINS`.
- Validar cookies secure.
- Rodar smoke tests.
- Avaliar ligar `SECURE_SSL_REDIRECT`.
- Avaliar ativar HSTS gradualmente.
