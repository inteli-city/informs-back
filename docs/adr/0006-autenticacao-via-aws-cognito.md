# ADR-0006: Autenticação e Autorização via AWS Cognito

**Status**: Aceito

**Data**: 2025-01-01

**Decisores**: Equipe Intelicity

**Tags**: autenticação, cognito, aws, jwt, autorização, segurança

## Contexto

O sistema precisa autenticar e autorizar usuários que acessam a API de formulários. A plataforma Intelicity já utiliza AWS Cognito como Identity Provider centralizado para todos os microserviços. Precisávamos de:

- Autenticação stateless via JWT
- Autorização baseada em grupos (qual sistema o usuário pode acessar)
- Identificação do usuário em cada request (nome, email, sub)
- Compatibilidade com o padrão de autenticação já estabelecido nos demais microserviços

## Decisão

Utilizamos **AWS Cognito** integrado ao API Gateway como autorizador, com extração de claims no Presenter de cada módulo.

**Fluxo de autenticação:**
1. Cliente obtém `id_token` via login no Cognito
2. Cliente envia requests com header `Authorization: Bearer {id_token}`
3. API Gateway valida o JWT via Cognito Authorizer
4. Claims são injetados em `event.requestContext.authorizer.claims`
5. Presenter extrai claims e injeta como `requester_user` no payload

**Claims utilizados:**
- `sub` — UUID do usuário no Cognito (identificador único)
- `name` — Nome do usuário
- `email` — Email do usuário
- `cognito:groups` — Lista de grupos (sistemas e permissões)

**Esquema de grupos Cognito:**
- Cada usuário pertence a um ou mais grupos que representam sistemas: `GAIA`, `SGC`, `GEOVISTA`, `INTELIFLEETS`, `FORMULARIOS`
- O grupo `FORMULARIOS` concede acesso ao microserviço
- Os demais grupos determinam quais sistemas o usuário pode operar

**RequesterUserSchema (Pydantic):**
```python
class RequesterUserSchema(RequestContractModel):
    sub: str
    name: str
    email: str
    cognito_groups: str = Field(
        validation_alias=AliasChoices("cognito:groups", "cognito_groups"),
        serialization_alias="cognito:groups",
    )
```

**Extração no Presenter:**
```python
httpRequest.data['requester_user'] = event.get('requestContext', {}).get('authorizer', {}).get('claims', None)
```

**Uso no Controller:**
```python
requester_user = UserGatewayDTO.from_api_gateway(payload.requester_user.model_dump(by_alias=True))
# requester_user.user_id → usado como created_by
# requester_user.systems → usado para filtrar formulários por sistema
```

## Consequências

### Positivas
- Autenticação stateless — sem sessões no servidor, ideal para Lambda
- Validação de JWT feita pelo API Gateway antes de chegar no Lambda — reduz invocações inválidas
- Padrão consistente com os demais microserviços da plataforma
- Grupos Cognito permitem autorização granular por sistema sem banco adicional
- `AliasChoices` no Pydantic resolve a incompatibilidade do `:` nos nomes de campo

### Negativas
- Dependência do AWS Cognito — vendor lock-in para autenticação
- `cognito:groups` vem como string (não array) em certos contextos — requer parsing
- Claims no JWT são imutáveis até o próximo login — alterações de grupo não são imediatas
- Testes locais requerem mock do authorizer ou token authorizer local

## Alternativas Consideradas

### Auth0
- **Descrição**: Identity Provider SaaS com suporte multi-cloud
- **Motivo da rejeição**: Custo adicional de licenciamento; integração com API Gateway menos nativa que Cognito; organização já padronizou em Cognito

### JWT custom (sem Cognito)
- **Descrição**: Implementar geração e validação de JWT próprios
- **Motivo da rejeição**: Reinventar a roda — Cognito já fornece user pool, MFA, rotação de keys, e integração nativa com API Gateway
