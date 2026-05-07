# ADR-0001: Clean Architecture com Python e AWS Lambda

**Status**: Aceito

**Data**: 2025-01-01

**Decisores**: Equipe Intelicity

**Tags**: arquitetura, clean-architecture, python, lambda, camadas

## Contexto

O Informs Backend é o serviço serverless responsável pela geração e pelo preenchimento de formulários em campo na plataforma Intelicity.

A decisão arquitetural foi guiada principalmente por:

- Familiaridade do time com Python e AWS Lambda
- Necessidade de entregar rápido com uma base organizada
- Falta de clareza sobre escala, volumetria e integrações futuras

Ou seja, não havia ainda informação suficiente para otimizar a arquitetura para alta escala ou cenários complexos.

Buscamos apenas:

- Separar minimamente regra de negócio da infraestrutura
- Permitir testes unitários básicos
- Manter o código organizado para evolução futura

## Decisão

Adotamos uma variação simples de Clean Architecture adaptada para Lambda.

A escolha foi motivada mais por organização de código e familiaridade do time do que por necessidade comprovada de uma arquitetura mais robusta.

A estrutura por camadas foi utilizada para evitar acoplamento direto com AWS e facilitar manutenção futura, caso o sistema cresça em complexidade.

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

A arquitetura poderá ser simplificada ou evoluída conforme o comportamento real do sistema em produção.

## Consequências

### Positivas
- Lógica de negócio 100% testável sem AWS — testes rodam com Mocks em memória
- Repositórios intercambiáveis — DynamoDB em produção, Mock em testes, sem alterar usecases
- Cada módulo é autocontido — mudanças em `submit_form` não afetam `create_form`
- Presenter isola preocupações de Lambda (parsing de eventos, claims Cognito)
- Viewmodel garante formato de resposta consistente e desacoplado do domínio
- Base preparada para evolução futura

### Negativas
- Overengineering para o momento atual
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
