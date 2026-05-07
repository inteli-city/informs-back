import pytest
from src.shared.domain.entities.field import CheckBoxGroupField, CheckboxField, DateField, DropDownField, FileField, Field, NumberField, RadioGroupField, SwitchButtonField, TextField, TypeAheadField
from src.shared.domain.enums.fields_enum import FIELD_TYPE
from src.shared.domain.enums.file_type_enum import FILE_TYPE
from src.shared.helpers.errors.domain_errors import EntityError


class Test_Field:

    def test_field_cannot_be_instanciated(self):
        with pytest.raises(TypeError):
            Field(field_type=FIELD_TYPE.TEXT_FIELD, label='label', required=True, key='key', order=1)

    def test_field_label_is_none(self):
        with pytest.raises(EntityError):
            TextField(label=None, required=True, key='key', order=1, max_length=10, value='value')
    
    def test_field_label_is_not_str(self):
        with pytest.raises(EntityError):
            TextField(label=1, required=True, key='key', order=1, max_length=10, value='value')
    
    def test_field_required_is_none(self):
        with pytest.raises(EntityError):
            TextField(label='label', required=None, key='key', order=1, max_length=10, value='value')
    
    def test_field_required_is_not_bool(self):
        with pytest.raises(EntityError):
            TextField(label='label', required='True', key='key', order=1, max_length=10, value='value')

    def test_field_key_is_none(self):
        with pytest.raises(EntityError):
            TextField(label='label', required=True, key=None, order=1, max_length=10, value='value')
    
    def test_field_key_is_not_str(self):
        with pytest.raises(EntityError):
            TextField(label='label', required=True, key=1, order=1, max_length=10, value='value')

    def test_field_order_is_not_int(self):
        with pytest.raises(EntityError):
            TextField(label='label', required=True, key='key', order='1', max_length=10, value='value')
    
    def test_field_regex_is_not_str(self):
        with pytest.raises(EntityError):
            TextField(label='label', required=True, key='key', order=1, regex=1, max_length=10, value='value')

    # TextField

    def test_text_field(self):
        text_field = TextField(label='label', required=True, key='key', order=1, max_length=10, value='value', regex='regex')

        assert text_field.field_type == FIELD_TYPE.TEXT_FIELD
    
    def test_text_field_max_length_is_not_int(self):
        with pytest.raises(EntityError):
            TextField(label='label', required=True, key='key', order=1, max_length='10', value='value', regex='regex')
    
    def test_text_field_value_is_not_str(self):
        with pytest.raises(EntityError):
            TextField(label='label', required=True, key='key', order=1, max_length=10, value=1, regex='regex')
    
    # NumberField

    def test_number_field(self):
        number_field = NumberField(label='label', required=True, key='key', order=1, max_value=10, min_value=1, decimal=True, value=1.0)

        assert number_field.field_type == FIELD_TYPE.NUMBER_FIELD

    def test_number_field_max_value_is_not_int(self):
        with pytest.raises(EntityError):
            NumberField(label='label', required=True, key='key', order=1, max_value='10', min_value=1, decimal=True, value=1)
    
    def test_number_field_min_value_is_not_int(self):
        with pytest.raises(EntityError):
            NumberField(label='label', required=True, key='key', order=1, max_value=10, min_value='1', decimal=True, value=1)
    
    def test_number_field_value_is_not_float(self):
        with pytest.raises(EntityError):
            NumberField(label='label', required=True, key='key', order=1, max_value=10, min_value=1, decimal=True, value='1')
    

    # DropDownField

    def test_drop_down_field(self):
        dropdown_field = DropDownField(label='label', required=True, key='key', order=1, options=['option1', 'option2'], value='option1')

        assert dropdown_field.field_type == FIELD_TYPE.DROPDOWN_FIELD

    def test_drop_down_field_options_is_not_list(self):
        with pytest.raises(EntityError):
            DropDownField(label='label', required=True, key='key', order=1, options='option1', value='option1')
    
    def test_drop_down_field_value_is_not_str(self):
        with pytest.raises(EntityError):
            DropDownField(label='label', required=True, key='key', order=1, options=['option1', 'option2'], value=1)
    
    def test_drop_down_field_value_is_not_in_options(self):
        with pytest.raises(EntityError):
            DropDownField(label='label', required=True, key='key', order=1, options=['option1', 'option2'], value='option3')
    
    # TypeAheadField

    def test_type_ahead_field(self):
        typeahead_field = TypeAheadField(label='label', required=True, key='key', order=1, options=['option1'], max_length=1, value='option1')

        assert typeahead_field.field_type == FIELD_TYPE.TYPEAHEAD_FIELD
    
    def test_type_ahead_field_options_is_not_list(self):
        with pytest.raises(EntityError):
            TypeAheadField(label='label', required=True, key='key', order=1, options='option1', max_length=1, value='option1')
    
    def test_type_ahead_field_max_length_is_not_int(self):
        with pytest.raises(EntityError):
            TypeAheadField(label='label', required=True, key='key', order=1, options=['option1', 'option2'], max_length='1', value='option1')
    
    def test_type_ahead_field_value_is_not_str(self):
        with pytest.raises(EntityError):
            TypeAheadField(label='label', required=True, key='key', order=1, options=['option1', 'option2'], max_length=1, value=1)
    
    # RadioGroupField

    def test_radio_group_field(self):
        radio_group_field = RadioGroupField(label='label', required=True, key='key', order=1, options=['option1', 'option2'], value='option1')

        assert radio_group_field.field_type == FIELD_TYPE.RADIO_GROUP_FIELD
    
    def test_radio_group_field_options_is_not_list(self):
        with pytest.raises(EntityError):
            RadioGroupField(label='label', required=True, key='key', order=1, options='option1', value='option1')
    
    def test_radio_group_field_value_is_not_str(self):
        with pytest.raises(EntityError):
            RadioGroupField(label='label', required=True, key='key', order=1, options=['option1', 'option2'], value=1)
    
    def test_radio_group_field_value_is_not_in_options(self):
        with pytest.raises(EntityError):
            RadioGroupField(label='label', required=True, key='key', order=1, options=['option1', 'option2'], value='option3')
    
    # DateField

    def test_date_field(self):
        date_field = DateField(label='label', required=True, key='key', order=1, min_date=946407600000, max_date=946407600000, value=946407600000)

        assert date_field.field_type == FIELD_TYPE.DATE_FIELD

    def test_date_field_min_date_is_not_int(self):
        with pytest.raises(EntityError):
            DateField(label='label', required=True, key='key', order=1, min_date='946407600000', max_date=946407600000, value=946407600000)
    
    def test_date_field_max_date_is_not_int(self):
        with pytest.raises(EntityError):
            DateField(label='label', required=True, key='key', order=1, min_date=946407600000, max_date='946407600000', value=946407600000)
    
    def test_date_field_value_is_not_int(self):
        with pytest.raises(EntityError):
            DateField(label='label', required=True, key='key', order=1, min_date=946407600000, max_date=946407600000, value='946407600000')
    
    # CheckboxField

    def test_checkbox_field(self):
        checkbox_field = CheckboxField(label='label', required=True, key='key', order=1, value=True)

        assert checkbox_field.field_type == FIELD_TYPE.CHECKBOX_FIELD
    
    def test_checkbox_field_value_is_not_bool(self):
        with pytest.raises(EntityError):
            CheckboxField(label='label', required=True, key='key', order=1, value='True')

    # CheckboxGroupField

    def test_checkbox_group_field(self):
        checkbox_group_field = CheckBoxGroupField(label='label', required=True, key='key', order=1, options=['option1', 'option2'], check_limit=1, value=[True, False])

        assert checkbox_group_field.field_type == FIELD_TYPE.CHECKBOX_GROUP_FIELD

    def test_checkbox_group_field_options_is_not_list(self):
        with pytest.raises(EntityError):
            CheckBoxGroupField(label='label', required=True, key='key', order=1, options='option1', check_limit=1, value=[True, False])
    
    def test_checkbox_group_field_check_limit_is_not_int(self):
        with pytest.raises(EntityError):
            CheckBoxGroupField(label='label', required=True, key='key', order=1, options=['option1', 'option2'], check_limit='1', value=[True, False])
    
    def test_checkbox_group_field_check_limit_is_not_less_than_options_length(self):
        with pytest.raises(EntityError):
            CheckBoxGroupField(label='label', required=True, key='key', order=1, options=['option1', 'option2'], check_limit=3, value=[True, False])
    
    def test_checkbox_group_field_value_is_not_list(self):
        with pytest.raises(EntityError):
            CheckBoxGroupField(label='label', required=True, key='key', order=1, options=['option1', 'option2'], check_limit=1, value='option1')
    
    def test_checkbox_group_field_value_is_not_in_options(self):
        with pytest.raises(EntityError):
            CheckBoxGroupField(label='label', required=True, key='key', order=1, options=['option1', 'option2'], check_limit=1, value=[True, True, False])
    
    # SwitchButtonField

    def test_switch_button_field(self):
        switch_button_field = SwitchButtonField(label='label', required=True, key='key', order=1, value=True)
    
        assert switch_button_field.field_type == FIELD_TYPE.SWITCH_BUTTON_FIELD
    
    def test_switch_button_field_value_is_not_bool(self):
        with pytest.raises(EntityError):
            SwitchButtonField(label='label', required=True, key='key', order=1, value='True')
    
    # FileField

    def test_file_field(self):
        file_field = FileField(label='label', required=True, key='key', order=1, file_type=FILE_TYPE.IMAGE, min_quantity=1, max_quantity=3, value=['file1', 'file2', 'file3'])

        assert file_field.field_type == FIELD_TYPE.FILE_FIELD
    
    def test_file_field_file_type_is_not_str(self):
        with pytest.raises(EntityError):
            FileField(label='label', required=True, key='key', order=1, file_type=1, min_quantity=1, max_quantity=3, value=['file1'])
    
    def test_file_field_min_quantity_is_not_int(self):
        with pytest.raises(EntityError):
            FileField(label='label', required=True, key='key', order=1, file_type=FILE_TYPE.IMAGE, min_quantity='1', max_quantity=3, value=['file1'])
    
    def test_file_field_max_quantity_is_not_int(self):
        with pytest.raises(EntityError):
            FileField(label='label', required=True, key='key', order=1, file_type=FILE_TYPE.IMAGE, min_quantity=1, max_quantity='3', value=['file1'])
    
    def test_file_field_value_is_not_list(self):
        with pytest.raises(EntityError):
            FileField(label='label', required=True, key='key', order=1, file_type=FILE_TYPE.IMAGE, min_quantity=1, max_quantity=3, value=1)
    
    def test_file_field_value_is_not_str(self):
        with pytest.raises(EntityError):
            FileField(label='label', required=True, key='key', order=1, file_type=FILE_TYPE.IMAGE, min_quantity=1, max_quantity=3, value=[1])
    
    def test_file_field_value_is_not_min_quantity(self):
        with pytest.raises(EntityError):
            FileField(label='label', required=True, key='key', order=1, file_type=FILE_TYPE.IMAGE, min_quantity=2, max_quantity=3, value=['file1'])
    
    def test_file_field_value_is_not_max_quantity(self):
        with pytest.raises(EntityError):
            FileField(label='label', required=True, key='key', order=1, file_type=FILE_TYPE.IMAGE, min_quantity=1, max_quantity=2, value=['file1', 'file2', 'file3'])

    def test_text_field_with_value_validates_and_keeps_original(self):
        text_field = TextField(label='label', required=True, key='key', order=1, max_length=5, value='old')

        updated = text_field.with_value('new')

        assert text_field.value == 'old'
        assert updated.value == 'new'

        with pytest.raises(EntityError):
            text_field.with_value('too-long')

    def test_number_field_set_value_normalizes(self):
        number_field = NumberField(label='label', required=True, key='key', order=1, max_value=10, min_value=1, decimal=True)

        number_field.set_value('2')

        assert number_field.value == 2.0

        with pytest.raises(EntityError):
            number_field.set_value('invalid')

    def test_date_field_set_value_normalizes(self):
        date_field = DateField(label='label', required=True, key='key', order=1, min_date=10, max_date=20)

        date_field.set_value('15')

        assert date_field.value == 15

        with pytest.raises(EntityError):
            date_field.set_value(21)

    def test_checkbox_and_switch_set_value_normalize(self):
        checkbox_field = CheckboxField(label='label', required=True, key='checkbox', order=1)
        switch_field = SwitchButtonField(label='label', required=True, key='switch', order=1)

        checkbox_field.set_value(1)
        switch_field.set_value(0)

        assert checkbox_field.value is True
        assert switch_field.value is False

    def test_checkbox_group_set_value_accepts_dict(self):
        checkbox_group_field = CheckBoxGroupField(
            label='label',
            required=True,
            key='key',
            order=1,
            options=['option1', 'option2'],
            check_limit=1,
        )

        checkbox_group_field.set_value({'option1': True})

        assert checkbox_group_field.value == [True, False]

        with pytest.raises(EntityError):
            checkbox_group_field.set_value({'unknown': True})

        with pytest.raises(EntityError):
            checkbox_group_field.set_value({'option1': True, 'option2': True})

    def test_file_field_set_value_validates_quantities(self):
        file_field = FileField(
            label='label',
            required=True,
            key='key',
            order=1,
            file_type=FILE_TYPE.IMAGE,
            min_quantity=1,
            max_quantity=2,
        )

        file_field.set_value([{'filename': 'a.jpg'}])

        assert file_field.value == [{'filename': 'a.jpg'}]

        with pytest.raises(EntityError):
            file_field.set_value([])

        with pytest.raises(EntityError):
            file_field.set_value(['a.jpg', 'b.jpg', 'c.jpg'])
