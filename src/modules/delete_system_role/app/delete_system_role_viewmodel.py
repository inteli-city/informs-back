from src.shared.helpers.contracts.endpoints.system_access_contract import DeleteSystemRoleResponseSchema


class DeleteSystemRoleViewmodel:
    def __init__(self, system: str, role_id: str):
        self.system = system
        self.role_id = role_id

    def to_dict(self) -> dict:
        payload = {"system": self.system, "role_id": self.role_id}
        return DeleteSystemRoleResponseSchema.model_validate(payload).model_dump()
