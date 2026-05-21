"""Implementação DynamoDB do ILocationRepository.

Aponta pra tabela Location provisionada pela FormulariosTrackingStack
(stack separada do IacStack). Nome físico é gerado pelo CFN
(`FormulariosTrackingStack-LocationTable{stage}-...`) e injetado via env
`DYNAMO_LOCATION_TABLE_NAME` pelo deploy do projeto.

Schema:
    PK = user#{user_id}
    SK = ts#{ts_server_ms}
    attrs: lat (N), lng (N), ts_device (N), accuracy (N opcional)
"""

from decimal import Decimal
from typing import List

from src.shared.domain.entities.location_ping import LocationPing
from src.shared.domain.repositories.location_repository_interface import (
    ILocationRepository,
)
from src.shared.environments import Environments
from src.shared.infra.external.dynamo.conditions import Key
from src.shared.infra.external.dynamo.datasources.dynamo_datasource import (
    DynamoDatasource,
)


class LocationRepositoryDynamo(ILocationRepository):
    def __init__(self):
        envs = Environments.get_envs()
        self.dynamo = DynamoDatasource(
            endpoint_url=envs.endpoint_url,
            dynamo_table_name=envs.dynamo_location_table_name,
            region=envs.region,
            partition_key=envs.dynamo_location_partition_key,
            sort_key=envs.dynamo_location_sort_key,
        )

    def query_history(
        self, *, user_id: str, since_ms: int, until_ms: int
    ) -> List[LocationPing]:
        items: List[dict] = []
        kwargs = {
            "ScanIndexForward": True,  # ordem cronológica ascendente
        }
        condition = Key(self.dynamo.partition_key).eq(f"user#{user_id}") & Key(
            self.dynamo.sort_key
        ).between(f"ts#{since_ms}", f"ts#{until_ms}")

        # Pagina internamente caso passe de 1MB.
        while True:
            resp = self.dynamo.query(condition, **kwargs)
            items.extend(resp.get("Items", []))
            if "LastEvaluatedKey" not in resp:
                break
            kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

        return [_to_entity(item, user_id) for item in items]


def _to_entity(item: dict, user_id: str) -> LocationPing:
    """Converte item DDB → LocationPing. Decimal → float, extrai ts da SK."""
    sk = item["SK"]  # formato "ts#{epoch_ms}"
    ts = int(sk.split("#", 1)[1])
    return LocationPing(
        user_id=user_id,
        lat=float(item["lat"]),
        lng=float(item["lng"]),
        ts=ts,
        ts_device=int(item["ts_device"]),
        accuracy=(
            float(item["accuracy"])
            if isinstance(item.get("accuracy"), (Decimal, float, int))
            else None
        ),
    )
