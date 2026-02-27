from src.shared.helpers.contracts.base import ResponseContractModel
from src.shared.helpers.contracts.schemas.form import FormResponseSchema


class GetAllFormsResponseSchema(ResponseContractModel):
    forms: list[FormResponseSchema]
    limit: int | None = None
    last_evaluated_key: str | None = None
