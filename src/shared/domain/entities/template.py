import abc
from typing import List, Optional
import uuid

from src.shared.domain.entities.section import Section
from src.shared.helpers.errors.domain_errors import EntityError


class Template(abc.ABC):
    id: str
    name: str
    description: Optional[str]
    system: str
    is_active: bool
    created_by: str
    created_at: int
    updated_at: int
    sections: List[Section]

    ID_LENGTH = 36

    def __init__(
        self,
        name: str,
        system: str,
        created_by: str,
        created_at: int,
        updated_at: int,
        sections: List[Section],
        id: Optional[str] = None,
        template_id: Optional[str] = None,
        description: Optional[str] = None,
        is_active: bool = True,
    ):
        template_identifier = id or template_id or str(uuid.uuid4())
        self._validate_id(template_identifier)
        self.id = template_identifier
        self.template_id = self.id

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

    @staticmethod
    def _validate_id(id_to_validate: str) -> None:
        if not isinstance(id_to_validate, str) or len(id_to_validate) != Template.ID_LENGTH:
            raise EntityError("id")

    @staticmethod
    def _validate_name(name: str) -> None:
        if not isinstance(name, str) or not name:
            raise EntityError("name")

    @staticmethod
    def _validate_description(description: Optional[str]) -> None:
        if description is not None and (not isinstance(description, str) or description == ""):
            raise EntityError("description")

    @staticmethod
    def _validate_system(system: str) -> None:
        if not isinstance(system, str) or not system:
            raise EntityError("system")

    @staticmethod
    def _validate_is_active(is_active: bool) -> None:
        if not isinstance(is_active, bool):
            raise EntityError("is_active")

    @staticmethod
    def _validate_created_by(created_by: str) -> None:
        if not isinstance(created_by, str):
            raise EntityError("created_by")

    @staticmethod
    def _validate_created_at(created_at: int) -> None:
        if not isinstance(created_at, int):
            raise EntityError("created_at")

    @staticmethod
    def _validate_updated_at(updated_at: int) -> None:
        if not isinstance(updated_at, int):
            raise EntityError("updated_at")

    @staticmethod
    def _validate_sections(sections: List[Section]) -> None:
        if not isinstance(sections, list) or not sections or not all(isinstance(section, Section) for section in sections):
            raise EntityError("sections")

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
