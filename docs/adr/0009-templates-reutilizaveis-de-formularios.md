# ADR-0009: Templates Reutilizáveis de Formulários

**Status**: Aceito

**Data**: 2025-01-01

**Decisores**: Equipe Intelicity

**Tags**: templates, formulários, reuso, domínio

## Contexto

Muitos formulários compartilham a mesma estrutura (mesmas seções e campos). Criar cada formulário do zero é repetitivo e propenso a inconsistências. Precisávamos de:

- Um mecanismo para pré-definir estruturas de formulário reutilizáveis
- Capacidade de ativar/desativar templates sem excluí-los
- Possibilidade de criar formulários a partir de um template ou de uma estrutura ad-hoc

## Decisão

Implementamos **Templates** como entidades independentes que servem de modelo para criação de formulários.

**Entidade Template:**
- `template_id` — UUID gerado automaticamente
- `name` — Nome descritivo do template
- `system` — Sistema ao qual pertence (GAIA, SGC, etc.)
- `description` — Descrição opcional
- `is_active` — Flag de ativação (templates inativos não aparecem em listagens padrão)
- `sections` — Lista de seções com campos (mesma estrutura do formulário)
- Métodos de mutação: `change_name()`, `change_description()`, `change_sections()`, `change_is_active()`

**Relação Template → Formulário:**
- Na criação de formulário (`create_form`), o campo `template` é opcional:
  - Se `template` é um UUID válido → busca o template no repositório e usa suas seções
  - Se `template` é ausente ou não é UUID → `sections` deve ser fornecido no payload
- Validação via `model_validator`:
```python
@model_validator(mode="after")
def validate_sections_when_template_absent(self):
    if self.sections is None:
        if self.template is None or not _is_uuid(self.template):
            raise ValueError("sections is required when template is not a UUID")
    return self
```

**Módulos de Template:**
| Módulo | Operação |
|--------|----------|
| `create_template` | Cria novo template com seções |
| `update_template` | Atualiza nome, descrição, seções, is_active |
| `get_template` | Busca template por ID |
| `get_all_templates` | Lista templates por sistema com filtros (nome, is_active) e paginação |

**Persistência:**
- Templates são armazenados na mesma tabela DynamoDB com PK=`template#{id}`, SK=`METADATA`
- Seções são serializadas como atributo nested (lista de maps)

## Consequências

### Positivas
- Formulários padronizados — mesma estrutura garantida entre múltiplos formulários
- Templates inativos preservam histórico sem poluir listagens
- Flexibilidade — formulários podem ser criados com ou sem template
- Seções do template são copiadas (deep copy) — alterações no template não afetam formulários existentes

### Negativas
- Sem versionamento de templates — ao alterar um template, a versão anterior é sobrescrita
- Templates e formulários compartilham a mesma tabela DynamoDB — podem competir por throughput
- Sem validação de que o template pertence ao mesmo sistema do formulário

## Alternativas Consideradas

### Templates embutidos no código (hardcoded)
- **Descrição**: Definir templates como constantes no código fonte
- **Motivo da rejeição**: Cada novo template exigiria deploy; não permite gestão por usuários não-técnicos

### Templates como JSON em S3
- **Descrição**: Armazenar templates como arquivos JSON no S3
- **Motivo da rejeição**: Sem suporte a queries (filtro por sistema, nome, status); sem controle de concorrência na edição
