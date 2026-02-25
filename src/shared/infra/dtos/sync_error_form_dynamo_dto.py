from src.shared.domain.entities.sync_error_form import SyncErrorForm


class SyncErrorFormDynamoDTO:
    def __init__(self, item: SyncErrorForm):
        self.item = item

    @staticmethod
    def from_entity(item: SyncErrorForm) -> "SyncErrorFormDynamoDTO":
        return SyncErrorFormDynamoDTO(item=item)

    @staticmethod
    def from_dynamo(item: dict) -> "SyncErrorFormDynamoDTO":
        pk = item.get("PK")
        sk = item.get("SK")
        if not isinstance(pk, str) or not pk.startswith("sync_error_form#"):
            raise KeyError("PK")
        if not isinstance(sk, str) or not sk.startswith("form#"):
            raise KeyError("SK")
        _, job_name, system = pk.split("#", 2)
        form_id = sk.split("form#", 1)[1]
        return SyncErrorFormDynamoDTO(
            item=SyncErrorForm(
                job_name=job_name,
                system=system,
                form_id=form_id,
                source_updated_at=int(item["source_updated_at"]) if item.get("source_updated_at") is not None else None,
                last_failed_at=int(item["last_failed_at"]),
            )
        )

    def to_dynamo(self) -> dict:
        return {
            "form_id": self.item.form_id,
            "source_updated_at": self.item.source_updated_at,
            "last_failed_at": self.item.last_failed_at,
        }

    def to_entity(self) -> SyncErrorForm:
        return self.item
