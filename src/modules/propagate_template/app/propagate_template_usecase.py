from copy import deepcopy
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from src.shared.domain.enums.action_enum import Action
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.domain.repositories.template_repository_interface import ITemplateRepository
from src.shared.domain.services.access_control import AccessControl
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.functions.datetime_utils import now_timestamp_ms
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


@dataclass
class PropagationResult:
    template_version: int
    updated: List[str] = field(default_factory=list)
    # (form_id, motivo) — ver `PropagateTemplateSkippedSchema`.
    skipped: List[Tuple[str, str]] = field(default_factory=list)


class PropagateTemplateUsecase:
    """
    Passa os formulários escolhidos para a versão atual do template: troca as
    seções e os motivos de cancelamento pelos da versão nova.

    Só formulário aberto (pendente ou em execução) muda — concluído e cancelado
    já foram salvos com os campos que tinham. Formulário aberto não tem resposta
    gravada no servidor (as respostas ficam no aparelho até o envio), então não
    há valor a migrar aqui; o app mantém as respostas dos campos que continuam
    existindo, e o envio feito contra a versão anterior é aceito (ver
    `SubmitFormUsecase`).

    Um formulário que não pode mudar não derruba o lote: entra em `skipped` com
    o motivo, e o resto segue.
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

    def __call__(self, template_id: str, requester: UserGatewayDTO, form_ids: List[str]) -> PropagationResult:
        template = self.template_repo.get_template(template_id)
        if template is None:
            raise NoItemsFound("Template não encontrado")
        if template.system not in requester.systems:
            raise ForbiddenAction("Usuário não tem permissão para acessar este template")
        if self.access_control is not None and not self.access_control.can(
            requester.user_id, template.system, Action.TEMPLATES_MANAGE
        ):
            raise ForbiddenAction(f"Usuário não pode alterar os templates do sistema {template.system}")

        result = PropagationResult(template_version=template.version)
        updated_at = now_timestamp_ms()

        for form_id in dict.fromkeys(form_ids):
            form = self.form_repo.get_form_by_id(user_id=requester.user_id, form_id=form_id)
            if form is None:
                result.skipped.append((form_id, "not_found"))
                continue
            if form.template != template.id:
                result.skipped.append((form_id, "other_template"))
                continue
            if not form.is_open_for_template_update():
                result.skipped.append((form_id, "closed"))
                continue
            if (form.template_version or 1) >= template.version:
                result.skipped.append((form_id, "already_current"))
                continue

            form.apply_template_version(
                sections=deepcopy(template.sections),
                # Sem motivos no template, o formulário fica com os que tinha.
                justification_options=deepcopy(template.justification_options),
                template_version=template.version,
                updated_at=max(updated_at, form.updated_at + 1),
            )
            if self.form_repo.apply_template_version(form, template.id) is None:
                result.skipped.append((form_id, "changed"))
                continue
            result.updated.append(form_id)

        return result
