# ADR-0014: Paginação com Tokens Opacos (DynamoDB)

**Status**: Aceito

**Data**: 2025-01-01

**Decisores**: Equipe Intelicity

**Tags**: paginação, dynamodb, api, performance

## Contexto

Listagens de formulários e templates podem retornar grandes volumes de dados. Precisávamos de paginação que:

- Funcione nativamente com DynamoDB (cursor-based, não offset-based)
- Seja eficiente em qualquer volume de dados
- Não exponha detalhes internos do DynamoDB (chaves de partição/sort) ao cliente
- Suporte filtros combinados (status, sistema, data de criação, busca textual)

## Decisão

Adotamos **paginação cursor-based com tokens opacos** usando o `ExclusiveStartKey` nativo do DynamoDB codificado em Base64.

**Fluxo:**
1. Cliente faz GET com `limit` (itens por página)
2. Backend faz Query no DynamoDB com `Limit=limit`
3. DynamoDB retorna `LastEvaluatedKey` se houver mais páginas
4. Backend codifica `LastEvaluatedKey` em Base64 → `next_token`
5. Cliente envia `next_token` na próxima request → `exclusive_start_key`
6. Backend decodifica e passa como `ExclusiveStartKey` ao DynamoDB

**Implementação:**
```python
# Encoding (repository → response)
if response.get("LastEvaluatedKey"):
    next_token = base64.b64encode(json.dumps(response["LastEvaluatedKey"]).encode()).decode()

# Decoding (request → repository)
if exclusive_start_key:
    start_key = json.loads(base64.b64decode(exclusive_start_key))
```

**Parâmetros de API:**
```
GET /forms?limit=20&exclusive_start_key={token}&status=IN_PROGRESS&system=GAIA
```

**Formato de resposta:**
```json
{
    "forms": [...],
    "last_form_id": "abc-123"   // token para próxima página (ou null)
}
```

**Filtros suportados:**
- `status` — Filtra por FORM_STATUS
- `system` — Filtra por sistema (GAIA, SGC, etc.)
- `created_at_start` / `created_at_end` — Range de data de criação
- `search` — Busca textual (título do formulário)
- `user_id` — Formulários de um usuário específico

**Validação:**
- Token inválido → `InvalidPaginationToken` → 400 Bad Request
- Token decodifica para JSON que não é um dict válido → erro tratado

## Consequências

### Positivas
- Paginação nativa do DynamoDB — performance O(1) independente do offset
- Tokens opacos não expõem estrutura interna das chaves DynamoDB
- Sem contagem total (COUNT) — operação cara no DynamoDB é evitada
- Funciona com qualquer GSI sem modificação
- Base64 é URL-safe e compacto

### Negativas
- Sem "pular para página N" — navegação é sempre sequencial (próxima/anterior)
- Sem contagem total de resultados — frontend não sabe quantas páginas existem
- Tokens são stateless mas vinculados ao query — mudar filtros invalida o token
- Base64 do DynamoDB key pode ser grande para GSIs com muitos atributos

## Alternativas Consideradas

### Paginação offset-based (skip/take)
- **Descrição**: Usar page number e page size, calculando offset
- **Motivo da rejeição**: DynamoDB não suporta offset nativo — teria que ler e descartar N itens; ineficiente em escala; inconsistente se dados mudam entre páginas

### Paginação por timestamp
- **Descrição**: Usar `created_at < last_seen_created_at` como cursor
- **Motivo da rejeição**: Timestamps não são únicos — formulários criados no mesmo millisegundo seriam perdidos; DynamoDB `ExclusiveStartKey` já resolve isso corretamente
