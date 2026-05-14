#!/usr/bin/env bash
# Setup das 2 policies anexáveis (admin + CI) ao user(s) que vão rodar
# cdk deploy / GH Actions. NÃO cria IAM user nem anexa a policy de
# runtime ao informs-ws-server — esses passos a infra faz manualmente
# (ver iac/policies/README.md).
#
# Pré-req: rodar com creds AWS de quem TEM iam:PutUserPolicy (admin /
# infra). Você não precisa rodar isso — só quem aplica permissões.

set -euo pipefail

ADMIN_USER_NAME="${ADMIN_USER_NAME:-rodrigosiqueira}"  # quem roda cdk deploy
CI_USER_NAME="${CI_USER_NAME:-rodrigosiqueira}"        # quem está no AWS_ACCESS_KEY_ID do GH

echo "==> Anexando policy 'tracking-stack-deploy-admin' ao user ${ADMIN_USER_NAME}"
aws iam put-user-policy \
    --user-name "${ADMIN_USER_NAME}" \
    --policy-name tracking-stack-deploy-admin \
    --policy-document file://"$(dirname "$0")"/../iac/policies/tracking-stack-deploy-admin.json

echo "==> Anexando policy 'tracking-runtime-ci' ao user ${CI_USER_NAME}"
aws iam put-user-policy \
    --user-name "${CI_USER_NAME}" \
    --policy-name tracking-runtime-ci \
    --policy-document file://"$(dirname "$0")"/../iac/policies/tracking-runtime-ci.json

echo ""
echo "==> OK. Próximos passos:"
echo "  1. Você (${ADMIN_USER_NAME}) roda 'cdk deploy FormulariosTrackingStack'"
echo "  2. Infra cria IAM user 'informs-ws-server' + access key, anexando"
echo "     iac/policies/informs-ws-server-runtime.json"
echo "  3. Você popula os 2 secrets em informs-ws/* via secretsmanager:PutSecretValue"
echo "  4. Re-roda workflow: gh workflow run 'Deploy WS Server' --ref dev"
echo ""
echo "Detalhes em iac/policies/README.md"
