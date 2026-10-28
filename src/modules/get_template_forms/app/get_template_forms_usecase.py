from dataclasses import dataclass
from typing import List, Optional

from src.shared.domain.entities.template import Template
from src.shared.domain.entities.template_form_summary import TemplateFormSummary
from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, InvalidPaginationToken, NoItemsFound
from src.shared.helpers.functions.pagination_token import try_decode_pagination_token
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


@dataclass(frozen=True)
class TemplateFormsPage:
    template: Template
    in_use: bool
    forms: List[TemplateFormSummary]
    last_evaluated_key: Optional[str]


class GetTemplateFormsUsecase:
    """
    Formulários de um template, para o admin decidir quais passam para a versão
    nova. Quem pode editar o template (`templates.manage` no sistema dele) pode
    ver esta lista — inclusive OS do pool e de outras pessoas.
    """

    def __init__(
        self,
        template_repo: ITemplateRepository,
        form_repo: IFormRepository,
        access_control: Optional[AccessControl] = None,
    ):
        self.template_repo = template_repo
        self.form_repo = form_repo
        self.access_control = access_control

    def __call__(
        self,
        template_id: str,
        requester: UserGatewayDTO,
        only_open: bool = True,
        limit: Optional[int] = None,
        exclusive_start_key: Optional[str] = None,
    ) -> TemplateFormsPage:
        template = self.template_repo.get_template(template_id)
        if template is None:
            raise NoItemsFound("Template não encontrado")
        if template.system not in requester.systems:
            raise ForbiddenAction("Usuário não tem permissão para acessar este template")
        if self.access_control is not None and not self.access_control.can(
            requester.user_id, template.system, Action.TEMPLATES_MANAGE
        ):
            raise ForbiddenAction(f"Usuário não pode alterar os templates do sistema {template.system}")

        start_key = None
        if exclusive_start_key is not None:
            start_key = try_decode_pagination_token(exclusive_start_key)
            if start_key is None:
                raise InvalidPaginationToken()

        forms, next_key = self.form_repo.get_forms_by_template(
            template_id=template.id,
            only_open=only_open,
            limit=limit,
            exclusive_start_key=start_key,
        )
        return TemplateFormsPage(
            template=template,
            # Uma página com formulário já prova o uso; vazia, pergunta ao índice
            # (os abertos podem não existir e o template ainda estar em uso).
            in_use=bool(forms) or self.form_repo.has_forms_with_template(template.id),
            forms=forms,
            last_evaluated_key=next_key,
        )
