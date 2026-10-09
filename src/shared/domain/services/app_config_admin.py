from typing import List

from src.shared.domain.enums.action_enum import Action
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.usecase_errors import ForbiddenAction


def editable_systems(access_control: AccessControl, user_id: str) -> List[str]:
    """
    Sistemas cuja configuração a pessoa edita no Admin (`app_config.edit` pelo
    role do sistema). Sem nenhum, e sem ser super admin, não entra no Admin.
    O super admin edita todo sistema — quem chama trata esse caso.
    """
    systems = access_control.systems_where(user_id, Action.APP_CONFIG_EDIT)
    if not systems and not access_control.is_super_admin(user_id):
        raise ForbiddenAction("Apenas quem edita a configuração de algum sistema acessa o Admin")
    return systems


STALE_VERSION_MESSAGE = (
    "A configuração foi alterada por outra pessoa enquanto você editava. "
    "Recarregue para ver a versão atual e refaça a alteração."
)
