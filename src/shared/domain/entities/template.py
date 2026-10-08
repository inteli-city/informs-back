from typing import List, Optional
from uuid import uuid4
from datetime import datetime, timezone
import uuid

from src.shared.domain.entities.justification import JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.helpers.errors.domain_errors import EntityError


class Template:
    id: str
    name: str
    system: str
    description: Optional[str]
    is_active: bool
    sections: List[Section]
    created_by: str
    created_at: int
    updated_at: int

    ID_LENGTH = 36

    def __init__(
        self,
        name: str,
        system: str,
        created_by: str,
        sections: List[Section],
        description: Optional[str] = None,
        is_active: bool = True,
        id: Optional[str] = None,
        created_at: Optional[int] = None,
        updated_at: Optional[int] = None,
        justification_options: Optional[List[JustificationOption]] = None,
    ):
        template_identifier = id or str(uuid.uuid4())
        self._validate_id(template_identifier)
        self.id = template_identifier

        self._validate_name(name)
        self.name = name

        self._validate_description(description)
        self.description = description

        self._validate_system(system)
        self.system = system

        self._validate_is_active(is_active)
        self.is_active = is_active

        self._validate_created_by(created_by)
        self.created_by = created_by

        self._validate_created_at(created_at)
        self.created_at = created_at

        self._validate_updated_at(updated_at)
        self.updated_at = updated_at

        self._validate_sections(sections)
        self.sections = sections

        # Motivos de cancelamento que todo formulário criado a partir deste
        # template herda (quando o criador não manda os próprios).
        self.justification_options = self._validate_justification_options(justification_options)

    @staticmethod
    def _validate_id(id_to_validate: str) -> None:
        if not isinstance(id_to_validate, str) or len(id_to_validate) != Template.ID_LENGTH:
            raise EntityError("ID do template inválido ou ausente")

    @staticmethod
    def _validate_name(name: str) -> None:
        if not isinstance(name, str) or not name:
            raise EntityError("Nome do template deve ser uma string não vazia")

    @staticmethod
    def _validate_description(description: Optional[str]) -> None:
        if description is not None and (not isinstance(description, str) or description == ""):
            raise EntityError("Descrição deve ser uma string não vazia")

    @staticmethod
    def _validate_system(system: str) -> None:
        if not isinstance(system, str) or not system:
            raise EntityError("Sistema deve ser uma string não vazia")

    @staticmethod
    def _validate_is_active(is_active: bool) -> None:
        if not isinstance(is_active, bool):
            raise EntityError("Campo 'is_active' deve ser verdadeiro ou falso")

    @staticmethod
    def _validate_created_by(created_by: str) -> None:
        if not isinstance(created_by, str):
            raise EntityError("ID do criador deve ser uma string")

    @staticmethod
    def _validate_created_at(created_at: int) -> None:
        if not isinstance(created_at, int):
            raise EntityError("Timestamp de criação deve ser um inteiro")

    @staticmethod
    def _validate_updated_at(updated_at: int) -> None:
        if not isinstance(updated_at, int):
            raise EntityError("Timestamp de atualização deve ser um inteiro")

    @staticmethod
    def _validate_sections(sections: List[Section]) -> None:
        if not isinstance(sections, list) or not sections or not all(isinstance(section, Section) for section in sections):
            raise EntityError("Seções devem ser uma lista não vazia de seções válidas")

    @staticmethod
    def _validate_justification_options(options: Optional[List[JustificationOption]]) -> List[JustificationOption]:
        if options is None:
            return []
        if not isinstance(options, list) or not all(isinstance(option, JustificationOption) for option in options):
            raise EntityError("Motivos de cancelamento devem ser uma lista de opções válidas")
        labels = [option.option.strip() for option in options]
        if any(not label for label in labels):
            raise EntityError("Motivo de cancelamento não pode ser vazio")
        if len(set(labels)) != len(labels):
            raise EntityError("Motivos de cancelamento repetidos")
        return options

    def change_justification_options(self, options: List[JustificationOption]):
        self.justification_options = self._validate_justification_options(options)

    @staticmethod
    def validate_id(id_to_validate: str) -> bool:
        try:
            Template._validate_id(id_to_validate)
        except EntityError:
            return False
        return True

    def change_name(self, name: str):
        self._validate_name(name)
        self.name = name

    def change_description(self, description: Optional[str]):
        self._validate_description(description)
        self.description = description

    def change_system(self, system: str):
        self._validate_system(system)
        self.system = system

    def change_is_active(self, is_active: bool):
        self._validate_is_active(is_active)
        self.is_active = is_active

    def change_sections(self, sections: List[Section]):
        self._validate_sections(sections)
        self.sections = sections

    def change_updated_at(self, updated_at: int):
        self._validate_updated_at(updated_at)
        self.updated_at = updated_at
