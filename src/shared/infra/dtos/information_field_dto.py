from decimal import Decimal
from src.shared.domain.entities.information_field import ImageInformationField, InformationField, MapInformationField, TextInformationField
from src.shared.domain.enums.information_field_type_enum import INFORMATION_FIELD_TYPE
from src.shared.helpers.errors.controller_errors import MissingParameters
from src.shared.helpers.errors.domain_errors import EntityError


class InformationFieldDTO():
    information_field: InformationField

    def __init__(self, information_field: InformationField):
        self.information_field = information_field

    def from_request(information_field_dict: dict) -> "InformationFieldDTO":
        if information_field_dict.get('information_field_type') is None:
            raise MissingParameters('information_field_type')
        if information_field_dict.get('information_field_type') not in [field.value for field in INFORMATION_FIELD_TYPE]:
            raise EntityError('information_field_type')

        information_field_type = INFORMATION_FIELD_TYPE[information_field_dict.get('information_field_type')]

        if information_field_type == INFORMATION_FIELD_TYPE.TEXT_INFORMATION_FIELD:
            if information_field_dict.get('value') is None:
                raise MissingParameters('value')
            return InformationFieldDTO(TextInformationField(value=information_field_dict.get('value')))

        if information_field_type == INFORMATION_FIELD_TYPE.MAP_INFORMATION_FIELD:
            if information_field_dict.get('latitude') is None:
                raise MissingParameters('latitude')
            if information_field_dict.get('longitude') is None:
                raise MissingParameters('longitude')
            return InformationFieldDTO(MapInformationField(latitude=information_field_dict.get('latitude'), longitude=information_field_dict.get('longitude')))

        if information_field_type == INFORMATION_FIELD_TYPE.IMAGE_INFORMATION_FIELD:
            if information_field_dict.get('file_path') is None:
                raise MissingParameters('file_path')
            return InformationFieldDTO(ImageInformationField(file_path=information_field_dict.get('file_path')))
        
        raise EntityError('information_field_type')
    
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
        if isinstance(self.information_field, ImageInformationField):
            return {
                "information_field_type": self.information_field.information_field_type.value,
                "file_path": self.information_field.file_path
            }
        raise EntityError('information_field_type')
    
    @staticmethod
    def from_dynamo(information_field_dict: dict) -> "InformationFieldDTO":
        if information_field_dict.get('information_field_type') is None:
            raise MissingParameters('information_field_type')
        
        if information_field_dict.get('information_field_type') not in [field.value for field in INFORMATION_FIELD_TYPE]:
            raise EntityError('information_field_type')

        information_field_type = INFORMATION_FIELD_TYPE[information_field_dict.get('information_field_type')]

        if information_field_type == INFORMATION_FIELD_TYPE.TEXT_INFORMATION_FIELD:
            return InformationFieldDTO(TextInformationField(value=information_field_dict.get('value')))
        if information_field_type == INFORMATION_FIELD_TYPE.MAP_INFORMATION_FIELD:
            return InformationFieldDTO(MapInformationField(latitude=float(information_field_dict.get('latitude')), longitude=float(information_field_dict.get('longitude'))))
        if information_field_type == INFORMATION_FIELD_TYPE.IMAGE_INFORMATION_FIELD:
            return InformationFieldDTO(ImageInformationField(file_path=information_field_dict.get('file_path')))
        raise EntityError('information_field_type')
    
    def to_entity(self) -> InformationField:
        return self.information_field
    
