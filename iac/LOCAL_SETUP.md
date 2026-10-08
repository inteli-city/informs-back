# Ambiente local do Informs

Back-end inteiro na sua máquina, sem conta na AWS: DynamoDB Local, S3 no
LocalStack e as Lambdas servidas por uma API HTTP local. O PWA
(`informs-front/clients/web`) fala com ela como fala com o API Gateway, e os
testes e2e do front rodam contra ela.

```
PWA (localhost:5174) ──HTTP──▶ API local (127.0.0.1:4010) ──▶ DynamoDB Local (:8000)
        │                       Lambdas no mesmo processo  └─▶ LocalStack S3  (:4566)
        └────── upload de fotos (URL assinada) ─────────────────▶ LocalStack S3
```

## Pré-requisitos

- Docker (Docker Desktop no Windows)
- Python 3.10+ com as dependências do projeto (`pip install -r requirements.txt`)

Não precisa de SAM, CDK, `.env` nem `env.json`: os defaults ficam em
`iac/local/local_env.py`, e qualquer variável definida no shell vence.

## Subir

Da raiz do `informs-back`:

```bash
python iac/local/bootstrap_local.py --seed   # containers, tabelas, bucket e dados de exemplo
python iac/local/local_api.py                # API em http://127.0.0.1:4010/mss-formularios
```

- `--reset-db` recria as tabelas, apagando os dados. Use `--reset-db --seed` para voltar ao estado inicial.
- Veja os dados no dynamodb-admin: http://localhost:8001
- Derrubar os containers: `docker compose -f iac/local/docker-compose.yml down`

Depois, no `informs-front/clients/web`: copie `.env.local.example` para
`.env.local` e rode `yarn dev`. A tela de login mostra **Entrar no ambiente
local**.

## O que cada peça faz

| Arquivo | Papel |
| --- | --- |
| `local/docker-compose.yml` | DynamoDB Local, dynamodb-admin e LocalStack (só S3) |
| `local/bootstrap_local.py` | Sobe os containers, espera ficarem prontos, cria tabelas e bucket (com CORS para o upload do navegador) |
| `local/create_dynamodb_tables.py` | As três tabelas do `dynamo_stack.py` (formulários com os GSIs `UserPriorityIndex`, `SystemUpdatedAtIndex` e `PoolIndex`; perfis com `ByRole`; localização) |
| `local/seed_local.py` | Templates de GAIA e UBERLANDIA, OS próprias em vários status e OS em aberto com foto no campo informativo |
| `local/local_api.py` | Recebe HTTP, monta o evento do API Gateway e chama o `lambda_handler` do módulo no mesmo processo |
| `local/local_env.py` | Variáveis de ambiente apontando para os containers |

### Autenticação

A API local lê as claims do JWT do header `Authorization` **sem validar a
assinatura**, como o autorizador local (`iac/authorizers/local_authorizer`).
Serve tanto o token de um login real no Gates quanto o token falso do login
local do front. O usuário do seed é
`10ca1000-0000-4000-8000-000000000001`, nos grupos `FORMULARIOS`, `GAIA` e
`UBERLANDIA`. O front usa os mesmos valores (`src/lib/local-auth.ts`).

Nunca exponha a API local fora da sua máquina: ela aceita qualquer token.

### Rotas

`local_api.py` espelha as rotas de `iac/iac/lambda_stack.py`. O teste
`tests/iac/local/test_local_api.py` falha se uma Lambda HTTP nova ficar de
fora. As Lambdas agendadas (`sync_forms_origin`, `reconcile_form_files`) não
têm rota: rode-as chamando o `lambda_handler` direto, se precisar.

## Testes e2e do front contra o ambiente local

Com o back-end de pé e o `.env.local` no `clients/web`:

```bash
npx playwright test
```

O `auth.setup.ts` usa o login local quando `VITE_LOCAL_AUTH=1` e pula o login
no Cognito. Os testes criam os próprios formulários; para recomeçar do zero,
`bootstrap_local.py --reset-db --seed`.

## Problemas conhecidos

- **LocalStack fixado na 4.9.** A partir da 2026.x a imagem `latest` exige
  conta e `LOCALSTACK_AUTH_TOKEN`, e o container sai com exit 55 sem eles.
- **Porta 4010, não 3000.** A 3000 costuma estar ocupada por outro dev server,
  e `localhost` pode resolver para IPv6 e cair nele. Use `127.0.0.1` na URL.
- **Service worker do PWA.** O cache de GETs do Workbox ignora endereços de
  loopback (`vite.config.ts`): o fetch do SW para `http://127.0.0.1` falha
  antes de sair. Depois de mudar o `vite.config.ts`, reinicie o `yarn dev`
  para o `dev-dist/sw.js` ser gerado de novo.

## Alternativa: SAM local

O caminho antigo continua no `Makefile` (`make local-api`): sobe as Lambdas com
`sam local start-api` a partir do template do CDK. Exige SAM CLI, CDK CLI, o
`.env` da raiz e o `iac/local/env.json`, e cada requisição sobe um container.
Serve para conferir o empacotamento das Lambdas, não para o dia a dia.
