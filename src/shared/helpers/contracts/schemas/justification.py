from pydantic import ConfigDict

from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel


class JustificationOptionSchema(RequestContractModel):
    option: str
    required_image: bool = False
    required_text: bool = False


class JustificationSelectedSchema(ResponseContractModel):
    option: str
    text: str | None = None
    image_url: str | None = None


class JustificationSchema(ResponseContractModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    options: list[JustificationOptionSchema]
    selected: JustificationSelectedSchema | None = None
