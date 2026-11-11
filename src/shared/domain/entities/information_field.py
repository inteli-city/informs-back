import abc

from typing import Optional

from src.shared.domain.enums.file_type_enum import FileType
from src.shared.domain.enums.information_field_type_enum import InformationFieldType
from src.shared.helpers.errors.domain_errors import EntityError


class InformationField(abc.ABC):
    information_field_type: InformationFieldType
    # Liga o valor à exigência do template (`TemplateInformationField.key`).
    # Campo sem chave é o formato anterior e segue válido.
    key: Optional[str]

    @abc.abstractmethod
    def __init__(self, information_field_type: InformationFieldType, key: Optional[str] = None):
        if not isinstance(information_field_type, InformationFieldType):
            raise EntityError('Tipo de campo informativo inválido')
        if key is not None and (not isinstance(key, str) or not key.strip()):
            raise EntityError('Chave do campo informativo deve ser uma string não vazia')
        self.information_field_type = information_field_type
        self.key = key


class TextInformationField(InformationField):
    value: str

    def __init__(self, value: str, key: Optional[str] = None):
        super().__init__(information_field_type=InformationFieldType.TEXT_INFORMATION_FIELD, key=key)
        if not isinstance(value, str):
            raise EntityError('Valor do campo informativo deve ser uma string')
        self.value = value


class MapInformationField(InformationField):
    latitude: float
    longitude: float

    def __init__(self, latitude: float, longitude: float, key: Optional[str] = None):
        super().__init__(information_field_type=InformationFieldType.MAP_INFORMATION_FIELD, key=key)
        if not isinstance(latitude, (float, int)):
            raise EntityError('Latitude deve ser um número')
        self.latitude = float(latitude)

        if not isinstance(longitude, (float, int)):
            raise EntityError('Longitude deve ser um número')
        self.longitude = float(longitude)


class FileInformationField(InformationField):
    file_path: str
    file_type: Optional[FileType]

    def __init__(self, file_path: str, file_type: Optional[FileType] = None, key: Optional[str] = None):
        super().__init__(information_field_type=InformationFieldType.FILE_INFORMATION_FIELD, key=key)
        if not isinstance(file_path, str):
            raise EntityError('Caminho do arquivo deve ser uma string')
        if file_type is not None and not isinstance(file_type, FileType):
            raise EntityError('Tipo de arquivo inválido')
        self.file_path = file_path
        self.file_type = file_type


class UrlInformationField(InformationField):
    """Aponta para um arquivo/foto já existente em algum lugar (uma URL).

    Diferente de FileInformationField, não gera upload/presigned URL: a URL já
    existe. O front renderiza o conteúdo de acordo com o `mimetype`.
    """
    url: str
    mimetype: str

    def __init__(self, url: str, mimetype: str, key: Optional[str] = None):
        super().__init__(information_field_type=InformationFieldType.URL_INFORMATION_FIELD, key=key)
        if not isinstance(url, str) or not url:
            raise EntityError('URL do campo informativo deve ser uma string não vazia')
        if not isinstance(mimetype, str) or not mimetype:
            raise EntityError('mimetype do campo informativo deve ser uma string não vazia')
        self.url = url
        self.mimetype = mimetype
