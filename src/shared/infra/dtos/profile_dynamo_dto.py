from src.shared.domain.entities.profile import Profile


class ProfileDynamoDTO:
    """
    Conversor entre a entidade Profile e o item DynamoDB (tabela de Profiles).

    Esquema do item:
        PK     = user#{user_id}
        SK     = METADATA
        GSI1PK = super_admin          (só quando super_admin — índice esparso)
        GSI1SK = user#{user_id}

    O GSI1 (`ByRole`) conta os super admins ativos antes de um DELETE
    (impede desativar o último). Os vínculos da pessoa com os sistemas ficam
    em itens próprios na mesma partição (ver SystemMembershipDynamoDTO).
    """

    SUPER_ADMIN_GSI1PK = "super_admin"

    def __init__(
        self,
        user_id: str,
        name: str,
        email: str,
        active: bool,
        created_at: int,
        updated_at: int,
        super_admin: bool = False,
    ):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.active = active
        self.super_admin = super_admin
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def from_entity(profile: Profile) -> "ProfileDynamoDTO":
        return ProfileDynamoDTO(
            user_id=profile.user_id,
            name=profile.name,
            email=profile.email,
            active=profile.active,
            super_admin=profile.super_admin,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    def to_dynamo(self) -> dict:
        item = {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "active": self.active,
            "super_admin": self.super_admin,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.super_admin:
            item["GSI1PK"] = ProfileDynamoDTO.SUPER_ADMIN_GSI1PK
            item["GSI1SK"] = ProfileDynamoDTO.build_pk(self.user_id)
        return item

    @staticmethod
    def from_dynamo(data: dict) -> "ProfileDynamoDTO":
        pk = data["PK"]
        if not isinstance(pk, str) or not pk.startswith("user#"):
            raise KeyError("PK")
        user_id = pk.split("user#", 1)[1]
        return ProfileDynamoDTO(
            user_id=user_id,
            name=data["name"],
            email=data["email"],
            active=bool(data["active"]),
            super_admin=bool(data.get("super_admin", False)),
            created_at=int(data["created_at"]),
            updated_at=int(data["updated_at"]),
        )

    def to_entity(self) -> Profile:
        return Profile(
            user_id=self.user_id,
            name=self.name,
            email=self.email,
            active=self.active,
            super_admin=self.super_admin,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @staticmethod
    def build_pk(user_id: str) -> str:
        return f"user#{user_id}"

    @staticmethod
    def build_sk() -> str:
        return "METADATA"
