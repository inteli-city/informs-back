"""
FormulariosTrackingStack — infraestrutura do serviço de tracking em tempo
real (inspectors → admins) via WebSocket.

Provisiona (sem nenhum recurso IAM):
- 3 tabelas DynamoDB Location (uma por env: dev/homolog/prod).
- 1 Lightsail instance Debian 12 nano $5/mês em sa-east-1.
- Static IP atrelado.
- Snapshot automático diário.
- 2 SecretsManager Secrets vazios (placeholders pro user popular):
    * informs-ws/lightsail-ssh-key  → PEM da chave SSH
    * informs-ws/aws-credentials    → JSON {AccessKeyId, SecretAccessKey}

NÃO criamos:
- IAM user `informs-ws-server`: precisa ser criado manualmente (ou via infra)
  com policy mínima nas tabelas Location + Profile. Decisão consciente: o
  user que roda esta stack tipicamente não tem permissão IAM no projeto.
- Lightsail Key Pair: a Lightsail cria uma "default key" automaticamente
  por região na primeira criação de instância (ou você pode criar uma
  específica via console e referenciar pelo nome via env LIGHTSAIL_KEYPAIR_NAME).

Setup pós-deploy (ver iac/policies/README.md):
1. Pedir pra infra criar IAM user informs-ws-server + access key.
2. Popular informs-ws/aws-credentials com o JSON da access key (você tem
   permissão SecretsManager).
3. Baixar PEM da default key Lightsail pelo console e popular
   informs-ws/lightsail-ssh-key.
"""

import os
from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    Stack,
    aws_dynamodb,
    aws_lightsail,
    aws_secretsmanager,
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
_OPEN_INTERNET_CIDR = "0.0.0.0/0"

# Nomes "lógicos" dos secrets — populados manualmente pelo user pós-deploy.
SSH_KEY_SECRET_NAME = "informs-ws/lightsail-ssh-key"
AWS_CREDS_SECRET_NAME = "informs-ws/aws-credentials"


class FormulariosTrackingStack(Stack):
    """Stack independente — não depende do IacStack principal nem cria IAM."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        github_ref_name = os.environ.get("GITHUB_REF_NAME", "dev")
        # Em prod retemos tabelas; demais envs destroem junto com a stack.
        removal_policy = (
            RemovalPolicy.RETAIN if "prod" in github_ref_name else RemovalPolicy.DESTROY
        )

        # ---------- Location tables (uma por stage) ----------
        # Schema:
        #   PK = user#{user_id}
        #   SK = ts#{epoch_ms}        (sortável cronologicamente)
        # Atributos: lat (N), lng (N), accuracy (N opc), ts_device (N opc).
        # Sem TTL: histórico completo retido por decisão do produto.
        # SEM table_name explícito: nome físico segue padrão da stack
        # (FormulariosTrackingStack-LocationTable{stage}-...).
        self.location_tables: dict[str, aws_dynamodb.Table] = {}
        for stage in STAGES:
            table = aws_dynamodb.Table(
                self,
                f"Location_Table_{stage}",
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
                export_name=f"FormulariosTrackingLocationTable{stage}",
            )

        # ---------- SecretsManager placeholders ----------
        # Criados vazios pelo CFN. Você popula manualmente UMA vez via
        # console/CLI (precisa de secretsmanager:PutSecretValue, que você tem).
        self.ssh_key_secret = aws_secretsmanager.Secret(
            self,
            "WSSSHKeySecret",
            secret_name=SSH_KEY_SECRET_NAME,
            description=(
                "Chave privada SSH (PEM, base64) da Lightsail informs-ws. "
                "Popular manualmente: baixe a default key Lightsail do console "
                "(Account → SSH keys), base64-encode, e use put-secret-value."
            ),
            removal_policy=RemovalPolicy.RETAIN,
        )
        self.aws_creds_secret = aws_secretsmanager.Secret(
            self,
            "WSAWSCredsSecret",
            secret_name=AWS_CREDS_SECRET_NAME,
            description=(
                "Access key do IAM user informs-ws-server. "
                "Conteúdo JSON: {\"AccessKeyId\":\"...\",\"SecretAccessKey\":\"...\"}. "
                "User criado fora desta stack (peça pra infra)."
            ),
            removal_policy=RemovalPolicy.RETAIN,
        )

        # ---------- Lightsail instance ----------
        # User-data é lido de bootstrap.sh — instala python, caddy, swap e
        # systemd units placeholder pros 3 envs. SEM key_pair_name: Lightsail
        # cria uma default key automática por região, baixável pelo console.
        # Se preferir uma key dedicada, crie no console com nome
        # "informs-ws-keypair" e descomente a linha key_pair_name abaixo.
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
            # key_pair_name=None  # → usa default key da região
            user_data=user_data,
            networking=aws_lightsail.CfnInstance.NetworkingProperty(
                ports=[
                    aws_lightsail.CfnInstance.PortProperty(
                        from_port=22, to_port=22, protocol="tcp",
                        access_from=_OPEN_INTERNET_CIDR,
                        access_type="public", access_direction="inbound",
                        common_name="SSH",
                    ),
                    aws_lightsail.CfnInstance.PortProperty(
                        from_port=80, to_port=80, protocol="tcp",
                        access_from=_OPEN_INTERNET_CIDR,
                        access_type="public", access_direction="inbound",
                        common_name="HTTP (Let's Encrypt HTTP-01)",
                    ),
                    aws_lightsail.CfnInstance.PortProperty(
                        from_port=443, to_port=443, protocol="tcp",
                        access_from=_OPEN_INTERNET_CIDR,
                        access_type="public", access_direction="inbound",
                        common_name="WSS",
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
