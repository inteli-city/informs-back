import pytest
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.section import Section
from src.shared.helpers.errors.domain_errors import EntityError

text_field = TextField(label='label', required=True, key='key', order=1, regex='regex', max_length=10, value='value')
text_field_2 = TextField(label='label 2', required=True, key='key_2', order=2, regex='regex', max_length=10, value='value')
class TestSection:

    def test_section(self):
        Section(section_id=1, fields=[text_field, text_field_2])

    def test_section_duplicate_field_key(self):
        with pytest.raises(EntityError):
            Section(section_id=1, fields=[text_field, text_field])
    
    def test_section_id_not_int(self):
        with pytest.raises(EntityError):
            Section(section_id='99999', fields=[text_field])
    
    def test_section_fields_not_list(self):
        with pytest.raises(EntityError):
            Section(section_id=1, fields=text_field)
    
    def test_section_fields_is_empty(self):
        with pytest.raises(EntityError):
            Section(section_id=1, fields=[])
    
    def test_section_fields_not_field(self):
        with pytest.raises(EntityError):
            Section(section_id=1, fields=['field'])

    def test_section_is_duplicable_default_false(self):
        s = Section(section_id=1, fields=[text_field])
        assert s.is_duplicable is False

    def test_section_is_duplicable_true(self):
        s = Section(section_id=1, fields=[text_field], is_duplicable=True)
        assert s.is_duplicable is True

    def test_section_is_duplicable_not_bool(self):
        with pytest.raises(EntityError):
            Section(section_id=1, fields=[text_field], is_duplicable='yes')

    def test_section_instance_default_zero(self):
        s = Section(section_id=1, fields=[text_field])
        assert s.section_instance == 0

    def test_section_instance_positive(self):
        s = Section(section_id=1, fields=[text_field], section_instance=2)
        assert s.section_instance == 2

    def test_section_instance_negative(self):
        with pytest.raises(EntityError):
            Section(section_id=1, fields=[text_field], section_instance=-1)

    def test_section_instance_not_int(self):
        with pytest.raises(EntityError):
            Section(section_id=1, fields=[text_field], section_instance='1')

