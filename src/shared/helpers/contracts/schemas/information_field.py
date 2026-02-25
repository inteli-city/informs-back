from typing import Annotated, Literal

from pydantic import BaseModel, Field


class TextInformationFieldInputSchema(BaseModel):
    information_field_type: Literal["TEXT_INFORMATION_FIELD"]
    value: str


class MapInformationFieldInputSchema(BaseModel):
    information_field_type: Literal["MAP_INFORMATION_FIELD"]
    latitude: float
    longitude: float


class FileInformationFieldInputSchema(BaseModel):
    information_field_type: Literal["FILE_INFORMATION_FIELD"]
    filename: str
    mimetype: str
    file_type: Literal["IMAGE", "DOCUMENT"] | None = None


InformationFieldInputSchema = Annotated[
    TextInformationFieldInputSchema | MapInformationFieldInputSchema | FileInformationFieldInputSchema,
    Field(discriminator="information_field_type"),
]


class TextInformationFieldSchema(BaseModel):
    information_field_type: Literal["TEXT_INFORMATION_FIELD"]
    value: str


class MapInformationFieldSchema(BaseModel):
    information_field_type: Literal["MAP_INFORMATION_FIELD"]
    latitude: float
    longitude: float


class FileInformationFieldSchema(BaseModel):
    information_field_type: Literal["FILE_INFORMATION_FIELD"]
    file_path: str
    file_type: Literal["IMAGE", "DOCUMENT"] | None = None


InformationFieldSchema = Annotated[
    TextInformationFieldSchema | MapInformationFieldSchema | FileInformationFieldSchema,
    Field(discriminator="information_field_type"),
]
