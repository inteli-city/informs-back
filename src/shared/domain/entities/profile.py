import abc
import re
from typing import Optional

from src.shared.domain.enums.profile_role_enum import PROFILE_ROLE
from src.shared.helpers.errors.domain_errors import EntityError


_EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Profile(abc.ABC):
    """
    Identidade interna do usuário no Informs.

    O Cognito (IdP) autentica o usuário e injeta o `sub` no JWT. O Profile
    associa esse `sub` (campo `user_id`) à role aplicacional (ADMIN ou
    INSPECTOR), ao sistema operado e a metadados de uso (placa de moto, etc.).

    A flag `active` permite "desligar" um perfil sem perder o histórico —
    como ainda não há endpoint de UPDATE, o DELETE faz soft delete setando
    `active=False`.
    """

    USER_ID_LENGTH = 36

    user_id: str
    role: PROFILE_ROLE
    name: str
    email: str
    system: str
    vehicle_plate: Optional[str]
    active: bool
    created_at: int
    updated_at: int

    def __init__(
        self,
        user_id: str,
        role: PROFILE_ROLE,
        name: str,
        email: str,
        system: str,
        active: bool,
        created_at: int,
        updated_at: int,
        vehicle_plate: Optional[str] = None,
    ):
        if not Profile.validate_user_id(user_id):
            raise EntityError("ID do usuário inválido ou ausente")
        self.user_id = user_id

        if not isinstance(role, PROFILE_ROLE):
            raise EntityError("Role inválida")
        self.role = role

        if not isinstance(name, str) or not name.strip():
            raise EntityError("Nome do perfil deve ser uma string não vazia")
        self.name = name

        if not isinstance(email, str) or not _EMAIL_REGEX.match(email):
            raise EntityError("Email do perfil inválido")
        self.email = email

        if not isinstance(system, str) or not system.strip():
            raise EntityError("Sistema do perfil deve ser uma string não vazia")
        self.system = system

        if vehicle_plate is not None and (not isinstance(vehicle_plate, str) or not vehicle_plate.strip()):
            raise EntityError("Placa do veículo deve ser uma string não vazia ou null")
        self.vehicle_plate = vehicle_plate

        if not isinstance(active, bool):
            raise EntityError("Campo 'active' deve ser verdadeiro ou falso")
        self.active = active

        if not isinstance(created_at, int) or isinstance(created_at, bool):
            raise EntityError("Timestamp de criação deve ser um inteiro")
        self.created_at = created_at

        if not isinstance(updated_at, int) or isinstance(updated_at, bool):
            raise EntityError("Timestamp de atualização deve ser um inteiro")
        self.updated_at = updated_at

    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        if not isinstance(user_id, str):
            return False
        return len(user_id) == Profile.USER_ID_LENGTH

    def deactivate(self, updated_at: int) -> None:
        """Soft delete: marca o perfil como inativo sem remover o item."""
        if not isinstance(updated_at, int) or isinstance(updated_at, bool):
            raise EntityError("Timestamp de atualização deve ser um inteiro")
        self.active = False
        self.updated_at = updated_at
