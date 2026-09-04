from typing import Annotated

from pydantic import Field, StringConstraints

from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
UserIdStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=36, max_length=36)]
# Regex simples e suficiente; evita a dependência do email-validator
# (não está em requirements.txt). Validação canônica fica na entidade Profile.
EmailLikeStr = Annotated[str, StringConstraints(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]


class CreateProfileRequestSchema(RequestContractModel):
    """
    Body do POST /profiles. Apenas ADMIN pode criar perfis (validado no
    controller). Pode criar tanto ADMIN quanto INSPECTOR.
    """

    user_id: UserIdStr
    role: str = Field(pattern="^(ADMIN|INSPECTOR)$")
    name: NonEmptyStr
    email: EmailLikeStr
    system: NonEmptyStr
    vehicle_plate: NonEmptyStr | None = None


class ProfileResponseSchema(ResponseContractModel):
    user_id: str
    role: str
    name: str
    email: str
    system: str
    vehicle_plate: str | None = None
    active: bool
    created_at: int
    updated_at: int
    scope: dict[str, list[str]] = Field(default_factory=dict)


class CreateProfileResponseSchema(ProfileResponseSchema):
    pass


class LoginProfileResponseSchema(ProfileResponseSchema):
    """
    Resposta do POST /profiles/login. Inclui flag indicando se este foi o
    primeiro login (Profile foi criado on-the-fly como INSPECTOR) ou se o
    perfil já existia.
    """

    just_created: bool


class DeleteProfileResponseSchema(ResponseContractModel):
    user_id: str
    active: bool
    updated_at: int


class UpdateProfileRequestSchema(RequestContractModel):
    """
    Body do PUT /profiles/{user_id}. Integração Apex (especificação
    Uberlândia §7.4) — empurra `role`/`scope` quando a permissão regional
    muda. Apenas ADMIN ativo pode chamar (validado no controller).
    """

    role: str = Field(pattern="^(ADMIN|INSPECTOR|MANAGER|SUPERVISOR)$")
    scope: dict[str, list[str]] = Field(default_factory=dict)


class UpdateProfileResponseSchema(ProfileResponseSchema):
    pass
