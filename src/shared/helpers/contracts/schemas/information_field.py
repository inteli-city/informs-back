from typing import Annotated, Literal

from pydantic import Field

from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel


class TextInformationFieldInputSchema(RequestContractModel):
    information_field_type: Literal["TEXT_INFORMATION_FIELD"]
    value: str


class MapInformationFieldInputSchema(RequestContractModel):
    information_field_type: Literal["MAP_INFORMATION_FIELD"]
    latitude: float
    longitude: float


class FileInformationFieldInputSchema(RequestContractModel):
    information_field_type: Literal["FILE_INFORMATION_FIELD"]
    filename: str
    mimetype: str
    file_type: Literal["IMAGE", "DOCUMENT"] | None = None


InformationFieldInputSchema = Annotated[
    TextInformationFieldInputSchema | MapInformationFieldInputSchema | FileInformationFieldInputSchema,
    Field(discriminator="information_field_type"),
]


class TextInformationFieldSchema(ResponseContractModel):
    information_field_type: Literal["TEXT_INFORMATION_FIELD"]
    value: str


class MapInformationFieldSchema(ResponseContractModel):
    information_field_type: Literal["MAP_INFORMATION_FIELD"]
    latitude: float
    longitude: float


class FileInformationFieldSchema(ResponseContractModel):
    information_field_type: Literal["FILE_INFORMATION_FIELD"]
    file_path: str
    file_type: Literal["IMAGE", "DOCUMENT"] | None = None


InformationFieldSchema = Annotated[
    TextInformationFieldSchema | MapInformationFieldSchema | FileInformationFieldSchema,
    Field(discriminator="information_field_type"),
]
