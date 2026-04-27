from datetime import datetime, timezone
from typing import List, Optional

from src.shared.domain.entities.section import Section
from src.shared.domain.entities.template import Template
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, NoItemsFound


class UpdateTemplateUsecase:
    def __init__(self, template_repo: ITemplateRepository):
        self.template_repo = template_repo

    def _validate_sections(self, sections: Optional[List[Section]]) -> None:
        if sections is None:
            return
        if not isinstance(sections, list) or not sections:
            raise EntityError("Seções devem ser uma lista não vazia")
        if any(len(section.fields) == 0 for section in sections):
            raise EntityError("Todas as seções devem ter ao menos um campo")

    def __call__(
        self,
        template_id: str,
        requester_user_id: str,
        name: Optional[str] = None,
        system: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        sections: Optional[List[Section]] = None,
    ) -> Template:
        template = self.template_repo.get_template(template_id)
        if template is None:
            raise NoItemsFound("Template não encontrado")

        new_name = name if name is not None else template.name
        new_system = system if system is not None else template.system
        new_description = description if description is not None else template.description
        new_is_active = is_active if is_active is not None else template.is_active
        new_sections = sections if sections is not None else template.sections

        self._validate_sections(sections)
        
        now_ts = int(datetime.now(timezone.utc).timestamp() * 1000)
        updated_at = max(now_ts, template.updated_at + 1)
        updated_template = Template(
            id=template.id,
            name=new_name,
            system=new_system,
            description=new_description,
            is_active=new_is_active,
            created_by=template.created_by,
            sections=new_sections,
            created_at=template.created_at,
            updated_at=updated_at,
        )

        return self.template_repo.update_template(updated_template)
