"""
TrackingStack — infraestrutura do serviço de tracking em tempo real
(motoverificadores → gestores) via WebSocket.

Provisiona:
- Tabela DynamoDB Location (histórico completo de pings, sem TTL).
- Lightsail instance (Debian 12, plano nano $5, sa-east-1).
- Static IP atrelado à instância (necessário pro DNS sslip.io estabilizar).
- Lightsail Key Pair (CDK gera, par privado vai pro Secrets Manager).
- Firewall: 22 (SSH), 80 (HTTP-01 challenge do Caddy), 443 (wss://).
- Snapshot automático diário (via add-on instanceSnapshot).

Uma única Lightsail compartilhada entre dev/homolog/prod, com 3 processos
uvicorn (8001/8002/8003) atrás do Caddy roteando por hostname (sslip.io).
A política de IAM da instância dá acesso às 3 tabelas Location (uma por env)
e à tabela informs-tracking-profile (lookup de role no handshake).

A separação por env das tabelas é controlada pelo nome
(`informs-tracking-location-{env}`), não por stack — isso permite que UM único
deploy do TrackingStack provisione as 3 tabelas Location de uma vez só.
"""

import os
from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    Stack,
    aws_dynamodb,
    aws_iam,
    aws_lightsail,
    aws_secretsmanager,
    custom_resources,
)
from constructs import Construct


# Stages atendidos por essa Lightsail compartilhada.
STAGES = ("dev", "homolog", "prod")

# Plano Lightsail mais barato em sa-east-1 (1 vCPU, 1GB RAM, 40GB SSD, $5/mês).
# Confere bundles atuais com: aws lightsail get-bundles --region sa-east-1
LIGHTSAIL_BUNDLE_ID = "nano_3_0"

# Blueprint Debian 12. Confere com: aws lightsail get-blueprints --region sa-east-1
LIGHTSAIL_BLUEPRINT_ID = "debian_12"

# Open-internet CIDR — usamos pra SSH (22), HTTP (80, Let's Encrypt) e WSS (443).
# Extrair constante evita python:S1192 (literal duplicado).
_OPEN_INTERNET_CIDR = "0.0.0.0/0"


