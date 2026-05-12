from typing import Optional

from src.shared.domain.entities.profile import Profile
from src.shared.domain.enums.profile_role_enum import ProfileRole


class ProfileDynamoDTO:
    """
    Conversor entre a entidade Profile e o item DynamoDB.

    Esquema do item:
        PK     = user#{user_id}
        SK     = METADATA
        GSI1PK = role#{role}
        GSI1SK = system#{system}#user#{user_id}

    O GSI1 (`ByRole`) é usado para:
      - Listar perfis por role/sistema (futuro)
      - Contar admins ativos antes de permitir DELETE (impede remoção
        do último admin).
    """

    def __init__(
        self,
        user_id: str,
        role: ProfileRole,
        name: str,
        email: str,
        system: str,
        active: bool,
        created_at: int,
        updated_at: int,
        vehicle_plate: Optional[str] = None,
    ):
        self.user_id = user_id
        self.role = role
        self.name = name
        self.email = email
        self.system = system
        self.active = active
        self.created_at = created_at
        self.updated_at = updated_at
        self.vehicle_plate = vehicle_plate

    @staticmethod
    def from_entity(profile: Profile) -> "ProfileDynamoDTO":
        return ProfileDynamoDTO(
            user_id=profile.user_id,
            role=profile.role,
            name=profile.name,
            email=profile.email,
            system=profile.system,
            active=profile.active,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
            vehicle_plate=profile.vehicle_plate,
        )

    def to_dynamo(self) -> dict:
        return {
            "user_id": self.user_id,
            "role": self.role.value,
            "name": self.name,
            "email": self.email,
            "system": self.system,
            "vehicle_plate": self.vehicle_plate,
            "active": self.active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "GSI1PK": ProfileDynamoDTO.build_gsi1_pk(self.role),
            "GSI1SK": ProfileDynamoDTO.build_gsi1_sk(self.system, self.user_id),
        }

    @staticmethod
    def from_dynamo(data: dict) -> "ProfileDynamoDTO":
        pk = data["PK"]
        if not isinstance(pk, str) or not pk.startswith("user#"):
            raise KeyError("PK")
        user_id = pk.split("user#", 1)[1]
        return ProfileDynamoDTO(
            user_id=user_id,
            role=ProfileRole(data["role"]),
            name=data["name"],
            email=data["email"],
            system=data["system"],
            active=bool(data["active"]),
            created_at=int(data["created_at"]),
            updated_at=int(data["updated_at"]),
            vehicle_plate=data.get("vehicle_plate"),
        )

    def to_entity(self) -> Profile:
        return Profile(
            user_id=self.user_id,
            role=self.role,
            name=self.name,
            email=self.email,
            system=self.system,
            active=self.active,
            created_at=self.created_at,
            updated_at=self.updated_at,
            vehicle_plate=self.vehicle_plate,
        )

    @staticmethod
    def build_pk(user_id: str) -> str:
        return f"user#{user_id}"

    @staticmethod
    def build_sk() -> str:
        return "METADATA"

    @staticmethod
    def build_gsi1_pk(role: ProfileRole) -> str:
        return f"role#{role.value}"

    @staticmethod
    def build_gsi1_sk(system: str, user_id: str) -> str:
        return f"system#{system}#user#{user_id}"
