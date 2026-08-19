# Portal Verbo da Vida JSP — Domínio de Pessoas e Membresia

**Versão:** 1.0  
**Data:** 18/08/2026  
**Status:** Definição inicial aprovada para orientar modelagem e desenvolvimento

## 1. Objetivo

Este documento formaliza as definições de domínio acordadas para a jornada de Pessoas do Portal Verbo da Vida JSP. Ele deve orientar a modelagem do backend Django, as APIs, o frontend React e as futuras jornadas de Discipulado, Membresia, Departamentos, Disponibilidade e Escalas.

O princípio central é separar a identidade da pessoa dos papéis e vínculos que ela pode assumir dentro da igreja.

## 2. Visão geral da jornada

```text
Person
├── Menor de 13 anos
│   └── Jornada Infantil
│       ├── ChildProfile
│       ├── GuardianRelationship
│       └── Infantil
│
└── A partir de 13 anos
    └── Visitor
        ↓
    Discipleship
        ↓
    Presença mínima atingida
        ↓
    Elegível para Membresia
        ↓
    Confirmação pela Secretaria
        ↓
    Membership ativa
        ↓
    DepartmentMembership
        ↓
    Critérios adicionais do departamento, quando existirem
        ↓
    Availability
        ↓
    Schedule
```

## 3. Pessoa (Person)

`Person` representa um ser humano conhecido pelo Portal, independentemente de ser criança, visitante, membro, responsável, voluntário ou usuário do sistema.

### 3.1 Dados básicos previstos

- `id`
- `full_name`
- `preferred_name` — opcional
- `birth_date` — opcional no cadastro inicial
- `email` — opcional
- `phone` — opcional
- `status`
- `created_at`
- `updated_at`

Foto poderá ser adicionada futuramente conforme necessidade funcional.

### 3.2 Princípios

- Pessoa não é sinônimo de Membro.
- Pessoa não é sinônimo de Usuário do sistema.
- Dados de membresia, departamento, disponibilidade, discipulado e escala não devem ser armazenados diretamente em `Person`.
- Não devem ser criados campos booleanos como `is_member`, `is_teacher` ou `discipleship_completed` para representar conceitos que possuem ciclo de vida próprio.
- O nome preferido, quando informado, deve ser utilizado para exibição; caso contrário, utiliza-se o nome completo.
- Dados pessoais só devem ser armazenados quando houver necessidade funcional clara.

### 3.3 Duplicidade

**PER-001 — Detecção de possível duplicidade**  
O Portal deve utilizar a combinação **Nome + Data de Nascimento** para identificar possíveis cadastros duplicados de Pessoa.

A detecção de duplicidade deve, inicialmente, funcionar como proteção de cadastro e não necessariamente como uma restrição absoluta de banco sem análise dos casos reais.

## 4. Jornada Infantil

Uma criança também é uma `Person`. Informações específicas da jornada infantil devem ficar em estruturas próprias, sem duplicar os dados pessoais.

### 4.1 ChildProfile

`ChildProfile` representa informações específicas necessárias ao atendimento da criança no módulo Infantil.

Pode futuramente conter informações como:

- alergias;
- observações relevantes;
- informações necessárias ao atendimento infantil;
- autorizações específicas.

### 4.2 Responsáveis

O responsável também deve ser uma `Person`.

A relação entre responsável e criança deve ser representada por uma entidade própria, conceitualmente denominada `GuardianRelationship`.

Exemplo:

```text
Maria (Person)
    ↓ mãe de
João (Person + ChildProfile)
```

### 4.3 Regras da jornada infantil

**CHD-001 — Faixa infantil**  
Pessoa com idade inferior a 13 anos pertence à jornada Infantil.

**CHD-002 — Transição aos 13 anos**  
Ao completar 13 anos, a Pessoa deixa a jornada Infantil e passa automaticamente à condição de Visitante.

A idade limite deve ser centralizada como regra de domínio/configuração, evitando o valor `13` espalhado pelo código.

**CHD-003 — Independência da Membresia**  
Uma criança pode estar plenamente cadastrada no Portal, possuir perfil infantil e vínculos com responsáveis sem possuir Membresia.

## 5. Visitante

Visitante representa a condição da Pessoa que ainda não possui Membresia ativa e está apta a seguir a jornada de Discipulado.

A condição de Visitante não deve exigir uma segunda tabela contendo novamente nome, telefone, nascimento e demais dados já pertencentes a `Person`.

