from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.profile_repository_interface import IProfileRepository
from src.shared.domain.repositories.system_group_repository_interface import ISystemGroupRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.domain.services.role_management import ensure_can
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, NoItemsFound


class DeleteSystemGroupUsecase:
    """
    Apaga um grupo do sistema (ADR-0022). Recusa (409) se:
      - alguém ainda está no grupo (tirar as pessoas antes);
      - alguma OS aberta no pool aponta para ele (ela ficaria sem ninguém
        que pudesse pegá-la).
    """

    def __init__(
        self,
        access_control: AccessControl,
        group_repo: ISystemGroupRepository,
        profile_repo: IProfileRepository,
        form_repo: IFormRepository,
    ):
        self.access_control = access_control
        self.group_repo = group_repo
        self.profile_repo = profile_repo
        self.form_repo = form_repo

    def __call__(self, requester_user_id: str, system: str, group_id: str) -> None:
        ensure_can(self.access_control, requester_user_id, system, Action.GROUPS_MANAGE)

        if self.group_repo.get_group(system, group_id) is None:
            raise NoItemsFound(f"Grupo {group_id} não encontrado no sistema {system}")

        members = sum(
            1 for membership in self.profile_repo.list_memberships_by_system(system) if group_id in membership.groups
        )
        if members:
            raise DuplicatedItem(f"Grupo com {members} pessoa(s): tire as pessoas do grupo antes de apagar")
        if self.form_repo.pool_has_group(system, group_id):
            raise DuplicatedItem("Há formulários abertos destinados a este grupo: atribua ou cancele-os antes de apagar")

        self.group_repo.delete_group(system, group_id)
