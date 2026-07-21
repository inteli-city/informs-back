[![codecov](https://codecov.io/gh/inteli-city/formularios_mss/graph/badge.svg?token=UB200QTY0I)](https://codecov.io/gh/inteli-city/formularios_mss)

![Graph](https://codecov.io/gh/inteli-city/formularios_mss/graphs/sunburst.svg?token=UB200QTY0I)

# Informs Backend

Backend serverless do **Informs**, app da Intelicity para geração e preenchimento de formulários em campo.

O serviço permite criar templates reutilizáveis, gerar formulários dinâmicos, distribuir formulários para usuários, registrar preenchimentos, anexar arquivos via URLs pré-assinadas e sincronizar formulários preenchidos com sistemas de origem. Usa AWS Lambda, API Gateway, DynamoDB single-table, S3 para uploads e CDK para infraestrutura.

## Comandos

```bash
venv\Scripts\python.exe -m pytest
venv\Scripts\python.exe -m pytest --cov=src --cov-report=term-missing
venv\Scripts\python.exe -m src.shared.helpers.functions.generate_openapi_from_contracts
```

Para desenvolvimento local com SAM/DynamoDB Local, veja `iac/LOCAL_SETUP.md`.

## Domínio

- **Templates**: modelos reutilizáveis com seções e campos.
- **Formulários**: instâncias criadas a partir de templates ou estruturas ad-hoc.
- **Campos**: tipos polimórficos como texto, número, data, seleção, checkbox, arquivo e informações complementares.
- **Preenchimento em campo**: ciclo de vida com início, submissão, cancelamento, anexos e justificativas.
- **Sincronização**: envio periódico dos formulários preenchidos para sistemas de origem da Intelicity.

## Variáveis principais

- `STAGE`: `TEST`, `DEV`, `HOMOLOG`, `PROD` ou `DOTENV`.
- `DYNAMO_TABLE_NAME`, `DYNAMO_PARTITION_KEY`, `DYNAMO_SORT_KEY`.
- `BUCKET_NAME`.
- `USER_POOL_ARN`, `USER_POOL_ID`, `APP_CLIENT_ID`.
- `SYNC_FORMS_PAGE_LIMIT`, `SYNC_FORMS_WINDOW_MINUTES`, `SYNC_FORMS_FIRST_RUN_FULL_SYNC`.

## Estrutura

- `src/modules`: Lambdas por feature.
- `src/shared/domain`: entidades, enums e interfaces do domínio.
- `src/shared/infra`: repositórios DynamoDB/S3 e DTOs.
- `src/shared/helpers/contracts`: contratos Pydantic e geração OpenAPI.
- `iac`: CDK, SAM local e scripts de bootstrap.

## Documentação

- `docs/adr`: decisões arquiteturais do projeto.
- `iac/README.md`: visão geral da infraestrutura como código.
- `iac/LOCAL_SETUP.md`: setup local com SAM, DynamoDB Local e LocalStack.
