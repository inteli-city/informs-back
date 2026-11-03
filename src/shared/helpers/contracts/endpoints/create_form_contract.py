from uuid import UUID

from pydantic import Field, model_validator

from src.shared.helpers.contracts.base import RequestContractModel
from src.shared.helpers.contracts.schemas.file_upload import FileUploadSchema
from src.shared.helpers.contracts.schemas.form import FormOriginLiteral, FormResponseSchema, FormSectionSchema
from src.shared.helpers.contracts.schemas.information_field import InformationFieldInputSchema
from src.shared.helpers.contracts.schemas.justification import JustificationOptionSchema
from src.shared.helpers.contracts.endpoints.system_access_contract import GroupIdStr


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
        return True
    except (ValueError, TypeError, AttributeError):
        return False


class CreateFormRequestSchema(RequestContractModel):
    form_title: str
    user_id: str | None = None
    system: str
    city: str
    street: str
    latitude: float
    longitude: float
    priority: int = Field(ge=0, le=3)
    justifications: list[JustificationOptionSchema]
    sections: list[FormSectionSchema] | None = None
    template: str | None = None
    observation: str | None = None
    expiration_date: int | None = None
    information_fields: list[InformationFieldInputSchema] | None = None
    external_id: str | None = None
    origin: FormOriginLiteral | None = None
    service_type: str | None = None
    occurred_at: int | None = None
    scheduled_start_at: int | None = None
    scheduled_end_at: int | None = None
    attributes: dict[str, list[str]] | None = None
    groups: list[GroupIdStr] | None = Field(
        default=None,
        description="Identificadores de grupos do sistema (GET /systems/{system}/groups). "
        "Sem user_id, só quem está num desses grupos vê e pega a OS no pool; "
        "com user_id, valem se a OS for devolvida ao pool. Grupo desconhecido = 400.",
    )

    @model_validator(mode="after")
    def validate_sections_when_template_absent(self) -> "CreateFormRequestSchema":
        if self.sections is None:
            if self.template is None or not _is_uuid(self.template):
                raise ValueError("sections is required when template is not a UUID")
        return self


class CreateFormResponseSchema(FormResponseSchema):
    files: list[FileUploadSchema] = Field(default_factory=list)
