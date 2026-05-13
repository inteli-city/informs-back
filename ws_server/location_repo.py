"""Persistência das localizações no DynamoDB.

Schema da tabela `informs-tracking-location-{stage}`:
- PK = user#{user_id}
- SK = ts#{ts_server_ms}    (server timestamp pra evitar colisão de ts_device)
- atributos: lat, lng, ts_device, accuracy (opc)

Sem TTL — histórico é fonte de verdade pra auditoria de rota.
Writes são fire-and-forget via batch writer? Não — usamos put_item
individual porque ping é 1 a cada 60s por inspector, volume baixo.
"""

import boto3
from decimal import Decimal
from typing import Optional


class LocationRepository:
    def __init__(self, table_name: str, region: str, dynamodb_resource=None) -> None:
        self._table = (
            dynamodb_resource or boto3.resource("dynamodb", region_name=region)
        ).Table(table_name)

    def put_ping(
        self,
        *,
        user_id: str,
        lat: float,
        lng: float,
        ts_server: int,
        ts_device: int,
        accuracy: Optional[float] = None,
    ) -> None:
        """Persiste um ping. ts_server é a chave de ordenação canônica."""
        item = {
            "PK": f"user#{user_id}",
            "SK": f"ts#{ts_server}",
            # DynamoDB não aceita float — converte tudo via Decimal.
            "lat": Decimal(str(lat)),
            "lng": Decimal(str(lng)),
            "ts_device": ts_device,
        }
        if accuracy is not None:
            item["accuracy"] = Decimal(str(accuracy))
        self._table.put_item(Item=item)
