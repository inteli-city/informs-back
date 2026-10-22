[![codecov](https://codecov.io/gh/inteli-city/formularios_mss/graph/badge.svg?token=UB200QTY0I)](https://codecov.io/gh/inteli-city/formularios_mss)

![Graph](https://codecov.io/gh/inteli-city/formularios_mss/graphs/sunburst.svg?token=UB200QTY0I)

# Informs Backend

Backend serverless do **Informs**, app da Intelicity para geração e preenchimento de formulários em campo.

O serviço permite criar templates reutilizáveis, gerar formulários dinâmicos, distribuir formulários para usuários, registrar preenchimentos, anexar arquivos via URLs pré-assinadas e sincronizar formulários preenchidos com sistemas de origem. Usa AWS Lambda, API Gateway, DynamoDB single-table, S3 para uploads e CDK para infraestrutura.

## Comandos

```bash
venv\Scripts\python.exe -m pytest
venv\Scripts\python.exe -m pytest --cov=src --cov-report=term-missing
venv\Scripts\python.exe -m src.shared.helpers.functions.generate_openapi_from_contracts
```

Para desenvolvimento local com SAM/DynamoDB Local, veja `iac/LOCAL_SETUP.md`.

## Domínio

- **Templates**: modelos reutilizáveis com seções e campos.
- **Formulários**: instâncias criadas a partir de templates ou estruturas ad-hoc.
- **Campos**: tipos polimórficos como texto, número, data, seleção, checkbox, arquivo e informações complementares.
- **Preenchimento em campo**: ciclo de vida com início, submissão, cancelamento, anexos e justificativas.
- **Sincronização**: envio periódico dos formulários preenchidos para sistemas de origem da Intelicity.

## Variáveis principais

- `STAGE`: `TEST`, `DEV`, `HOMOLOG`, `PROD` ou `DOTENV`.
- `DYNAMO_TABLE_NAME`, `DYNAMO_PARTITION_KEY`, `DYNAMO_SORT_KEY`.
- `BUCKET_NAME`.
- `USER_POOL_ARN`, `USER_POOL_ID`, `APP_CLIENT_ID`.
- `SYNC_FORMS_PAGE_LIMIT`, `SYNC_FORMS_WINDOW_MINUTES`, `SYNC_FORMS_FIRST_RUN_FULL_SYNC`.

## Envio ao Apex por origem

O envio ao Apex só sai de PROD por padrão (`APEX_SYNC_ENABLED`). Fora de PROD, o checkpoint avança e nada é
enviado, por causa do incidente de 08/09/2026 (ver ADR-0010 e ADR-0021).

Para habilitar uma origem em DEV, sem ligar as demais:

```bash
cd iac
cdk deploy -c apex_sync_enabled_origins=uberlandia
```

- Vale a lista separada por vírgula. Origem que não existe em `SYSTEM_TO_ORIGIN` é ignorada, com aviso no log.
- Sem o contexto, a variável fica vazia e nenhuma origem envia fora de PROD.
- `APEX_URL_<ORIGEM>` troca a URL inteira de uma origem, sem deploy de código.
- Origens: `gaia` e `servicos_poa` (GIPAV) usam os endpoints que já existiam. `uberlandia` usa o host do GAIA
  com o alias `supervisao`.

**Estado (22/10/2026):** a origem `uberlandia` está **ligada em DEV**, com
`cdk deploy -c apex_sync_enabled_origins=uberlandia`. GAIA, GIPAV e as demais seguem travadas fora de PROD. O
endpoint é `.../ords/supervisao/informs/cadastrar_formulario`, validado com o responsável do Apex (Henrique Curci)
com envios de teste: HTTP 200, com `gravados` igual ao enviado.

**Como se faz o deploy de DEV hoje:** o workflow `CD.yml` **não roda**, porque as Actions do repositório estão
desligadas. O deploy de DEV é local: `cdk deploy` a partir da máquina de quem tem acesso à conta de DEV. Os valores
que o CD tirava dos secrets (user pool, bucket, Kuma, `RECONCILE_SYSTEMS`) são lidos da Lambda já implantada e
exportados sem serem impressos, junto com `-c apex_sync_enabled_origins=uberlandia`. Se o CD voltar, ele **não**
passa esse contexto: seria preciso um secret ou variável no workflow.

**Armadilha do deploy local no Mac (incidente de 22/10/2026):** o `iac/adjust_layer_directory.py` monta a layer das
Lambdas com `pip install -r lambda_layer_requirements.txt -t ...` usando o **pip da máquina que roda o CDK**. Num Mac
ele instala binários de macOS (ex.: `pydantic_core/_pydantic_core.cpython-310-darwin.so`), e a Lambda (Linux x86_64,
Python 3.10) falha ao iniciar com `Runtime.ImportModuleError: No module named 'pydantic_core._pydantic_core'`. Como
as 35 Lambdas usam a mesma layer, o DEV inteiro ficou fora (21:27 a 21:39 UTC de 22/10). O CD do GitHub (Ubuntu) não
tem o problema. Antes do `cdk deploy`, exporte as quatro variáveis — o mesmo pip passa a baixar wheels Linux:

```bash
export PIP_PLATFORM=manylinux2014_x86_64 PIP_PYTHON_VERSION=3.10 PIP_IMPLEMENTATION=cp PIP_ONLY_BINARY=:all:
```

O `cdk diff` **não** mostra esse problema (só diz que a layer muda), e o status `UPDATE_COMPLETE` do deploy **também
não basta**: a função sobe pela CloudFormation e só falha na primeira invocação. Confira depois do deploy:

1. Dispare uma invocação do sync e leia o log da função em `/aws/lambda/<função do sync>`: **não** pode haver
   `ImportModuleError`.
2. Confira que a layer atual traz `_pydantic_core.cpython-310-x86_64-linux-gnu.so` e **nenhum** arquivo `darwin`.

**Pendência conhecida:** `RECONCILE_SYSTEMS` do deploy ainda não lista `UBERLANDIA`. A reconciliação registra um aviso
para o sistema.

**Comportamentos que já existiam e não mudaram:** o checkpoint avança mesmo quando o Apex falha (a recuperação é pela
fila `SyncErrorForm`). Com a trava fechada, o resumo conta os formulários como `sent`.

E2E local com um Apex falso, fora do pytest (precisa do DynamoDB Local e do LocalStack de pé, e de
`python iac/local/bootstrap_local.py --reset-db --seed`). A guarda recusa qualquer origem que não aponte para
localhost:

```bash
python iac/local/e2e_sync_uberlandia.py --saida rodada-1   # exit 0 só se os 13 cenários passarem; grava em iac/local/.e2e-saida/rodada-1
python iac/local/e2e_sync_uberlandia.py --so-guarda --sem-sobrescrita-de gaia   # prova a recusa (exit 2)
```

`--saida` é uma subpasta de `iac/local/.e2e-saida`: caminho que sai dela (com `..` ou absoluto) é recusado antes de
qualquer cenário.

Não foi feito: envio real de Uberlândia ao Apex de produção. Em DEV, o envio já foi validado com o Apex, como descrito
acima.

## Estrutura

- `src/modules`: Lambdas por feature.
- `src/shared/domain`: entidades, enums e interfaces do domínio.
- `src/shared/infra`: repositórios DynamoDB/S3 e DTOs.
- `src/shared/helpers/contracts`: contratos Pydantic e geração OpenAPI.
- `iac`: CDK, SAM local e scripts de bootstrap.

## Documentação

- `docs/adr`: decisões arquiteturais do projeto.
- `iac/README.md`: visão geral da infraestrutura como código.
- `iac/LOCAL_SETUP.md`: setup local com SAM, DynamoDB Local e LocalStack.
