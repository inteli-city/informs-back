from typing import Annotated, Any, Literal

from pydantic import Discriminator, Field, Tag

from src.shared.helpers.contracts.base import RequestContractModel, ResponseContractModel


class TextInformationFieldInputSchema(RequestContractModel):
    key: str | None = None
    information_field_type: Literal["TEXT_INFORMATION_FIELD"]
    value: str


class MapInformationFieldInputSchema(RequestContractModel):
    key: str | None = None
    information_field_type: Literal["MAP_INFORMATION_FIELD"]
    latitude: float
    longitude: float


class FileUploadInformationFieldInputSchema(RequestContractModel):
    """Arquivo enviado ao Informs: a resposta traz a URL pré-assinada para o PUT."""
    key: str | None = None
    information_field_type: Literal["FILE_INFORMATION_FIELD"]
    source: Literal["UPLOAD"] = "UPLOAD"
    filename: str
    mimetype: str
    file_type: Literal["IMAGE", "DOCUMENT"] | None = None


class FileUrlInformationFieldInputSchema(RequestContractModel):
    """Arquivo que quem cria já hospeda: guardamos só o endereço, sem upload."""
    key: str | None = None
    information_field_type: Literal["FILE_INFORMATION_FIELD"]
    source: Literal["URL"]
    url: str = Field(min_length=1)
    mimetype: str = Field(min_length=1)
    file_type: Literal["IMAGE", "DOCUMENT"] | None = None


def _file_source(value: Any) -> str:
    # Sem `source` é upload: o formato de antes da ADR-0026 continua valendo.
    source = value.get("source") if isinstance(value, dict) else getattr(value, "source", None)
    return source or "UPLOAD"


# União discriminada por `source` (ADR-0026). Um tipo, duas formas de entregar
# o arquivo; o link de site é outro tipo (`URL_INFORMATION_FIELD`).
FileInformationFieldInputSchema = Annotated[
    Annotated[FileUploadInformationFieldInputSchema, Tag("UPLOAD")]
    | Annotated[FileUrlInformationFieldInputSchema, Tag("URL")],
    Discriminator(_file_source),
]


class UrlInformationFieldInputSchema(RequestContractModel):
    key: str | None = None
    information_field_type: Literal["URL_INFORMATION_FIELD"]
    # Quando um campo URL é enviado, url/mimetype são obrigatórios e não-vazios:
    # min_length=1 alinha o contrato à validação do domínio (UrlInformationField)
    # e documenta a restrição no OpenAPI, falhando já na camada de contrato em vez
    # de só depois como EntityError.
    url: str = Field(min_length=1)
    mimetype: str = Field(min_length=1)


InformationFieldInputSchema = Annotated[
    TextInformationFieldInputSchema
    | MapInformationFieldInputSchema
    | FileInformationFieldInputSchema
    | UrlInformationFieldInputSchema,
    Field(discriminator="information_field_type"),
]


class TextInformationFieldSchema(ResponseContractModel):
    key: str | None = None
    information_field_type: Literal["TEXT_INFORMATION_FIELD"]
    value: str


class MapInformationFieldSchema(ResponseContractModel):
    key: str | None = None
    information_field_type: Literal["MAP_INFORMATION_FIELD"]
    latitude: float
    longitude: float


class FileInformationFieldSchema(ResponseContractModel):
    key: str | None = None
    information_field_type: Literal["FILE_INFORMATION_FIELD"]
    # UPLOAD: URL do nosso armazenamento. URL: endereço hospedado por quem criou.
    file_path: str
    file_type: Literal["IMAGE", "DOCUMENT"] | None = None
    source: Literal["UPLOAD", "URL"] = "UPLOAD"


class UrlInformationFieldSchema(ResponseContractModel):
    key: str | None = None
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
