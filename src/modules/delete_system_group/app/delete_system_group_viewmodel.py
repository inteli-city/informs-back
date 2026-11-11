from src.shared.helpers.contracts.endpoints.system_access_contract import DeleteSystemGroupResponseSchema


class DeleteSystemGroupViewmodel:
    def __init__(self, system: str, group_id: str):
        self.system = system
        self.group_id = group_id

    def to_dict(self) -> dict:
        payload = {"system": self.system, "group_id": self.group_id}
        return DeleteSystemGroupResponseSchema.model_validate(payload).model_dump()
