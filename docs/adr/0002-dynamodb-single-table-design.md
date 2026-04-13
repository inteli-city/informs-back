# ADR-0002: DynamoDB Single-Table Design

**Status**: Aceito

**Data**: 2025-01-01

**Decisores**: Equipe Intelicity

**Tags**: banco-de-dados, dynamodb, aws, single-table, nosql

## Contexto

O sistema precisa persistir formulários, templates, estados de sincronização e erros de sincronização. Precisávamos de um banco de dados que:

- Escale automaticamente com a demanda (serverless-friendly)
- Suporte acesso por múltiplas chaves (user_id, form_id, system, status)
- Tenha latência previsível em qualquer escala
- Minimize custos operacionais (sem gerenciamento de instâncias)

## Decisão

Adotamos **DynamoDB com Single-Table Design** usando uma tabela principal (`formularios-table`) com chaves compostas e dois Global Secondary Indexes (GSIs).

**Esquema de chaves:**

| Entidade | PK | SK |
|----------|-----|-----|
| Form | `form#{form_id}` | `METADATA` |
| Form (por usuário) | `user#{user_id}` | `form#{form_id}` |
| Template | `template#{template_id}` | `METADATA` |
| SyncState | `sync_state#{job_name}#{system}` | `METADATA` |
| SyncErrorForm | `sync_error#{job_name}#{system}` | `form#{form_id}` |

**GSI1 (consulta por usuário com filtros):**
- PK: `user#{user_id}`
- SK: `priority#{priority}#status#{status}#created_at#{created_at}`

**GSI2 (consulta por sistema para sincronização):**
- PK: `system#{system}`
- SK: `updated_at#{padded_int}#form#{form_id}`

**Padrões de acesso suportados:**
- Buscar formulário por ID → Query PK=`form#{id}`, SK=`METADATA`
- Listar formulários de um usuário → Query GSI1 PK=`user#{user_id}` com filtros
- Buscar formulários por sistema (sync) → Query GSI2 PK=`system#{sys}` com range de updated_at
- Buscar template por ID → Query PK=`template#{id}`
- Buscar estado de sync → Query PK=`sync_state#{job}#{system}`

**Tratamentos especiais:**
- Conversão automática de `float` ↔ `Decimal` (DynamoDB não suporta float nativamente)
- Escape de palavras reservadas via `ExpressionAttributeNames`
- Billing mode: `PAY_PER_REQUEST` (on-demand)

## Consequências

### Positivas
- Zero administração de infraestrutura de banco — totalmente gerenciado pela AWS
- Escala automática sem provisionamento de capacidade
- Latência de single-digit milliseconds independente do volume de dados
- Custo proporcional ao uso real (pay-per-request)
- GSIs permitem queries eficientes sem scans completos

### Negativas
- Queries complexas com múltiplos filtros podem requerer FilterExpression (menos eficiente)
- Modelagem Single-Table exige planejamento antecipado dos access patterns
- Sem suporte nativo a joins — relações devem ser resolvidas na aplicação
- Transações limitadas a 25 itens por operação
- Migração de schema requer scripts custom (sem framework de migration)

## Alternativas Consideradas

### PostgreSQL (RDS/Aurora)
- **Descrição**: Banco relacional gerenciado com suporte a queries complexas e joins
- **Motivo da rejeição**: Custo fixo de instância (não ideal para workloads serverless com tráfego variável); necessidade de gerenciar conexões em Lambda (connection pooling); não aproveita o modelo pay-per-request

### MongoDB (DocumentDB/Atlas)
- **Descrição**: Banco de documentos com schema flexível
- **Motivo da rejeição**: Custo de instância similar ao RDS; DynamoDB oferece integração nativa mais profunda com o ecossistema AWS (IAM, CloudWatch, EventBridge)
