# Church Journey Compatibility Foundation

Esta camada existe para centralizar leituras da jornada eclesiastica sem alterar
o comportamento legado atual.

Hoje, a fonte de verdade continua sendo `usuarios.Usuario`:

- `Usuario.status_eclesiastico`
- `Usuario.discipulado_concluido`
- `Usuario.discipulado_concluido_em`
- `Usuario.eh_pastor`
- `Usuario.is_superuser`

Consumidores novos devem preferir consultar `church_journey.selectors` a partir
de `pessoas.Person`. Isso preserva a distincao entre `Person.status`, que
representa cadastro/identidade, e `ChurchStatus`, que representa a situacao
eclesiastica legada.

## ChurchStatus

`ChurchStatus` e um enum interno, nao persistido no banco:

- `VISITOR`: `Usuario.status_eclesiastico == "visitante"`
- `MEMBER`: `Usuario.status_eclesiastico == "membro"`
- `UNKNOWN`: `Person` sem `Usuario` vinculado ou estado legado desconhecido

Uma `Person` sem `Usuario` nao deve ser tratada automaticamente como membro nem
como visitante. Ela retorna `UNKNOWN`.

## Selectors Disponiveis

- `get_church_status(person)`
- `is_member(person)`
- `is_visitor(person)`
- `has_completed_discipleship(person)`
- `get_discipleship_completed_at(person)`
- `is_legacy_department_eligible(person)`

Tambem existem helpers transitorios para os pontos que ainda recebem
`Usuario`, como permissoes legadas e querysets de formularios:

- `get_church_status_for_user_account(usuario)`
- `is_legacy_department_eligible_for_user_account(usuario)`
- `get_legacy_department_eligible_user_filter(prefix="")`

Esses helpers sao compatibilidade, nao a API final do novo dominio.

## Excecoes Legadas

Na regra legada de departamentos, uma pessoa pode ser elegivel por ser membro,
pastor ou superuser. Pastor e superuser nao sao `ChurchStatus`; eles entram
apenas como excecoes da elegibilidade departamental existente.

## Plano Futuro

Na v1, os selectors leem de `Usuario`.

Na v2, os mesmos selectors poderao ler de modelos futuros como `Membership` e
`Discipleship`, sem obrigar consumidores como Departamentos e Escalas a conhecer
os detalhes da nova persistencia.

Esta feature nao cria `Membership`, `Discipleship`, `Visitor`, dual write,
migration de dados ou novas telas.
