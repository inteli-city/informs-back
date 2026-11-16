import uuid
from typing import List, Optional, Sequence

from src.shared.domain.enums.action_enum import Action
from src.shared.domain.enums.assignment_option_enum import (
    DEFAULT_ASSIGNMENT,
    DEFAULT_ASSIGNMENT_OPTIONS,
    AssignmentOption,
)
from src.shared.domain.enums.home_tab_enum import HomeTab
from src.shared.helpers.errors.domain_errors import EntityError


# O único role fixo: existe em todo sistema, tem todas as ações e só um
# super admin pode dá-lo a alguém. Não é gravado como SystemRole.
ADMIN_ROLE_ID = "ADMIN"
ADMIN_ROLE_NAME = "Administrador"


class SystemRole:
    """
    Role criado por um sistema: um nome e as ações (do catálogo fixo) que ele
    libera. `is_default` marca o role dado a quem entra no sistema pela
    primeira vez — no máximo um por sistema. `home_tab` é a aba em que o app
    abre para quem tem o role. `assignment_options` diz para quem a pessoa pode
    criar formulário no app e `default_assignment`, qual vem marcado.
    """

    NAME_MAX_LENGTH = 40

    system: str
    role_id: str
    name: str
    actions: List[Action]
    is_default: bool
    home_tab: HomeTab
    assignment_options: List[AssignmentOption]
    default_assignment: AssignmentOption
    created_at: int
    updated_at: int

    def __init__(
        self,
        system: str,
        name: str,
        actions: List[Action],
        created_at: int,
        updated_at: int,
        is_default: bool = False,
        role_id: str = None,
        home_tab: HomeTab = HomeTab.LIST,
        assignment_options: Optional[Sequence[AssignmentOption]] = None,
        default_assignment: Optional[AssignmentOption] = None,
    ):
        self.system = self._validate_system(system)
        self.role_id = self._validate_role_id(role_id if role_id is not None else str(uuid.uuid4()))
        self.name = self._validate_name(name)
        self.actions = self._validate_actions(actions)
        self.is_default = self._validate_is_default(is_default)
        self.home_tab = self._validate_home_tab(home_tab)
        self.assignment_options = self._validate_assignment_options(
            list(DEFAULT_ASSIGNMENT_OPTIONS) if assignment_options is None else assignment_options
        )
        self.default_assignment = self._validate_default_assignment(
            DEFAULT_ASSIGNMENT if default_assignment is None else default_assignment, self.assignment_options
        )
        self.created_at = self._validate_timestamp(created_at, label="criação")
        self.updated_at = self._validate_timestamp(updated_at, label="atualização")

    @staticmethod
    def _validate_system(system: str) -> str:
        if not isinstance(system, str) or not system.strip():
            raise EntityError("Sistema do role deve ser uma string não vazia")
        return system

    @staticmethod
    def _validate_role_id(role_id: str) -> str:
        if not isinstance(role_id, str) or not role_id.strip():
            raise EntityError("ID do role deve ser uma string não vazia")
        if role_id == ADMIN_ROLE_ID:
            raise EntityError(f"'{ADMIN_ROLE_ID}' é reservado para o role fixo de administrador")
        return role_id

    @staticmethod
    def _validate_name(name: str) -> str:
        if not isinstance(name, str) or not name.strip():
            raise EntityError("Nome do role deve ser uma string não vazia")
        if len(name.strip()) > SystemRole.NAME_MAX_LENGTH:
            raise EntityError(f"Nome do role deve ter no máximo {SystemRole.NAME_MAX_LENGTH} caracteres")
        if name.strip().casefold() == ADMIN_ROLE_NAME.casefold():
            raise EntityError(f"'{ADMIN_ROLE_NAME}' é o nome do role fixo de administrador")
        return name.strip()

    @staticmethod
    def _validate_actions(actions: List[Action]) -> List[Action]:
        if not isinstance(actions, list) or not all(isinstance(action, Action) for action in actions):
            raise EntityError("Ações do role devem ser uma lista de ações do catálogo")
        return list(dict.fromkeys(actions))

    @staticmethod
    def _validate_is_default(is_default: bool) -> bool:
        if not isinstance(is_default, bool):
            raise EntityError("is_default deve ser verdadeiro ou falso")
        return is_default

    @staticmethod
    def _validate_home_tab(home_tab: HomeTab) -> HomeTab:
        if not isinstance(home_tab, HomeTab):
            raise EntityError("Aba inicial do role deve ser create, list ou map")
        return home_tab

    @staticmethod
    def _validate_assignment_options(options: Sequence[AssignmentOption]) -> List[AssignmentOption]:
        if not isinstance(options, (list, tuple)) or not all(isinstance(o, AssignmentOption) for o in options):
            raise EntityError("Opções de destino do role devem ser self, targeted ou open")
        if not options:
            raise EntityError("O role precisa de ao menos uma opção de para quem criar formulário")
        # Ordem fixa (a da tela), sem repetição.
        return [option for option in AssignmentOption if option in options]

    @staticmethod
    def _validate_default_assignment(
        default: AssignmentOption, options: List[AssignmentOption],
    ) -> AssignmentOption:
        if not isinstance(default, AssignmentOption):
            raise EntityError("Opção padrão de destino deve ser self, targeted ou open")
        if default not in options:
            raise EntityError("A opção que vem marcada precisa ser uma das opções ligadas no role")
        return default

    @staticmethod
    def _validate_timestamp(value: int, *, label: str) -> int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise EntityError(f"Timestamp de {label} deve ser um inteiro")
        return value
