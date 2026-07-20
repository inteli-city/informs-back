import pytest
from src.shared.domain.entities.justification import Justification, JustificationOption
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.infra.dtos.justification_dto import JustificationDTO


class TestJustificationDTO:

    def test_justification_dto_from_request(self):
        justification_dict = {
            'options': [
                {
                    'option': 'option',
                    'required_image': True,
                    'required_text': True
                }
            ],
            'selected_option': 'selected_option',
            'justification_text': 'text',
            'justification_image': 'image'
        }

        justification = JustificationDTO.from_request(justification_dict)

        assert len(justification.options) == 1
        assert justification.options[0].option == 'option'
        assert justification.options[0].required_image == True
        assert justification.options[0].required_text == True

        assert justification.selected_option == 'selected_option'
        assert justification.justification_text == 'text'
        assert justification.justification_image == 'image'
    
    def test_justification_dto_from_request_with_none_values(self):
        justification_dict = {
            'options': [
                {
                    'option': 'option',
                    'required_image': True,
                    'required_text': True
                }
            ],
            'selected_option': None,
            'justification_text': None,
            'justification_image': None
        }

        justification = JustificationDTO.from_request(justification_dict)

        assert len(justification.options) == 1
        assert justification.options[0].option == 'option'
        assert justification.options[0].required_image == True
        assert justification.options[0].required_text == True

        assert justification.selected_option == None
        assert justification.justification_text == None
        assert justification.justification_image == None
    
    def test_justification_dto_from_request_with_no_options(self):
        justification_dict = {
            'selected_option': 'selected_option',
            'justification_text': 'text',
            'justification_image': 'image'
        }

        with pytest.raises(EntityError):
            JustificationDTO.from_request(justification_dict)
    
    def test_justification_dto_from_request_with_no_option(self):
        justification_dict = {
            'options': [
                {
                    'required_image': True,
                    'required_text': True
                }
            ],
            'selected_option': 'selected_option',
            'justification_text': 'text',
            'justification_image': 'image'
        }

        with pytest.raises(EntityError):
            JustificationDTO.from_request(justification_dict)
    
    def test_justification_dto_from_request_with_no_required_image(self):
        justification_dict = {
            'options': [
                {
                    'option': 'option',
                    'required_text': True
                }
            ],
            'selected_option': 'selected_option',
            'justification_text': 'text',
            'justification_image': 'image'
        }

        with pytest.raises(EntityError):
            JustificationDTO.from_request(justification_dict)
    
    def test_justification_dto_to_entity(self):
        justification_dto = JustificationDTO(
                options=[
                    JustificationOption(
                        option='option',
                        required_image=True,
                        required_text=True
                    ),
                    JustificationOption(
                        option='option2',
                        required_image=True,
                        required_text=True
                    )
                ],
                selected_option='option',
                justification_text='text',
                justification_image='image'
        )

        justification = justification_dto.to_entity()

        assert len(justification.options) == 2
        assert justification.options[0].option == 'option'
        assert justification.options[0].required_image == True
        assert justification.options[0].required_text == True

        assert justification.selected_option == 'option'
        assert justification.justification_text == 'text'
        assert justification.justification_image == 'image'
    
    def test_justification_dto_from_request_with_no_required_image(self):
        justification_dict = {
            'options': [
                {
                    'option': 'option',
                    'required_text': True
                }
            ],
            'selected_option': 'option',
            'text': 'text',
            'image': 'image'
        }

        with pytest.raises(EntityError):
            JustificationDTO.from_request(justification_dict)
    
    def test_justification_dto_from_request_with_no_option(self):
        justification_dict = {
            'options': [
                {
                    'required_image': True,
                    'required_text': True
                }
            ],
            'selected_option': 'option',
            'text': 'text',
            'image': 'image'
        }

        with pytest.raises(EntityError):
            JustificationDTO.from_request(justification_dict)
    
    def test_justification_dto_from_entity(self):
        justification_option = JustificationOption(
            option='option',
            required_image=True,
            required_text=True
        )

        justification = Justification(
            options=[justification_option],
            selected_option='option',
            justification_text='text',
            justification_image='image'
        )

        justification_dto = JustificationDTO.from_entity(justification)

        assert len(justification_dto.options) == 1
        assert justification_dto.options[0].option == 'option'
        assert justification_dto.options[0].required_image == True
        assert justification_dto.options[0].required_text == True

        assert justification_dto.selected_option == 'option'
        assert justification_dto.justification_text == 'text'
        assert justification_dto.justification_image == 'image'
    
    def test_justification_dto_to_dynamo(self):
        justification_dto = JustificationDTO(
                options=[
                    JustificationOption(
                        option='option',
                        required_image=True,
                        required_text=True
                    ),
                    JustificationOption(
                        option='option',
                        required_image=True,
                        required_text=True
                    )
                ],
                selected_option='option',
                justification_text='text',
                justification_image='image'
        )

        dynamo = justification_dto.to_dynamo()

        assert len(dynamo['options']) == 2
        assert dynamo['options'][0]['option'] == 'option'
        assert dynamo['options'][0]['required_image'] == True
        assert dynamo['options'][0]['required_text'] == True

        assert dynamo['selected_option'] == 'option'
        assert dynamo['justification_text'] == 'text'
        assert dynamo['justification_image'] == 'image'
    
    def test_justification_dto_from_dynamo(self):
        justification_dict = {
            'options': [
                {
                    'option': 'option',
                    'required_image': True,
                    'required_text': True
                }
            ],
            'selected_option': 'option',
            'justification_text': 'text',
            'justification_image': 'image'
        }

        justification_dto = JustificationDTO.from_dynamo(justification_dict)

        assert len(justification_dto.options) == 1
        assert justification_dto.options[0].option == 'option'
        assert justification_dto.options[0].required_image == True
        assert justification_dto.options[0].required_text == True

        assert justification_dto.selected_option == 'option'
        assert justification_dto.justification_text == 'text'
        assert justification_dto.justification_image == 'image'
    
    def test_justification_dto_to_entity(self):
        justification_dto = JustificationDTO(
                options=[
                    JustificationOption(
                        option='option',
                        required_image=True,
                        required_text=True
                    ),
                    JustificationOption(
                        option='option',
                        required_image=True,
                        required_text=True
                    )
                ],
                selected_option='option',
                justification_text='text',
                justification_image='image'
        )

        justification = justification_dto.to_entity()

        assert len(justification.options) == 2
        assert justification.options[0].option == 'option'
        assert justification.options[0].required_image == True
        assert justification.options[0].required_text == True

        assert justification.selected_option == 'option'
        assert justification.justification_text == 'text'
        assert justification.justification_image == 'image'