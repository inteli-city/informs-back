from src.shared.helpers.contracts.base import ResponseContractModel
from src.shared.helpers.contracts.schemas.template import TemplateSchema


class GetAllTemplatesResponseSchema(ResponseContractModel):
    templates: list[TemplateSchema]
    limit: int | None = None
    last_evaluated_key: str | None = None
    systems: list[str] | None = None
