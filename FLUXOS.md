# Fluxos Principais e Mockups Estruturais

Este documento descreve os fluxos atuais e desejados do Portal Verbo JSP em formato textual. Nao representa implementacao nova; serve como guia de produto, arquitetura e UX.

## Fluxo: cadastro de usuario

Objetivo: permitir que uma pessoa crie login e acesse a area basica.

Passos:

1. Pessoa acessa `usuarios/registro/`.
2. Preenche nome, sobrenome, e-mail, telefone, usuario e senha.
3. Sistema cria `Usuario`.
4. Novo usuario nasce como visitante.
5. Sistema autentica e redireciona para dashboard.
6. Visitante pode completar perfil, cadastrar criancas e acompanhar interacoes basicas.

Regras:

- Cadastro publico nao deve criar membro oficial.
- Visitante nao deve montar escala nem gerenciar departamentos.
- Visitante pode acessar area basica e funcionalidades permitidas ao responsavel.

## Fluxo: visitante virando membro

Objetivo: Secretaria qualificar uma pessoa apos discipulado.

Passos:

1. Secretaria acessa `usuarios/conteudo/secretaria/pessoas/`.
2. Lista visitantes ativos.
3. Localiza pessoa por nome, usuario ou e-mail.
4. Marca discipulado concluido.
5. Informa data de conclusao, quando necessario.
6. Promove para membro.
7. Sistema registra:
   - `status_eclesiastico=membro`
   - `discipulado_concluido=True`
   - `discipulado_concluido_em`
   - `qualificado_por`
   - `qualificado_em`

Regras:

- Secretaria ou pastor podem qualificar conforme regra de acesso.
- Historico de qualificacao deve ser preservado.
- Futuramente, ideal registrar log de mudancas.

## Fluxo: membro entrando em departamento

Objetivo: vincular um membro a um departamento com papel especifico.

Passos:

1. Lider do departamento acessa membros do departamento.
2. Seleciona usuario qualificado como membro.
3. Define papel: liderado, auxiliar, voluntario, lider.
4. Define ativo e data de entrada.
5. Sistema cria `DepartamentoMembro`.

Regras:

- Um usuario pode estar em varios departamentos.
- Pode ser lider em um e voluntario/liderado em outro.
- Deve existir no maximo um vinculo ativo por usuario/departamento.

## Fluxo: lider montando escala

Objetivo: lider criar escala do departamento que lidera.

Passos:

1. Lider acessa `usuarios/departamentos/escalas/`.
2. Sistema lista apenas departamentos gerenciaveis pelo usuario.
3. Lider cria escala com departamento, culto padrao ou data/horario manual.
4. Lider acessa itens da escala.
5. Sistema lista participantes ativos daquele departamento.
6. Lider adiciona membro e funcao.
7. Sistema valida:
   - participante ativo;
   - mesmo departamento da escala;
   - conflito de horario;
   - indisponibilidade.

Regras:

- Lider monta apenas escala do departamento em que e lider.
- Pastor e superuser tem acesso amplo.
- Visitante nao deve ser escalado.

## Fluxo: ministro sendo escalado

Objetivo: escalar ministro, especialmente no Verbo no Lar.

Passos:

1. Secretaria/lider autorizado cadastra ministro.
2. Se ministro for da casa, vincula `Ministro.usuario`.
3. Cadastro e aprovado/atualizado.
4. No Verbo no Lar, responsavel autorizado cria escala.
5. Seleciona ministro ativo/aprovado.
6. Sistema registra `EscalaVerboNoLar`.

Regras:

- Ministro nao precisa ser lider de departamento.
- Ministro pode ser externo sem usuario vinculado.
- Usuario vinculado a ministro aprovado deve ser reconhecido como ministro.

## Fluxo: Verbo no Lar

Objetivo: gerenciar casas, participantes, escalas, materiais e relatorios.

Passos:

1. Usuario autorizado acessa modulo Verbo no Lar.
2. Lista casas.
3. Cria/edita casa com responsavel e anfitriao.
4. Gerencia participantes.
5. Agenda ministro em escala da casa.
6. Vincula materiais de apoio.
7. Registra relatorio do encontro.

Regras:

- Secretaria/pastor gerenciam globalmente.
- Responsavel/anfitriao operam casa especifica.
- Ministro escalado aparece no contexto ministerial.

## Fluxo: Departamento Infantil

