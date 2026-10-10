from typing import Iterable, Optional

from src.shared.domain.entities.system_role import SystemRole
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.system_role_repository_interface import ISystemRoleRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction


def ensure_can(access_control: AccessControl, user_id: str, system: str, action: Action) -> None:
    if not access_control.can(user_id, system, action):
        raise ForbiddenAction(f"Usuário não tem a permissão '{action.value}' no sistema {system}")


def ensure_no_escalation(access_control: AccessControl, user_id: str, system: str, actions: Iterable[Action]) -> None:
    """Quem não administra o sistema só cria, edita ou dá roles com ações que
    ele mesmo tem — senão `roles.manage` + `users.manage` viraria ADMIN."""
    own = access_control.access_in(user_id, system).actions
    missing = sorted(action.value for action in set(actions) - own)
    if missing:
        raise ForbiddenAction(f"Usuário não pode conceder ações que não tem: {', '.join(missing)}")


def ensure_unique_name(role_repo: ISystemRoleRepository, system: str, name: str, ignore_role_id: Optional[str] = None) -> None:
    for role in role_repo.list_roles(system):
        if role.role_id != ignore_role_id and role.name.casefold() == name.strip().casefold():
            raise DuplicatedItem(f"Já existe um role '{role.name}' no sistema {system}")


def clear_other_defaults(role_repo: ISystemRoleRepository, system: str, keep_role_id: str, now_ms: int) -> None:
    """Um role padrão por sistema: marcar um tira a marca dos outros."""
    for role in role_repo.list_roles(system):
        if role.is_default and role.role_id != keep_role_id:
            role_repo.put_role(SystemRole(
                system=role.system,
                role_id=role.role_id,
                name=role.name,
                actions=role.actions,
                is_default=False,
                created_at=role.created_at,
                updated_at=now_ms,
            ))