class TrackingStack(Stack):
    """Stack independente — não depende do IacStack principal."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        github_ref_name = os.environ.get("GITHUB_REF_NAME", "dev")
        # Em prod retemos tabela; demais envs destroem junto com a stack.
        removal_policy = (
            RemovalPolicy.RETAIN if "prod" in github_ref_name else RemovalPolicy.DESTROY
        )

        # ---------- Location tables (uma por stage) ----------
        # Schema:
        #   PK = user#{user_id}
        #   SK = ts#{epoch_ms}        (sortável cronologicamente)
        # Atributos: lat (N), lng (N), accuracy (N opc), ts_device (N opc).
        # Sem TTL: histórico completo retido por decisão do produto.
        self.location_tables: dict[str, aws_dynamodb.Table] = {}
        for stage in STAGES:
            table = aws_dynamodb.Table(
                self,
                f"Location_Table_{stage}",
                table_name=f"informs-tracking-location-{stage}",
                partition_key=aws_dynamodb.Attribute(
                    name="PK", type=aws_dynamodb.AttributeType.STRING
                ),
                sort_key=aws_dynamodb.Attribute(
                    name="SK", type=aws_dynamodb.AttributeType.STRING
                ),
                billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
                point_in_time_recovery=True,
                # Em prod: RETAIN. Outros envs: DESTROY (recriam fácil).
                removal_policy=(
                    RemovalPolicy.RETAIN if stage == "prod" else removal_policy
                ),
            )
            self.location_tables[stage] = table
            CfnOutput(
                self,
                f"LocationTableName_{stage}",
                value=table.table_name,
                export_name=f"InformsLocationTable{stage}",
            )

        # ---------- Lightsail Key Pair (custom resource) ----------
        # aws-cdk-lib não expõe CfnKeyPair pro módulo Lightsail (só EC2 tem).
        # Usamos AwsCustomResource pra chamar lightsail.CreateKeyPair direto
        # via SDK no momento do deploy. A chave privada (PEM) volta no response
        # e é gravada no Secrets Manager via outro AwsCustomResource em
        # cascata (depende do primeiro pra extrair o PrivateKeyBase64).
        key_pair_name = "informs-ws-keypair"
        create_keypair = custom_resources.AwsCustomResource(
            self,
            "CreateWSKeyPair",
            on_create=custom_resources.AwsSdkCall(
                service="Lightsail",
                action="createKeyPair",
                parameters={"keyPairName": key_pair_name},
                physical_resource_id=custom_resources.PhysicalResourceId.of(key_pair_name),
            ),
            on_delete=custom_resources.AwsSdkCall(
                service="Lightsail",
                action="deleteKeyPair",
                parameters={"keyPairName": key_pair_name},
            ),
            policy=custom_resources.AwsCustomResourcePolicy.from_statements(
                [
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=["lightsail:CreateKeyPair", "lightsail:DeleteKeyPair"],
                        # Restringe ao ARN do key pair específico —
                        # silencia python:S6304 e dá menor privilégio real.
                        resources=[
                            f"arn:aws:lightsail:{self.region}:{self.account}:KeyPair/{key_pair_name}"
                        ],
                    )
                ]
            ),
            install_latest_aws_sdk=False,
        )
        self.key_pair_name = key_pair_name

        # Secret pra chave privada — populado no mesmo deploy via PutSecretValue.
        # Marcamos RETAIN: se a stack for destruída, mantém-se o secret pra
        # auditoria (mas a key pair em si some, então o conteúdo fica obsoleto).
        self.ssh_key_secret = aws_secretsmanager.Secret(
            self,
            "WSSSHKeySecret",
            secret_name="informs-ws/lightsail-ssh-key",
            description="Chave privada SSH (PEM) da Lightsail informs-ws.",
            removal_policy=RemovalPolicy.RETAIN,
        )
        store_keypair = custom_resources.AwsCustomResource(
            self,
            "StoreWSKeyPairSecret",
            on_create=custom_resources.AwsSdkCall(
                service="SecretsManager",
                action="putSecretValue",
                parameters={
                    "SecretId": self.ssh_key_secret.secret_name,
                    "SecretString": create_keypair.get_response_field("privateKeyBase64"),
                },
                physical_resource_id=custom_resources.PhysicalResourceId.of(
                    f"{key_pair_name}-secret"
                ),
            ),
            policy=custom_resources.AwsCustomResourcePolicy.from_statements(
                [
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=["secretsmanager:PutSecretValue"],
                        resources=[self.ssh_key_secret.secret_arn],
                    )
                ]
            ),
            install_latest_aws_sdk=False,
        )
        store_keypair.node.add_dependency(create_keypair)
        store_keypair.node.add_dependency(self.ssh_key_secret)

        # ---------- IAM user pra instância (Lightsail não tem instance role) ----------
        # Lightsail é IaaS gerenciada e não suporta IAM Instance Profile como EC2.
        # Solução: criamos um IAM user com política mínima e geramos
        # access key, salva no Secrets Manager. O bootstrap.sh recupera e
        # configura ~/.aws/credentials no usuário do serviço.
        self.ws_iam_user = aws_iam.User(self, "WSServerUser", user_name="informs-ws-server")
        location_arns = [t.table_arn for t in self.location_tables.values()]
        self.ws_iam_user.add_to_policy(
            aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                actions=[
                    "dynamodb:PutItem",
                    "dynamodb:Query",
                    "dynamodb:GetItem",
                    "dynamodb:BatchWriteItem",
                ],
                resources=location_arns,
            )
        )
        # Permite ler tabela de profiles (lookup de role no handshake).
        # Nome segue convenção do DynamoStack existente.
        profile_table_arns = [
            f"arn:aws:dynamodb:{self.region}:{self.account}:table/informs-tracking-profile-{s}"
            for s in STAGES
        ]
        self.ws_iam_user.add_to_policy(
            aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                actions=["dynamodb:GetItem"],
                resources=profile_table_arns,
            )
        )

        access_key = aws_iam.CfnAccessKey(
            self, "WSServerAccessKey", user_name=self.ws_iam_user.user_name
        )
        # Secret pra credenciais AWS da instância (consumidas pelo boto3 do WS).
        # Conteúdo: JSON {"AccessKeyId": "...", "SecretAccessKey": "..."}
        # consumido pelo deploy (PR3) que escreve em ~/.aws/credentials.
        self.aws_creds_secret = aws_secretsmanager.Secret(
            self,
            "WSAWSCredsSecret",
            secret_name="informs-ws/aws-credentials",
            description="Access key do IAM user informs-ws-server (consumido pelo deploy).",
            removal_policy=RemovalPolicy.RETAIN,
        )
        # Popula o Secret no mesmo deploy via custom resource — assim
        # o GH Actions já encontra o conteúdo pronto sem passo manual.
        store_creds = custom_resources.AwsCustomResource(
            self,
            "StoreWSAWSCredsSecret",
            on_create=custom_resources.AwsSdkCall(
                service="SecretsManager",
                action="putSecretValue",
                parameters={
                    "SecretId": self.aws_creds_secret.secret_name,
                    "SecretString": (
                        f'{{"AccessKeyId":"{access_key.ref}",'
                        f'"SecretAccessKey":"{access_key.attr_secret_access_key}"}}'
                    ),
                },
                physical_resource_id=custom_resources.PhysicalResourceId.of(
                    "informs-ws-aws-creds-secret"
                ),
            ),
            policy=custom_resources.AwsCustomResourcePolicy.from_statements(
                [
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=["secretsmanager:PutSecretValue"],
                        resources=[self.aws_creds_secret.secret_arn],
                    )
                ]
            ),
            install_latest_aws_sdk=False,
        )
        store_creds.node.add_dependency(self.aws_creds_secret)

        # ---------- Lightsail instance ----------
        # User-data é lido de bootstrap.sh — instala python, caddy, swap e
        # systemd units placeholder pros 3 envs.
        bootstrap_path = os.path.join(
            os.path.dirname(__file__), "..", "ws_server_bootstrap", "bootstrap.sh"
        )
        with open(bootstrap_path, "r", encoding="utf-8") as f:
            user_data = f.read()

        self.instance = aws_lightsail.CfnInstance(
            self,
            "WSInstance",
            instance_name="informs-ws",
            availability_zone=f"{self.region}a",
            blueprint_id=LIGHTSAIL_BLUEPRINT_ID,
            bundle_id=LIGHTSAIL_BUNDLE_ID,
            key_pair_name=self.key_pair_name,
            user_data=user_data,
            networking=aws_lightsail.CfnInstance.NetworkingProperty(
                ports=[
                    aws_lightsail.CfnInstance.PortProperty(
                        from_port=22, to_port=22, protocol="tcp", access_from=_OPEN_INTERNET_CIDR,
                        access_type="public", access_direction="inbound", common_name="SSH",
                    ),
                    aws_lightsail.CfnInstance.PortProperty(
                        from_port=80, to_port=80, protocol="tcp", access_from=_OPEN_INTERNET_CIDR,
                        access_type="public", access_direction="inbound",
                        common_name="HTTP (Let's Encrypt HTTP-01)",
                    ),
                    aws_lightsail.CfnInstance.PortProperty(
                        from_port=443, to_port=443, protocol="tcp", access_from=_OPEN_INTERNET_CIDR,
                        access_type="public", access_direction="inbound", common_name="WSS",
                    ),
                ]
            ),
            # Snapshot automático diário (às 03:00 UTC).
            add_ons=[
                aws_lightsail.CfnInstance.AddOnProperty(
                    add_on_type="AutoSnapshot",
                    auto_snapshot_add_on_request=aws_lightsail.CfnInstance.AutoSnapshotAddOnProperty(
                        snapshot_time_of_day="03:00"
                    ),
                    status="Enabled",
                )
            ],
        )
        self.instance.node.add_dependency(create_keypair)

        # ---------- Static IP ----------
        # Sem static IP, o IP público muda a cada stop/start, o que quebra
        # tanto o DNS sslip.io quanto os certs Let's Encrypt em cache.
        self.static_ip = aws_lightsail.CfnStaticIp(
            self, "WSStaticIp", static_ip_name="informs-ws-ip",
            attached_to=self.instance.instance_name,
        )
        self.static_ip.add_dependency(self.instance)

        CfnOutput(self, "WSInstanceName", value=self.instance.instance_name)
        CfnOutput(self, "WSStaticIpName", value=self.static_ip.static_ip_name)
        CfnOutput(
            self,
            "WSPublicURLHint",
            value="wss://<env>-<dashed-ip>.sslip.io  (ver IP em Outputs após deploy)",
        )
