from pydantic import ConfigDict

from src.shared.helpers.contracts.base import RequestContractModel


class GenericFieldSchema(RequestContractModel):
    model_config = ConfigDict(extra="allow")

    field_type: str
    label: str
    required: bool
    key: str
    order: int
    help_text: str | None = None
