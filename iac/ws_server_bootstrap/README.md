# Tracking WebSocket — Lightsail bootstrap

Provisionado pelo `iac/iac/tracking_stack.py` (stack `FormulariosTrackingStack`).

## O que essa pasta contém

- `bootstrap.sh` — user-data executado UMA vez na criação da Lightsail.
  Instala Python 3.11, Caddy, awscli, cria estrutura `/opt/informs-ws/{dev,homolog,prod}`
  e systemd units placeholder (sem startar — sem código ainda).

- `Caddyfile.template` — template do Caddyfile final. O GitHub Actions (PR3)
  substitui `{{IP_DASHED}}` pelo static IP da Lightsail no formato dash
  (ex: `54-232-10-5`) e copia pra `/etc/caddy/Caddyfile`.

## Deploy inicial

```bash
# da raiz do repo, com venv ativo e AWS creds configurados:
cd iac
AWS_REGION=sa-east-1 \
AWS_ACCOUNT_ID=<conta> \
GITHUB_REF_NAME=dev \
npx cdk deploy FormulariosTrackingStack --app "python app.py"
```

Após o deploy:
1. **DynamoDB**: tabelas `informs-tracking-location-{dev,homolog,prod}` criadas.
2. **Lightsail**: instância `informs-ws` rodando o bootstrap. Aguarde ~2min
   (acompanhe via Lightsail console → Manage instance → Connect → veja
   `/var/log/informs-ws-bootstrap.log`).
3. **Secrets Manager**:
   - `informs-ws/lightsail-ssh-key` — chave privada PEM, populada
     automaticamente pelo CDK via custom resource.
   - `informs-ws/aws-credentials` — JSON `{AccessKeyId, SecretAccessKey}` do
     IAM user `informs-ws-server`, também populado automaticamente.
4. **Static IP**: anote o IP em Outputs (`WSStaticIpName` → procura no
   console pra ver o IP literal). Esse IP vai pro PR3 (deploy).

## Endpoints WebSocket (depois do PR3 montar o Caddy)

```
wss://dev-<dashed-ip>.sslip.io
wss://homolog-<dashed-ip>.sslip.io
wss://prod-<dashed-ip>.sslip.io
```

Ex: se static IP é `54.232.10.5`, dev fica `wss://dev-54-232-10-5.sslip.io`.
