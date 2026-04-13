# ADR-0012: Padrão DTO para Serialização entre Camadas

**Status**: Aceito

**Data**: 2025-01-01

**Decisores**: Equipe Intelicity

**Tags**: dto, serialização, camadas, dynamodb, clean-architecture

## Contexto

As entidades de domínio (Form, Section, Field, etc.) precisam ser convertidas para formatos diferentes conforme a camada:

- **DynamoDB**: Maps com convenções específicas (Decimal, reserved words, chaves compostas)
- **API Response**: JSON flat com campos serializados
- **API Request**: Payloads validados via Pydantic

Misturar essas preocupações dentro das entidades de domínio violaria a Clean Architecture.

## Decisão

Implementamos uma **camada de DTOs** dedicada em `src/shared/infra/dtos/` que converte entre domínio e infraestrutura.

**DTOs implementados:**

| DTO | Responsabilidade |
|-----|-----------------|
| `FormDynamoDTO` | Form ↔ DynamoDB item |
| `TemplateDTO` | Template ↔ DynamoDB item |
| `FieldDTO` | Field (polimórfico) ↔ DynamoDB map |
| `SectionDTO` | Section ↔ DynamoDB map / Request dict |
| `JustificationDTO` | Justification ↔ Request dict / DynamoDB map |
| `InformationFieldDTO` | InformationField ↔ DynamoDB map |
| `UserGatewayDTO` | Cognito claims → RequesterUser |
| `FileUploadDTO` | FileUpload ↔ Response dict |

**Padrão de conversão:**
```python
class FormDynamoDTO:
    @staticmethod
    def from_entity(form: Form) -> dict:
        # Entidade → Item DynamoDB
        return {"PK": f"form#{form.id}", "SK": "METADATA", ...}

    @staticmethod
    def to_entity(item: dict) -> Form:
        # Item DynamoDB → Entidade
        return Form(id=item["form_id"], ...)
```

**FieldDTO com Factory Pattern:**
O FieldDTO é especial por lidar com 10 tipos polimórficos. Usa um registry de builders:
```python
_FIELD_BUILDERS = {
    FIELD_TYPE.TEXT_FIELD: (required_set, build_function),
    FIELD_TYPE.FILE_FIELD: ({"file_type", "min_quantity", "max_quantity"}, _build_file_field),
    ...
}
```

Cada builder:
1. Valida campos obrigatórios do tipo (`_ensure_required`)
2. Constrói a entidade de domínio com os parâmetros corretos
3. Retorna `FieldDTO(field)` encapsulando a entidade

**Serialização para DynamoDB:**
```python
def to_dynamo(self) -> dict:
    # Serializa campos base (field_type, label, required, key, order)
    # + campos específicos do tipo (options, file_type, etc.)
    # Enums convertidos via .name, listas recursivamente serializadas
```

**Fluxo típico:**
```
Request JSON → Pydantic Schema (validação) → DTO.from_request() → Entity
Entity → DTO.to_dynamo() → DynamoDB Item
DynamoDB Item → DTO.from_dynamo() → Entity → Viewmodel → Response JSON
```

## Consequências

### Positivas
- Entidades de domínio puras — sem lógica de serialização ou dependências de infra
- Conversões DynamoDB centralizadas — tratamento de Decimal, reserved words em um só lugar
- FieldDTO factory garante que campos obrigatórios por tipo são sempre validados
- DTOs podem evoluir independentemente das entidades (ex: adicionar campo no DynamoDB sem alterar domínio)

### Negativas
- Camada adicional de código — cada entidade tem pelo menos um DTO correspondente
- Risco de dessincronização entre DTO e entidade se não mantidos juntos
- Conversão manual pode introduzir bugs sutis (ex: esquecer de converter um campo novo)
- FieldDTO é complexo (255+ linhas) devido aos 10 tipos polimórficos

## Alternativas Consideradas

### Serialização nas entidades (to_dict/from_dict)
- **Descrição**: Cada entidade sabe se converter para dict e vice-versa
- **Motivo da rejeição**: Acopla domínio à infraestrutura; entidade precisaria saber sobre DynamoDB, Decimal, etc.

### ORM (PynamoDB, dynamodb-toolbox)
- **Descrição**: Usar ORM que mapeia classes diretamente para DynamoDB
- **Motivo da rejeição**: Acopla domínio ao ORM; dificulta testes com mock; abstração a mais sobre algo que DTOs manuais resolvem bem
