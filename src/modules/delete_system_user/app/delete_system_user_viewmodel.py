from src.shared.helpers.contracts.endpoints.system_access_contract import DeleteSystemUserResponseSchema


class DeleteSystemUserViewmodel:
    def __init__(self, system: str, user_id: str):
        self.system = system
        self.user_id = user_id

    def to_dict(self) -> dict:
        payload = {"system": self.system, "user_id": self.user_id}
        return DeleteSystemUserResponseSchema.model_validate(payload).model_dump()
