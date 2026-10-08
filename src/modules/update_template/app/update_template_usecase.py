from typing import List, Optional

from src.shared.domain.entities.justification import JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.template import Template
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
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


class UpdateTemplateUsecase:
    def __init__(self, template_repo: ITemplateRepository, profile_repo=None):
        self.profile_repo = profile_repo
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
        requester_systems: Optional[List[str]] = None,
        name: Optional[str] = None,
        system: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        sections: Optional[List[Section]] = None,
        justification_options: Optional[List[JustificationOption]] = None,
    ) -> Template:
        template = self.template_repo.get_template(template_id)
        if template is None:
            raise NoItemsFound("Template não encontrado")
        if requester_systems is not None:
            if template.system not in requester_systems:
                raise ForbiddenAction("Usuário não tem permissão para acessar este template")
            if system is not None and system not in requester_systems:
                raise ForbiddenAction("Usuário não tem permissão para acessar este sistema")

        _ensure_system_admin(self.profile_repo, requester_user_id, {template.system, system or template.system})
        self._validate_sections(sections)

        if name is not None:
            template.change_name(name)
        if system is not None:
            template.change_system(system)
        if description is not None:
            template.change_description(description)
        if is_active is not None:
            template.change_is_active(is_active)
        if sections is not None:
            template.change_sections(sections)
        if justification_options is not None:
            template.change_justification_options(justification_options)

        now_ts = now_timestamp_ms()
        template.change_updated_at(max(now_ts, template.updated_at + 1))

        return self.template_repo.update_template(template)
