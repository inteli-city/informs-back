from typing import List, Optional

from src.shared.domain.entities.system_role import SystemRole
from src.shared.domain.repositories.system_role_repository_interface import ISystemRoleRepository
from src.shared.environments import Environments
from src.shared.infra.dtos.system_role_dynamo_dto import SystemRoleDynamoDTO
from src.shared.infra.external.dynamo.conditions import Key
from src.shared.infra.external.dynamo.datasources.dynamo_datasource import DynamoDatasource


class SystemRoleRepositoryDynamo(ISystemRoleRepository):
    """
    Roles de cada sistema na tabela de Profiles (`system#{system}` /
    `role#{role_id}`) — junto do resto do RBAC, sem tabela nova.
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

    def get_role(self, system: str, role_id: str) -> Optional[SystemRole]:
        resp = self.dynamo.get_item(
            partition_key=SystemRoleDynamoDTO.build_pk(system),
            sort_key=SystemRoleDynamoDTO.build_sk(role_id),
        )
        if "Item" not in resp:
            return None
        return SystemRoleDynamoDTO.from_dynamo(resp["Item"]).to_entity()

    def list_roles(self, system: str) -> List[SystemRole]:
        key_condition = Key(self.dynamo.partition_key).eq(SystemRoleDynamoDTO.build_pk(system)) & Key(
            self.dynamo.sort_key
        ).begins_with(SystemRoleDynamoDTO.SK_PREFIX)
        roles: List[SystemRole] = []
        kwargs = {}
        while True:
            resp = self.dynamo.query(key_condition_expression=key_condition, **kwargs)
            roles.extend(SystemRoleDynamoDTO.from_dynamo(item).to_entity() for item in resp.get("Items", []))
            if not resp.get("LastEvaluatedKey"):
                return roles
            kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

    def put_role(self, role: SystemRole) -> SystemRole:
        self.dynamo.put_item(
            item=SystemRoleDynamoDTO.from_entity(role).to_dynamo(),
            partition_key=SystemRoleDynamoDTO.build_pk(role.system),
            sort_key=SystemRoleDynamoDTO.build_sk(role.role_id),
        )
        return role

    def delete_role(self, system: str, role_id: str) -> None:
        self.dynamo.delete_item(
            partition_key=SystemRoleDynamoDTO.build_pk(system),
            sort_key=SystemRoleDynamoDTO.build_sk(role_id),
        )
