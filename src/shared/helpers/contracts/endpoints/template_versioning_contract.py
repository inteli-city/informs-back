from typing import Literal

from pydantic import Field

from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel

FormStatusLiteral = Literal["PENDING", "IN_PROGRESS", "COMPLETED", "SENT", "CANCELLED"]
PossessionLiteral = Literal["OPEN", "OWNED"]

# Teto de formulários por chamada de propagação: cada um é uma escrita
# condicional no Dynamo, e a Lambda tem 15 s. O app manda em lotes.
PROPAGATE_MAX_FORMS = 100


class TemplateFormSummarySchema(ResponseContractModel):
    id: str
    form_title: str
    system: str
    status: FormStatusLiteral
    possession: PossessionLiteral
    created_at: int
    template_version: int = Field(description="Versão do template em que o formulário está.")
    user_id: str | None = None
    street: str | None = None
    number: int | None = None
    city: str | None = None


class GetTemplateFormsResponseSchema(ResponseContractModel):
    template_id: str
    template_version: int = Field(description="Versão atual do template.")
    in_use: bool = Field(
        description=(
            "Algum formulário (de qualquer status) nasceu deste template. Em uso, "
            "seções e motivos só mudam como nova versão."
        )
    )
    forms: list[TemplateFormSummarySchema]
    limit: int | None = None
    last_evaluated_key: str | None = None


class PropagateTemplateRequestSchema(RequestContractModel):
    form_ids: list[str] = Field(
        min_length=1,
        max_length=PROPAGATE_MAX_FORMS,
        description=(
            f"Formulários que passam para a versão atual do template (até "
            f"{PROPAGATE_MAX_FORMS} por chamada). Só pendentes e em execução mudam."
        ),
    )


SkipReasonLiteral = Literal["not_found", "other_template", "closed", "already_current", "changed"]


class PropagateTemplateSkippedSchema(ResponseContractModel):
    form_id: str
    reason: SkipReasonLiteral = Field(
        description=(
            "not_found: não existe; other_template: é de outro template; closed: "
            "concluído ou cancelado; already_current: já está na versão atual; "
            "changed: mudou de estado durante a propagação."
        )
    )


class PropagateTemplateResponseSchema(ResponseContractModel):
    template_version: int
    updated: list[str]
    skipped: list[PropagateTemplateSkippedSchema]
