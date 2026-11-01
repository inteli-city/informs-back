from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from src.shared.domain.enums.action_enum import Action
from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel


# Literal montado do catálogo: o OpenAPI mostra as ações válidas e uma ação
# desconhecida é recusada (400) já na validação do request.
ActionLiteral = Literal[tuple(action.value for action in Action)]
RoleNameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
RoleIdStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
# Identificador de grupo (ADR-0022): curto, minúsculo, com hífen — é o que o
# sistema de origem manda no POST /forms. Mesma regra de `SystemGroup`.
GroupIdStr = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?$")]
GroupNameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]


class SystemAccessSchema(ResponseContractModel):
    """O que a pessoa pode fazer em um sistema. Sem vínculo: role nulo e
    nenhuma ação (super admin: todas as ações mesmo sem vínculo)."""

    system: str
    role_id: str | None = None
    role_name: str | None = None
    actions: list[ActionLiteral]


# --- Catálogo de ações ------------------------------------------------------

class ActionSchema(ResponseContractModel):
    action: ActionLiteral
    description: str


class GetPermissionActionsResponseSchema(ResponseContractModel):
    actions: list[ActionSchema]


# --- Roles do sistema -------------------------------------------------------

class SystemRoleSchema(ResponseContractModel):
    system: str
    role_id: str
    name: str
    actions: list[ActionLiteral]
    is_default: bool
    # O ADMIN é o role fixo: não se edita nem se apaga, e só super admin o dá.
    fixed: bool


class GetSystemRolesResponseSchema(ResponseContractModel):
    system: str
    roles: list[SystemRoleSchema]


class SystemRoleRequestSchema(RequestContractModel):
    """Body do POST e do PUT de role: o PUT substitui o role inteiro."""

    name: RoleNameStr
    actions: list[ActionLiteral]
    # Role dado a quem entra no sistema pela primeira vez. Marcar um tira a
    # marca do anterior.
    is_default: bool = False


class SystemRoleResponseSchema(SystemRoleSchema):
    pass


class DeleteSystemRoleResponseSchema(ResponseContractModel):
    system: str
    role_id: str


# --- Pessoas do sistema -----------------------------------------------------

class SystemUserSchema(ResponseContractModel):
    user_id: str
    name: str | None = None
    email: str | None = None
    active: bool
    role_id: str
    role_name: str | None = None
    groups: list[str] = Field(default_factory=list)


class GetSystemUsersResponseSchema(ResponseContractModel):
    system: str
    users: list[SystemUserSchema]


class PutSystemUserRequestSchema(RequestContractModel):
    """Body do PUT /systems/{system}/users/{user_id}: o role da pessoa no
    sistema (id de um role do sistema, ou "ADMIN")."""

    role_id: RoleIdStr


class PutSystemUserResponseSchema(ResponseContractModel):
    system: str
    user_id: str
    role_id: str
    role_name: str | None = None


class DeleteSystemUserResponseSchema(ResponseContractModel):
    system: str
    user_id: str


# --- Grupos do sistema (ADR-0022) --------------------------------------------

class SystemGroupSchema(ResponseContractModel):
    system: str
    group_id: str
    name: str


class GetSystemGroupsResponseSchema(ResponseContractModel):
    system: str
    groups: list[SystemGroupSchema]


class CreateSystemGroupRequestSchema(RequestContractModel):
    """Body do POST de grupo. `group_id` não muda depois: é o identificador que
    o sistema de origem manda no POST /forms."""

    group_id: GroupIdStr
    name: GroupNameStr


class UpdateSystemGroupRequestSchema(RequestContractModel):
    """Body do PUT de grupo: só o nome muda."""

    name: GroupNameStr


class SystemGroupResponseSchema(SystemGroupSchema):
    pass


class DeleteSystemGroupResponseSchema(ResponseContractModel):
    system: str
    group_id: str


class PutSystemUserGroupsRequestSchema(RequestContractModel):
    """Body do PUT /systems/{system}/users/{user_id}/groups: a lista inteira de
    grupos da pessoa no sistema (substitui a anterior)."""

    groups: list[GroupIdStr]


class PutSystemUserGroupsResponseSchema(ResponseContractModel):
    system: str
    user_id: str
    groups: list[str]
