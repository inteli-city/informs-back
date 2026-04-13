# ADR-0001: Clean Architecture com Python e AWS Lambda

**Status**: Aceito

**Data**: 2025-01-01

**Decisores**: Equipe Intelicity

**Tags**: arquitetura, clean-architecture, python, lambda, camadas

## Contexto

O MSS Formulários (mss-formularios) é um microserviço serverless responsável por gerenciar formulários dinâmicos na plataforma Intelicity. Precisávamos de uma arquitetura que:

- Isolasse a lógica de negócio da infraestrutura AWS (Lambda, DynamoDB, S3)
- Permitisse testes unitários sem dependências externas
- Facilitasse a manutenção e evolução do sistema por múltiplos desenvolvedores
- Suportasse troca de implementações de infraestrutura sem impactar regras de negócio

## Decisão

Adotamos uma variação de **Clean Architecture** adaptada para o contexto serverless com Python. Cada módulo (feature) segue a estrutura:

```
src/modules/{modulo}/app/
├── {modulo}_presenter.py    # Ponto de entrada Lambda (lambda_handler)
├── {modulo}_controller.py   # Validação de entrada e orquestração
├── {modulo}_usecase.py      # Lógica de negócio pura
└── {modulo}_viewmodel.py    # Serialização de saída
```

**Fluxo de execução:**
```
API Gateway → Lambda Event
  → Presenter (extrai claims Cognito, monta HttpRequest)
    → Controller (valida via Pydantic, converte DTOs)
      → Usecase (lógica de negócio, opera sobre entidades)
        → Repository Interface (abstração de persistência)
          → Viewmodel (serializa resposta)
            → HttpResponse → API Gateway
```

**Regras de dependência (apontam para dentro):**
- **Presenter**: conhece Controller, Usecase, Repositories (composição)
- **Controller**: conhece Usecase, Schemas, DTOs
- **Usecase**: conhece apenas Domain (Entities, Enums, Repository Interfaces)
- **Domain**: não conhece nenhuma camada externa

**Camada compartilhada (`src/shared/`):**
- `domain/entities/` — Entidades de domínio (Form, Section, Field, etc.)
- `domain/enums/` — Enums de valor (FIELD_TYPE, FORM_STATUS, PRIORITY, etc.)
- `domain/repositories/` — Interfaces abstratas de repositórios
- `infra/repositories/` — Implementações concretas (DynamoDB, S3, Mock)
- `infra/dtos/` — DTOs para conversão entre camadas
- `helpers/contracts/` — Schemas Pydantic de validação
- `helpers/errors/` — Hierarquia de erros
- `helpers/external_interfaces/` — Abstrações HTTP e EventBridge
- `helpers/functions/` — Utilitários (paginação, URLs S3, etc.)
- `environments.py` — Configuração e injeção de dependência

## Consequências

### Positivas
- Lógica de negócio 100% testável sem AWS — testes rodam com Mocks em memória
- Repositórios intercambiáveis — DynamoDB em produção, Mock em testes, sem alterar usecases
- Cada módulo é autocontido — mudanças em `submit_form` não afetam `create_form`
- Presenter isola preocupações de Lambda (parsing de eventos, claims Cognito)
- Viewmodel garante formato de resposta consistente e desacoplado do domínio

### Negativas
- Mais boilerplate por módulo (4 arquivos por feature mesmo para operações simples)
- Curva de aprendizado para novos desenvolvedores entenderem o fluxo entre camadas
- Duplicação de estrutura entre módulos que compartilham padrões similares

## Alternativas Consideradas

### Monolítico com Flask/FastAPI
- **Descrição**: Usar um framework web tradicional em um único Lambda ou container
- **Motivo da rejeição**: Maior acoplamento com framework, cold starts mais pesados, não aproveita o modelo de billing por invocação do Lambda

### Sem separação de camadas (Handler direto)
- **Descrição**: Toda lógica no lambda_handler, sem controller/usecase/viewmodel
- **Motivo da rejeição**: Impossível testar lógica de negócio isoladamente; dificulta manutenção conforme o sistema cresce
