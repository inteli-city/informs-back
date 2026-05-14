#!/usr/bin/env bash
# Deploy do ws_server pra Lightsail.
#
# Roda no GitHub Actions runner (ubuntu-latest) com:
#   - AWS CLI configurado (aws-actions/configure-aws-credentials)
#   - SSH agent populável (vamos popular daqui mesmo, da Secrets Manager)
#
# Args via env:
#   STAGE                 dev | homolog | prod
#   COGNITO_USER_POOL_ID  passado via secret do GH Environment
#   COGNITO_APP_CLIENT_ID idem
#
# Idempotente: re-execução no mesmo commit não rebuilda venv (rsync ignora
# arquivos iguais), e systemctl restart sempre devolve estado ok.

set -euo pipefail

STAGE="${STAGE:?STAGE não definido (dev|homolog|prod)}"
case "${STAGE}" in
    dev)     PORT=8001 ;;
    homolog) PORT=8002 ;;
    prod)    PORT=8003 ;;
    *) echo "STAGE inválido: ${STAGE}"; exit 1 ;;
esac

INSTANCE_NAME="informs-ws"
STATIC_IP_NAME="informs-ws-ip"
SSH_KEY_SECRET="informs-ws/lightsail-ssh-key"
AWS_CREDS_SECRET="informs-ws/aws-credentials"
SSH_USER="admin"   # Debian 12 na Lightsail usa "admin", não "ec2-user"
REMOTE_BASE="/opt/informs-ws/${STAGE}"

echo "==> [1/7] Recuperando IP estático e chave SSH"
STATIC_IP=$(aws lightsail get-static-ip --static-ip-name "${STATIC_IP_NAME}" \
    --query 'staticIp.ipAddress' --output text)
IP_DASHED="${STATIC_IP//./-}"
echo "    IP=${STATIC_IP} (${IP_DASHED}.sslip.io)"

# Chave privada vai pra ~/.ssh/informs-ws.pem (modo 600).
mkdir -p ~/.ssh
aws secretsmanager get-secret-value --secret-id "${SSH_KEY_SECRET}" \
    --query SecretString --output text \
    | base64 --decode > ~/.ssh/informs-ws.pem
chmod 600 ~/.ssh/informs-ws.pem

# Aceita host key na primeira vez (não validamos fingerprint — IP fixo,
# Lightsail confiável).
SSH_OPTS="-i ${HOME}/.ssh/informs-ws.pem -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=/dev/null"

echo "==> [2/7] Renderizando Caddyfile"
CADDYFILE_RENDERED=$(mktemp)
sed "s/{{IP_DASHED}}/${IP_DASHED}/g" iac/ws_server_bootstrap/Caddyfile.template > "${CADDYFILE_RENDERED}"

echo "==> [3/7] Renderizando arquivo de env do systemd"
# AWS credentials da própria instância (IAM user informs-ws-server) — o
# CDK populou esse secret. Pegamos o JSON e extraímos.
AWS_CREDS_JSON=$(aws secretsmanager get-secret-value --secret-id "${AWS_CREDS_SECRET}" \
    --query SecretString --output text)
INSTANCE_AWS_KEY=$(echo "${AWS_CREDS_JSON}" | jq -r '.AccessKeyId')
INSTANCE_AWS_SECRET=$(echo "${AWS_CREDS_JSON}" | jq -r '.SecretAccessKey')

# Nomes físicos das tabelas DynamoDB são auto-gerados pelo CFN (PR #49).
# Descobrimos via CFN Outputs:
#   - LocationTableName_{stage} na FormulariosTrackingStack
#   - ProfileTableName na FormulariosStack{stage}
LOCATION_TABLE=$(aws cloudformation describe-stacks \
    --stack-name FormulariosTrackingStack \
    --query "Stacks[0].Outputs[?OutputKey=='LocationTableName_${STAGE}'].OutputValue" \
    --output text)
PROFILE_TABLE=$(aws cloudformation describe-stacks \
    --stack-name "FormulariosStack${STAGE}" \
    --query "Stacks[0].Outputs[?OutputKey=='ProfileTableName'].OutputValue" \
    --output text)
if [[ -z "${LOCATION_TABLE}" || -z "${PROFILE_TABLE}" ]]; then
    echo "!! Não consegui descobrir nomes das tabelas via CFN Outputs."
    echo "   LOCATION_TABLE=${LOCATION_TABLE} PROFILE_TABLE=${PROFILE_TABLE}"
    echo "   Verifica se FormulariosTrackingStack e FormulariosStack${STAGE} já foram deployadas."
    exit 1
