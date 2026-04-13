# ADR-0015: Organização Modular por Feature

**Status**: Aceito

**Data**: 2025-01-01

**Decisores**: Equipe Intelicity

**Tags**: arquitetura, módulos, organização, feature, lambda

## Contexto

O sistema possui 13 operações distintas (criar formulário, submeter, cancelar, listar, etc.). Precisávamos organizar o código de forma que:

- Cada operação seja autocontida e deployável independentemente (1 Lambda por operação)
- Mudanças em uma operação não impactem outras
- Novos desenvolvedores encontrem rapidamente o código de uma feature
- A estrutura escale sem conflitos de merge entre features paralelas

## Decisão

Adotamos **organização por feature** (vertical slicing), onde cada módulo contém todas as camadas necessárias para sua operação.

**Estrutura dos módulos:**
```
src/modules/
├── create_form/app/
│   ├── create_form_presenter.py      # Lambda handler
│   ├── create_form_controller.py     # Validação e orquestração
│   ├── create_form_usecase.py        # Lógica de negócio
│   └── create_form_viewmodel.py      # Serialização de resposta
├── submit_form/app/
│   ├── submit_form_presenter.py
│   ├── submit_form_controller.py
│   ├── submit_form_usecase.py
│   └── submit_form_viewmodel.py
├── cancel_form/app/             # Mesma estrutura
├── start_form/app/
├── get_form/app/
├── get_all_forms/app/
├── create_template/app/
├── update_template/app/
├── get_template/app/
├── get_all_templates/app/
├── sync_forms_origin/app/
├── sync_forms_origin_callback/app/
└── docs/app/
```

**13 módulos totais:**

| Módulo | Método | Rota | Descrição |
|--------|--------|------|-----------|
| `create_form` | POST | `/forms` | Criar formulário |
| `get_all_forms` | GET | `/forms` | Listar formulários |
| `get_form` | GET | `/forms/{id}` | Buscar formulário |
| `start_form` | POST | `/forms/{id}/start` | Iniciar preenchimento |
| `submit_form` | POST | `/forms/{id}/submit` | Submeter formulário |
| `cancel_form` | POST | `/forms/{id}/cancel` | Cancelar formulário |
| `create_template` | POST | `/templates` | Criar template |
| `get_all_templates` | GET | `/templates` | Listar templates |
| `get_template` | GET | `/templates/{id}` | Buscar template |
| `update_template` | PUT | `/templates/{id}` | Atualizar template |
| `sync_forms_origin` | EventBridge | — | Job de sincronização |
| `sync_forms_origin_callback` | POST | `/sync/callback` | Webhook de callback |
| `docs` | GET | `/docs` | Documentação OpenAPI |

**Código compartilhado (`src/shared/`):**
- Entidades, enums, interfaces de repositório (domínio)
- Implementações de repositório (infraestrutura)
- DTOs, schemas de validação, utilitários
- Erros, HTTP helpers, configuração

**Mapeamento 1:1 com Lambda:**
- Cada módulo corresponde a exatamente 1 Lambda function no CDK
- O CDK aponta `handler` para `{modulo}_presenter.lambda_handler`
- Todas as Lambdas compartilham a mesma Layer de dependências

**Testes espelhados:**
```
tests/modules/
├── create_form/app/
│   ├── test_create_form_controller.py
│   ├── test_create_form_usecase.py
│   └── test_create_form_presenter.py
├── submit_form/app/
│   └── ...
└── ...
```

## Consequências

### Positivas
- Isolamento total por feature — mudanças em `submit_form` não requerem deploy de `create_form`
- Facilidade de navegação — "onde fica a lógica de cancelamento?" → `src/modules/cancel_form/`
- Cold starts independentes por Lambda — payload leve por function
- Conflitos de merge minimizados — desenvolvedores trabalham em módulos diferentes
- Testes rodam por módulo: `pytest tests/modules/submit_form/ -v`

### Negativas
- Duplicação de padrão entre módulos (4 arquivos por feature com estrutura similar)
- Lógica compartilhada entre módulos (ex: validação de form status) precisa estar em `shared/`
- 13 Lambdas para gerenciar (configuração, monitoring, logs)
- Layer compartilhada precisa ser atualizada quando qualquer dependência muda

## Alternativas Consideradas

### Organização por camada (horizontal slicing)
- **Descrição**: `controllers/`, `usecases/`, `presenters/` com todos os handlers agrupados por tipo
- **Motivo da rejeição**: Mudança em uma feature requer editar múltiplos diretórios; dificulta isolamento; merge conflicts entre features

### Monolito Lambda (single handler)
- **Descrição**: Uma única Lambda com roteamento interno (ex: via Flask)
- **Motivo da rejeição**: Cold starts mais pesados; uma falha afeta todas as rotas; não aproveita scaling independente do Lambda por endpoint; billing menos eficiente
