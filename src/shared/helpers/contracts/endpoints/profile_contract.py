from typing import Annotated

from pydantic import StringConstraints

from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel
from src.shared.helpers.contracts.endpoints.system_access_contract import SystemAccessSchema


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
UserIdStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=36, max_length=36)]
# Regex simples e suficiente; evita a dependência do email-validator
# (não está em requirements.txt). Validação canônica fica na entidade Profile.
EmailLikeStr = Annotated[str, StringConstraints(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]


class CreateProfileRequestSchema(RequestContractModel):
    """
    Body do POST /profiles. Só super admin cria perfis (validado no usecase).
    Cria a pessoa; o role em cada sistema vem de
    PUT /systems/{system}/users/{user_id}.
    """

    user_id: UserIdStr
    name: NonEmptyStr
    email: EmailLikeStr


class ProfileResponseSchema(ResponseContractModel):
    user_id: str
    name: str
    email: str
    active: bool
    super_admin: bool
    created_at: int
    updated_at: int


class CreateProfileResponseSchema(ProfileResponseSchema):
    pass


class LoginProfileResponseSchema(ProfileResponseSchema):
    """
    Resposta do POST /profiles/login. `just_created` indica o primeiro login
    (perfil criado agora). `systems` traz, para cada sistema do usuário, o
    role e as ações que ele libera — o app decide o que mostrar por aqui.
    """

    just_created: bool
    systems: list[SystemAccessSchema]


class DeleteProfileResponseSchema(ResponseContractModel):
    user_id: str
    active: bool
    updated_at: int
