from src.shared.domain.entities.system_group import SystemGroup


class SystemGroupDynamoDTO:
    """
    Conversor entre SystemGroup e o item DynamoDB (tabela de Profiles).

    Esquema do item:
        PK = system#{system}
        SK = group#{group_id}

    Query PK = system#{system}, SK begins_with group# → grupos do sistema.
    """

    SK_PREFIX = "group#"

    def __init__(self, system: str, group_id: str, name: str, created_at: int, updated_at: int):
        self.system = system
        self.group_id = group_id
        self.name = name
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def from_entity(group: SystemGroup) -> "SystemGroupDynamoDTO":
        return SystemGroupDynamoDTO(
            system=group.system,
            group_id=group.group_id,
            name=group.name,
            created_at=group.created_at,
            updated_at=group.updated_at,
        )

    def to_dynamo(self) -> dict:
        return {
            "system": self.system,
            "group_id": self.group_id,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @staticmethod
    def from_dynamo(data: dict) -> "SystemGroupDynamoDTO":
        return SystemGroupDynamoDTO(
            system=data["system"],
            group_id=data["group_id"],
            name=data["name"],
            created_at=int(data["created_at"]),
            updated_at=int(data["updated_at"]),
        )

    def to_entity(self) -> SystemGroup:
        return SystemGroup(
            system=self.system,
            group_id=self.group_id,
            name=self.name,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @staticmethod
    def build_pk(system: str) -> str:
        return f"system#{system}"

    @staticmethod
    def build_sk(group_id: str) -> str:
        return f"{SystemGroupDynamoDTO.SK_PREFIX}{group_id}"
