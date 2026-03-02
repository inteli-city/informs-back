from src.shared.domain.entities.sync_state import SyncState


class SyncStateDynamoDTO:
    def __init__(self, state: SyncState):
        self.state = state

    @staticmethod
    def from_entity(state: SyncState) -> "SyncStateDynamoDTO":
        return SyncStateDynamoDTO(state=state)

    @staticmethod
    def from_dynamo(item: dict) -> "SyncStateDynamoDTO":
        pk = item.get("PK")
        if not isinstance(pk, str) or not pk.startswith("sync_state#"):
            raise KeyError("PK")
        _, job_name, system = pk.split("#", 2)
        return SyncStateDynamoDTO(
            state=SyncState(
                job_name=job_name,
                system=system,
                checkpoint_synced_at=int(item["checkpoint_synced_at"]),
                status=item["status"],
                execution_id=item.get("execution_id"),
                started_at=int(item["started_at"]) if item.get("started_at") is not None else None,
                ended_at=int(item["ended_at"]) if item.get("ended_at") is not None else None,
                window_end=int(item["window_end"]) if item.get("window_end") is not None else None,
                updated_at=int(item["updated_at"]),
            )
        )

    def to_dynamo(self) -> dict:
        return {
            "checkpoint_synced_at": self.state.checkpoint_synced_at,
            "status": self.state.status,
            "execution_id": self.state.execution_id,
            "started_at": self.state.started_at,
            "ended_at": self.state.ended_at,
            "window_end": self.state.window_end,
            "updated_at": self.state.updated_at,
        }

    def to_entity(self) -> SyncState:
        return self.state
