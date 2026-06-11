from typing import List

from src.shared.domain.entities.location_ping import LocationPing
from src.shared.helpers.contracts.endpoints.location_history_contract import (
    LocationHistoryResponseSchema,
)


class GetLocationHistoryViewmodel:
    def __init__(self, pings: List[LocationPing]):
        self.pings = pings

    def to_dict(self) -> dict:
        payload = {
            "items": [
                {
                    "user_id": p.user_id,
                    "lat": p.lat,
                    "lng": p.lng,
                    "ts": p.ts,
                    "ts_device": p.ts_device,
                    "accuracy": p.accuracy,
                }
                for p in self.pings
            ],
            "count": len(self.pings),
        }
        return LocationHistoryResponseSchema.model_validate(payload).model_dump()
