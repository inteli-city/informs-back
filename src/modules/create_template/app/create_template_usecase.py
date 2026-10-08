from typing import List, Optional

from src.shared.domain.entities.justification import JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.template import Template
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms



def _ensure_system_admin(profile_repo, user_id: str, systems) -> None:
    """Criar e editar template é do Admin: quem administra o sistema (ou a
    plataforma). Sem profile_repo (testes antigos, chamadas internas) não checa."""
    if profile_repo is None:
        return
    profile = profile_repo.get_by_user_id(user_id)
    for system in systems:
        if profile is None or not profile.can_admin_system(system):
            raise ForbiddenAction(f"Apenas quem administra o sistema {system} pode alterar seus templates")


class CreateTemplateUsecase:
    def __init__(self, template_repo: ITemplateRepository, profile_repo=None):
        self.template_repo = template_repo
        self.profile_repo = profile_repo

    def __call__(
        self,
        created_by: str,
        name: str,
        system: str,
        description: Optional[str],
        is_active: bool,
        sections: List[Section],
        requester_systems: Optional[List[str]] = None,
        justification_options: Optional[List[JustificationOption]] = None,
    ) -> Template:
        if requester_systems is not None and system not in requester_systems:
            raise ForbiddenAction("Usuário não tem permissão para acessar este sistema")
        _ensure_system_admin(self.profile_repo, created_by, [system])
        if not sections:
            raise EntityError("Template deve ter ao menos uma seção")
        if any(len(section.fields) == 0 for section in sections):
            raise EntityError("Todas as seções devem ter ao menos um campo")

        now_ts = now_timestamp_ms()

        template = Template(
            name=name,
            system=system,
            description=description,
            is_active=is_active,
            created_by=created_by,
            created_at=now_ts,
            updated_at=now_ts,
            sections=sections,
            justification_options=justification_options,
        )

        return self.template_repo.create_template(template)
