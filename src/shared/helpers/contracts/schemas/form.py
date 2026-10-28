from typing import Literal

from pydantic import Field

from src.shared.helpers.contracts.base import NonNegativeStrictInt, RequestContractModel, ResponseContractModel
from .field import GenericFieldSchema
from .information_field import InformationFieldSchema
from .justification import JustificationSchema

FormStatusLiteral = Literal["PENDING", "IN_PROGRESS", "COMPLETED", "SENT", "CANCELLED"]
FormOriginLiteral = Literal["CITIZEN", "AI", "FIELD", "ORIGIN_SYSTEM"]
PossessionLiteral = Literal["OPEN", "OWNED"]
AssignmentSourceLiteral = Literal["ORIGIN_SYSTEM", "CLAIM", "MANAGER"]


class FormSectionSchema(RequestContractModel):
    section_id: int
    fields: list[GenericFieldSchema]
    is_duplicable: bool = False
    section_instance: NonNegativeStrictInt = Field(
        default=0,
        description=(
            "Somente leitura: preenchido nas respostas para identificar instâncias "
            "duplicadas (0 = seção original). Na criação do formulário deve ser 0 "
            "(default) — instâncias novas são criadas apenas na submissão."
        ),
    )


class FormResponseSchema(ResponseContractModel):
    id: str
    status: FormStatusLiteral
    form_title: str
    user_id: str | None = None
    template: str | None = None
    area: str | None = None
    system: str
    city: str
    street: str
    latitude: float
    longitude: float
    priority: int = Field(
        ge=0, le=3, description="0 = Baixa, 1 = Média, 2 = Alta, 3 = Emergência."
    )
    observation: str | None = None
    expiration_date: int | None = None
    justification: JustificationSchema
    sections: list[FormSectionSchema]
    in_progress_at: int | None = None
    cancelled_at: int | None = None
    completed_at: int | None = None
    created_by: str
    created_at: int
    updated_at: int
    information_fields: list[InformationFieldSchema] | None = None
    number: int | None = None
    external_id: str | None = None
    origin: FormOriginLiteral | None = Field(
        default=None,
        description="De onde partiu a demanda que virou a OS. Ausente para sistemas "
        "que não informam origem (ex.: Gaia).",
    )
    service_type: str | None = None
    occurred_at: int | None = None
    scheduled_start_at: int | None = None
    scheduled_end_at: int | None = None
    attributes: dict[str, list[str]] = Field(default_factory=dict)
    completed_by: str | None = None
    possession: PossessionLiteral = Field(
        description="OPEN = no pool, sem dono, visível a quem o escopo cobrir. "
        "OWNED = direcionada (criação) ou reivindicada (claim/assign)."
    )
    claimed_at: int | None = None
    released_at: int | None = None
    assignment_source: AssignmentSourceLiteral | None = Field(
        default=None,
        description="Como a OS ganhou responsável: ORIGIN_SYSTEM (direcionada na "
        "criação), CLAIM (reivindicada pelo próprio usuário) ou MANAGER (atribuída "
        "por um Gestor/Fiscal/Admin).",
    )
    template_version: int | None = Field(
        default=None,
        description="Versão do template de que as seções foram copiadas. Sem "
        "template (seções enviadas na criação), vem nula. Ao enviar o "
        "preenchimento, mande esta mesma versão em `template_version`.",
    )
