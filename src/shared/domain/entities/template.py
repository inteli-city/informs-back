from typing import List, Optional
from uuid import uuid4
from datetime import datetime, timezone

from src.shared.domain.entities.section import Section
from src.shared.helpers.errors.domain_errors import EntityError


class Template:
    id: str
    template_id: str
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
        template_id: Optional[str] = None,
        created_at: Optional[int] = None,
        updated_at: Optional[int] = None,
    ):
        if not isinstance(name, str) or not name:
            raise EntityError("name")
        self.name = name

        if not isinstance(system, str) or not system:
            raise EntityError("system")
        self.system = system

        if description is not None and not isinstance(description, str):
            raise EntityError("description")
        self.description = description

        if not isinstance(is_active, bool):
            raise EntityError("is_active")
        self.is_active = is_active

        if not isinstance(created_by, str) or not created_by:
            raise EntityError("created_by")
        self.created_by = created_by

        if not isinstance(sections, list) or not sections or not all(isinstance(section, Section) for section in sections):
            raise EntityError("sections")
        self.sections = sections

        now_ts = int(datetime.now(timezone.utc).timestamp() * 1000)
        chosen_id = id or template_id or str(uuid4())
        if not isinstance(chosen_id, str):
            raise EntityError("id")
        self.id = chosen_id
        self.template_id = chosen_id

        self.created_at = created_at if created_at is not None else now_ts
        if not isinstance(self.created_at, int):
            raise EntityError("created_at")

        self.updated_at = updated_at if updated_at is not None else self.created_at
        if not isinstance(self.updated_at, int):
            raise EntityError("updated_at")

    @property
    def sessions(self) -> List[Section]:
        return self.sections

    def changeName(self, new_name: str, updated_at: int):
        if not isinstance(new_name, str) or not new_name:
            raise EntityError("name")
        if not isinstance(updated_at, int):
            raise EntityError("updated_at")
        self.name = new_name
        self.updated_at = updated_at

    def changeDescription(self, new_description: Optional[str], updated_at: int):
        if new_description is not None and not isinstance(new_description, str):
            raise EntityError("description")
        if not isinstance(updated_at, int):
            raise EntityError("updated_at")
        self.description = new_description
        self.updated_at = updated_at

    def changeSections(self, sections: List[Section], updated_at: int):
        if not isinstance(sections, list) or not sections or not all(isinstance(section, Section) for section in sections):
            raise EntityError("sections")
        if not isinstance(updated_at, int):
            raise EntityError("updated_at")
        self.sections = sections
        self.updated_at = updated_at
