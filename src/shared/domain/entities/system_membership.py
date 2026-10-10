from src.shared.helpers.errors.domain_errors import EntityError


class SystemMembership:
    """
    Vínculo de uma pessoa com um sistema: qual role ela tem ali. `role_id` é
    o id de um SystemRole daquele sistema ou `ADMIN_ROLE_ID`.

    O acesso ao sistema continua vindo do grupo do Cognito; o vínculo só diz
    o que a pessoa pode fazer dentro dele.
    """

    user_id: str
    system: str
    role_id: str
    created_at: int
    updated_at: int

    def __init__(self, user_id: str, system: str, role_id: str, created_at: int, updated_at: int):
        self.user_id = self._validate_str(user_id, "ID do usuário")
        self.system = self._validate_str(system, "Sistema")
        self.role_id = self._validate_str(role_id, "Role")
        self.created_at = self._validate_timestamp(created_at, label="criação")
        self.updated_at = self._validate_timestamp(updated_at, label="atualização")

    @staticmethod
    def _validate_str(value: str, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise EntityError(f"{label} do vínculo deve ser uma string não vazia")
        return value

    @staticmethod
    def _validate_timestamp(value: int, *, label: str) -> int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise EntityError(f"Timestamp de {label} deve ser um inteiro")
        return value
