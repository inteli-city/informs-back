from typing import List

from src.shared.domain.entities.sync_error_form import SyncErrorForm
from src.shared.domain.repositories.sync_error_form_repository_interface import ISyncErrorFormRepository
from src.shared.environments import Environments
from src.shared.infra.dtos.sync_error_form_dynamo_dto import SyncErrorFormDynamoDTO
from src.shared.infra.external.dynamo.conditions import Key
from src.shared.infra.external.dynamo.datasources.dynamo_datasource import DynamoDatasource


class SyncErrorFormRepositoryDynamo(ISyncErrorFormRepository):
    def __init__(self):
        self.dynamo = DynamoDatasource(
            endpoint_url=Environments.get_envs().endpoint_url,
            dynamo_table_name=Environments.get_envs().dynamo_table_name,
            region=Environments.get_envs().region,
            partition_key=Environments.get_envs().dynamo_partition_key,
            sort_key=Environments.get_envs().dynamo_sort_key,
        )

    def upsert_error_form(self, item: SyncErrorForm) -> None:
        payload = SyncErrorFormDynamoDTO.from_entity(item).to_dynamo()
        self.dynamo.put_item(
            item=payload,
            partition_key=SyncErrorForm.make_pk(item.job_name, item.system),
            sort_key=SyncErrorForm.make_sk(item.form_id),
        )

    def list_error_forms(self, job_name: str, system: str) -> List[SyncErrorForm]:
        query = Key(self.dynamo.partition_key).eq(SyncErrorForm.make_pk(job_name, system))
        resp = self.dynamo.query(key_condition_expression=query, Select="ALL_ATTRIBUTES")
        items = resp.get("Items", [])
        return [SyncErrorFormDynamoDTO.from_dynamo(item).to_entity() for item in items]

    def delete_error_forms(self, job_name: str, system: str, form_ids: List[str]) -> None:
        for form_id in form_ids:
            self.dynamo.delete_item(
                partition_key=SyncErrorForm.make_pk(job_name, system),
                sort_key=SyncErrorForm.make_sk(form_id),
            )
