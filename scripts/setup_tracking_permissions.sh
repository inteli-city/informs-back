#!/usr/bin/env bash
# Setup das permissões IAM necessárias pro deploy da feature de tracking.
#
# Roda UMA vez, com credenciais admin (não o user do CI). Depois disso:
#   1. cdk deploy FormulariosTrackingStack (1 vez, manual)
#   2. push em dev/homolog/prod dispara o workflow GH Actions que vai
#      conseguir rodar deploy_ws_server.sh (porque o user do CI agora
#      tem as permissões mínimas).
#
# 2 policies criadas:
#
# A. tracking-stack-deploy-admin (pro user que vai rodar cdk deploy):
#    Permissões amplas em Lightsail/SecretsManager/IAM/DynamoDB pra
#    provisionar tudo via CFN.
#
# B. tracking-runtime-ci (pro user do GitHub Actions):
#    Permissões MÍNIMAS pro deploy_ws_server.sh ler o que precisa.
#
# Os dois podem ser o mesmo user (ex: o que já está em AWS_ACCESS_KEY_ID
# do GH repo), mas se separar usa só a B no CI.

set -euo pipefail

# ===== Config =====
ADMIN_USER_NAME="${ADMIN_USER_NAME:-rodrigosiqueira}"  # quem roda cdk deploy
CI_USER_NAME="${CI_USER_NAME:-rodrigosiqueira}"        # quem roda GH Actions
REGION="${AWS_REGION:-sa-east-1}"

echo "==> Anexando policy A (tracking-stack-deploy-admin) ao user ${ADMIN_USER_NAME}"
aws iam put-user-policy \
    --user-name "${ADMIN_USER_NAME}" \
    --policy-name tracking-stack-deploy-admin \
    --policy-document file://"$(dirname "$0")"/../iac/policies/tracking-stack-deploy-admin.json

echo "==> Anexando policy B (tracking-runtime-ci) ao user ${CI_USER_NAME}"
aws iam put-user-policy \
    --user-name "${CI_USER_NAME}" \
    --policy-name tracking-runtime-ci \
    --policy-document file://"$(dirname "$0")"/../iac/policies/tracking-runtime-ci.json

echo "==> OK. Próximos passos:"
echo "  1. cd iac"
echo "  2. AWS_REGION=${REGION} AWS_ACCOUNT_ID=\$(aws sts get-caller-identity --query Account --output text) \\"
echo "     STACK_NAME=FormulariosStackdev GITHUB_REF_NAME=dev \\"
echo "     USER_POOL_ARN=... USER_POOL_ID=... APP_CLIENT_ID=... BUCKET_NAME=... \\"
echo "     npx cdk deploy FormulariosTrackingStack --app \"python app.py\" --require-approval never"
echo "  3. Após sucesso, dispara o workflow GH Actions (push em ws_server/** ou workflow_dispatch)."
