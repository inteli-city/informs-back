# ADR-0003: Pydantic para Validação e Contratos de API

**Status**: Aceito

**Data**: 2025-01-01

**Decisores**: Equipe Intelicity

**Tags**: validação, pydantic, contratos, api, schemas

## Contexto

O sistema recebe payloads JSON complexos via API Gateway (formulários com seções, campos polimórficos, justificativas, information fields). Precisávamos de:

- Validação robusta de tipos e formatos em tempo de execução
- Schemas reutilizáveis entre criação, submissão e listagem de formulários
- Geração automática de documentação OpenAPI/Swagger
- Mensagens de erro claras e localizáveis para o frontend

## Decisão

Adotamos **Pydantic v2** como framework de validação e definição de contratos em todas as camadas de entrada/saída.

**Organização dos schemas:**

```
src/shared/helpers/contracts/
├── base.py                          # RequestContractModel (base class)
├── schemas/
│   ├── field.py                     # GenericFieldSchema
│   ├── form.py                      # FormSectionSchema, FormResponseSchema
│   ├── justification.py             # JustificationOptionSchema
│   ├── information_field.py         # InformationFieldInputSchema (discriminated union)
│   ├── file_upload.py               # FileUploadSchema
│   └── template.py                  # TemplateSectionSchema
├── endpoints/
│   ├── create_form_contract.py      # CreateFormRequestSchema + ResponseSchema
│   ├── submit_form_contract.py      # SubmitFormRequestSchema
│   ├── cancel_form_contract.py      # CancelFormRequestSchema
│   ├── start_form_contract.py       # StartFormRequestSchema
│   └── create_template_contract.py  # CreateTemplateRequestSchema
└── runtime_requests.py              # Controller-level schemas com RequesterUser
```

**Padrões adotados:**
- `model_validate(data)` no Controller para validação de entrada
- `Field(ge=0, le=3)` para constraints numéricos (ex: priority)
- `model_validator(mode="after")` para validações cruzadas (ex: sections obrigatórias quando template ausente)
- `AliasChoices` para compatibilidade com nomes de campo legados (ex: `cognito:groups` / `cognito_groups`)
- `Discriminated Union` para campos polimórficos (information_field_type como discriminador)

**Geração OpenAPI:**
- Schemas Pydantic alimentam o módulo `docs` que gera `swagger.json` automaticamente
- Endpoint `/docs` serve a documentação interativa

## Consequências

### Positivas
- Validação de tipos em runtime com mensagens de erro detalhadas
- Schemas como fonte única de verdade para contratos da API
- Geração automática de OpenAPI/Swagger sempre sincronizada com o código
- Composição de schemas (FormSection contém GenericField, que pode ser qualquer field type)
- Parser de erros customizado (`pydantic_error_parser.py`) para mensagens user-friendly

### Negativas
- Schemas Pydantic e entidades de domínio são estruturas separadas — requerem conversão manual via DTOs
- Schemas complexos (discriminated unions, validators cruzados) podem ser difíceis de debugar
- Pydantic v2 tem breaking changes significativas em relação à v1, exigindo atenção em upgrades

## Alternativas Consideradas

### Marshmallow
- **Descrição**: Biblioteca de serialização/deserialização com validação
- **Motivo da rejeição**: Menos integração com tipagem Python nativa; ecossistema menor; não gera OpenAPI nativamente

### Validação manual (dicts + if/else)
- **Descrição**: Validar cada campo manualmente no controller
- **Motivo da rejeição**: Propenso a erros, não escalável para payloads complexos com campos polimórficos, sem geração de documentação
