from typing import Annotated

from pydantic import Field, StringConstraints

from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class SyncCallbackRequestSchema(RequestContractModel):
    form_ids: list[NonEmptyStr] = Field(min_length=1)
    execution_id: NonEmptyStr | None = None


class SyncCallbackSavedErrorFormSchema(ResponseContractModel):
    job_name: str
    system: str
    form_id: str
    source_updated_at: int | None = None
    last_failed_at: int


class SyncCallbackResponseSchema(ResponseContractModel):
    received_count: int
    saved_error_forms: list[SyncCallbackSavedErrorFormSchema]
    received_at: int
    execution_id: str | None = None
    message: str
