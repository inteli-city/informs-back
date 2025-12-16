from typing import List, Optional

from src.shared.domain.entities.section import Section
from src.shared.domain.entities.template import Template
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository
from src.shared.helpers.errors.domain_errors import EntityError

class CreateTemplateUsecase:
    def __init__(self, template_repo: ITemplateRepository):
        self.template_repo = template_repo

    def __call__(
        self,
        creator_user_id: str,
        name: str,
        system: str,
        description: Optional[str],
        is_active: bool,
        sessions: List[Section],
    ) -> Template:
        if not sessions:
            raise EntityError("sessions")
        if any(len(section.fields) == 0 for section in sessions):
            raise EntityError("sessions")

        template = Template(
            name=name,
            system=system,
            description=description,
            is_active=is_active,
            created_by=creator_user_id,
            sections=sessions,
        )

        return self.template_repo.create_template(template)