**VIS-001 — Visitante sem Discipulado**  
Uma Pessoa pode existir no Portal como Visitante sem ter iniciado ou concluído o Discipulado.

**VIS-002 — Transição infantil**  
Uma Pessoa que completa 13 anos passa automaticamente à condição de Visitante.

## 6. Discipulado

O Discipulado deve ser tratado como uma jornada própria e, futuramente, o Portal deverá controlar suas turmas.

A conclusão do Discipulado não deve ser representada apenas por um campo booleano em Pessoa.

### 6.1 Estruturas previstas

#### DiscipleshipClass

Representa uma turma de Discipulado.

Campos conceituais iniciais:

- `id`
- `name`
- `start_date`
- `end_date`
- `status`
- responsáveis/instrutores

#### DiscipleshipEnrollment

Representa a matrícula de uma Pessoa em uma turma.

Campos conceituais iniciais:

- `person`
- `class`
- `status`
- `enrolled_at`
- `completed_at`
- resultado/conclusão

### 6.2 Evolução futura

O módulo poderá posteriormente controlar:

- aulas/encontros da turma (`DiscipleshipSession`);
- datas e temas;
- presença por encontro (`Attendance`);
- percentual de frequência;
- critérios de conclusão.

### 6.3 Regras do Discipulado

**DSC-001 — Origem da conclusão**  
A conclusão do Discipulado deve ser derivada de uma matrícula concluída em uma Turma de Discipulado, e não de um simples campo booleano em Pessoa.

**DSC-002 — Presença mínima**  
A conclusão do Discipulado depende do cumprimento da presença mínima definida pela igreja.

O percentual mínimo ainda poderá ser parametrizado posteriormente.

**DSC-003 — Elegibilidade para Membresia**  
A conclusão do Discipulado torna a Pessoa elegível para Membresia, mas não a transforma automaticamente em Membro.

## 7. Membresia (Membership)

Membresia representa o vínculo formal da Pessoa como Membro da igreja.

Pessoa e Membresia são conceitos diferentes.

```text
Person
   ↓ opcionalmente possui
Membership
```

### 7.1 Estrutura conceitual inicial

- `id`
- `person`
- `status`
- `member_since`
- `approved_by`
- `approved_at`
- `created_at`
- `updated_at`

### 7.2 Regras da Membresia

**MEM-001 — Pré-requisito de Discipulado**  
Uma Pessoa somente poderá possuir Membresia ativa após concluir o Discipulado.

**MEM-002 — Não automatização**  
A conclusão do Discipulado apenas torna a Pessoa elegível para Membresia. A Membresia não deve ser ativada automaticamente.

**MEM-003 — Confirmação pela Secretaria**  
A ativação da Membresia deve ser confirmada por um usuário autorizado da Secretaria.

O sistema deve registrar quem realizou a confirmação e quando ela ocorreu.

**MEM-004 — Inativação com histórico**  
Uma Membresia pode ser inativada sem apagar a Pessoa, a Membresia ou seus registros históricos.

**MEM-005 — Reativação**  
Caso um ex-membro retorne, a Membresia existente deve ser reativada em vez de criar uma nova identidade de Membresia.

**MEM-006 — Histórico de status**  
Mudanças de situação da Membresia devem preservar histórico, permitindo reconstruir períodos de atividade e inatividade.

Exemplo:

```text
Membership — Pessoa X

2024-02-10 → ACTIVE
2025-08-03 → INACTIVE
2026-01-15 → ACTIVE
```

Uma estrutura como `MembershipStatusHistory` poderá ser utilizada para essa finalidade.

## 8. Departamentos

A participação em Departamento é um vínculo posterior à Membresia.

`Membership` e `DepartmentMembership` são conceitos diferentes.

Uma Pessoa pode ser Membro ativo sem participar de nenhum Departamento.

Uma Pessoa também poderá participar de mais de um Departamento, respeitando as regras aplicáveis.

### 8.1 Regras de Departamento

**DEP-001 — Membresia ativa**  
Somente uma Pessoa com Membresia ativa pode receber vínculo com Departamento.

**DEP-002 — Critérios adicionais**  
Departamentos podem possuir critérios adicionais de elegibilidade além da Membresia ativa.

Esses critérios não devem ser incorporados como campos específicos em `Person`.

Exemplos futuros de critérios:

- idade mínima;
- treinamento específico;
- aprovação de liderança;
- requisito próprio do ministério.

