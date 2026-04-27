# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests
pytest

# Run tests with coverage report
cd iac && make coverage
# equivalent: pytest --cov=src --cov-report=term-missing

# Run a single test file
pytest tests/modules/cancel_form/app/test_cancel_form_controller.py

# Run a single test function
pytest tests/modules/cancel_form/app/test_cancel_form_controller.py::TestClass::test_method

# Local development (requires Docker)
cd iac && make local-bootstrap      # spin up DynamoDB local + LocalStack, create tables
cd iac && make local-api            # build Lambda layer + start SAM local API
cd iac && make local-api-no-build   # start SAM local API without rebuilding
cd iac && make local-down           # tear down Docker containers
```

Prerequisites for local API: `.env` file at repo root (CDK config) and `iac/local/env.json` (SAM runtime env vars).

## Architecture

This is a **serverless Python backend** for a dynamic forms management system. It uses AWS Lambda + API Gateway + DynamoDB + S3, deployed via AWS CDK.

### Clean Architecture per module

Each module under `src/modules/` follows four strict layers:

```
Presenter  (lambda_handler — extracts Cognito claims, builds HttpRequest, returns HTTP response)
  └── Controller  (Pydantic validation of the request)
        └── Usecase  (business logic, orchestrates domain entities)
              └── Repository  (interface; DynamoDB/S3 impl in shared/infra, mock impl in shared/infra/mocks)
```

### Dependency injection via STAGE env var

`src/shared/environments.py` defines `Environments` with stages: `TEST`, `DEV`, `HOMOLOG`, `PROD`. The presenter injects the correct repository implementation at cold-start based on `STAGE`:
- `TEST` → in-memory mock repositories (used by all unit tests)
- `DEV`/`HOMOLOG`/`PROD` → real DynamoDB/S3 repositories

### Modules

`src/modules/` contains one directory per Lambda function:
- **Forms**: `create_form`, `get_form`, `get_all_forms`, `submit_form`, `cancel_form`
- **Templates**: `create_template`, `get_template`, `get_all_templates`, `update_template`
- **Sync**: `sync_forms_origin`, `sync_forms_origin_callback` (integration with external origin system)
- **Docs**: `docs` (OpenAPI/Swagger generation)

### Shared layer (`src/shared/`)

- `domain/entities/` — core domain models (`Form`, `Template`, `Field`, `Section`, etc.)
- `domain/enums/` — state machines and field types
- `domain/repositories/` — abstract repository interfaces
- `infra/repos/` — DynamoDB and S3 concrete implementations
- `infra/mocks/` — in-memory implementations used by tests
- `helpers/errors/` — typed error hierarchy (used across all layers)
- `helpers/external_interfaces/` — `HttpRequest`/`HttpResponse` abstractions and Lambda adapters
- `helpers/http/` — Pydantic request/response contracts per module

### Infrastructure (`iac/`)

- `app.py` — CDK app entry point
- `iac/iac_stack.py` — API Gateway, Cognito, S3, IAM
- `iac/lambda_stack.py` — all Lambda functions, routes, and environment variables
- `local/` — Docker Compose for DynamoDB-local + LocalStack, bootstrap script, env templates

### DynamoDB

Single-table design with composite PK/SK keys. All entity access patterns are defined in the repository implementations under `src/shared/infra/repos/`.

### Testing pattern

All tests use mock repositories — no AWS credentials or infrastructure needed. Tests are co-located under `tests/modules/{module_name}/app/` mirroring the source structure.
