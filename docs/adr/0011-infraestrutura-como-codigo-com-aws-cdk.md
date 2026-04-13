# ADR-0011: Infraestrutura como Código com AWS CDK

**Status**: Aceito

**Data**: 2025-01-01

**Decisores**: Equipe Intelicity

**Tags**: infraestrutura, cdk, aws, iac, lambda, api-gateway, deploy

## Contexto

O microserviço precisa provisionar e gerenciar múltiplos recursos AWS (Lambda functions, API Gateway, DynamoDB, S3, IAM roles, CloudWatch). Precisávamos de:

- Definição de infraestrutura versionada e auditável (git)
- Deploy reprodutível entre ambientes (dev, homolog, prod)
- Tipagem e composição para evitar erros de configuração
- Alinhamento com o padrão já adotado nos demais microserviços Intelicity

## Decisão

Adotamos **AWS CDK (Cloud Development Kit)** com Python para definir toda a infraestrutura como código.

**Estrutura do IaC:**
```
iac/
├── app.py              # Entry point do CDK
├── iac_stack.py         # Stack principal (orquestrador)
├── lambda_stack.py      # Lambda functions + API Gateway
├── dynamo_stack.py      # Tabelas DynamoDB + GSIs
└── authorizers/
    ├── cognito_authorizer.py   # Authorizer com Cognito (prod)
    └── local_token_authorizer.py # Token authorizer (local dev)
```

**Recursos provisionados:**

| Recurso | Configuração |
|---------|-------------|
| **Lambda Functions** | Python 3.10, 512MB RAM, 15s timeout, 1 por módulo |
| **Lambda Layer** | Dependências compartilhadas (boto3, pydantic, etc.) |
| **API Gateway (REST)** | CORS enabled (all origins), Cognito authorizer |
| **DynamoDB** | PAY_PER_REQUEST, 2 GSIs, tabela única |
| **S3 Bucket** | Upload de arquivos (presigned URLs) |
| **CloudWatch Logs** | Retenção de 1 mês por function |
| **IAM Roles** | Permissões granulares por function (DynamoDB, S3) |
| **EventBridge Rule** | Cron para sync_forms_origin |

**Ambientes suportados:**
- `DEV` — Desenvolvimento na AWS com dados de teste
- `HOMOLOG` — Homologação com dados próximos de produção
- `PROD` — Produção

**Padrão de deploy:**
```bash
cd iac && cdk deploy --all
```

**Variáveis de ambiente injetadas nas Lambdas:**
```
STAGE, REGION, DYNAMO_TABLE_NAME, DYNAMO_PARTITION_KEY,
DYNAMO_SORT_KEY, BUCKET_NAME, USER_POOL_ID, USER_POOL_ARN,
APP_CLIENT_ID, S3_ENDPOINT_URL, SYNC_FORMS_*
```

**Authorizer condicional:**
- Em `PROD`/`HOMOLOG`: Cognito Authorizer (valida JWT real)
- Em `DEV` local: Token Authorizer com Lambda custom (para testes sem Cognito)

## Consequências

### Positivas
- Infraestrutura versionada no git — auditoria e rollback facilitados
- CDK com Python permite reutilizar lógica e tipagem do mesmo ecossistema
- Deploy idempotente — CDK calcula diffs e aplica apenas mudanças necessárias
- Stacks compostas (DynamoDB + Lambda separados) permitem deploys parciais
- Mesmo código IaC para dev/homolog/prod, variando apenas parâmetros

### Negativas
- CDK tem curva de aprendizado (constructs, L1/L2/L3)
- Mudanças em recursos stateful (DynamoDB) podem requerer cuidado especial
- CDK bootstrapping necessário por conta/região antes do primeiro deploy
- Synth + deploy pode ser lento para muitas Lambdas

## Alternativas Consideradas

### Serverless Framework
- **Descrição**: Framework YAML-based para deploy de aplicações serverless
- **Motivo da rejeição**: Menos flexibilidade que CDK para composição de stacks; YAML dificulta lógica condicional; CDK já era padrão na organização

### AWS SAM (Serverless Application Model)
- **Descrição**: Extensão do CloudFormation focada em serverless
- **Motivo da rejeição**: Menos expressivo que CDK; limitado em composição de constructs; CDK pode gerar SAM templates se necessário

### Terraform
- **Descrição**: IaC multi-cloud com HCL
- **Motivo da rejeição**: Organização é 100% AWS — benefícios multi-cloud não se aplicam; CDK tem integração mais profunda com AWS; time já tem expertise em CDK
