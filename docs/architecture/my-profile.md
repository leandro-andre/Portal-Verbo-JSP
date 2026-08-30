# Meu Perfil

## Escopo

`Meu Perfil` e a foto pessoal fazem parte do dominio de Pessoas. A conta de acesso (`Usuario`) autentica e autoriza, mas os dados exibidos no perfil do usuario logado sao derivados da `Person` vinculada em `request.user.person`.

## Modelo

`Person.photo` usa o storage default de MEDIA configurado no Django:

- desenvolvimento local sem R2: `FileSystemStorage`, `MEDIA_ROOT` e `MEDIA_URL`;
- producao com R2 completo: Cloudflare R2 via backend S3 do `django-storages`.
- Upload path: `people/photos/<person_id>/<uuid>.<ext>`.

O campo aceita vazio/nulo. Remover a foto limpa apenas `Person.photo`; a `Person` nunca e excluida por esse fluxo.

## API

Endpoints self-service:

- `GET /api/me/profile/`
- `PATCH /api/me/profile/`
- `POST /api/me/profile/photo/`
- `DELETE /api/me/profile/photo/`

Todos exigem usuario autenticado e ativo. O endpoint usa sempre `request.user.person`; nao recebe `person_id` e nao permite editar outra pessoa.

Quando o usuario nao possui `Person` vinculada, a API retorna estado amigavel e nao cria cadastro automaticamente.

## Campos Editaveis

Nesta fase, o usuario pode alterar apenas:

- `phone`
- `photo`

Campos administrativos continuam fora do self-service:

- nome completo
- nome preferido
- data de nascimento
- e-mail
- status cadastral
- jornada da igreja
- membresia
- departamentos
- cargos
- status de acesso

Envio desses campos em `PATCH /api/me/profile/` e rejeitado.

## Foto

O upload de foto aceita:

- JPEG
- PNG
- WEBP

Limite: 5MB.

Ao substituir ou remover foto, o arquivo anterior e apagado do storage quando ainda existe e pertence ao campo anterior.

Em producao, o bucket R2 permanece privado. `photo_url` e gerada por `photo.url`;
com R2 isso resulta em uma URL temporaria assinada pelo storage, com expiracao
padrao de 3600 segundos (`R2_QUERYSTRING_EXPIRE`). Nao habilitar `r2.dev`
nem dominio publico sem decisao explicita de infraestrutura.

## Frontend

A rota React `/meu-perfil` consome a API self-service. O menu lateral exibe `Meu Perfil` em `Minha area`; `Minhas Escalas` e `Minhas indisponibilidades` continuam dependentes de `Person` vinculada.

O `current-user` retorna `photo_url`, permitindo que o topo do app use a foto de `Person` como avatar. Quando nao ha foto, o fallback visual continua sendo as iniciais.
