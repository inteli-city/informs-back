from typing import List, Optional

from src.shared.domain.entities.section import Section
from src.shared.domain.entities.justification import JustificationOption
from src.shared.domain.entities.template import Template
from src.shared.infra.dtos.section_dto import SectionDTO


class TemplateDynamoDTO:
    id: str
    name: str
    description: Optional[str]
    system: str
    is_active: bool
    created_by: str
    created_at: int
    updated_at: int
    sections: List[Section]

    def __init__(
        self,
        id: str,
        name: str,
        system: str,
        is_active: bool,
        created_by: str,
        created_at: int,
        updated_at: int,
        sections: List[Section],
        description: Optional[str] = None,
        justification_options: Optional[List[JustificationOption]] = None,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.system = system
        self.is_active = is_active
        self.created_by = created_by
        self.created_at = created_at
        self.updated_at = updated_at
        self.sections = sections
        self.justification_options = justification_options or []

    @staticmethod
    def from_entity(template: Template) -> "TemplateDynamoDTO":
        return TemplateDynamoDTO(
            id=template.id,
            name=template.name,
            description=template.description,
            system=template.system,
            is_active=template.is_active,
            created_by=template.created_by,
            created_at=template.created_at,
            updated_at=template.updated_at,
            sections=template.sections,
            justification_options=template.justification_options,
        )

    def to_dynamo(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "system": self.system,
            "is_active": self.is_active,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "sections": [SectionDTO.from_entity(section).to_dynamo() for section in self.sections],
            "justification_options": [
                {"option": o.option, "required_image": o.required_image, "required_text": o.required_text}
                for o in self.justification_options
            ],
        }

    @staticmethod
    def from_dynamo(data: dict) -> "TemplateDynamoDTO":
        pk = data["PK"]
        if not isinstance(pk, str) or not pk.startswith("template#"):
            raise KeyError("PK")
        template_id = pk.split("template#", 1)[1]
        return TemplateDynamoDTO(
            id=template_id,
            name=data["name"],
            description=data.get("description"),
            system=data["system"],
            is_active=bool(data["is_active"]),
            created_by=data["created_by"],
            created_at=int(data["created_at"]),
            updated_at=int(data["updated_at"]),
            sections=[SectionDTO.from_dynamo(section).to_entity() for section in data["sections"]],
            justification_options=[
                JustificationOption(
                    option=item["option"],
                    required_image=bool(item.get("required_image", False)),
                    required_text=bool(item.get("required_text", False)),
                )
                for item in data.get("justification_options") or []
            ],
        )

    def to_entity(self) -> Template:
        return Template(
            id=self.id,
            name=self.name,
            description=self.description,
            system=self.system,
            is_active=self.is_active,
            created_by=self.created_by,
            created_at=self.created_at,
            updated_at=self.updated_at,
            sections=self.sections,
            justification_options=self.justification_options,
        )
