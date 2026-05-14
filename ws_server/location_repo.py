"""Persistência das localizações no DynamoDB.

Schema da tabela Location (nome físico auto-gerado pela
FormulariosTrackingStack — passado via env LOCATION_TABLE):
- PK = user#{user_id}
- SK = ts#{ts_server_ms}    (server timestamp pra evitar colisão de ts_device)
- atributos: lat, lng, ts_device, accuracy (opc)

Sem TTL — histórico é fonte de verdade pra auditoria de rota.
Writes são fire-and-forget via batch writer? Não — usamos put_item
individual porque ping é 1 a cada 60s por inspector, volume baixo.
"""

import boto3
from boto3.dynamodb.conditions import Key
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

    def query_history(
        self, *, user_id: str, since_ms: int, until_ms: int
    ) -> list[dict]:
        """Lê pings de um inspector entre [since_ms, until_ms] (ts_server).

        Retorna items normalizados (Decimal → float, sem PK/SK) ordenados
        ascendentemente por ts_server. Pagina automaticamente se passar de 1MB.
        """
        items: list[dict] = []
        kwargs = {
            "KeyConditionExpression": (
                Key("PK").eq(f"user#{user_id}")
                & Key("SK").between(f"ts#{since_ms}", f"ts#{until_ms}")
            ),
            "ScanIndexForward": True,  # ordem cronológica ascendente
        }
        while True:
            resp = self._table.query(**kwargs)
            items.extend(resp.get("Items", []))
            if "LastEvaluatedKey" not in resp:
                break
            kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]

        return [_normalize(item) for item in items]


def _normalize(item: dict) -> dict:
    """Decimal → float, extrai ts_server da SK, drop PK/SK."""
    return {
        "lat": float(item["lat"]),
        "lng": float(item["lng"]),
        "ts": int(item["SK"].removeprefix("ts#")),
        "ts_device": int(item["ts_device"]),
        "accuracy": float(item["accuracy"]) if "accuracy" in item else None,
    }
