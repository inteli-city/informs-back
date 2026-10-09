from src.shared.domain.entities.system_membership import SystemMembership


class SystemMembershipDynamoDTO:
    """
    Conversor entre SystemMembership e o item DynamoDB (tabela de Profiles).

    Esquema do item (na mesma partição da pessoa):
        PK     = user#{user_id}
        SK     = system#{system}
        GSI1PK = system#{system}
        GSI1SK = role#{role_id}#user#{user_id}

    - Query PK = user#{id}, SK begins_with system#  → vínculos da pessoa.
    - Query GSI1 PK = system#{system}                → pessoas do sistema.
    - ... e GSI1SK begins_with role#{role_id}#       → pessoas com o role.
    """

    SK_PREFIX = "system#"

    def __init__(self, user_id: str, system: str, role_id: str, created_at: int, updated_at: int):
        self.user_id = user_id
        self.system = system
        self.role_id = role_id
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def from_entity(membership: SystemMembership) -> "SystemMembershipDynamoDTO":
        return SystemMembershipDynamoDTO(
            user_id=membership.user_id,
            system=membership.system,
            role_id=membership.role_id,
            created_at=membership.created_at,
            updated_at=membership.updated_at,
        )

    def to_dynamo(self) -> dict:
        return {
            "user_id": self.user_id,
            "system": self.system,
            "role_id": self.role_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "GSI1PK": SystemMembershipDynamoDTO.build_gsi1_pk(self.system),
            "GSI1SK": SystemMembershipDynamoDTO.build_gsi1_sk(self.role_id, self.user_id),
        }

    @staticmethod
    def from_dynamo(data: dict) -> "SystemMembershipDynamoDTO":
        return SystemMembershipDynamoDTO(
            user_id=data["user_id"],
            system=data["system"],
            role_id=data["role_id"],
            created_at=int(data["created_at"]),
            updated_at=int(data["updated_at"]),
        )

    def to_entity(self) -> SystemMembership:
        return SystemMembership(
            user_id=self.user_id,
            system=self.system,
            role_id=self.role_id,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @staticmethod
    def build_pk(user_id: str) -> str:
        return f"user#{user_id}"

    @staticmethod
    def build_sk(system: str) -> str:
        return f"{SystemMembershipDynamoDTO.SK_PREFIX}{system}"

    @staticmethod
    def build_gsi1_pk(system: str) -> str:
        return f"system#{system}"

    @staticmethod
    def build_gsi1_sk(role_id: str, user_id: str) -> str:
        return f"{SystemMembershipDynamoDTO.build_gsi1_sk_role_prefix(role_id)}user#{user_id}"

    @staticmethod
    def build_gsi1_sk_role_prefix(role_id: str) -> str:
        return f"role#{role_id}#"
