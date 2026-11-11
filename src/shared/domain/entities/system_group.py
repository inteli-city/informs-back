import re

from src.shared.helpers.errors.domain_errors import EntityError


GROUP_ID_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?$")


class SystemGroup:
    """
    Grupo de pessoas de um sistema (ADR-0022). Uma OS aberta com `groups` só
    é vista e pega no pool por quem está num deles.

    `group_id` é curto, escolhido na criação e não muda: é o que o sistema de
    origem manda no POST /forms. `name` é só o rótulo de exibição.
    """

    NAME_MAX_LENGTH = 60

    system: str
    group_id: str
    name: str
    created_at: int
    updated_at: int

    def __init__(self, system: str, group_id: str, name: str, created_at: int, updated_at: int):
        self.system = self._validate_system(system)
        self.group_id = self.validate_group_id(group_id)
        self.name = self._validate_name(name)
        self.created_at = self._validate_timestamp(created_at, label="criação")
        self.updated_at = self._validate_timestamp(updated_at, label="atualização")

    @staticmethod
    def _validate_system(system: str) -> str:
        if not isinstance(system, str) or not system.strip():
            raise EntityError("Sistema do grupo deve ser uma string não vazia")
        return system

    @staticmethod
    def validate_group_id(group_id: str) -> str:
        if not isinstance(group_id, str) or not GROUP_ID_PATTERN.match(group_id):
            raise EntityError(
                "Identificador do grupo deve ter de 1 a 40 caracteres: letras minúsculas, números e hífen"
            )
        return group_id

    @staticmethod
    def _validate_name(name: str) -> str:
        if not isinstance(name, str) or not name.strip():
            raise EntityError("Nome do grupo deve ser uma string não vazia")
        if len(name.strip()) > SystemGroup.NAME_MAX_LENGTH:
            raise EntityError(f"Nome do grupo deve ter no máximo {SystemGroup.NAME_MAX_LENGTH} caracteres")
        return name.strip()

    @staticmethod
    def _validate_timestamp(value: int, *, label: str) -> int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise EntityError(f"Timestamp de {label} do grupo deve ser um inteiro")
        return value