## 9. Disponibilidade e Escalas

Disponibilidade e Escala são etapas posteriores ao vínculo departamental.

Fluxo conceitual:

```text
Person
  ↓
Membership ativa
  ↓
DepartmentMembership
  ↓
Critérios do departamento atendidos
  ↓
Availability
  ↓
Schedule
```

Regras críticas de escala devem ser garantidas pelo backend Django. O frontend React pode orientar o usuário e antecipar mensagens, mas não deve ser a única camada responsável pela integridade das regras.

Princípio arquitetural:

> **Frontend orienta. Backend garante.**

## 10. Pessoa x Usuário do sistema

`Person` e conta de acesso (`User`) são conceitos distintos.

Uma Pessoa pode existir no Portal sem possuir login.

```text
Person
   ↓ opcionalmente associada a
User
```

Autenticação, senha e permissões pertencem ao domínio de identidade/acesso e não devem ser misturadas aos dados básicos de Pessoa.

## 11. Entidades conceituais identificadas

A modelagem técnica deverá avaliar as seguintes entidades:

```text
Person
ChildProfile
GuardianRelationship
DiscipleshipClass
DiscipleshipEnrollment
DiscipleshipSession        (evolução futura)
Attendance                 (evolução futura)
Membership
MembershipStatusHistory
Department
DepartmentMembership
Availability
Schedule
User / Identity
```

A presença nesta lista não significa que todas devam ser implementadas na primeira feature. O desenvolvimento deve permanecer incremental e evitar abstrações prematuras.

## 12. Resumo das regras formais

| Código | Regra |
|---|---|
| PER-001 | Possíveis duplicidades de Pessoa devem ser identificadas por Nome + Data de Nascimento. |
| CHD-001 | Pessoa com menos de 13 anos pertence à jornada Infantil. |
| CHD-002 | Ao completar 13 anos, a Pessoa passa automaticamente à condição de Visitante. |
| CHD-003 | A jornada Infantil é independente da Membresia. |
| VIS-001 | Uma Pessoa pode ser Visitante sem ter iniciado ou concluído o Discipulado. |
| VIS-002 | A transição da jornada Infantil aos 13 anos leva automaticamente à condição de Visitante. |
| DSC-001 | A conclusão do Discipulado deve decorrer de uma matrícula concluída em uma Turma. |
| DSC-002 | A conclusão do Discipulado depende do cumprimento da presença mínima. |
| DSC-003 | Concluir o Discipulado gera elegibilidade para Membresia, não Membresia automática. |
| MEM-001 | Membresia ativa exige Discipulado concluído. |
| MEM-002 | A Membresia não é ativada automaticamente após o Discipulado. |
| MEM-003 | A Secretaria deve confirmar a ativação da Membresia. |
| MEM-004 | Membresia pode ser inativada sem perda de histórico. |
| MEM-005 | O retorno de ex-membro reativa a Membresia existente. |
| MEM-006 | Alterações de status da Membresia devem manter histórico. |
| DEP-001 | Apenas Membro ativo pode receber vínculo com Departamento. |
| DEP-002 | Departamentos podem possuir critérios adicionais de elegibilidade. |

## 13. Decisões arquiteturais decorrentes

1. `Person` será a identidade central reutilizada pelas diferentes jornadas.
2. Não haverá duplicação de cadastro pessoal para Criança, Responsável, Visitante ou Membro.
3. Discipulado possuirá ciclo de vida próprio e será preparado para gestão futura de turmas e presenças.
4. Membresia possuirá aprovação explícita pela Secretaria e histórico de status.
5. Vínculo departamental será separado da Membresia.
6. Critérios específicos de departamentos não serão incorporados diretamente em `Person`.
7. Regras de domínio serão garantidas no backend Django, ainda que o React também ofereça validações e orientação de interface.
8. A implementação será incremental; entidades futuras não deverão ser implementadas antes de existir necessidade da feature correspondente.

## 14. Próximo passo recomendado

Transformar este domínio conceitual em uma proposta de modelagem Django, começando pelo menor conjunto necessário para a Jornada de Pessoas e preservando compatibilidade futura com:

```text
Pessoa
  ↓
Infantil / Visitante
  ↓
Discipulado
  ↓
Membresia
  ↓
Departamento
  ↓
Disponibilidade
  ↓
Escala
```

Antes de implementação, cada model deverá ter sua responsabilidade, relacionamentos, invariantes e ciclo de vida revisados.
