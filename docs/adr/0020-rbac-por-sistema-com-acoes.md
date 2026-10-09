# ADR-0020: RBAC por sistema, com roles montados a partir de um catálogo de ações

**Status**: Proposto

**Data**: 2026-10-09

**Decisores**: Equipe Intelicity

**Tags**: profile, rbac, dynamodb, autorização, sistemas

## Contexto

A ADR-0016 criou o `Profile` com um único `role` global (ADMIN, INSPECTOR e depois MANAGER/SUPERVISOR). Com vários sistemas no Informs, isso deixou de servir:

- o role valia para todos os sistemas da pessoa: quem é gestor em um sistema virava gestor em todos;
- um ADMIN de qualquer sistema tinha poder sobre todos os outros;
- os papéis eram fixos no código: cada sistema que precisasse de um papel diferente exigia deploy;
- `system`, `scope` e `vehicle_plate` ficavam no perfil sem uso real (o `system` era só o primeiro grupo do Cognito).

## Decisão

1. **Super admin** (`Profile.super_admin`): pode tudo em todo sistema e é o único que dá o role ADMIN de um sistema. Marcado à mão.
2. **Catálogo fixo de ações** (`Action`): `forms.view_all`, `forms.assign`, `forms.release`, `tracking.start`, `tracking.view`, `users.manage`, `roles.manage`. Ação nova só nasce no código.
3. **ADMIN** é o único role fixo: em um sistema, tem todas as ações.
4. **Roles de sistema** (`SystemRole`): cada sistema cria os seus, com nome e um subconjunto das ações. Um deles pode ser o padrão, dado a quem entra no sistema pela primeira vez.
5. **Vínculo** (`SystemMembership`): uma pessoa tem um role por sistema. O acesso ao sistema continua vindo do grupo do Cognito.
6. **Regra única** (`AccessControl.can(pessoa, sistema, ação)`): super admin, ou ADMIN no sistema, ou role do sistema com a ação.
7. **Sem escalada**: quem não é ADMIN do sistema só cria, edita ou dá roles com ações que ele mesmo tem.

Tudo fica na tabela de Profiles, reaproveitando o índice `ByRole` (GSI1):

| Item | PK | SK | GSI1PK | GSI1SK |
|---|---|---|---|---|
| Pessoa | `user#{id}` | `METADATA` | `super_admin` (só super admin) | `user#{id}` |
| Vínculo | `user#{id}` | `system#{system}` | `system#{system}` | `role#{role_id}#user#{id}` |
| Role | `system#{system}` | `role#{role_id}` | — | — |

Saem do perfil: `role`, `system`, `scope`, `vehicle_plate` e o `PUT /profiles/{user_id}`. Entram as rotas `/permissions/actions` e `/systems/{system}/roles|users`.

A migração dos dados é feita por `scripts/migrate_profiles_to_system_roles.py`.

## Consequências

### Positivas
- Permissão por sistema: a mesma pessoa pode ser gestora em um sistema e técnica em outro.
- Cada sistema define os próprios papéis sem deploy.
- Nenhum scan: login, permissão e listagens são queries por chave ou pelo GSI1.

### Negativas
- Toda checagem de permissão precisa do sistema; rotas sem sistema (histórico de localização, `ws_server`) usam "algum sistema em comum" ou "algum sistema".
- Uma checagem custa 2–3 leituras (perfil, vínculo, role).
- O `ws_server` replica a regra (é um deploy separado e não importa `src`).
- O escopo regional por atributos (especificação Uberlândia §7) sai; se voltar, entra por sistema.

## Alternativas Consideradas

### Mapa `roles: {sistema: role}` dentro do item da pessoa
- **Descrição**: um único item por pessoa.
- **Motivo da rejeição**: o DynamoDB não indexa chaves de um mapa; listar as pessoas de um sistema exigiria scan.

### Roles fixos por sistema (ADMIN/MANAGER/SUPERVISOR/INSPECTOR)
- **Descrição**: manter o enum, só que por sistema.
- **Motivo da rejeição**: cada sistema novo com necessidades diferentes exigiria mudar o código.
