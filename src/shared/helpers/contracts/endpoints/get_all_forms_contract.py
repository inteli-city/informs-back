from pydantic import BaseModel

from src.shared.helpers.contracts.schemas.form import FormResponseSchema


class GetAllFormsResponseSchema(BaseModel):
    forms: list[FormResponseSchema]
    limit: int | None = None
    last_evaluated_key: str | None = None
