SHELL := /bin/bash
.DEFAULT_GOAL := help

# --- Configs ---
NETWORK ?= formularios-network
ENV_VARS ?= ./local/env.json
CDK_OUT ?= cdk.out
BUILD_SCRIPT ?= ./build_with_sam.sh
SAM ?= sam

# Template do CDK (stack)
STACK_TEMPLATE ?= $(CDK_OUT)/FormulariosStackdev.template.json

.PHONY: help template build local-api local-api-no-build local-bootstrap local-bootstrap-reset local-up local-down

help:
	@echo ""
	@echo "Targets:"
	@echo "  make local-bootstrap        # sobe docker compose + cria Dynamo (com GSIs)"
	@echo "  make local-bootstrap-reset  # idem, mas reseta a tabela local"
	@echo "  make local-up               # sobe somente docker compose local"
	@echo "  make local-down             # derruba docker compose local"
	@echo "  make local-api              # build_with_sam.sh + sam local start-api"
	@echo "  make build                  # roda apenas o build_with_sam.sh"
	@echo "  make local-api-no-build     # só sam local start-api (sem build)"
	@echo "  make template               # mostra qual template será usado"
	@echo "  make coverage			     # roda os testes e gera relatório de cobertura"
	@echo ""
	@echo "Vars úteis:"
	@echo "  STACK_TEMPLATE=cdk.out/OutraStack.template.json"
	@echo "  NETWORK=formularios-network"
	@echo "  ENV_VARS=./local/env.json"
	@echo "  BUILD_SCRIPT=./build_with_sam.sh"
	@echo ""

local-up:
	@docker compose -f ./local/docker-compose.yml up -d

local-down:
	@docker compose -f ./local/docker-compose.yml down

local-bootstrap:
	@if [[ -x ../venv/bin/python ]]; then \
		PYTHON_BIN=../venv/bin/python; \
	else \
		PYTHON_BIN=python3; \
	fi; \
	PYTHONPATH=.. $$PYTHON_BIN ./local/bootstrap_local.py

local-bootstrap-reset:
	@if [[ -x ../venv/bin/python ]]; then \
		PYTHON_BIN=../venv/bin/python; \
	else \
		PYTHON_BIN=python3; \
	fi; \
	PYTHONPATH=.. $$PYTHON_BIN ./local/bootstrap_local.py --reset-db

template:
	@if [[ ! -f "$(STACK_TEMPLATE)" ]]; then \
		echo "❌ Template não encontrado: $(STACK_TEMPLATE)"; \
		echo "   Rode seu build/synth do CDK para gerar o cdk.out, ou passe STACK_TEMPLATE=..."; \
		exit 1; \
	fi
	@echo "✅ Template: $(STACK_TEMPLATE)"

build:
	@if [[ ! -f "$(BUILD_SCRIPT)" ]]; then \
		echo "❌ Script não encontrado: $(BUILD_SCRIPT)"; exit 1; \
	fi
	@if [[ ! -x "$(BUILD_SCRIPT)" ]]; then \
		echo "ℹ️ Tornando executável: $(BUILD_SCRIPT)"; chmod +x "$(BUILD_SCRIPT)"; \
	fi
	@echo "▶ Rodando build: $(BUILD_SCRIPT)"
	@$(BUILD_SCRIPT)

local-api: build template
	@echo "▶ Subindo API local com SAM..."
	@$(SAM) local start-api \
		-t "$(STACK_TEMPLATE)" \
		--docker-network "$(NETWORK)" \
		--env-vars "$(ENV_VARS)"

local-api-no-build: template
	@echo "▶ Subindo API local com SAM (sem build)..."
	@$(SAM) local start-api \
		-t "$(STACK_TEMPLATE)" \
		--docker-network "$(NETWORK)" \
		--env-vars "$(ENV_VARS)"

coverage:
	@echo "▶ Rodando testes com cobertura, sem relatorios em html, apenas terminal"
	@cd .. && pytest --cov=src --cov-report=term-missing
