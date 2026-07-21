#!/bin/bash

# Script para limpar cache e rebuildar com CDK + SAM
# Uso: ./build_with_sam.sh

set -e  # Para na primeira falha

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🚀 Clean Build - CDK + SAM${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar se está na pasta iac com app.py
if [[ ! -f "app.py" ]]; then
    echo -e "${RED}❌ Erro: arquivo app.py não encontrado${NC}"
    echo -e "${YELLOW}💡 Execute este script da pasta 'iac' onde está o app.py${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Pasta correta detectada${NC}"
echo ""

# Python command (prefere o venv do repositório quando disponível)
if [[ -x "../venv/bin/python" ]]; then
    PYTHON_BIN="../venv/bin/python"
else
    PYTHON_BIN="python3"
fi

ensure_python_dep() {
    local import_name="$1"
    local install_spec="$2"
    if ! "${PYTHON_BIN}" - <<PY >/dev/null 2>&1
import ${import_name}
PY
    then
        echo -e "${YELLOW}📦 Instalando dependência Python: ${install_spec}${NC}"
        "${PYTHON_BIN}" -m pip install "${install_spec}"
    fi
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}📚 Sincronizando OpenAPI (local)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

ensure_python_dep "pydantic" "pydantic==2.9.2"

echo -e "${YELLOW}🧩 Gerando OpenAPI JSON por contracts (Pydantic)...${NC}"
PYTHONPATH=.. "${PYTHON_BIN}" -m src.shared.helpers.functions.generate_openapi_from_contracts

echo -e "${GREEN}✅ OpenAPI sincronizado${NC}"
echo ""

# Remover cdk.out
if [[ -d "cdk.out" ]]; then
    echo -e "${YELLOW}🗑️  Removendo pasta cdk.out...${NC}"
    rm -rf cdk.out
    echo -e "${GREEN}✅ cdk.out removido${NC}"
else
    echo -e "${BLUE}ℹ️  Pasta cdk.out não existe${NC}"
fi

# Remover .aws-sam
if [[ -d ".aws-sam" ]]; then
    echo -e "${YELLOW}🗑️  Removendo pasta .aws-sam...${NC}"
    rm -rf .aws-sam
    echo -e "${GREEN}✅ .aws-sam removido${NC}"
else
    echo -e "${BLUE}ℹ️  Pasta .aws-sam não existe${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}📦 Executando CDK Synth...${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Executar cdk synth
cdk synth

echo ""
echo -e "${GREEN}✅ CDK Synth concluído${NC}"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🔨 Executando SAM Build...${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Executar sam build
sam build -t ./cdk.out/FormulariosStackdev.template.json

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Build concluído com sucesso!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo -e "${BLUE}💡 Próximos passos:${NC}"
echo -e "   Para rodar localmente:"
echo -e "   ${YELLOW}sam local start-api${NC}"
echo ""
echo -e "   Ou com variáveis de ambiente:"
echo -e "   ${YELLOW}sam local start-api --env-vars local/env.json${NC}"
echo ""
echo -e "   Para deploy:"
echo -e "   ${YELLOW}cdk deploy${NC}"
echo ""
