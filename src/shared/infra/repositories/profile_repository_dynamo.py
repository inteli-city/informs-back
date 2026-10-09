from typing import List, Optional

from src.shared.domain.entities.profile import Profile
from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.environments import Environments
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, NoItemsFound
from src.shared.infra.dtos.profile_dynamo_dto import ProfileDynamoDTO
from src.shared.infra.dtos.system_membership_dynamo_dto import SystemMembershipDynamoDTO
from src.shared.infra.external.dynamo.conditions import Key
from src.shared.infra.external.dynamo.datasources.dynamo_datasource import DynamoDatasource


BY_ROLE_INDEX = "ByRole"


class ProfileRepositoryDynamo(IProfileRepository):
    """
    Implementação DynamoDB do IProfileRepository.

    Aponta pra tabela de Profiles (separada da Formularios_Table). Nome
    físico é gerado pelo CFN (FormulariosStack{stage}-...-ProfilesTable...)
    e injetado via env `DYNAMO_PROFILE_TABLE_NAME`. Partition/sort keys
    via `DYNAMO_PROFILE_PARTITION_KEY`/`DYNAMO_PROFILE_SORT_KEY`.

    Pessoa (`user#{id}` / `METADATA`) e vínculos (`user#{id}` /
    `system#{system}`) dividem a partição; o índice `ByRole` (GSI1) lista
    pessoas por sistema/role e conta super admins.
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

    # --- Pessoa ---------------------------------------------------------------

    def get_by_user_id(self, user_id: str) -> Optional[Profile]:
        resp = self.dynamo.get_item(
            partition_key=ProfileDynamoDTO.build_pk(user_id),
            sort_key=ProfileDynamoDTO.build_sk(),
        )
        if "Item" not in resp:
            return None
        return ProfileDynamoDTO.from_dynamo(resp["Item"]).to_entity()

    def create(self, profile: Profile) -> Profile:
        item = ProfileDynamoDTO.from_entity(profile).to_dynamo()
        # ConditionExpression evita criar em cima de um item existente
        # (corrida entre dois login_profile concorrentes do mesmo user, etc.).
        try:
            self.dynamo.put_item(
                item=item,
                partition_key=ProfileDynamoDTO.build_pk(profile.user_id),
                sort_key=ProfileDynamoDTO.build_sk(),
                ConditionExpression="attribute_not_exists(PK)",
            )
        except self.dynamo.dynamo_table.meta.client.exceptions.ConditionalCheckFailedException as exc:
            raise DuplicatedItem(f"Perfil já existe para user_id={profile.user_id}") from exc
        return profile

    def soft_delete(self, user_id: str, updated_at: int) -> Profile:
        # Atualiza apenas active e updated_at, e usa ConditionExpression para
        # garantir que o item realmente exista antes de marcar como inativo.
        try:
            resp = self.dynamo.update_item(
                partition_key=ProfileDynamoDTO.build_pk(user_id),
                sort_key=ProfileDynamoDTO.build_sk(),
                update_dict={"active": False, "updated_at": updated_at},
                condition_expression="attribute_exists(PK)",
            )
        except self.dynamo.dynamo_table.meta.client.exceptions.ConditionalCheckFailedException as exc:
            raise NoItemsFound(f"Perfil não encontrado para user_id={user_id}") from exc

        item = resp.get("Attributes")
        if item is None:
            raise NoItemsFound(f"Perfil não encontrado para user_id={user_id}")
        return ProfileDynamoDTO.from_dynamo(item).to_entity()

    def count_active_super_admins(self) -> int:
        # Índice esparso: só o item de super admin tem GSI1PK = super_admin.
        # Select=COUNT não trafega items; o filtro de active vem depois do key match.
        return self._count(
            Key("GSI1PK").eq(ProfileDynamoDTO.SUPER_ADMIN_GSI1PK),
            FilterExpression="active = :true",
            ExpressionAttributeValues={":true": True},
        )

    # --- Vínculos ---------------------------------------------------------

    def get_memberships(self, user_id: str) -> List[SystemMembership]:
        items = self._query_all(
            Key(self.dynamo.partition_key).eq(SystemMembershipDynamoDTO.build_pk(user_id))
            & Key(self.dynamo.sort_key).begins_with(SystemMembershipDynamoDTO.SK_PREFIX)
        )
        return [SystemMembershipDynamoDTO.from_dynamo(item).to_entity() for item in items]

    def get_membership(self, user_id: str, system: str) -> Optional[SystemMembership]:
        resp = self.dynamo.get_item(
            partition_key=SystemMembershipDynamoDTO.build_pk(user_id),
            sort_key=SystemMembershipDynamoDTO.build_sk(system),
        )
        if "Item" not in resp:
            return None
        return SystemMembershipDynamoDTO.from_dynamo(resp["Item"]).to_entity()

    def put_membership(self, membership: SystemMembership) -> SystemMembership:
        self.dynamo.put_item(
            item=SystemMembershipDynamoDTO.from_entity(membership).to_dynamo(),
            partition_key=SystemMembershipDynamoDTO.build_pk(membership.user_id),
            sort_key=SystemMembershipDynamoDTO.build_sk(membership.system),
        )
        return membership

    def delete_membership(self, user_id: str, system: str) -> None:
        self.dynamo.delete_item(
            partition_key=SystemMembershipDynamoDTO.build_pk(user_id),
            sort_key=SystemMembershipDynamoDTO.build_sk(system),
        )

    def list_memberships_by_system(self, system: str) -> List[SystemMembership]:
        items = self._query_all(
            Key("GSI1PK").eq(SystemMembershipDynamoDTO.build_gsi1_pk(system)),
            IndexName=BY_ROLE_INDEX,
        )
        return [SystemMembershipDynamoDTO.from_dynamo(item).to_entity() for item in items]

    def count_memberships_by_role(self, system: str, role_id: str) -> int:
        return self._count(
            Key("GSI1PK").eq(SystemMembershipDynamoDTO.build_gsi1_pk(system))
            & Key("GSI1SK").begins_with(SystemMembershipDynamoDTO.build_gsi1_sk_role_prefix(role_id)),
        )

    # --- Helpers ----------------------------------------------------------

    def _query_all(self, key_condition, **kwargs) -> List[dict]:
        items: List[dict] = []
        while True:
            resp = self.dynamo.query(key_condition_expression=key_condition, **kwargs)
            items.extend(resp.get("Items", []))
            if not resp.get("LastEvaluatedKey"):
                return items
            kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

    def _count(self, key_condition, **kwargs) -> int:
        total = 0
        kwargs = {"IndexName": BY_ROLE_INDEX, "Select": "COUNT", **kwargs}
        while True:
            resp = self.dynamo.query(key_condition_expression=key_condition, **kwargs)
            total += int(resp.get("Count", 0))
            if not resp.get("LastEvaluatedKey"):
                return total
            kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
