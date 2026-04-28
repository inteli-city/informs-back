# Setup Local do Informs Backend (SAM + DynamoDB Local)

Este guia sobe localmente o backend do **Informs**, app da Intelicity para geração e preenchimento de formulários em campo.

## Pré-requisitos
- Python 3.10+ com `venv`
- Docker + Docker Compose
- AWS SAM CLI
- AWS CDK CLI (`npm i -g aws-cdk`)

## Conceito importante: `.env` e `env.json` têm papéis diferentes
- `.env` (na raiz do projeto) é usado pelo **CDK** no `cdk synth`.
- `iac/local/env.json` é usado pelo **SAM local** para injetar env vars nas Lambdas em runtime.
- Sem `.env` correto, o template `cdk.out/*.template.json` pode não ser gerado.
- Sem `iac/local/env.json`, a Lambda sobe no SAM sem as envs esperadas.

## Requisito obrigatório do `cdk synth`
O arquivo `iac/app.py` precisa ter `load_dotenv()` ativo para ler o `.env`.
Sem isso, o synth local quebra por ausência de variáveis.

## 1) Criar e instalar ambiente Python
No root do projeto:

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install -r iac/requirements.txt
```

## 2) Criar `.env` (raiz do projeto)
Exemplo mínimo para synth local:

```env
STAGE=DEV
REGION=sa-east-1
DYNAMO_TABLE_NAME=Formularios_Table
ENDPOINT_URL=http://localhost:8000
DYNAMO_PARTITION_KEY=PK
DYNAMO_SORT_KEY=SK
GITHUB_REF_NAME=dev
STACK_NAME=FormulariosStackdev
BUCKET_NAME=formularios-dev
USE_LOCAL_AUTHORIZER=true
USER_POOL_ID=sa-east-1_xxxxx
USER_POOL_ARN=arn:aws:cognito-idp:sa-east-1:123456789012:userpool/sa-east-1_xxxxx
APP_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
S3_ENDPOINT_URL=http://localstack:4566
```

Os nomes `Formularios_Table`, `FormulariosStackdev` e `formularios-dev` são mantidos por compatibilidade com recursos já existentes.

## 3) Criar `iac/local/env.json` (env de runtime da Lambda no SAM)
Exemplo:

```json
{
  "Parameters": {
    "STAGE": "DEV",
    "REGION": "sa-east-1",
    "DYNAMO_TABLE_NAME": "Formularios_Table",
    "S3_ENDPOINT_URL": "http://localstack:4566",
    "ENDPOINT_URL": "http://dynamodb-local:8000",
    "DYNAMO_PARTITION_KEY": "PK",
    "DYNAMO_SORT_KEY": "SK",
    "GITHUB_REF_NAME": "dev",
    "BUCKET_NAME": "formularios-dev",
    "STACK_NAME": "FormulariosStackdev",
    "USE_LOCAL_AUTHORIZER": "true"
  }
}
```

## 4) Subir serviços locais e preparar Dynamo (com GSIs)
Dentro de `iac/`:

```bash
make local-bootstrap
```

Para resetar tabela:

```bash
make local-bootstrap-reset
```

## 5) Rodar API local com SAM
Dentro de `iac/`:

```bash
make local-api
```

O `make local-api` usa `--env-vars ./local/env.json`, então esse arquivo precisa existir.

## Sem Make (ex.: Windows)
No root do projeto:

```bash
venv\Scripts\python.exe iac\local\bootstrap_local.py --reset-db
```