Objetivo: gerenciar salas, equipe, criancas, aulas e chamadas.

Passos:

1. Responsavel cadastra crianca em `minhas criancas`.
2. Equipe infantil revisa cadastro.
3. Crianca aprovada e vinculada a sala.
4. Lider infantil gerencia sala, equipe, aulas e criancas.
5. Durante culto, equipe cria chamada de responsavel.
6. Midia visualiza chamadas pendentes.
7. Chamada e marcada como exibida.
8. Sala resolve ou reabre chamada.

Regras:

- Responsavel ve apenas suas criancas.
- Lider de sala gerencia criancas/aulas da sala.
- Lider do departamento Infantil tem visao ampla.
- Midia opera exibicao, nao resolve atendimento pastoral.

## Fluxo: Dizimos e Ofertas

Objetivo: permitir contribuicoes via Mercado Pago.

Passos:

1. Usuario logado acessa `financeiro/contribuir/`.
2. Seleciona tipo: dizimo, oferta, missoes ou campanha.
3. Informa valor e descricao opcional.
4. Sistema cria `Contribuicao` pendente.
5. Sistema cria preferencia no Mercado Pago.
6. Usuario e redirecionado para pagamento.
7. Mercado Pago chama webhook.
8. Sistema consulta pagamento e atualiza status.
9. Admin financeiro acompanha lista de contribuicoes.

Regras:

- Access token nao deve ir para frontend.
- Webhook e publico, mas deve validar assinatura.
- Valores usam `DecimalField`.
- Falhas de webhook devem ser rastreaveis por log.

## Fluxo: Chamado Infantil para Midia

Objetivo: permitir que a equipe infantil chame responsavel pelo painel de midia.

Passos:

1. Equipe da sala cria `ChamadaResponsavel`.
2. Chamada fica pendente.
3. Painel de Midia consulta chamadas pendentes.
4. Midia marca como exibida.
5. Equipe da sala marca como resolvida.
6. Se necessario, equipe reabre/reenvia chamada.

Regras:

- Midia ve chamadas pendentes.
- Equipe infantil resolve atendimento.
- Status da chamada deve impedir acoes fora de ordem.

---

# Mockups estruturais

Os mockups abaixo sao esquemas de informacao, nao layout final.

## Dashboard

```text
+------------------------------------------------------+
| Header publico                                       |
+----------------------+-------------------------------+
| Sidebar usuario      | Ola, Nome                     |
| - Painel             | [Perfil 80%] [Membro/Visit.] |
| - Meu perfil         | [Departamentos] [Escalas]    |
| - Contribuir         |                               |
| - Minhas criancas    | Proximas acoes                |
| - Minhas inscricoes  | - Completar perfil           |
| - Escalas            | - Ver agenda                 |
| - Departamentos      |                               |
| - Infantil           | Meus departamentos            |
| - Secretaria         | Minhas escalas                |
| - Eventos            | Proximos eventos              |
| - Ministros          | Noticias recentes             |
| - Verbo no Lar       | Mensagens                     |
| - Financeiro         |                               |
+----------------------+-------------------------------+
```

## Gestao de usuarios

```text
+------------------------------------------------------+
| Gestao de Pessoas                                    |
| [Buscar nome/email] [Status] [Perfil] [Filtrar]      |
+------------------------------------------------------+
| Pessoa | Status | Discipulado | Perfis | Acoes       |
| Ana    | Visit. | Pendente    | -      | Ver/Qualif. |
| Joao   | Membro | Concluido   | Lider  | Ver         |
| Maria  | Membro | Concluido   | Pastor | Ver         |
+------------------------------------------------------+
| Painel lateral/detalhe                               |
| - Dados pessoais                                     |
| - Status eclesiastico                                |
| - Vinculos departamentais                            |
| - Perfil ministerial                                 |
| - Historico de qualificacao                          |
+------------------------------------------------------+
```

## Gestao de permissoes

```text
+------------------------------------------------------+
| Matriz de Acessos                                    |
| [Usuario/Grupo] [Modulo] [Departamento]              |
+------------------------------------------------------+
| Regra                         | Origem | Resultado   |
| Pastor                        | Usuario| Acesso total|
| Lider Louvor                  | Vinculo| Escalas     |
| Secretaria                    | Depto  | Conteudo    |
| Ministro aprovado             | Perfil | Verbo Lar   |
+------------------------------------------------------+
| Simulador: usuario X tentando acessar modulo Y       |
| Resultado: permitido/negado + motivo                 |
+------------------------------------------------------+
```

