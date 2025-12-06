from src.modules.submit_form.app.submit_form_viewmodel import SubmitFormViewmodel, FieldViewmodel, FormViewmodel, InformationFieldViewmodel, JustificationOptionViewmodel, JustificationViewmodel, SectionViewmodel
from src.shared.domain.entities.field import FileField, TextField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.information_field import ImageInformationField, MapInformationField, TextInformationField
from src.shared.domain.entities.justification import Justification, JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.file_type_enum import FILE_TYPE
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.enums.priority_enum import PRIORITY

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

class Test_SubmitFormViewmodel:

    def test_field_viewmodel(self):
        viewmodel = FieldViewmodel(field=TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='value'))

        response = viewmodel.to_dict()

        excepted = {
            'field_type': 'TEXT_FIELD',
            'label': 'placeholder',
            'placeholder': 'placeholder',
            'required': True,
            'key': 'key',
            'order': 0,
            'help_text': None,
            'regex': 'regex',
            'formatting': 'formatting',
            'max_length': 10,
            'value': 'value'
        }

        assert response == excepted
    
    def test_field_viewmodel_with_enum(self):
        viewmodel = FieldViewmodel(field=FileField(placeholder='placeholder', required=True, key='key', file_type=FILE_TYPE.IMAGE, min_quantity=1, max_quantity=10, value=['value']))

        response = viewmodel.to_dict()

        excepted = {
            'field_type': 'FILE_FIELD',
            'label': 'placeholder',
            'placeholder': 'placeholder',
            'required': True,
            'key': 'key',
            'order': 0,
            'help_text': None,
            'file_type': 'IMAGE',
            'min_quantity': 1,
            'max_quantity': 10,
            'value': ['value']
        }

        assert response == excepted

    def test_informarion_field_viewmodel(self):
        viewmodel = InformationFieldViewmodel(information_field=TextInformationField(value='value'))

        response = viewmodel.to_dict()

        excepted = {
            'information_field_type': 'TEXT_INFORMATION_FIELD',
            'value': 'value'
        }

        assert response == excepted
    
    def test_field_viewmodel_with_none(self):
        viewmodel = FieldViewmodel(field=TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=None, value=None))

        response = viewmodel.to_dict()

        excepted = {
            'field_type': 'TEXT_FIELD',
            'label': 'placeholder',
            'placeholder': 'placeholder',
            'required': True,
            'key': 'key',
            'order': 0,
            'help_text': None,
            'regex': 'regex',
            'formatting': 'formatting',
            'max_length': None,
            'value': None
        }

        assert response == excepted
    
    def test_section_viewmodel(self):

        field = FileField(placeholder='placeholder', required=True, key='key', file_type=FILE_TYPE.IMAGE, min_quantity=1, max_quantity=10, value=['value'])

        viewmodel = SectionViewmodel(
            section=Section(
                section_id=1,
                fields=[field]
            )
        )

        response = viewmodel.to_dict()

        excepted = {
            'section_id': 1,
            'fields': [{
                'field_type': 'FILE_FIELD',
                'label': 'placeholder',
                'placeholder': 'placeholder',
                'required': True,
                'key': 'key',
                'order': 0,
                'help_text': None,
                'file_type': 'IMAGE',
                'min_quantity': 1,
                'max_quantity': 10,
                'value': ['value']
            }]
        }

        assert response == excepted
    
    def test_jusificative_option_viewmodel(self):
        viewmodel = JustificationOptionViewmodel(justification_option)

        response = viewmodel.to_dict()

        excepted = {
            'option': 'option',
            'required_image': True,
            'required_text': True
        }

        assert response == excepted
    
    def test_justification_viewmodel(self):
        viewmodel = JustificationViewmodel(
            justification=justification
        )

        response = viewmodel.to_dict()

        excepted = {
            'options': [{
                'option': 'option',
                'required_image': True,
                'required_text': True
            }],
            'selected_option': 'option',
            'justification_text': 'text',
            'justification_image': 'image'
        }

        assert response == excepted
    
    def test_form_viewmodel(self):
        field = FileField(placeholder='placeholder', required=True, key='key', file_type=FILE_TYPE.IMAGE, min_quantity=1, max_quantity=10, value=['value'])

        section = Section(
                section_id=1,
                fields=[field]
            )
        
        viewmodel = FormViewmodel(
            form=Form(
                form_title='FORM_TITLE',
                form_id='d61dbf66-a10f-11ed-a8fc-0242ac120001',
                creator_user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001',
                created_by='d61dbf66-a10f-11ed-a8fc-0242ac120001',
                user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001',
                vinculation_form_id='d61dbf66-a10f-11ed-a8fc-0242ac120001',
                can_vinculate=True,
                template='template',
                area='area',
                system='system',
                street='street',
                city='city',
                number=1,
                latitude=1.0,
                longitude=1.0,
                region='region',
                description='description',
                priority=PRIORITY.HIGH,
                status=FORM_STATUS.IN_PROGRESS,
                expiration_date=1,
                creation_date=1,
                created_at=1,
                updated_at=1,
                in_progress_at=1,
                completed_at=1,
                justification=justification,
                comments='comments',
                sections=[section],
                information_fields=[
                    TextInformationField(value='value'),
                    MapInformationField(latitude=1.0, longitude=1.0),
                    ImageInformationField(file_path='file_path')
                ]
            )
        )

        response = viewmodel.to_dict()

        excepted = {
            'form_title': 'FORM_TITLE',
            'form_id': 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
            'creator_user_id': 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
            'user_id': 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
            'vinculation_form_id': 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
            'can_vinculate': True,
            'template': 'template',
            'area': 'area',
            'system': 'system',
            'street': 'street',
            'city': 'city',
            'number': 1,
            'latitude': 1.0,
            'longitude': 1.0,
            'region': 'region',
            'description': 'description',
            'priority': PRIORITY.HIGH.value,
            'status': 'IN_PROGRESS',
            'expiration_date': 1,
            'creation_date': 1,
            'start_date': 1,
            'conclusion_date': 1,
            'justification': {
                'options': [{
                    'option': 'option',
                    'required_image': True,
                    'required_text': True
                }],
                'selected_option': 'option',
                'justification_text': 'text',
                'justification_image': 'image'
            
            },
            'comments': 'comments',
            'sections': [{
                'section_id': 1,
                'fields': [{
                    'field_type': 'FILE_FIELD',
                    'label': 'placeholder',
                    'placeholder': 'placeholder',
                    'required': True,
                    'key': 'key',
                    'order': 0,
                    'help_text': None,
                    'file_type': 'IMAGE',
                    'min_quantity': 1,
                    'max_quantity': 10,
                    'value': ['value']
                }]
            }],
            'information_fields': [
                {
                    'information_field_type': 'TEXT_INFORMATION_FIELD',
                    'value': 'value'
                },
                {
                    'information_field_type': 'MAP_INFORMATION_FIELD',
                    'latitude': 1.0,
                    'longitude': 1.0
                },
                {
                    'information_field_type': 'IMAGE_INFORMATION_FIELD',
                    'file_path': 'file_path'
                }
            ]
        }

        assert response == excepted
    
    def test_submit_form_viewmodel(self):
        field = FileField(placeholder='placeholder', required=True, key='key', file_type=FILE_TYPE.IMAGE, min_quantity=1, max_quantity=10, value=['value'])

        section = Section(
                section_id=1,
                fields=[field]
            )
        
        form = Form(
                form_title='FORM TITLE',
                form_id='d61dbf66-a10f-11ed-a8fc-0242ac120001',
                creator_user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001',
                created_by='d61dbf66-a10f-11ed-a8fc-0242ac120001',
                user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001',
                vinculation_form_id='d61dbf66-a10f-11ed-a8fc-0242ac120001',
                can_vinculate=True,
                template='template',
                area='area',
                system='system',
                street='street',
                city='city',
                number=1,
                latitude=1.0,
                longitude=1.0,
                region='region',
                description='description',
                priority=PRIORITY.HIGH,
                status=FORM_STATUS.IN_PROGRESS,
                expiration_date=1,
                creation_date=1,
                created_at=1,
                updated_at=1,
                in_progress_at=1,
                completed_at=1,
                justification=justification,
                comments='comments',
                sections=[section],
                information_fields=[
                    TextInformationField(value='value'),
                    MapInformationField(latitude=1.0, longitude=1.0),
                    ImageInformationField(file_path='file_path')
                ]
            )

        viewmodel = SubmitFormViewmodel(
            form=form
        )

        response = viewmodel.to_dict()

        excepted = {
            'form': {
                    'form_title': 'FORM TITLE',
                    'form_id': 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                    'creator_user_id': 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                    'user_id': 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                    'vinculation_form_id': 'd61dbf66-a10f-11ed-a8fc-0242ac120001',
                    'can_vinculate': True,
                    'template': 'template',
                    'area': 'area',
                    'system': 'system',
                    'street': 'street',
                    'city': 'city',
                    'number': 1,
                    'latitude': 1.0,
                    'longitude': 1.0,
                    'region': 'region',
                    'description': 'description',
                    'priority': PRIORITY.HIGH.value,
                    'status': 'IN_PROGRESS',
                    'expiration_date': 1,
                    'creation_date': 1,
                    'start_date': 1,
                    'conclusion_date': 1,
                    'justification': {
                        'options': [{
                            'option': 'option',
                            'required_image': True,
                            'required_text': True
                        }],
                        'selected_option': 'option',
                        'justification_text': 'text',
                        'justification_image': 'image'
                    },
                    'comments': 'comments',
                    'sections': [
                        {
                            'section_id': 1,
                            'fields': [
                                {
                                    'field_type': 'FILE_FIELD',
                                    'label': 'placeholder',
                                    'placeholder': 'placeholder',
                                    'required': True,
                                    'key': 'key',
                                    'order': 0,
                                    'help_text': None,
                                    'file_type': 'IMAGE',
                                    'min_quantity': 1,
                                    'max_quantity': 10,
                                    'value': ['value']
                                }
                            ]
                        }
                    ],
                    'information_fields': [
                        {
                            'information_field_type': 'TEXT_INFORMATION_FIELD',
                            'value': 'value'
                        },
                        {
                            'information_field_type': 'MAP_INFORMATION_FIELD',
                            'latitude': 1.0,
                            'longitude': 1.0
                        },
                        {
                            'information_field_type': 'IMAGE_INFORMATION_FIELD',
                            'file_path': 'file_path'
                        }
                    ]
                },
            'message': 'Formulário finalizado com sucesso!'
        }

        assert response == excepted
