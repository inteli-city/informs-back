# ADR-0016: RBAC com Profile em tabela DynamoDB separada do Cognito

**Status**: Aceito

**Data**: 2026-05-12

**Decisores**: Equipe Intelicity

**Tags**: profile, rbac, cognito, dynamodb, autorização, autenticação

## Contexto

Até agora a única forma de "perfil" no Informs era o grupo `FORMULARIOS` no Cognito — qualquer usuário com esse grupo tinha o mesmo nível de acesso a todas as operações (criar/cancelar/submeter formulários, etc.).

Com a evolução do produto, surgiu a necessidade de distinguir dois papéis:
- Quem **gerencia** quem usa o sistema (cadastrar e desativar usuários)
- Quem **opera** o sistema no campo (recebe e preenche formulários)

Essa separação é RBAC clássico. As opções consideradas para implementar:

1. **Cognito groups novos** — criar `ADMIN` e `INSPECTOR` no User Pool. Lê do JWT.
2. **Cognito custom claims** — atributo `role` no atributo customizado do Cognito.
3. **DynamoDB próprio** — tabela tabela de Profiles (auto-gerada pela FormulariosStack) independente.

A escolha precisava considerar:
- Velocidade pra alterar a role de um usuário (sem precisar recadastrar no Cognito)
- Capacidade de armazenar metadados aplicacionais (placa de moto, sistema operado)
- Acoplamento com a infra do Cognito (compartilhada com outros microsserviços)
- Facilidade de evolução (adicionar novos perfis no futuro)

## Decisão

Adotamos a opção **(3) — tabela DynamoDB própria**, separando claramente:

- **Cognito** = Identity Provider (autentica e diz "esse user existe")
- **Profile na DynamoDB** = Authorization & Identity (diz "esse user é quem, com qual role")

### Estrutura da tabela tabela de Profiles (auto-gerada pela FormulariosStack)

```
PK = user#{user_id}     (user_id é o Cognito sub)
SK = METADATA

Atributos:
  user_id, role, name, email, system, vehicle_plate?, active,
  created_at, updated_at
  GSI1PK = role#{role}
  GSI1SK = system#{system}#user#{user_id}
```

GSI `ByRole` é usado hoje para contar admins ativos antes de permitir DELETE (impede remoção do último admin) e no futuro para listagens por role/sistema.

### Roles iniciais

- **ADMIN** — pode criar e desativar perfis. Demais permissões aplicacionais (criar formulários, etc.) seguem disponíveis como qualquer outro usuário.
- **INSPECTOR** — usuário de campo (motoverificador). Recebe e preenche formulários. Não pode gerenciar perfis.

### Endpoints v1

| Método | Path | Quem pode | Comportamento |
|--------|------|-----------|---------------|
| POST | `/profiles` | ADMIN ativo | Cria ADMIN ou INSPECTOR. Body com `user_id`, `role`, `name`, `email`, `system`, `vehicle_plate?` |
| POST | `/profiles/login` | Qualquer Cognito user com grupo `FORMULARIOS` | Retorna o profile do requester. Se não existir, **auto-cria como INSPECTOR** usando dados do JWT (`name`, `email`, primeiro grupo ≠ `FORMULARIOS` como `system`). Devolve flag `just_created`. |
| DELETE | `/profiles/{user_id}` | ADMIN ativo | Soft delete (`active=false`). Bloqueia self-delete e a remoção do último admin ativo. |

### Bootstrap do primeiro ADMIN

Como admin cria os outros, o primeiro admin é **inserido manualmente via AWS CLI** após o deploy criar a tabela. Sem seeder automático (decisão consciente: poucos admins, controle explícito sobre quem entra). UPDATE de role chega em PR futuro.

### Auto-create no login (escolha consciente)

Inicialmente avaliamos forçar pré-cadastro (admin tem que criar antes do primeiro login), mas como o User Pool é restrito a pessoas conhecidas da organização, optamos pelo auto-create como INSPECTOR. Vantagens:
- Frontend não precisa lidar com 404 pré-cadastro no fluxo de onboarding
- Admin não precisa cadastrar manualmente cada inspector — basta liberar o acesso ao Cognito
- Se acidentalmente alguém indesejado entrar no Cognito, ainda assim vira só INSPECTOR (não ADMIN), e admin pode desativar

Risco: se o User Pool for vazado ou aberto inadvertidamente, qualquer um vira INSPECTOR. Mitigação: o controle continua sendo do User Pool (gestão da Intelicity).

### Soft delete (sem UPDATE no v1)

Como UPDATE não está no escopo deste PR, o `active=false` por enquanto só pode ser **setado** (via DELETE) e não revertido (não há "reativar"). Se virar problema operacional, basta editar o item via console DynamoDB ou aguardar o PR de UPDATE. Optamos por não criar um PUT só pra reativar agora pra manter o escopo enxuto.

### Why DynamoDB e não Cognito groups

| Critério | Cognito groups | DynamoDB Profile |
|----------|----------------|-------------------|
| Mudar role de um user | Requer chamada admin no Cognito (lento, restrito) | UPDATE simples na tabela |
| Armazenar metadados (placa, system) | Não suportado nativamente | Suportado |
| Coupling com infra de auth compartilhada | Alto (afeta outros microsserviços) | Zero |
| Histórico de perfis (soft delete) | Difícil | Trivial |
| Custo extra | $0 | ~$0 (DynamoDB on-demand, baixo volume) |

## Consequências

### Positivas
- Identidade e autenticação ficam no Cognito (responsabilidade certa)
- Autorização e metadados aplicacionais ficam no Informs (controle local)
- Cada lambda valida a role lendo o Profile (1 GetItem por request — cache não necessário no volume atual)
- Tabela isolada de `formularios-table` — não compete por throughput nem capacity
- Soft delete preserva integridade referencial com forms que apontam pro user

### Negativas
- Toda lambda que precisa validar role faz 1 GetItem extra por chamada (overhead pequeno, mas presente)
- Bootstrap do primeiro admin é manual — esperado, mas requer documentação para times novos
- Sem UPDATE neste PR: para alterar nome/placa/system de um inspector, é necessário deletar e recriar (workaround feio até PR de UPDATE chegar)
- Auto-create no login significa que `Profile.create` pode falhar com `DuplicatedItem` em corridas (dois logins simultâneos do mesmo user) — tratado retornando 409, cliente pode retry

## Alternativas Consideradas

### Cognito groups (`ADMIN`, `INSPECTOR`)
- **Descrição**: Adicionar grupos novos no User Pool e ler `cognito:groups` no JWT.
- **Motivo da rejeição**: Cognito é compartilhado com outros microsserviços; criar grupos do domínio Informs poluiria a estrutura comum. Mudar role exige chamada admin (lenta) e não armazena metadados aplicacionais (placa, sistema).

### Custom claims no Cognito
- **Descrição**: Atributo `custom:role` no perfil do usuário no User Pool.
- **Motivo da rejeição**: Mesma limitação do anterior — custom attributes são limitados (50 por pool) e não dá pra armazenar listas/objetos complexos. Alterar requer chamada admin.

### Single-table design (na `formularios-table`)
- **Descrição**: Reaproveitar a tabela existente com PK=`profile#{user_id}`.
- **Motivo da rejeição**: Profile e Form têm padrões de acesso muito diferentes (volume, frequência de leitura). Separar evita hot partition e simplifica permissões IAM granulares.
