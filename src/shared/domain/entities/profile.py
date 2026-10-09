import abc

from src.shared.helpers.errors.domain_errors import EntityError


class Profile(abc.ABC):
    """
    Identidade interna do usuário no Informs.

    O Cognito (IdP) autentica o usuário e injeta o `sub` no JWT; o Profile
    associa esse `sub` (campo `user_id`) à pessoa no Informs. O que ela pode
    fazer em cada sistema fica nos vínculos (`SystemMembership`), não aqui.

    `super_admin` é quem administra a plataforma: pode tudo em todo sistema e
    é o único que dá o role ADMIN de um sistema a alguém.

    A flag `active` permite "desligar" um perfil sem perder o histórico — o
    DELETE faz soft delete setando `active=False`.
    """

    USER_ID_LENGTH = 36

    user_id: str
    name: str
    email: str
    active: bool
    super_admin: bool
    created_at: int
    updated_at: int

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
        # Cada validação fica num método auxiliar pra manter o construtor
        # com baixa cognitive complexity (regra python:S3776).
        self.user_id = self._validate_user_id(user_id)
        self.name = self._validate_name(name)
        self.email = self._validate_email(email)
        self.active = self._validate_bool(active, "active")
        self.super_admin = self._validate_bool(super_admin, "super_admin")
        self.created_at = self._validate_timestamp(created_at, label="criação")
        self.updated_at = self._validate_timestamp(updated_at, label="atualização")

    # --- Validações --------------------------------------------------------

    @staticmethod
    def _validate_user_id(user_id: str) -> str:
        if not Profile.validate_user_id(user_id):
            raise EntityError("ID do usuário inválido ou ausente")
        return user_id

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
    def _validate_bool(value: bool, field: str) -> bool:
        if not isinstance(value, bool):
            raise EntityError(f"Campo '{field}' deve ser verdadeiro ou falso")
        return value

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

    def is_active_super_admin(self) -> bool:
        return self.active and self.super_admin

    def deactivate(self, updated_at: int) -> None:
        """Soft delete: marca o perfil como inativo sem remover o item."""
        self.updated_at = self._validate_timestamp(updated_at, label="atualização")
        self.active = False
