# Deploy do ws_server no Railway

Setup feito uma vez. Depois é só `git push` na branch certa pra deploy automático.

## Setup inicial (1 vez)

### 1. Provisionar IAM user na AWS (pedir pra infra, 1 vez)

Crie um IAM user chamado `informs-ws-railway` com a policy abaixo e
gere uma access key. As 2 strings (AccessKeyId + SecretAccessKey) vão
como env var no Railway.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ReadWriteLocationAndReadProfile",
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:Query",
                "dynamodb:GetItem",
                "dynamodb:BatchWriteItem"
            ],
            "Resource": [
                "arn:aws:dynamodb:*:*:table/FormulariosStack*-FormulariosDynamoLocationsTable*",
                "arn:aws:dynamodb:*:*:table/FormulariosStack*-FormulariosDynamoProfilesTable*"
            ]
        }
    ]
}
```

(Profile só é GetItem, mas pra simplificar a policy reuni tudo num
statement só com o mesmo set de actions — `dynamodb:GetItem` cobre
o caso do Profile.)

### 2. Garantir que o IacStack está deployado

A tabela `Locations_Table` agora vive **dentro do IacStack** (1 por env,
nome auto-gerado pelo CFN). Sai automaticamente no CD.yml a cada push
em `dev`/`homolog`/`prod`. Se ainda não rodou, dê um
`git commit --allow-empty` + push numa das branches.

### 3. Criar projeto e service no Railway

1. railway.com → New Project → Deploy from GitHub Repo → escolha `informs-back`
2. New Service → escolha o repo informs-back de novo
3. **Service Settings → Source → Root Directory**: `ws_server`
4. **Service Settings → Source → Watch Paths**: `ws_server/**` (só rebuild quando WS muda)
5. **Service Settings → Build → Builder**: Dockerfile (autodetecta o `ws_server/Dockerfile`)

### 4. Criar 3 environments no projeto

Project Settings → Environments → New Environment. Crie:
- `dev` (atrelar branch `dev`)
- `homolog` (atrelar branch `homolog`)
- `prod` (atrelar branch `prod`)

Cada environment tem suas próprias variables.

### 5. Configurar Service Variables por environment

Em cada environment do service, defina:

| Variável | Valor (exemplo dev) |
|---|---|
| `STAGE` | `dev` |
| `AWS_REGION` | `sa-east-1` |
| `AWS_ACCESS_KEY_ID` | (do user `informs-ws-railway` criado no passo 1) |
| `AWS_SECRET_ACCESS_KEY` | idem |
| `COGNITO_USER_POOL_ID` | (mesmo do GH Environment dev) |
| `COGNITO_APP_CLIENT_ID` | (mesmo do GH Environment dev) |
| `LOCATION_TABLE` | `aws cloudformation describe-stacks --stack-name FormulariosStackdev --query "Stacks[0].Outputs[?OutputKey=='LocationTableName'].OutputValue" --output text` |
| `PROFILE_TABLE` | `aws cloudformation describe-stacks --stack-name FormulariosStackdev --query "Stacks[0].Outputs[?OutputKey=='ProfileTableName'].OutputValue" --output text` |

(Repete pro homolog e prod com os respectivos valores.)

### 6. Deploy

Push em qualquer uma das branches `dev`/`homolog`/`prod` → Railway
detecta, build Docker, deploya, dá um domínio `*.up.railway.app`.

Anote o domínio de cada environment — vai como WSS endpoint pro app.

## Endpoints finais

```
wss://informs-ws-dev.up.railway.app/ws       (ou domínio custom)
wss://informs-ws-homolog.up.railway.app/ws
wss://informs-ws-prod.up.railway.app/ws
```

Cliente conecta com header `Authorization: Bearer <Cognito ID Token>`
ou `Sec-WebSocket-Protocol: Bearer.<token>` (browser fallback).

## Custom domain (opcional)

Se quiser `wss://tracking.intelicity.com/ws`:
1. Service → Settings → Networking → Custom Domain → adiciona
2. Railway dá um CNAME pra apontar no DNS
3. TLS automático após DNS propagar

## Logs / debug

Railway dashboard tem logs em tempo real. Filtra por environment.
Pra erro 401 no WS: provavelmente `COGNITO_*` errada ou role do user
não é INSPECTOR/ADMIN.
