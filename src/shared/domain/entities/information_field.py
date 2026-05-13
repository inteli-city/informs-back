import abc

from typing import Optional

from src.shared.domain.enums.file_type_enum import FileType
from src.shared.domain.enums.information_field_type_enum import InformationFieldType
from src.shared.helpers.errors.domain_errors import EntityError


class InformationField(abc.ABC):
    information_field_type: InformationFieldType

    @abc.abstractmethod
    def __init__(self, information_field_type: InformationFieldType):
        if not isinstance(information_field_type, InformationFieldType):
            raise EntityError('Tipo de campo informativo inválido')
        self.information_field_type = information_field_type


class TextInformationField(InformationField):
    value: str

    def __init__(self, value: str):
        super().__init__(information_field_type=InformationFieldType.TEXT_INFORMATION_FIELD)
        if not isinstance(value, str):
            raise EntityError('Valor do campo informativo deve ser uma string')
        self.value = value


class MapInformationField(InformationField):
    latitude: float
    longitude: float

    def __init__(self, latitude: float, longitude: float):
        super().__init__(information_field_type=InformationFieldType.MAP_INFORMATION_FIELD)
        if not isinstance(latitude, (float, int)):
            raise EntityError('Latitude deve ser um número')
        self.latitude = float(latitude)

        if not isinstance(longitude, (float, int)):
            raise EntityError('Longitude deve ser um número')
        self.longitude = float(longitude)


class FileInformationField(InformationField):
    file_path: str
    file_type: Optional[FileType]

    def __init__(self, file_path: str, file_type: Optional[FileType] = None):
        super().__init__(information_field_type=InformationFieldType.FILE_INFORMATION_FIELD)
        if not isinstance(file_path, str):
            raise EntityError('Caminho do arquivo deve ser uma string')
        if file_type is not None and not isinstance(file_type, FileType):
            raise EntityError('Tipo de arquivo inválido')
        self.file_path = file_path
        self.file_type = file_type
