import pytest
from src.shared.domain.entities.justification import Justification, JustificationOption
from src.shared.helpers.errors.domain_errors import EntityError


class TestJustification:

    option = JustificationOption(option='option', required_image=True, required_text=True)
    
    def test_justification_option(self):
        option = JustificationOption(option='option', required_image=True, required_text=True)

        assert option.option == 'option'
        assert option.required_image == True
        assert option.required_text == True
    
    def test_justification_option_is_not_str(self):
        with pytest.raises(EntityError):
            JustificationOption(option=1, required_image=True, required_text=True)
    
    def test_justification_option_required_image_is_not_bool(self):
        with pytest.raises(EntityError):
            JustificationOption(option='option', required_image='True', required_text=True)
    
    def test_justification_option_required_text_is_not_bool(self):
        with pytest.raises(EntityError):
            JustificationOption(option='option', required_image=True, required_text='True')
    
    def test_justification(self):
        justification = Justification(options=[self.option], selected_option='option', justification_text='text', justification_image='image')

        assert justification.options == [self.option]
        assert justification.selected_option == 'option'
        assert justification.justification_text == 'text'
        assert justification.justification_image == 'image'
    
    def test_justification_options_is_not_list(self):
        with pytest.raises(EntityError):
            Justification(options=self.option, selected_option='option', justification_text='text', justification_image='image')
    
    def test_justification_options_is_not_justification_option(self):
        with pytest.raises(EntityError):
            Justification(options=['option'], selected_option='option', justification_text='text', justification_image='image')
    
    def test_justification_selected_option_is_not_str(self):
        with pytest.raises(EntityError):
            Justification(options=[self.option], selected_option=1, justification_text='text', justification_image='image')
    
    def test_justification_text_is_not_str(self):
        with pytest.raises(EntityError):
            Justification(options=[self.option], selected_option='option', justification_text=1, justification_image='image')

    def test_justification_image_is_not_str(self):
        with pytest.raises(EntityError):
            Justification(options=[self.option], selected_option='option', justification_text='text', justification_image=1)
    
    def test_justification_selected_option_is_none(self):
        justification = Justification(options=[self.option], selected_option=None, justification_text='text', justification_image='image')

        assert justification.selected_option == None
    
    def test_justification_text_is_none(self):
        justification = Justification(options=[self.option], selected_option='option', justification_text=None, justification_image='image')

        assert justification.justification_text == None

    def test_justification_image_is_none(self):
        justification = Justification(options=[self.option], selected_option='option', justification_text='text', justification_image=None)

        assert justification.justification_image == None