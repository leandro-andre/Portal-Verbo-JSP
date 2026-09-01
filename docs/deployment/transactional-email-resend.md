# E-mail Transacional Com Resend

## Arquitetura

O Portal usa uma camada interna em `core.email` para e-mails transacionais.
Fluxos de negocio nao devem chamar `resend.Emails.send(...)` diretamente.

O provedor atual e Resend, via SDK oficial Python `resend`.

## Configuracao

Variaveis esperadas no ambiente:

- `RESEND_API_KEY`
- `EMAIL_FROM`
- `APP_BASE_URL`

`RESEND_API_KEY` e `EMAIL_FROM` habilitam o envio. Sem essas duas variaveis, o
servico interno falha de forma explicita e nao faz chamada externa.

`APP_BASE_URL` fica disponivel para proximas features que montarao links para o
Portal. O valor e normalizado sem barra final nos settings.

Nenhuma chave deve ser enviada para o frontend, versionada em `.env.example` ou
impressa em logs.

## Remetente De Teste

O remetente atual `Portal Verbo da Vida <onboarding@resend.dev>` e provisório
para validar a integracao. Enquanto um dominio proprio nao estiver verificado
no Resend, as restricoes de remetente/destinatario do ambiente de teste devem
ser respeitadas.

Nao criar workaround para contornar essas restricoes.

## Comando De Teste

Depois do deploy e revisao das variaveis no Railway:

```bash
python manage.py send_test_email destinatario@example.com
```

Saida esperada:

```text
Email enviado com sucesso.
Provider: resend
Message ID: <id>
```

O comando imprime apenas dados seguros. Em falha de configuracao ou entrega, ele
retorna `CommandError` com mensagem clara.

## Testes Automatizados

Os testes usam mocks/fakes e nao fazem chamadas reais ao Resend.

Nesta etapa nenhum fluxo funcional envia e-mail automaticamente. Aprovacao de
solicitacao, ativacao de conta, recuperacao de senha e escalas continuam fora
do escopo ate as proximas PVVs.
