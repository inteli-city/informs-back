# ADR-0004: Sistema de Campos Polimórficos (Field Hierarchy)

**Status**: Aceito

**Data**: 2025-01-01

**Decisores**: Equipe Intelicity

**Tags**: domínio, campos, polimorfismo, formulários, design-pattern

## Contexto

Formulários dinâmicos precisam suportar múltiplos tipos de campo (texto, número, dropdown, arquivo, etc.), cada um com propriedades e validações específicas. O sistema precisa:

- Permitir que cada tipo de campo tenha atributos exclusivos (ex: `options` para dropdown, `file_type` para arquivo)
- Validar campos obrigatórios específicos por tipo na criação e submissão
- Serializar/deserializar campos para DynamoDB preservando o tipo
- Ser extensível para novos tipos de campo sem alterar código existente

## Decisão

Implementamos uma **hierarquia de classes com herança** usando uma classe base abstrata `Field` e subclasses concretas para cada tipo.

**Hierarquia:**
```
Field (base)
├── TextField          — regex, max_length, formatting
├── NumberField         — decimal (bool), min_value, max_value
├── DropDownField       — options (list)
├── TypeAheadField      — options (list), max_length
├── RadioGroupField     — options (list)
├── DateField           — min_date, max_date (timestamps)
├── CheckboxField       — value (bool)
├── CheckBoxGroupField  — options (list), check_limit
├── SwitchButtonField   — value (bool)
└── FileField           — file_type (IMAGE|DOCUMENT), min_quantity, max_quantity
```

**Enum FIELD_TYPE** define os 10 tipos suportados:
```python
TEXT_FIELD, NUMBER_FIELD, DROPDOWN_FIELD, TYPEAHEAD_FIELD,
RADIO_GROUP_FIELD, DATE_FIELD, CHECKBOX_FIELD,
CHECKBOX_GROUP_FIELD, SWITCH_BUTTON_FIELD, FILE_FIELD
```

**FieldDTO como Factory:** O `FieldDTO` usa um padrão de **registry/factory** para construir e validar campos:

```python
_FIELD_BUILDERS = {
    FIELD_TYPE.TEXT_FIELD:           (set(),                                    _build_text_field),
    FIELD_TYPE.NUMBER_FIELD:         ({"decimal"},                              _build_number_field),
    FIELD_TYPE.DROPDOWN_FIELD:       ({"options"},                              _build_dropdown_field),
    FIELD_TYPE.FILE_FIELD:           ({"file_type", "min_quantity", "max_quantity"}, _build_file_field),
    ...
}
```

Cada entrada define: `(campos_obrigatórios, função_construtora)`. Isso garante validação automática dos campos obrigatórios por tipo antes da construção.

**Campos comuns a todos os tipos:**
- `field_type` (str) — identifica o tipo
- `label` (str) — rótulo visível
- `required` (bool) — se é obrigatório no preenchimento
- `key` (str) — identificador único dentro da seção
- `order` (int) — posição de exibição
- `help_text` (str, opcional) — texto de ajuda
- `value` (Any, opcional) — valor preenchido

## Consequências

### Positivas
- Cada tipo de campo encapsula suas próprias regras de validação
- Factory pattern centraliza a lógica de construção — adicionar novo tipo requer apenas nova entrada no registry
- Campos obrigatórios por tipo são declarativos (set no registry), não imperativos
- Serialização para DynamoDB via `to_dynamo()` é genérica e extensível
- Sistema suporta tanto criação de formulário (sem value) quanto submissão (com value)

### Negativas
- Hierarquia com 10 subclasses gera volume de código significativo
- Alterações na classe base podem impactar todos os tipos
- CheckBoxGroupField tem lógica de normalização de value complexa (dict → list de bools)

## Alternativas Consideradas

### Dicionários puros (sem classes)
- **Descrição**: Representar campos como dicts simples com validação ad-hoc
- **Motivo da rejeição**: Sem encapsulamento de regras por tipo; validações espalhadas pelo código; propenso a erros silenciosos

### Schema-driven (JSON Schema para cada tipo)
- **Descrição**: Definir tipos de campo via JSON Schema externo validado em runtime
- **Motivo da rejeição**: Maior complexidade de infraestrutura; perde os benefícios de tipagem estática do Python; mais difícil de debugar
