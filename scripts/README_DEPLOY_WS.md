# Deploy do WS server — guia rápido

## Setup uma única vez (após PRs #45/#48/#49 mergeados e `cdk deploy FormulariosTrackingStack` + `cdk deploy FormulariosStack{stage}` rodados)

1. Anote o IP estático da Lightsail:
   ```bash
   aws lightsail get-static-ip --static-ip-name informs-ws-ip \
       --query 'staticIp.ipAddress' --output text --region sa-east-1
   ```

2. Configure os secrets nos GitHub Environments **dev / homolog / prod**
   (Settings → Environments → New environment):

   | Secret | Valor |
   |---|---|
   | `AWS_ACCESS_KEY_ID` | (da conta AWS que vai rodar o deploy) |
   | `AWS_SECRET_ACCESS_KEY` | idem |
   | `AWS_REGION` | `sa-east-1` |
   | `USER_POOL_ID` | (mesmo valor já usado no CD.yml por env) |
   | `APP_CLIENT_ID` | idem |

   Os secrets `informs-ws/lightsail-ssh-key` e `informs-ws/aws-credentials`
   foram **populados automaticamente pelo CDK** e o script puxa direto
   via AWS CLI — não precisa configurar no GitHub.

## Como roda

Push em `dev`/`homolog`/`prod` (com mudanças em `ws_server/**`,
`Caddyfile.template`, `deploy_ws_server.sh` ou `deploy-ws-server.yml`)
dispara `.github/workflows/deploy-ws-server.yml`, que:

1. Configura AWS credentials (do GH secret).
2. Roda `scripts/deploy_ws_server.sh`:
   - Recupera IP estático e chave SSH (Secrets Manager)
   - Renderiza `Caddyfile` substituindo `{{IP_DASHED}}`
   - **Descobre nomes auto-gerados das tabelas** via CFN Outputs:
     - `LOCATION_TABLE` ← `FormulariosTrackingStack` Output `LocationTableName_{stage}`
     - `PROFILE_TABLE` ← `FormulariosStack{stage}` Output `ProfileTableName`
   - Renderiza arquivo de env do systemd (Cognito + AWS creds + nomes de tabela)
   - `rsync` do código pra `/opt/informs-ws/{stage}/code/`
   - Cria venv + `pip install -e .` (idempotente)
   - Reload do Caddy + restart do systemd unit do env
   - Health check em `https://{stage}-{ip-dashed}.sslip.io/health`

## Testar manualmente

```bash
export STAGE=dev
export AWS_REGION=sa-east-1
export COGNITO_USER_POOL_ID=...
export COGNITO_APP_CLIENT_ID=...
bash scripts/deploy_ws_server.sh
```

## Endpoints WS finais (após deploy)

```
wss://dev-<ip-dashed>.sslip.io/ws        # processo dev :8001
wss://homolog-<ip-dashed>.sslip.io/ws    # processo homolog :8002
wss://prod-<ip-dashed>.sslip.io/ws       # processo prod :8003
```

Cliente conecta com header `Authorization: Bearer <id_token Cognito>` ou
`Sec-WebSocket-Protocol: Bearer.<token>` (fallback browser).
