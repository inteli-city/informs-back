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
        if not Template.validate_id(template_identifier):
            raise EntityError("id")
        self.id = template_identifier
        self.template_id = template_identifier  # compatibility alias

        if not isinstance(name, str) or not name:
            raise EntityError("name")
        self.name = name

        if description is not None and (not isinstance(description, str) or description == ""):
            raise EntityError("description")
        self.description = description

        if not isinstance(system, str) or not system:
            raise EntityError("system")
        self.system = system

        if not isinstance(is_active, bool):
            raise EntityError("is_active")
        self.is_active = is_active

        if not isinstance(created_by, str):
            raise EntityError("created_by")
        self.created_by = created_by

        if not isinstance(created_at, int):
            raise EntityError("created_at")
        self.created_at = created_at

        if not isinstance(updated_at, int):
            raise EntityError("updated_at")
        self.updated_at = updated_at

        if not isinstance(sections, list) or not sections or not all(isinstance(section, Section) for section in sections):
            raise EntityError("sections")
        self.sections = sections

    @staticmethod
    def validate_id(id_to_validate: str) -> bool:
        if not isinstance(id_to_validate, str):
            return False
        if len(id_to_validate) != Template.ID_LENGTH:
            return False
        return True

    def changeName(self, name: str, updated_at: int):
        if not isinstance(name, str) or not name:
            raise EntityError("name")
        self.name = name
        self.changeUpdatedAt(updated_at)

    def changeDescription(self, description: Optional[str], updated_at: int):
        if description is not None and (not isinstance(description, str) or description == ""):
            raise EntityError("description")
        self.description = description
        self.changeUpdatedAt(updated_at)

    def changeSystem(self, system: str, updated_at: int):
        if not isinstance(system, str) or not system:
            raise EntityError("system")
        self.system = system
        self.changeUpdatedAt(updated_at)

    def changeIsActive(self, is_active: bool, updated_at: int):
        if not isinstance(is_active, bool):
            raise EntityError("is_active")
        self.is_active = is_active
        self.changeUpdatedAt(updated_at)

    def changeSections(self, sections: List[Section], updated_at: int):
        if not isinstance(sections, list) or not sections or not all(isinstance(section, Section) for section in sections):
            raise EntityError("sections")
        self.sections = sections
        self.changeUpdatedAt(updated_at)

    def changeUpdatedAt(self, updated_at: int):
        if not isinstance(updated_at, int):
            raise EntityError("updated_at")
        self.updated_at = updated_at