fi

ENV_FILE_RENDERED=$(mktemp)
cat > "${ENV_FILE_RENDERED}" <<EOF
STAGE=${STAGE}
PORT=${PORT}
AWS_REGION=${AWS_REGION:-sa-east-1}
COGNITO_USER_POOL_ID=${COGNITO_USER_POOL_ID:?}
COGNITO_APP_CLIENT_ID=${COGNITO_APP_CLIENT_ID:?}
LOCATION_TABLE=${LOCATION_TABLE}
PROFILE_TABLE=${PROFILE_TABLE}
AWS_ACCESS_KEY_ID=${INSTANCE_AWS_KEY}
AWS_SECRET_ACCESS_KEY=${INSTANCE_AWS_SECRET}
EOF

echo "==> [4/7] Sincronizando código via rsync"
# --delete: remove arquivos antigos no remote.
# Excluímos venv (mantido no remote) e tests (não rodam em prod).
rsync -az --delete \
    -e "ssh ${SSH_OPTS}" \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='venv' \
    --exclude='tests' \
    ws_server/ \
    "${SSH_USER}@${STATIC_IP}:${REMOTE_BASE}/code/"

# rsync do env file (modo 600, não checked-in, vai como arquivo separado).
scp ${SSH_OPTS} "${ENV_FILE_RENDERED}" "${SSH_USER}@${STATIC_IP}:/tmp/informs-ws-env-${STAGE}"

echo "==> [5/7] Setup venv + deps na instância"
# Heredoc pra rodar tudo numa SSH session só.
ssh ${SSH_OPTS} "${SSH_USER}@${STATIC_IP}" bash <<EOF
set -euo pipefail
sudo install -o informs-ws -g informs-ws -m 600 /tmp/informs-ws-env-${STAGE} ${REMOTE_BASE}/env
sudo rm /tmp/informs-ws-env-${STAGE}

# Cria venv se não existe (primeiro deploy).
if [ ! -d "${REMOTE_BASE}/venv" ]; then
    sudo -u informs-ws python3 -m venv ${REMOTE_BASE}/venv
fi

# pip install em modo editável aponta pra ${REMOTE_BASE}/code (mesma pasta
# que o systemd usa como WorkingDirectory).
sudo -u informs-ws ${REMOTE_BASE}/venv/bin/pip install --quiet --upgrade pip
sudo -u informs-ws ${REMOTE_BASE}/venv/bin/pip install --quiet -e ${REMOTE_BASE}/code
EOF

echo "==> [6/7] Atualizando Caddyfile e reload"
# Caddyfile é compartilhado entre os 3 envs — só faz sentido escrever uma
# vez por deploy (qualquer um dos 3 stages serve), mas é idempotente: se
# já estava igual, caddy reload é no-op.
scp ${SSH_OPTS} "${CADDYFILE_RENDERED}" "${SSH_USER}@${STATIC_IP}:/tmp/Caddyfile.new"
ssh ${SSH_OPTS} "${SSH_USER}@${STATIC_IP}" bash <<'EOF'
set -euo pipefail
sudo install -o root -g root -m 644 /tmp/Caddyfile.new /etc/caddy/Caddyfile
sudo rm /tmp/Caddyfile.new
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
EOF

echo "==> [7/7] Restart do systemd unit do env ${STAGE}"
ssh ${SSH_OPTS} "${SSH_USER}@${STATIC_IP}" \
    "sudo systemctl enable --now informs-ws-${STAGE}.service && sudo systemctl restart informs-ws-${STAGE}.service"

echo "==> Aguardando health check (15s)"
sleep 5
HEALTH=$(curl -fsS --max-time 10 "https://${STAGE}-${IP_DASHED}.sslip.io/health" || echo "FAIL")
if [[ "${HEALTH}" == "FAIL" ]] || ! echo "${HEALTH}" | grep -q '"status":"ok"'; then
    echo "!! Health check falhou. Output: ${HEALTH}"
    echo "!! Logs recentes do serviço:"
    ssh ${SSH_OPTS} "${SSH_USER}@${STATIC_IP}" \
        "sudo journalctl -u informs-ws-${STAGE} -n 50 --no-pager"
    exit 1
fi

echo "==> Deploy ${STAGE} concluído com sucesso"
echo "    wss://${STAGE}-${IP_DASHED}.sslip.io/ws"
