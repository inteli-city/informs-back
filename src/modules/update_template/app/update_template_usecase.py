from typing import List, Optional

from src.shared.domain.entities.justification import JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.domain.entities.template import Template
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound, TemplateVersionRequired
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms
from src.shared.helpers.viewmodels.form_dict_builders import build_field_vars_dict, build_section_dict


def _ensure_can_manage_templates(access_control: Optional[AccessControl], user_id: str, systems) -> None:
    """Criar e editar template pede `templates.manage` no sistema (o ADMIN dele
    tem). Sem access_control (testes antigos, chamadas internas) não checa."""
    if access_control is None:
        return
    for system in systems:
        if not access_control.can(user_id, system, Action.TEMPLATES_MANAGE):
            raise ForbiddenAction(f"Usuário não pode alterar os templates do sistema {system}")


def _content_snapshot(sections: List[Section], justification_options: List[JustificationOption]):
    """O que um formulário copia do template, num formato comparável."""
    return (
        [build_section_dict(section, field_serializer=build_field_vars_dict) for section in sections],
        [(option.option, option.required_image, option.required_text) for option in justification_options],
    )


class UpdateTemplateUsecase:
    """
    Edita um template. Nome, descrição, sistema e ativo mudam sempre no lugar.
    Seções e motivos de cancelamento são copiados para cada formulário criado:
    enquanto nenhum formulário nasceu do template, mudam no lugar; depois disso,
    só como nova versão (`new_version`), para os formulários existentes não
    ficarem com um conteúdo que ninguém sabe de onde veio. Quais formulários
    abertos passam para a versão nova é outra decisão (`propagate_template`).
    """

    def __init__(
        self,
        template_repo: ITemplateRepository,
        access_control: Optional[AccessControl] = None,
        form_repo: Optional[IFormRepository] = None,
    ):
        self.access_control = access_control
        self.template_repo = template_repo
        self.form_repo = form_repo

    @staticmethod
    def _content_changes(
        template: Template,
        sections: Optional[List[Section]],
        justification_options: Optional[List[JustificationOption]],
    ) -> bool:
        """O pedido muda as seções ou os motivos? O app manda o template
        inteiro a cada salvar, então "veio no corpo" não basta."""
        if sections is None and justification_options is None:
            return False
        current = _content_snapshot(template.sections, template.justification_options)
        requested = _content_snapshot(
            sections if sections is not None else template.sections,
            justification_options if justification_options is not None else template.justification_options,
        )
        return current != requested

    def _is_in_use(self, template_id: str) -> bool:
        # Sem repositório de formulários (testes antigos), vale a regra de antes.
        return self.form_repo is not None and self.form_repo.has_forms_with_template(template_id)

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
        new_version: bool = False,
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
        content_changed = self._content_changes(template, sections, justification_options)
        if content_changed and not new_version and self._is_in_use(template.id):
            raise TemplateVersionRequired()

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
        if new_version and content_changed:
            template.bump_version()

        now_ts = now_timestamp_ms()
        template.change_updated_at(max(now_ts, template.updated_at + 1))

        return self.template_repo.update_template(template)
