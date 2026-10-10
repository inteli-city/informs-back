from typing import List, Optional

from boto3.dynamodb.conditions import Attr

from src.shared.domain.entities.default_app_config import DefaultAppConfig
from src.shared.domain.entities.system_config import SystemConfig
from src.shared.domain.repositories.system_config_repository_interface import ISystemConfigRepository
from src.shared.environments import Environments
from src.shared.infra.dtos.default_app_config_dynamo_dto import DefaultAppConfigDynamoDTO
from src.shared.infra.dtos.system_config_dynamo_dto import SystemConfigDynamoDTO
from src.shared.infra.external.dynamo.datasources.dynamo_datasource import DynamoDatasource


class SystemConfigRepositoryDynamo(ISystemConfigRepository):
    """
    Implementação DynamoDB de `ISystemConfigRepository`. Usa a mesma
    `Formularios_Table` (`PK = system#{system}`, `SK = CONFIG`; o padrão da
    aplicação em `PK = app_config#DEFAULT`, `SK = CONFIG`) — sem tabela ou
    índice novo.
    """

    def __init__(self):
        envs = Environments.get_envs()
        self.dynamo = DynamoDatasource(
            endpoint_url=envs.endpoint_url,
            dynamo_table_name=envs.dynamo_table_name,
            region=envs.region,
            partition_key=envs.dynamo_partition_key,
            sort_key=envs.dynamo_sort_key,
        )

    def get_by_system(self, system: str) -> Optional[SystemConfig]:
        resp = self.dynamo.get_item(
            partition_key=SystemConfigDynamoDTO.build_pk(system),
            sort_key=SystemConfigDynamoDTO.build_sk(),
        )
        if "Item" not in resp:
            return None
        return SystemConfigDynamoDTO.from_dynamo(resp["Item"]).to_entity()

    def put(self, config: SystemConfig) -> SystemConfig:
        item = SystemConfigDynamoDTO.from_entity(config).to_dynamo()
        self.dynamo.put_item(
            item=item,
            partition_key=SystemConfigDynamoDTO.build_pk(config.system),
            sort_key=SystemConfigDynamoDTO.build_sk(),
        )
        return config

    def list_all(self) -> List[SystemConfig]:
        # Scan com filtro: são poucos itens de configuração (um por sistema), e
        # só o Admin da plataforma chama isto.
        filter_expression = Attr(self.dynamo.partition_key).begins_with("system#") & Attr(
            self.dynamo.sort_key
        ).eq(SystemConfigDynamoDTO.build_sk())
        configs: List[SystemConfig] = []
        kwargs = {}
        while True:
            resp = self.dynamo.scan_items(filter_expression=filter_expression, **kwargs)
            configs.extend(SystemConfigDynamoDTO.from_dynamo(item).to_entity() for item in resp.get("Items", []))
            if "LastEvaluatedKey" not in resp:
                return configs
            kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

    def get_default_app_config(self) -> Optional[DefaultAppConfig]:
        resp = self.dynamo.get_item(
            partition_key=DefaultAppConfigDynamoDTO.build_pk(),
            sort_key=DefaultAppConfigDynamoDTO.build_sk(),
        )
        if "Item" not in resp:
            return None
        return DefaultAppConfigDynamoDTO.from_dynamo(resp["Item"]).to_entity()

    def put_default_app_config(self, config: DefaultAppConfig) -> DefaultAppConfig:
        item = DefaultAppConfigDynamoDTO.from_entity(config).to_dynamo()
        self.dynamo.put_item(
            item=item,
            partition_key=DefaultAppConfigDynamoDTO.build_pk(),
            sort_key=DefaultAppConfigDynamoDTO.build_sk(),
        )
        return config
