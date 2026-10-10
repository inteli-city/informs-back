from typing import List, Optional

from src.shared.domain.entities.justification import JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.template import Template
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms


def _ensure_can_manage_templates(access_control: Optional[AccessControl], user_id: str, systems) -> None:
    """Criar e editar template pede `templates.manage` no sistema (o ADMIN dele
    tem). Sem access_control (testes antigos, chamadas internas) não checa."""
    if access_control is None:
        return
    for system in systems:
        if not access_control.can(user_id, system, Action.TEMPLATES_MANAGE):
            raise ForbiddenAction(f"Usuário não pode alterar os templates do sistema {system}")


class CreateTemplateUsecase:
    def __init__(self, template_repo: ITemplateRepository, access_control: Optional[AccessControl] = None):
        self.template_repo = template_repo
        self.access_control = access_control

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
        _ensure_can_manage_templates(self.access_control, created_by, [system])
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
