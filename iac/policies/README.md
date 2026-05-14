# Setup de IAM e secrets pra feature de tracking

A `FormulariosTrackingStack` foi propositalmente desenhada **sem criar
nenhum recurso IAM** — assumimos que você (que vai rodar `cdk deploy`)
não tem permissão de IAM no projeto.

## Recursos por responsável

| Recurso | Quem cria | Como |
|---|---|---|
| 3 tabelas DynamoDB Location | CDK (você) | `cdk deploy FormulariosTrackingStack` |
| Lightsail instance + static IP | CDK (você) | idem |
| 2 SecretsManager secrets (vazios) | CDK (você) | idem |
| **IAM user `informs-ws-server`** | **Infra (1 vez)** | console/CLI manual |
| Conteúdo dos 2 secrets | **Você (1 vez)** | console/CLI após o deploy |
| **`tracking-runtime-ci` policy no user do CI** | **Infra (1 vez)** | console/CLI manual |

## Sequência completa de setup

### 1. Você roda o `cdk deploy` (sem IAM no caminho crítico)

Pré-requisito: pedir pra infra anexar a `tracking-stack-deploy-admin.json`
ao SEU user (uma vez, mas as actions cabem em Lightsail/SecretsManager/CFN/DynamoDB
puros — sem IAM).

```bash
cd iac
AWS_REGION=sa-east-1 \
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text) \
STACK_NAME=FormulariosStackdev GITHUB_REF_NAME=dev \
USER_POOL_ARN=<seu> USER_POOL_ID=<seu> APP_CLIENT_ID=<seu> BUCKET_NAME=<seu> \
npx cdk deploy FormulariosTrackingStack --app "python app.py" --require-approval never
```

Os env vars do Cognito não são realmente usadas pela TrackingStack — só
precisam estar setadas porque o `app.py` instancia também o IacStack.

### 2. Pedir pra infra fazer 2 coisas (uma única vez na vida)

a. **Criar o IAM user `informs-ws-server` + access key**, anexando a
   policy `iac/policies/informs-ws-server-runtime.json` (DynamoDB Query/PutItem
   na Location + GetItem na Profile, escopo restrito).

b. **Anexar policy `tracking-runtime-ci.json` ao user que está em
   `AWS_ACCESS_KEY_ID` do GitHub repo** (3 actions mínimas pra CI ler
   secrets/IP/CFN outputs).

### 3. Você popula os 2 secrets manualmente

Você tem `secretsmanager:PutSecretValue` em `informs-ws/*` (vem da
`tracking-stack-deploy-admin.json`).

```bash
# a) SSH key — baixar a "default key" Lightsail do console:
#    Account → SSH keys → "LightsailDefaultKey-sa-east-1" → Download.
#    Codificar em base64 e armazenar:
base64 -w 0 LightsailDefaultKey-sa-east-1.pem | \
  aws secretsmanager put-secret-value \
    --secret-id informs-ws/lightsail-ssh-key \
    --secret-string file:///dev/stdin \
    --region sa-east-1

# b) AWS credentials do informs-ws-server (que infra criou no passo 2a):
aws secretsmanager put-secret-value \
  --secret-id informs-ws/aws-credentials \
  --secret-string '{"AccessKeyId":"AKIA...","SecretAccessKey":"..."}' \
  --region sa-east-1
```

### 4. Re-rodar o workflow GH Actions

```bash
gh workflow run "Deploy WS Server" --ref dev
```

Agora deve passar até o final (`==> Deploy dev concluído com sucesso`).

## As 3 policies em ação

| Arquivo | Pra quem | Quem aplica |
|---|---|---|
| `tracking-stack-deploy-admin.json` | VOCÊ (que roda `cdk deploy`) | Infra anexa ao seu user |
| `tracking-runtime-ci.json` | User do GH Actions (`AWS_ACCESS_KEY_ID` no repo) | Infra anexa |
| `informs-ws-server-runtime.json` | IAM user `informs-ws-server` (consumido pelo WS server na Lightsail) | Infra cria o user e anexa |

Nenhuma das 3 contém actions IAM — só DDB/Lightsail/SecretsManager/CFN.
A criação do user `informs-ws-server` em si é o único passo IAM, mas é
uma única chamada (`iam:CreateUser` + `iam:CreateAccessKey`) feita pela
infra, sem código ou stack.
