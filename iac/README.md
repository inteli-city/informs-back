
# Infraestrutura do Informs Backend

Este diretório contém a infraestrutura como código do **Informs Backend**, o backend da Intelicity para geração e preenchimento de formulários em campo.

O projeto usa AWS CDK em Python para definir API Gateway, Lambdas, DynamoDB, S3, Cognito, permissões IAM e recursos auxiliares usados pelo serviço.

## Estrutura

- `app.py`: entrada da aplicação CDK.
- `iac/iac_stack.py`: stack principal com API Gateway, Cognito, S3 e permissões.
- `iac/lambda_stack.py`: definição das Lambdas e rotas HTTP.
- `iac/dynamo_stack.py`: tabela DynamoDB single-table e índices.
- `local/`: apoio para execução local com SAM, DynamoDB Local e LocalStack.

## Instalação

No root do repositório:

```bash
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe -m pip install -r iac\requirements.txt
```

Em Linux/macOS, troque `venv\Scripts\python.exe` por `./venv/bin/python`.

## Comandos úteis

- `cdk ls`: lista stacks.
- `cdk synth`: gera o template CloudFormation.
- `cdk diff`: compara o template local com o deploy atual.
- `cdk deploy`: faz deploy da stack.

## Desenvolvimento local

Para rodar API local com SAM e serviços locais, veja `LOCAL_SETUP.md`.

Alguns nomes de recursos ainda usam `formularios` por compatibilidade com ambientes e stacks existentes.
