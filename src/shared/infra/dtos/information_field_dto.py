from decimal import Decimal
from src.shared.domain.entities.information_field import FileInformationField, InformationField, MapInformationField, TextInformationField, UrlInformationField
from src.shared.domain.enums.file_type_enum import FileType
from src.shared.domain.enums.information_field_type_enum import InformationFieldType
from src.shared.helpers.errors.controller_errors import MissingParameters
from src.shared.helpers.errors.domain_errors import EntityError


class InformationFieldDTO():
    information_field: InformationField

    def __init__(self, information_field: InformationField):
        self.information_field = information_field

    @staticmethod
    def from_request(information_field_dict: dict) -> "InformationFieldDTO":
        information_field_type = InformationFieldDTO._resolve_type(information_field_dict)
        builders = {
            InformationFieldType.TEXT_INFORMATION_FIELD: InformationFieldDTO._text_from_request,
            InformationFieldType.MAP_INFORMATION_FIELD: InformationFieldDTO._map_from_request,
            InformationFieldType.FILE_INFORMATION_FIELD: InformationFieldDTO._file_from_request,
            InformationFieldType.URL_INFORMATION_FIELD: InformationFieldDTO._url_from_request,
        }
        return InformationFieldDTO(builders[information_field_type](information_field_dict))

    @staticmethod
    def _resolve_type(information_field_dict: dict) -> InformationFieldType:
        information_field_type_raw = information_field_dict.get('information_field_type')
        if information_field_type_raw is None:
            raise MissingParameters('information_field_type')
        if information_field_type_raw not in [field.value for field in InformationFieldType]:
            raise EntityError('information_field_type')
        return InformationFieldType[information_field_type_raw]

    @staticmethod
    def _text_from_request(information_field_dict: dict) -> TextInformationField:
        if information_field_dict.get('value') is None:
            raise MissingParameters('value')
        return TextInformationField(value=information_field_dict.get('value'))

    @staticmethod
    def _map_from_request(information_field_dict: dict) -> MapInformationField:
        if information_field_dict.get('latitude') is None:
            raise MissingParameters('latitude')
        if information_field_dict.get('longitude') is None:
            raise MissingParameters('longitude')
        return MapInformationField(latitude=information_field_dict.get('latitude'), longitude=information_field_dict.get('longitude'))

    @staticmethod
    def _file_from_request(information_field_dict: dict) -> FileInformationField:
        if information_field_dict.get('file_path') is None:
            raise MissingParameters('file_path')
        file_type = InformationFieldDTO._parse_file_type(information_field_dict.get('file_type'))
        return FileInformationField(file_path=information_field_dict.get('file_path'), file_type=file_type)

    @staticmethod
    def _url_from_request(information_field_dict: dict) -> UrlInformationField:
        if information_field_dict.get('url') is None:
            raise MissingParameters('url')
        if information_field_dict.get('mimetype') is None:
            raise MissingParameters('mimetype')
        return UrlInformationField(url=information_field_dict.get('url'), mimetype=information_field_dict.get('mimetype'))

    @staticmethod
    def _parse_file_type(file_type_raw) -> "FileType | None":
        if file_type_raw is None:
            return None
        if not isinstance(file_type_raw, str) or file_type_raw not in [ft.value for ft in FileType]:
            raise EntityError('file_type')
        return FileType(file_type_raw)
    
    @staticmethod
    def from_entity(information_field: InformationField) -> "InformationFieldDTO":
        return InformationFieldDTO(information_field)

    def to_dynamo(self) -> dict:
        if isinstance(self.information_field, TextInformationField):
            return {
                "information_field_type": self.information_field.information_field_type.value,
                "value": self.information_field.value
            }
        if isinstance(self.information_field, MapInformationField):
            return {
                "information_field_type": self.information_field.information_field_type.value,
                "latitude": Decimal(str(self.information_field.latitude)),
                "longitude": Decimal(str(self.information_field.longitude))
            }
        if isinstance(self.information_field, FileInformationField):
            payload = {
                "information_field_type": self.information_field.information_field_type.value,
                "file_path": self.information_field.file_path
            }
            if self.information_field.file_type is not None:
                payload["file_type"] = self.information_field.file_type.value
            return payload
        if isinstance(self.information_field, UrlInformationField):
            return {
                "information_field_type": self.information_field.information_field_type.value,
                "url": self.information_field.url,
                "mimetype": self.information_field.mimetype,
            }
        raise EntityError('information_field_type')
    
    @staticmethod
    def from_dynamo(information_field_dict: dict) -> "InformationFieldDTO":
        if information_field_dict.get('information_field_type') is None:
            raise MissingParameters('information_field_type')
        
        information_field_type_raw = information_field_dict.get('information_field_type')
        if information_field_type_raw not in [field.value for field in InformationFieldType]:
            raise EntityError('information_field_type')

        information_field_type = InformationFieldType[information_field_type_raw]

        if information_field_type == InformationFieldType.TEXT_INFORMATION_FIELD:
            return InformationFieldDTO(TextInformationField(value=information_field_dict.get('value')))
        if information_field_type == InformationFieldType.MAP_INFORMATION_FIELD:
            return InformationFieldDTO(MapInformationField(latitude=float(information_field_dict.get('latitude')), longitude=float(information_field_dict.get('longitude'))))
        if information_field_type == InformationFieldType.FILE_INFORMATION_FIELD:
            file_type_raw = information_field_dict.get("file_type")
            file_type = FileType(file_type_raw) if file_type_raw in [ft.value for ft in FileType] else None
            return InformationFieldDTO(FileInformationField(file_path=information_field_dict.get('file_path'), file_type=file_type))
        if information_field_type == InformationFieldType.URL_INFORMATION_FIELD:
            return InformationFieldDTO(UrlInformationField(url=information_field_dict.get('url'), mimetype=information_field_dict.get('mimetype')))
        raise EntityError('information_field_type')

    def to_entity(self) -> InformationField:
        return self.information_field
    
