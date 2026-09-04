from typing import Optional

from src.shared.domain.entities.system_config import SystemConfig
from src.shared.domain.repositories.system_config_repository_interface import ISystemConfigRepository
from src.shared.environments import Environments
from src.shared.infra.dtos.system_config_dynamo_dto import SystemConfigDynamoDTO
from src.shared.infra.external.dynamo.datasources.dynamo_datasource import DynamoDatasource


class SystemConfigRepositoryDynamo(ISystemConfigRepository):
    """
    Implementação DynamoDB de `ISystemConfigRepository`. Usa a mesma
    `Formularios_Table` (`PK = system#{system}`, `SK = CONFIG`) — sem
    tabela ou índice novo.
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
