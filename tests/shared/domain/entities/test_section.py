import pytest
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.section import Section
from src.shared.helpers.errors.domain_errors import EntityError

text_field = TextField(label='label', required=True, key='key', order=1, regex='regex', max_length=10, value='value')
class Test_Section:

    def test_section(self):
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
        
