from typing import List, Optional

from src.shared.domain.entities.system_group import SystemGroup
from src.shared.domain.repositories.system_group_repository_interface import ISystemGroupRepository
from src.shared.environments import Environments
from src.shared.infra.dtos.system_group_dynamo_dto import SystemGroupDynamoDTO
from src.shared.infra.external.dynamo.conditions import Key
from src.shared.infra.external.dynamo.datasources.dynamo_datasource import DynamoDatasource


class SystemGroupRepositoryDynamo(ISystemGroupRepository):
    """
    Grupos de cada sistema na tabela de Profiles (`system#{system}` /
    `group#{group_id}`), ao lado dos roles (ADR-0022).
    """

    def __init__(self):
        envs = Environments.get_envs()
        self.dynamo = DynamoDatasource(
            endpoint_url=envs.endpoint_url,
            dynamo_table_name=envs.dynamo_profile_table_name,
            region=envs.region,
            partition_key=envs.dynamo_profile_partition_key,
            sort_key=envs.dynamo_profile_sort_key,
        )

    def get_group(self, system: str, group_id: str) -> Optional[SystemGroup]:
        resp = self.dynamo.get_item(
            partition_key=SystemGroupDynamoDTO.build_pk(system),
            sort_key=SystemGroupDynamoDTO.build_sk(group_id),
        )
        if "Item" not in resp:
            return None
        return SystemGroupDynamoDTO.from_dynamo(resp["Item"]).to_entity()

    def list_groups(self, system: str) -> List[SystemGroup]:
        key_condition = Key(self.dynamo.partition_key).eq(SystemGroupDynamoDTO.build_pk(system)) & Key(
            self.dynamo.sort_key
        ).begins_with(SystemGroupDynamoDTO.SK_PREFIX)
        groups: List[SystemGroup] = []
        kwargs = {}
        while True:
            resp = self.dynamo.query(key_condition_expression=key_condition, **kwargs)
            groups.extend(SystemGroupDynamoDTO.from_dynamo(item).to_entity() for item in resp.get("Items", []))
            if not resp.get("LastEvaluatedKey"):
                return groups
            kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

    def put_group(self, group: SystemGroup) -> SystemGroup:
        self.dynamo.put_item(
            item=SystemGroupDynamoDTO.from_entity(group).to_dynamo(),
            partition_key=SystemGroupDynamoDTO.build_pk(group.system),
            sort_key=SystemGroupDynamoDTO.build_sk(group.group_id),
        )
        return group

    def delete_group(self, system: str, group_id: str) -> None:
        self.dynamo.delete_item(
            partition_key=SystemGroupDynamoDTO.build_pk(system),
            sort_key=SystemGroupDynamoDTO.build_sk(group_id),
        )
