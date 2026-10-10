from typing import List, Optional

from src.shared.domain.entities.justification import JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.template import Template
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms


def _ensure_can_manage_templates(access_control: Optional[AccessControl], user_id: str, systems) -> None:
    """Criar e editar template pede `templates.manage` no sistema (o ADMIN dele
    tem). Sem access_control (testes antigos, chamadas internas) não checa."""
    if access_control is None:
        return
    for system in systems:
        if not access_control.can(user_id, system, Action.TEMPLATES_MANAGE):
            raise ForbiddenAction(f"Usuário não pode alterar os templates do sistema {system}")


class UpdateTemplateUsecase:
    def __init__(self, template_repo: ITemplateRepository, access_control: Optional[AccessControl] = None):
        self.access_control = access_control
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
        clear_description: bool = False,
    ) -> Template:
        template = self.template_repo.get_template(template_id)
        if template is None:
            raise NoItemsFound("Template não encontrado")
        if requester_systems is not None:
            if template.system not in requester_systems:
                raise ForbiddenAction("Usuário não tem permissão para acessar este template")
            if system is not None and system not in requester_systems:
                raise ForbiddenAction("Usuário não tem permissão para acessar este sistema")

        _ensure_can_manage_templates(
            self.access_control, requester_user_id, {template.system, system or template.system},
        )
        self._validate_sections(sections)

        if name is not None:
            template.change_name(name)
        if system is not None:
            template.change_system(system)
        if description is not None:
            template.change_description(description)
        elif clear_description:
            template.change_description(None)
        if is_active is not None:
            template.change_is_active(is_active)
        if sections is not None:
            template.change_sections(sections)
        if justification_options is not None:
            template.change_justification_options(justification_options)

        now_ts = now_timestamp_ms()
        template.change_updated_at(max(now_ts, template.updated_at + 1))

        return self.template_repo.update_template(template)
