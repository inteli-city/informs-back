# ADR-0007: Padrão Repository com Mock e DynamoDB

**Status**: Aceito

**Data**: 2025-01-01

**Decisores**: Equipe Intelicity

**Tags**: repository, padrão, mock, dynamodb, testes, clean-architecture

## Contexto

Os usecases precisam acessar dados (formulários, templates, arquivos, estados de sync) sem se acoplar a uma tecnologia de persistência específica. Também precisávamos rodar testes unitários rápidos sem depender de serviços AWS reais.

## Decisão

Adotamos o **padrão Repository** com interfaces abstratas no domínio e duas implementações concretas: DynamoDB (produção) e Mock (testes).

**Interfaces definidas em `src/shared/domain/repositories/`:**

| Interface | Responsabilidade |
|-----------|-----------------|
| `IFormRepository` | CRUD de formulários, queries por usuário/sistema/status |
| `ITemplateRepository` | CRUD de templates, busca por sistema |
| `IFileRepository` | Geração de presigned URLs para S3 |
| `ISyncStateRepository` | Estado de checkpoint de sincronização |
| `ISyncErrorFormRepository` | Registro de formulários com erro de sync |
| `IOriginRepository` | Envio de formulários ao sistema de origem |

**Implementações concretas em `src/shared/infra/repositories/`:**

```
repositories/
├── form_repository_dynamo.py       # DynamoDB
├── form_repository_mock.py         # In-memory (testes)
├── template_repository_dynamo.py
├── template_repository_mock.py
├── file_repository_s3.py           # S3 presigned URLs
├── file_repository_mock.py         # Mock URLs
├── sync_state_repository_dynamo.py
├── sync_state_repository_mock.py
├── sync_error_form_repository_dynamo.py
├── sync_error_form_repository_mock.py
└── origin_repository_apex.py       # HTTP para Oracle Apex
```

**Injeção de dependência via `Environments`:**
```python
class Environments:
    @staticmethod
    def get_form_repo() -> IFormRepository:
        if os.environ.get("STAGE") == "TEST":
            return FormRepositoryMock()
        return FormRepositoryDynamo()
```

**Mock Repositories:**
- Usam listas em memória (`self.forms = [...]`)
- Pré-populados com dados de teste (3 formulários com diferentes status)
- Implementam exatamente a mesma interface que os repositórios reais
- Permitem inspeção direta do estado interno nos testes (`repo.forms[0].status`)

**Composição no Presenter (ponto de entrada):**
```python
repo = Environments.get_form_repo()
file_repo = Environments.get_file_repo()
usecase = CreateFormUsecase(repo, file_repo)
controller = CreateFormController(usecase)
```

## Consequências

### Positivas
- Usecases 100% agnósticos de infraestrutura — mesmo código roda com DynamoDB ou Mock
- Testes unitários rodam em <1 segundo sem dependências externas
- Mocks pré-populados com dados realistas facilitam cenários de teste variados
- Adicionar nova implementação (ex: PostgreSQL) requer apenas implementar a interface
- Composição explícita no Presenter — sem magia de DI framework

### Negativas
- Mocks precisam ser mantidos sincronizados com a interface real
- Mocks simplificam comportamentos (ex: não validam indexes únicos como DynamoDB)
- Sem framework de DI, cada Presenter faz a composição manualmente (duplicação)

## Alternativas Consideradas

### Acesso direto ao DynamoDB nos usecases
- **Descrição**: Importar boto3 diretamente nos usecases sem abstração
- **Motivo da rejeição**: Impossibilita testes unitários sem LocalStack; acopla lógica de negócio à infraestrutura

### Framework de DI (dependency-injector, python-inject)
- **Descrição**: Usar container de injeção de dependência com decorators
- **Motivo da rejeição**: Overhead de complexidade para um projeto com composição simples; Lambda functions têm lifecycle curto; composição manual no Presenter é suficiente e explícita
