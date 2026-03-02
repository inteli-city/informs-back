from typing import Optional

from src.shared.domain.entities.sync_state import SyncState
from src.shared.domain.repositories.sync_state_repository_interface import ISyncStateRepository
from src.shared.environments import Environments
from src.shared.infra.dtos.sync_state_dynamo_dto import SyncStateDynamoDTO
from src.shared.infra.external.dynamo.datasources.dynamo_datasource import DynamoDatasource


class SyncStateRepositoryDynamo(ISyncStateRepository):
    def __init__(self):
        self.dynamo = DynamoDatasource(
            endpoint_url=Environments.get_envs().endpoint_url,
            dynamo_table_name=Environments.get_envs().dynamo_table_name,
            region=Environments.get_envs().region,
            partition_key=Environments.get_envs().dynamo_partition_key,
            sort_key=Environments.get_envs().dynamo_sort_key,
        )

    def get_state(self, job_name: str, system: str) -> Optional[SyncState]:
        resp = self.dynamo.get_item(
            partition_key=SyncState.make_pk(job_name, system),
            sort_key=SyncState.make_sk(),
        )
        item = resp.get("Item")
        if item is None:
            return None
        return SyncStateDynamoDTO.from_dynamo(item).to_entity()

    def set_state(self, state: SyncState) -> None:
        payload = SyncStateDynamoDTO.from_entity(state).to_dynamo()
        self.dynamo.put_item(
            item=payload,
            partition_key=SyncState.make_pk(state.job_name, state.system),
            sort_key=SyncState.make_sk(),
        )
