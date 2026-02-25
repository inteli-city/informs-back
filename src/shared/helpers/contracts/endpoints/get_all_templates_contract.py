from pydantic import BaseModel

from src.shared.helpers.contracts.schemas.template import TemplateSchema


class GetAllTemplatesResponseSchema(BaseModel):
    templates: list[TemplateSchema]
    limit: int | None = None
    last_evaluated_key: str | None = None
    systems: list[str] | None = None
