# ADR-0013: Hierarquia de Erros e Mapeamento HTTP

**Status**: Aceito

**Data**: 2025-01-01

**Decisores**: Equipe Intelicity

**Tags**: erros, http, mapeamento, clean-architecture, exceções

## Contexto

O sistema precisa comunicar erros de diferentes camadas (domínio, usecase, controller) para o cliente via HTTP de forma consistente. Precisávamos de:

- Erros tipados por camada (não misturar erros de validação com erros de negócio)
- Mapeamento determinístico de exceção → status HTTP
- Mensagens de erro claras e úteis para o frontend
- Tratamento centralizado no controller (try/catch único)

## Decisão

Implementamos uma **hierarquia de exceções por camada** com mapeamento para HTTP status codes no Controller.

**Hierarquia de erros:**

```
BaseError
├── domain_errors (src/shared/helpers/errors/domain_errors.py)
│   └── EntityError              → 400 Bad Request
│       ├── EntityParameterTypeError
│       └── EntityParameterError
├── usecase_errors (src/shared/helpers/errors/usecase_errors.py)
│   ├── NoItemsFound             → 404 Not Found
│   ├── DuplicatedItem           → 409 Conflict
│   ├── ForbiddenAction          → 403 Forbidden
│   ├── ErrorWithFile            → 500 Internal Server Error
│   └── InvalidPaginationToken   → 400 Bad Request
└── controller_errors (src/shared/helpers/errors/controller_errors.py)
    ├── MissingParameters        → 400 Bad Request
    └── WrongTypeParameter       → 400 Bad Request
```

**Mapeamento no Controller (padrão em todos os módulos):**
```python
def __call__(self, request: IRequest) -> IResponse:
    try:
        # ... lógica do controller
        return Created(viewmodel.to_dict())
    except ValidationError as err:
        return BadRequest(body=get_validation_error_message(err))
    except NoItemsFound as err:
        return NotFound(body=err.message)
    except DuplicatedItem as err:
        return Conflict(body=err.message)
    except MissingParameters as err:
        return BadRequest(body=err.message)
    except ForbiddenAction as err:
        return Forbidden(body=err.message)
    except WrongTypeParameter as err:
        return BadRequest(body=err.message)
    except EntityError as err:
        return BadRequest(body=f"Parâmetro inválido: {err.message}")
    except Exception as err:
        return InternalServerError(body=err.args[0])
```

**HTTP Response helpers (`src/shared/helpers/external_interfaces/http_codes.py`):**
```python
class OK(IResponse):         status_code = 200
class Created(IResponse):    status_code = 201
class NoContent(IResponse):  status_code = 204
class BadRequest(IResponse): status_code = 400
class Forbidden(IResponse):  status_code = 403
class NotFound(IResponse):   status_code = 404
class Conflict(IResponse):   status_code = 409
class InternalServerError:   status_code = 500
```

**Parser de erros Pydantic:**
- `get_validation_error_message(err)` converte `ValidationError` em mensagem legível
- Extrai campo e tipo de erro do Pydantic para mensagens como "Parâmetro ausente: field_name"

**Formato de resposta de erro:**
```json
{
    "statusCode": 400,
    "body": "{\"error_message\": \"Parâmetro ausente: form_title\"}"
}
```

## Consequências

### Positivas
- Cada camada lança exceções do seu domínio — sem acoplamento cruzado
- Mapeamento exceção → HTTP é explícito e previsível
- Controller é o único ponto de tradução — usecases nunca retornam HTTP codes
- `Exception` genérica sempre capturada como 500 — nenhuma exceção escapa sem tratamento
- Mensagens em português para o frontend consumir diretamente

### Negativas
- Try/catch extenso duplicado em cada controller (boilerplate)
- Adicionar novo tipo de erro requer atualizar todos os controllers
- Exceção genérica (`Exception`) como catch-all pode mascarar bugs
- Sem código de erro padronizado (apenas mensagem textual) — dificulta i18n

## Alternativas Consideradas

### Códigos de erro numéricos
- **Descrição**: Cada erro com código único (ex: E1001, E1002) além do HTTP status
- **Motivo da rejeição**: Complexidade adicional para um sistema com poucos tipos de erro; mensagens textuais são suficientes para o frontend atual

### Middleware de erro global
- **Descrição**: Interceptar exceções em uma camada acima do controller
- **Motivo da rejeição**: No modelo Lambda, cada handler é isolado; não há middleware compartilhado como em frameworks web; o try/catch no controller é o equivalente natural
