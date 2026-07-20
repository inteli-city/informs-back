import pytest

from src.shared.domain.entities.information_field import FileInformationField, InformationField, MapInformationField, TextInformationField, UrlInformationField
from src.shared.domain.enums.information_field_type_enum import InformationFieldType
from src.shared.helpers.errors.domain_errors import EntityError


class Test_InformationField:

    def test_information_field_cannot_be_instanciated(self):
        with pytest.raises(TypeError):
            InformationField(information_field_type=InformationFieldType.MAP_INFORMATION_FIELD)
    
    # TextInformationField

    def test_text_information_field(self):
        text_information_field = TextInformationField(value='value')
        assert text_information_field.information_field_type == InformationFieldType.TEXT_INFORMATION_FIELD
        assert text_information_field.value == 'value'

    def test_text_information_field_value_is_none(self):
        with pytest.raises(EntityError):
            TextInformationField(value=None)
    
    def test_text_information_field_value_is_not_str(self):
        with pytest.raises(EntityError):
            TextInformationField(value=1)
    
    # MapInformationField

    def test_map_information_field(self):
        map_information_field = MapInformationField(latitude=1.0, longitude=1.0)
        assert map_information_field.information_field_type == InformationFieldType.MAP_INFORMATION_FIELD
        assert map_information_field.latitude == 1.0
        assert map_information_field.longitude == 1.0
    
    def test_map_information_field_latitude_is_none(self):
        with pytest.raises(EntityError):
            MapInformationField(latitude=None, longitude=1.0)
    
    def test_map_information_field_latitude_is_not_float(self):
        with pytest.raises(EntityError):
            MapInformationField(latitude='1', longitude=1.0)
    
    def test_map_information_field_longitude_is_none(self):
        with pytest.raises(EntityError):
            MapInformationField(latitude=1.0, longitude=None)
    
    def test_map_information_field_longitude_is_not_float(self):
        with pytest.raises(EntityError):
            MapInformationField(latitude=1.0, longitude='1')
    
    # FileInformationField

    def test_file_information_field(self):
        file_information_field = FileInformationField(file_path='file_path')
        assert file_information_field.information_field_type == InformationFieldType.FILE_INFORMATION_FIELD
    
    def test_file_information_field_file_path_is_none(self):
        with pytest.raises(EntityError):
            FileInformationField(file_path=None)
    
    def test_file_information_field_file_path_is_not_str(self):
        with pytest.raises(EntityError):
            FileInformationField(file_path=1)

    # UrlInformationField

    def test_url_information_field(self):
        url_information_field = UrlInformationField(url='https://example.com/photo.jpg', mimetype='image/jpeg')
        assert url_information_field.information_field_type == InformationFieldType.URL_INFORMATION_FIELD
        assert url_information_field.url == 'https://example.com/photo.jpg'
        assert url_information_field.mimetype == 'image/jpeg'

    def test_url_information_field_url_is_none(self):
        with pytest.raises(EntityError):
            UrlInformationField(url=None, mimetype='image/jpeg')

    def test_url_information_field_url_is_empty(self):
        with pytest.raises(EntityError):
            UrlInformationField(url='', mimetype='image/jpeg')

    def test_url_information_field_url_is_not_str(self):
        with pytest.raises(EntityError):
            UrlInformationField(url=1, mimetype='image/jpeg')

    def test_url_information_field_mimetype_is_none(self):
        with pytest.raises(EntityError):
            UrlInformationField(url='https://example.com/photo.jpg', mimetype=None)

    def test_url_information_field_mimetype_is_empty(self):
        with pytest.raises(EntityError):
            UrlInformationField(url='https://example.com/photo.jpg', mimetype='')
