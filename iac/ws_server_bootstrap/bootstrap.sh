#!/usr/bin/env bash
# user-data executado UMA vez na criação da Lightsail.
# Idempotente quando possível (re-execução manual via ssh não quebra).
#
# Responsabilidades:
#   1. Swap 1GB (rede de segurança contra OOM no plano $5).
#   2. Pacotes base: python3.11 + venv + pip + caddy + jq + awscli.
#   3. Estrutura /opt/informs-ws/{dev,homolog,prod} pronta pra deploy.
#   4. systemd units placeholder pros 3 envs (não startam — sem código ainda).
#   5. Caddyfile placeholder (sem hostname — preenchido depois que static IP
#      for atribuído e a gente conhecer o sslip.io final).
#
# O CÓDIGO do WS server e a configuração final do Caddy entram via
# GitHub Actions (PR3), não aqui.

set -euxo pipefail
exec > >(tee /var/log/informs-ws-bootstrap.log) 2>&1

echo "==> [1/5] Swap 1GB"
if [[ ! -f /swapfile ]]; then
    fallocate -l 1G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo "/swapfile none swap sw 0 0" >> /etc/fstab
fi

echo "==> [2/5] APT install"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y \
    python3 python3-venv python3-pip \
    debian-keyring debian-archive-keyring apt-transport-https curl \
    jq awscli

# Caddy oficial (repo da Cloudsmith). https://caddyserver.com/docs/install
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
    | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
    > /etc/apt/sources.list.d/caddy-stable.list
apt-get update -y
apt-get install -y caddy

echo "==> [3/5] Estrutura /opt/informs-ws"
useradd --system --create-home --home-dir /opt/informs-ws --shell /usr/sbin/nologin informs-ws || true
for STAGE in dev homolog prod; do
    mkdir -p /opt/informs-ws/${STAGE}/code
    mkdir -p /opt/informs-ws/${STAGE}/logs
done
chown -R informs-ws:informs-ws /opt/informs-ws

# ~/.aws/credentials será preenchido pelo deploy (GitHub Actions puxa do
# Secrets Manager e copia via SSH). Aqui só garante o diretório.
install -d -o informs-ws -g informs-ws -m 700 /opt/informs-ws/.aws

echo "==> [4/5] systemd units placeholder"
for STAGE in dev homolog prod; do
    case "${STAGE}" in
        dev)     PORT=8001 ;;
        homolog) PORT=8002 ;;
        prod)    PORT=8003 ;;
        # `for` itera só sobre dev/homolog/prod, mas SonarQube shelldre:S131
        # exige default explícito. Mantemos uma falha barulhenta no caso
        # improvável de alguém editar a lista acima sem atualizar o case.
        *) echo "STAGE inesperado: ${STAGE}"; exit 1 ;;
    esac

    cat > /etc/systemd/system/informs-ws-${STAGE}.service <<EOF
[Unit]
Description=Informs Tracking WebSocket server (${STAGE})
After=network.target

[Service]
Type=simple
User=informs-ws
Group=informs-ws
WorkingDirectory=/opt/informs-ws/${STAGE}/code
Environment="STAGE=${STAGE}"
Environment="PORT=${PORT}"
Environment="HOME=/opt/informs-ws"
EnvironmentFile=-/opt/informs-ws/${STAGE}/env
ExecStart=/opt/informs-ws/${STAGE}/venv/bin/uvicorn main:app --host 127.0.0.1 --port \${PORT} --proxy-headers
Restart=on-failure
RestartSec=3
StandardOutput=append:/opt/informs-ws/${STAGE}/logs/stdout.log
StandardError=append:/opt/informs-ws/${STAGE}/logs/stderr.log

[Install]
WantedBy=multi-user.target
EOF
done
systemctl daemon-reload
# NÃO habilita/inicia ainda — código não existe. PR3 (deploy) ativa.

echo "==> [5/5] Caddy placeholder"
# Caddyfile final é gerado no primeiro deploy (sabendo o static IP definitivo
# pra montar os hostnames sslip.io). Aqui só um stub que responde 503 —
# evita o Caddy ficar em crashloop e bater rate-limit do Let's Encrypt.
cat > /etc/caddy/Caddyfile <<'EOF'
:80 {
    respond "informs-ws bootstrap ok — Caddyfile final será injetado pelo deploy" 503
}
EOF
systemctl enable caddy
systemctl restart caddy

echo "==> bootstrap concluído"
