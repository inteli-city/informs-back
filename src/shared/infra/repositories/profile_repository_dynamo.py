from typing import Dict, List, Optional

from src.shared.domain.entities.profile import Profile
from src.shared.domain.enums.profile_role_enum import ProfileRole
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.environments import Environments
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, NoItemsFound
from src.shared.infra.dtos.profile_dynamo_dto import ProfileDynamoDTO
from src.shared.infra.external.dynamo.conditions import Key
from src.shared.infra.external.dynamo.datasources.dynamo_datasource import DynamoDatasource


class ProfileRepositoryDynamo(IProfileRepository):
    """
    Implementação DynamoDB do IProfileRepository.

    Aponta pra tabela de Profiles (separada da Formularios_Table). Nome
    físico é gerado pelo CFN (FormulariosStack{stage}-...-ProfilesTable...)
    e injetado via env `DYNAMO_PROFILE_TABLE_NAME`. Partition/sort keys
    via `DYNAMO_PROFILE_PARTITION_KEY`/`DYNAMO_PROFILE_SORT_KEY`.
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

    def count_active_by_role(self, role: ProfileRole) -> int:
        # Usa GSI `ByRole` com Select=COUNT — não trafega items, só o número.
        # FilterExpression filtra por active=True após o key match.
        total = 0
        last_evaluated_key: Optional[dict] = None
        while True:
            kwargs = {
                "key_condition_expression": Key("GSI1PK").eq(ProfileDynamoDTO.build_gsi1_pk(role)),
                "IndexName": "ByRole",
                "Select": "COUNT",
                "FilterExpression": "active = :true",
                "ExpressionAttributeValues": {":true": True},
            }
            if last_evaluated_key is not None:
                kwargs["ExclusiveStartKey"] = last_evaluated_key
            resp = self.dynamo.query(**kwargs)
            total += int(resp.get("Count", 0))
            last_evaluated_key = resp.get("LastEvaluatedKey")
            if not last_evaluated_key:
                break
        return total

    def update_profile(
        self,
        user_id: str,
        role: Optional[ProfileRole] = None,
        scope: Optional[Dict[str, List[str]]] = None,
        updated_at: Optional[int] = None,
    ) -> Profile:
        update_dict = {}
        if role is not None:
            update_dict["role"] = role.value
            update_dict["GSI1PK"] = ProfileDynamoDTO.build_gsi1_pk(role)
        if scope is not None:
            update_dict["scope"] = scope
        if updated_at is not None:
            update_dict["updated_at"] = updated_at

        try:
            resp = self.dynamo.update_item(
                partition_key=ProfileDynamoDTO.build_pk(user_id),
                sort_key=ProfileDynamoDTO.build_sk(),
                update_dict=update_dict,
                condition_expression="attribute_exists(PK)",
            )
        except self.dynamo.dynamo_table.meta.client.exceptions.ConditionalCheckFailedException as exc:
            raise NoItemsFound(f"Perfil não encontrado para user_id={user_id}") from exc

        item = resp.get("Attributes")
        if item is None:
            raise NoItemsFound(f"Perfil não encontrado para user_id={user_id}")
        return ProfileDynamoDTO.from_dynamo(item).to_entity()
