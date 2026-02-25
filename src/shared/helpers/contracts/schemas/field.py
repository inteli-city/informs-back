from pydantic import BaseModel, ConfigDict


class GenericFieldSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    field_type: str
    label: str
    required: bool
    key: str
    order: int
    help_text: str | None = None
