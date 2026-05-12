import abc
from typing import Optional

from src.shared.domain.enums.profile_role_enum import ProfileRole
from src.shared.helpers.errors.domain_errors import EntityError


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
    role: ProfileRole
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
        role: ProfileRole,
        name: str,
        email: str,
        system: str,
        active: bool,
        created_at: int,
        updated_at: int,
        vehicle_plate: Optional[str] = None,
    ):
        # Cada validação fica num método auxiliar pra manter o construtor
        # com baixa cognitive complexity (regra python:S3776).
        self.user_id = self._validate_user_id(user_id)
        self.role = self._validate_role(role)
        self.name = self._validate_name(name)
        self.email = self._validate_email(email)
        self.system = self._validate_system(system)
        self.vehicle_plate = self._validate_vehicle_plate(vehicle_plate)
        self.active = self._validate_active(active)
        self.created_at = self._validate_timestamp(created_at, label="criação")
        self.updated_at = self._validate_timestamp(updated_at, label="atualização")

    # --- Validações --------------------------------------------------------

    @staticmethod
    def _validate_user_id(user_id: str) -> str:
        if not Profile.validate_user_id(user_id):
            raise EntityError("ID do usuário inválido ou ausente")
        return user_id

    @staticmethod
    def _validate_role(role: ProfileRole) -> ProfileRole:
        if not isinstance(role, ProfileRole):
            raise EntityError("Role inválida")
        return role

    @staticmethod
    def _validate_name(name: str) -> str:
        if not isinstance(name, str) or not name.strip():
            raise EntityError("Nome do perfil deve ser uma string não vazia")
        return name

    @staticmethod
    def _validate_email(email: str) -> str:
        # Validação simples sem regex catastrófica (rule python:S5852):
        # exige presença de '@', algo antes e depois, e um ponto na parte
        # do domínio. Suficiente para um sanity-check; validação canônica
        # do email (DNS, MX, etc.) fica no lado do IdP/Cognito.
        if not isinstance(email, str):
            raise EntityError("Email do perfil inválido")
        local, sep, domain = email.partition("@")
        if not sep or not local or not domain or "." not in domain:
            raise EntityError("Email do perfil inválido")
        return email

    @staticmethod
    def _validate_system(system: str) -> str:
        if not isinstance(system, str) or not system.strip():
            raise EntityError("Sistema do perfil deve ser uma string não vazia")
        return system

    @staticmethod
    def _validate_vehicle_plate(plate: Optional[str]) -> Optional[str]:
        if plate is None:
            return None
        if not isinstance(plate, str) or not plate.strip():
            raise EntityError("Placa do veículo deve ser uma string não vazia ou null")
        return plate

    @staticmethod
    def _validate_active(active: bool) -> bool:
        if not isinstance(active, bool):
            raise EntityError("Campo 'active' deve ser verdadeiro ou falso")
        return active

    @staticmethod
    def _validate_timestamp(value: int, *, label: str) -> int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise EntityError(f"Timestamp de {label} deve ser um inteiro")
        return value

    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        if not isinstance(user_id, str):
            return False
        return len(user_id) == Profile.USER_ID_LENGTH

    def deactivate(self, updated_at: int) -> None:
        """Soft delete: marca o perfil como inativo sem remover o item."""
        self.updated_at = self._validate_timestamp(updated_at, label="atualização")
        self.active = False
