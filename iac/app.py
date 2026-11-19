#!/usr/bin/env python3
import os

import aws_cdk as cdk

from adjust_layer_directory import adjust_layer_directory
from iac.iac_stack import IacStack

print("Starting the CDK")

print("Adjusting the layer directory")
adjust_layer_directory(shared_dir_name="shared", destination="lambda_layer_out_temp")
print("Finished adjusting the layer directory")


app = cdk.App()

aws_region = os.environ.get("AWS_REGION")
aws_account_id = os.environ.get("AWS_ACCOUNT_ID")
stack_name = os.environ.get("STACK_NAME")
github_ref_name = os.environ.get("GITHUB_REF_NAME")


# O ambiente vem da branch publicada (GITHUB_REF_NAME). Fora de dev, homolog e
# prod o deploy falha, em vez de marcar os recursos com um ambiente que não
# existe no padrão de tags da conta.
ENVIRONMENTS = {'dev', 'homolog', 'prod'}
if github_ref_name not in ENVIRONMENTS:
    raise SystemExit(
        f"GITHUB_REF_NAME={github_ref_name!r} is not dev, homolog or prod; "
        "set it to the target environment before cdk deploy"
    )

# Padrão de tags da conta AWS: project, environment e owner (time responsável),
# minúsculas. São as tags usadas para filtrar custo no Cost Explorer.
tags = {
    'project': 'informs',
    'environment': github_ref_name,
    'owner': 'back',
}

IacStack(app, stack_name, env=cdk.Environment(account=aws_account_id, region=aws_region), tags=tags)

app.synth()
