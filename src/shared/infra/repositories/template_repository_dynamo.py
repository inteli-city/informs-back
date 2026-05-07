from typing import List, Optional, Tuple

from src.shared.domain.entities.template import Template
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository
from src.shared.environments import Environments
from src.shared.infra.dtos.template_dynamo_dto import TemplateDynamoDTO
from src.shared.infra.external.dynamo.conditions import Attr, Key
from src.shared.infra.external.dynamo.datasources.dynamo_datasource import DynamoDatasource
from src.shared.helpers.functions.pagination_token import encode_pagination_token


class TemplateRepositoryDynamo(ITemplateRepository):
    @staticmethod
    def template_partition_key(template_id: str) -> str:
        return f"template#{template_id}"

    @staticmethod
    def template_sort_key() -> str:
        return "METADATA"
    
    @staticmethod
    def template_gsi_partition_key(system: str) -> str:
        return f"system#{system}"
    
    @staticmethod
    def template_gsi_sort_key(is_active: bool, name: str, template_id: str) -> str:
        return f"active#{int(is_active)}#name#{name}#template#{template_id}"

    def __init__(self):
        self.dynamo = DynamoDatasource(
            endpoint_url=Environments.get_envs().endpoint_url,
            dynamo_table_name=Environments.get_envs().dynamo_table_name,
            region=Environments.get_envs().region,
            partition_key=Environments.get_envs().dynamo_partition_key,
            sort_key=Environments.get_envs().dynamo_sort_key,
        )

    def create_template(self, template: Template) -> Template:
        dto = TemplateDynamoDTO.from_entity(template).to_dynamo()

        dto["GSI1PK"] = self.template_gsi_partition_key(template.system)
        dto["GSI1SK"] = self.template_gsi_sort_key(template.is_active, template.name, template.id)

        self.dynamo.put_item(
            item=dto,
            partition_key=self.template_partition_key(template.id),
            sort_key=self.template_sort_key(),
        )
        return template

    def get_template(self, template_id: str) -> Optional[Template]:
        resp = self.dynamo.get_item(
            partition_key=self.template_partition_key(template_id),
            sort_key=self.template_sort_key(),
        )
        if "Item" not in resp:
            return None
        return TemplateDynamoDTO.from_dynamo(resp["Item"]).to_entity()

    def get_all_templates(
        self,
        system: str,
        limit: Optional[int],
        exclusive_start_key: Optional[dict] = None,
        name_contains: Optional[str] = None,
        is_active: Optional[bool] = True,
    ) -> Tuple[List[Template], Optional[str]]:
        key_condition = Key("GSI1PK").eq(self.template_gsi_partition_key(system))

        if is_active is not None:
            key_condition = key_condition & Key("GSI1SK").begins_with(f"active#{int(is_active)}#")

        query_kwargs = {
            "key_condition_expression": key_condition,
            "IndexName": "UserPriorityIndex",
            "Select": "ALL_ATTRIBUTES",
        }
        start_key = exclusive_start_key
        if start_key is not None:
            query_kwargs["ExclusiveStartKey"] = start_key

        if name_contains is not None:
            query_kwargs["FilterExpression"] = Attr("name").contains(name_contains)

        items: List[dict] = []
        start_key = exclusive_start_key
        while True:
            if limit is not None and name_contains is None:
                remaining = limit - len(items)
                if remaining <= 0:
                    break
                query_kwargs["Limit"] = remaining
            else:
                query_kwargs.pop("Limit", None)
            if start_key is not None:
                query_kwargs["ExclusiveStartKey"] = start_key
            else:
                query_kwargs.pop("ExclusiveStartKey", None)
            resp = self.dynamo.query(**query_kwargs)
            items.extend(resp.get("Items", []))
            start_key = resp.get("LastEvaluatedKey")
            if start_key is None:
                break

        templates = [TemplateDynamoDTO.from_dynamo(item).to_entity() for item in items]
        if limit is not None and name_contains is not None:
            templates = templates[:limit]

        next_key = start_key if limit is not None and name_contains is None else None
        return templates, encode_pagination_token(next_key)

    def update_template(self, template: Template) -> Template:
        dto = TemplateDynamoDTO.from_entity(template).to_dynamo()
        dto["GSI1PK"] = self.template_gsi_partition_key(template.system)
        dto["GSI1SK"] = self.template_gsi_sort_key(template.is_active, template.name, template.id)

        transaction_items = []

        transaction_items.append(
            self.dynamo.build_transaction_item_delete(
                partition_key=self.template_partition_key(template.id),
                sort_key=self.template_sort_key()
            )
        )

        transaction_items.append(
            self.dynamo.build_transaction_item_put(
                item=dto,
                partition_key=self.template_partition_key(template.id),
                sort_key=self.template_sort_key()
            )
        )

        self.dynamo.transact_write_items(transaction_items)

        return template
