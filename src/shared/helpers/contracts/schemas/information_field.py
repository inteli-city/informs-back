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


class UrlInformationFieldInputSchema(RequestContractModel):
    information_field_type: Literal["URL_INFORMATION_FIELD"]
    url: str
    mimetype: str


InformationFieldInputSchema = Annotated[
    TextInformationFieldInputSchema
    | MapInformationFieldInputSchema
    | FileInformationFieldInputSchema
    | UrlInformationFieldInputSchema,
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


class UrlInformationFieldSchema(ResponseContractModel):
    information_field_type: Literal["URL_INFORMATION_FIELD"]
    url: str
    mimetype: str


InformationFieldSchema = Annotated[
    TextInformationFieldSchema
    | MapInformationFieldSchema
    | FileInformationFieldSchema
    | UrlInformationFieldSchema,
    Field(discriminator="information_field_type"),
]