## Escalas

```text
+------------------------------------------------------+
| Escalas                                              |
| [Departamento] [Status] [Periodo] [Filtrar]          |
| [Nova escala] [Gerar mes] [Cultos padrao]            |
+------------------------------------------------------+
| Titulo | Departamento | Data | Horario | Pessoas     |
| Culto  | Louvor       | ...  | ...     | 8           |
+------------------------------------------------------+
| Itens da escala                                      |
| [Membro] [Funcao] [Confirmado] [Adicionar]           |
| Indisponiveis na data                                |
| Lista de pessoas escaladas                           |
+------------------------------------------------------+
```

## Departamento Infantil

```text
+------------------------------------------------------+
| Infantil                                             |
| [Salas] [Cadastros pendentes] [Chamadas]             |
+------------------------------------------------------+
| Sala | Faixa etaria | Equipe | Criancas | Acoes      |
+------------------------------------------------------+
| Detalhe da sala                                      |
| - Equipe                                             |
| - Criancas                                           |
| - Aulas                                              |
| - Chamadas                                           |
+------------------------------------------------------+
| Chamada de responsavel                               |
| Crianca | Responsavel | Status | Acoes               |
+------------------------------------------------------+
```

## Verbo no Lar

```text
+------------------------------------------------------+
| Verbo no Lar                                         |
| [Casas] [Escalas] [Materiais] [Relatorios]           |
+------------------------------------------------------+
| Casa | Responsavel | Dia | Bairro | Status | Acoes   |
+------------------------------------------------------+
| Detalhe da casa                                      |
| - Dados e endereco                                   |
| - Participantes                                      |
| - Proximas escalas                                   |
| - Materiais                                          |
| - Relatorios recentes                                |
+------------------------------------------------------+
```

## Financeiro / Dizimos e Ofertas

```text
+------------------------------------------------------+
| Nova Contribuicao                                    |
| Tipo: [Dizimo/Oferta/Missoes/Campanha]               |
| Valor: [R$ 0,00]                                     |
| Descricao: [opcional]                                |
| [Contribuir]                                         |
+------------------------------------------------------+
| Area administrativa                                  |
| [Tipo] [Status] [Periodo] [Filtrar]                  |
| Usuario | Valor | Tipo | Status | Data               |
+------------------------------------------------------+
```

## Configuracoes do Mercado Pago

```text
+------------------------------------------------------+
| Configuracoes Financeiras                            |
| Ambiente: [Teste/Producao]                           |
| Access token: [********]                             |
| Public key: [texto]                                  |
| Segredo webhook: [********]                          |
| Webhook URL: [url]                                   |
| Status: Conectado/Nao conectado                      |
| Ultima verificacao: data/hora                        |
| Mensagem: retorno da API                             |
| [Salvar] [Testar conexao]                            |
+------------------------------------------------------+
```

## Tela de teste de conexao

```text
+------------------------------------------------------+
| Teste de Integracao                                  |
| Provedor: Mercado Pago                               |
| Ambiente: Teste/Producao                             |
| Credenciais: token configurado? sim/nao              |
| Webhook: segredo configurado? sim/nao                |
| [Executar teste]                                     |
+------------------------------------------------------+
| Resultado                                            |
| - Status HTTP/API                                    |
| - Conta identificada                                 |
| - Horario do teste                                   |
| - Proximas acoes sugeridas                           |
+------------------------------------------------------+
```

## Relatorios

```text
+------------------------------------------------------+
| Relatorios                                           |
| [Modulo] [Periodo] [Departamento] [Exportar]         |
+------------------------------------------------------+
| Cards                                                |
| - Membros por status                                 |
| - Escalas realizadas                                 |
| - Criancas cadastradas                               |
| - Contribuicoes aprovadas                            |
| - Encontros Verbo no Lar                             |
+------------------------------------------------------+
| Tabela detalhada                                     |
| Data | Modulo | Indicador | Valor | Observacao       |
+------------------------------------------------------+
```

## Proximos fluxos recomendados para documentar

- Auditoria de alteracoes sensiveis.
- Ciclo de vida de ministro externo.
- Cancelamento/reembolso de contribuicao.
- Arquivamento/inativacao de membro.
- Transferencia de lideranca departamental.
- Relatorios pastorais consolidados.
