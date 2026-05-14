# IAM Policies pra feature de tracking

Quando o PR #45 mergeou, ele subiu o **código** da `FormulariosTrackingStack`
pro main — mas alguém (humano com creds admin) precisa rodar `cdk deploy`
**uma vez** pra criar os recursos AWS reais (Lightsail, static IP, secrets,
IAM user `informs-ws-server`, tabela Location, etc).

Esses 2 JSONs descrevem as permissões mínimas:

| Arquivo | Pra quem | Quando |
|---|---|---|
| `tracking-stack-deploy-admin.json` | User humano que vai rodar `cdk deploy FormulariosTrackingStack` UMA vez | Antes do 1º deploy da TrackingStack |
| `tracking-runtime-ci.json` | User do GitHub Actions (`AWS_ACCESS_KEY_ID` no repo) | Depois da TrackingStack existir, todo deploy do ws_server roda com isso |

## Setup (uma vez)

Com creds admin AWS configuradas localmente (alguém com permissão IAM:PutUserPolicy):

```bash
ADMIN_USER_NAME=rodrigosiqueira CI_USER_NAME=ci-deploy-user \
  bash scripts/setup_tracking_permissions.sh
```

Se admin e CI são o **mesmo user**, basta omitir os 2 vars (default ambos = `rodrigosiqueira`).

## Próximos passos depois das policies aplicadas

1. **Deploy da TrackingStack** (uma vez):
   ```bash
   cd iac
   AWS_REGION=sa-east-1 AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text) \
   STACK_NAME=FormulariosStackdev GITHUB_REF_NAME=dev \
   USER_POOL_ARN=<seu> USER_POOL_ID=<seu> APP_CLIENT_ID=<seu> BUCKET_NAME=<seu> \
   npx cdk deploy FormulariosTrackingStack --app "python app.py" --require-approval never
   ```
   (As env vars do Cognito não são realmente usadas pela TrackingStack — só
   precisam estar setadas porque o `app.py` instancia também o IacStack
   no mesmo synth.)

2. **Anotar o static IP** que apareceu nos Outputs (ou via console).

3. **Re-rodar o workflow GH Actions** — push em qualquer arquivo de
   `ws_server/**` ou via `gh workflow run "Deploy WS Server" --ref dev`.
   Agora deve passar até o final (rsync + restart + health check).

## Por que duas policies separadas

A `deploy-admin` é **larga** (precisa criar/deletar tudo). Não queremos
que isso fique permanentemente no user do CI — risco de blast radius. O
CI só precisa **ler** 3 coisas (static IP, 2 secrets, outputs CFN).
