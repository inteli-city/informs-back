from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.information_field import TextInformationField
from src.shared.domain.entities.justification import Justification, JustificationOption
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.enums.priority_enum import PRIORITY
from src.shared.infra.dtos.form_dynamo_dto import FormDynamoDTO


class Test_FormDynamoDTO:

    def test_from_entity(self):
        form = Form(
            form_title='form_title',
            form_id='d61dbf66-a10f-11ed-a8fc-0242ac120010',
            created_by='d61dbf66-a10f-11ed-a8fc-0242ac120010',
            user_id='d61dbf66-a10f-11ed-a8fc-0242ac120010',
            template='template',
            area='area',
            system='system',
            street='street',
            city='city',
            number=123,
            latitude=0.0,
            longitude=0.0,
            description='description',
            priority=PRIORITY.EMERGENCY,
            status=FORM_STATUS.IN_PROGRESS,
            expiration_date=12345678,
            created_at=12345678,
            updated_at=12345678,
            in_progress_at=12345678,
            completed_at=12345678,
            justification=Justification(
                options=[
                    JustificationOption(
                        option='option',
                        required_image=True,
                        required_text=True
                    )
                ],
                selected_option='option',
                justification_text='justification_text',
                justification_image='justification_image'
            ),
            sections=[
                Section(
                    section_id=0,
                    fields=[
                        TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='poggers')
                    ]
                )
            ],
            information_fields=[
                TextInformationField(
                    value='value'
                )
            ]
        )
        
        form_dto = FormDynamoDTO.from_entity(form)

        assert form_dto.form_title == 'form_title'
        assert form_dto.form_id == 'd61dbf66-a10f-11ed-a8fc-0242ac120010'
        assert form_dto.created_by == 'd61dbf66-a10f-11ed-a8fc-0242ac120010'
        assert form_dto.user_id == 'd61dbf66-a10f-11ed-a8fc-0242ac120010'
        assert form_dto.template == 'template'
        assert form_dto.area == 'area'
        assert form_dto.system == 'system'
        assert form_dto.street == 'street'
        assert form_dto.city == 'city'
        assert form_dto.number == 123
        assert form_dto.latitude == 0.0
        assert form_dto.longitude == 0.0
        assert form_dto.description == 'description'
        assert form_dto.priority == PRIORITY.EMERGENCY
        assert form_dto.status == FORM_STATUS.IN_PROGRESS
        assert form_dto.expiration_date == 12345678
        assert form_dto.created_at == 12345678
        assert form_dto.in_progress_at == 12345678
        assert form_dto.completed_at == 12345678
        assert form_dto.justification.options[0].option == 'option'
        assert form_dto.justification.options[0].required_image == True
        assert form_dto.justification.options[0].required_text == True
        assert form_dto.justification.selected_option == 'option'
        assert form_dto.justification.justification_text == 'justification_text'
        assert form_dto.justification.justification_image == 'justification_image'
        assert form_dto.sections[0].section_id == 0
        assert form_dto.sections[0].fields[0].placeholder == 'placeholder'
        assert form_dto.sections[0].fields[0].required == True
        assert form_dto.sections[0].fields[0].key == 'key'
        assert form_dto.sections[0].fields[0].regex == 'regex'
        assert form_dto.sections[0].fields[0].formatting == 'formatting'
        assert form_dto.sections[0].fields[0].max_length == 10
        assert form_dto.sections[0].fields[0].value == 'poggers'
        assert form_dto.information_fields[0].value == 'value'

    def test_to_dynamo(self):
        form_dto = FormDynamoDTO(
            form_title='form_title',
            form_id='d61dbf66-a10f-11ed-a8fc-0242ac120010',
            created_by='d61dbf66-a10f-11ed-a8fc-0242ac120010',
            user_id='d61dbf66-a10f-11ed-a8fc-0242ac120010',
            template='template',
            area='area',
            system='system',
            street='street',
            city='city',
            number=123,
            latitude=0.0,
            longitude=0.0,
            description='description',
            priority=PRIORITY.EMERGENCY,
            status=FORM_STATUS.IN_PROGRESS,
            expiration_date=12345678,
            created_at=12345678,
            in_progress_at=12345678,
            completed_at=12345678,
            justification=Justification(
                options=[
                    JustificationOption(
                        option='option',
                        required_image=True,
                        required_text=True
                    )
                ],
                selected_option='option',
                justification_text='justification_text',
                justification_image='justification_image'
            ),
            sections=[
                Section(
                    section_id=0,
                    fields=[
                        TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='poggers')
                    ]
                )
            ],
            information_fields=[
                TextInformationField(
                    value='value'
                )
            ]
        )

        form = form_dto.to_dynamo()

        assert form['form_title'] == 'form_title'
        assert form['form_id'] == 'd61dbf66-a10f-11ed-a8fc-0242ac120010'
        assert form['created_by'] == 'd61dbf66-a10f-11ed-a8fc-0242ac120010'
        assert form['user_id'] == 'd61dbf66-a10f-11ed-a8fc-0242ac120010'
        assert form['template'] == 'template'
        assert form['area'] == 'area'
        assert form['system'] == 'system'
        assert form['street'] == 'street'
        assert form['city'] == 'city'
        assert form['number'] == 123
        assert form['latitude'] == 0.0
        assert form['longitude'] == 0.0
        assert form['description'] == 'description'
        assert form['priority'] == PRIORITY.EMERGENCY.value
        assert form['status'] == FORM_STATUS.IN_PROGRESS.value
        assert form['expiration_date'] == 12345678
        assert form['created_at'] == 12345678
        assert form['in_progress_at'] == 12345678
        assert form['completed_at'] == 12345678
        assert form['justification']['options'][0]['option'] == 'option'
        assert form['justification']['options'][0]['required_image'] == True
        assert form['justification']['options'][0]['required_text'] == True
        assert form['justification']['selected_option'] == 'option'
        assert form['justification']['justification_text'] == 'justification_text'
        assert form['justification']['justification_image'] == 'justification_image'
        assert form['sections'][0]['section_id'] == '0'
        assert form['sections'][0]['fields'][0]['placeholder'] == 'placeholder'
        assert form['sections'][0]['fields'][0]['required'] == True
        assert form['sections'][0]['fields'][0]['key'] == 'key'
        assert form['sections'][0]['fields'][0]['regex'] == 'regex'
        assert form['sections'][0]['fields'][0]['formatting'] == 'formatting'
        assert form['sections'][0]['fields'][0]['max_length'] == 10
        assert form['sections'][0]['fields'][0]['value'] == 'poggers'
        assert form['information_fields'][0]['value'] == 'value'
    
    def test_from_dynamo(self):
        form = FormDynamoDTO.from_dynamo({
            'form_title': 'form_title',
            'form_id': 'd61dbf66-a10f-11ed-a8fc-0242ac120010',
            'created_by': 'd61dbf66-a10f-11ed-a8fc-0242ac120010',
            'user_id': 'd61dbf66-a10f-11ed-a8fc-0242ac120010',
            'template': 'template',
            'area': 'area',
            'system': 'system',
            'street': 'street',
            'city': 'city',
            'number': 123,
            'latitude': 0.0,
            'longitude': 0.0,
            'description': 'description',
            'priority': PRIORITY.EMERGENCY.value,
            'status': FORM_STATUS.IN_PROGRESS.value,
            'expiration_date': 12345678,
            'created_at': 12345678,
            'in_progress_at': 12345678,
            'completed_at': 12345678,
            'justification': {
                'options': [
                    {
                        'option': 'option',
                        'required_image': True,
                        'required_text': True
                    }
                ],
                'selected_option': 'option',
                'justification_text': 'justification_text',
                'justification_image': 'justification_image'
            },
            'sections': [
                {
                    'section_id': '0',
                    'fields': [
                        {
                            'field_type': 'TEXT_FIELD',
                            'placeholder': 'placeholder',
                            'required': True,
                            'key': 'key',
                            'regex': 'regex',
                            'formatting': 'formatting',
                            'max_length': 10,
                            'value': 'poggers'
                        }
                    ]
                }
            ],
            'information_fields': [
                {
                    'information_field_type': 'TEXT_INFORMATION_FIELD',
                    'value': 'value'
                }
            ]
        })

        assert form.form_title == 'form_title'
        assert form.form_id == 'd61dbf66-a10f-11ed-a8fc-0242ac120010'
        assert form.created_by == 'd61dbf66-a10f-11ed-a8fc-0242ac120010'
        assert form.user_id == 'd61dbf66-a10f-11ed-a8fc-0242ac120010'
        assert form.template == 'template'
        assert form.area == 'area'
        assert form.system == 'system'
        assert form.street == 'street'
        assert form.city == 'city'
        assert form.number == 123
        assert form.latitude == 0.0
        assert form.longitude == 0.0
        assert form.description == 'description'
        assert form.priority == PRIORITY.EMERGENCY
        assert form.status == FORM_STATUS.IN_PROGRESS
        assert form.expiration_date == 12345678
        assert form.created_at == 12345678
        assert form.in_progress_at == 12345678
        assert form.completed_at == 12345678
        assert form.justification.options[0].option == 'option'
        assert form.justification.options[0].required_image == True
        assert form.justification.options[0].required_text == True
        assert form.justification.selected_option == 'option'
        assert form.justification.justification_text == 'justification_text'
        assert form.justification.justification_image == 'justification_image'
        assert form.sections[0].section_id == 0
        assert form.sections[0].fields[0].placeholder == 'placeholder'
        assert form.sections[0].fields[0].required == True
        assert form.sections[0].fields[0].key == 'key'
        assert form.sections[0].fields[0].regex == 'regex'
        assert form.sections[0].fields[0].formatting == 'formatting'
        assert form.sections[0].fields[0].max_length == 10
        assert form.sections[0].fields[0].value == 'poggers'
        assert form.information_fields[0].value == 'value'

    def test_to_entity(self):
        form_dto = FormDynamoDTO(
            form_title='form_title',
            form_id='d61dbf66-a10f-11ed-a8fc-0242ac120010',
            created_by='d61dbf66-a10f-11ed-a8fc-0242ac120010',
            user_id='d61dbf66-a10f-11ed-a8fc-0242ac120010',
            template='template',
            area='area',
            system='system',
            street='street',
            city='city',
            number=123,
            latitude=0.0,
            longitude=0.0,
            description='description',
            priority=PRIORITY.EMERGENCY,
            status=FORM_STATUS.IN_PROGRESS,
            expiration_date=12345678,
            created_at=12345678,
            in_progress_at=12345678,
            completed_at=12345678,
            justification=Justification(
                options=[
                    JustificationOption(
                        option='option',
                        required_image=True,
                        required_text=True
                    )
                ],
                selected_option='option',
                justification_text='justification_text',
                justification_image='justification_image'
            ),
            sections=[
                Section(
                    section_id=0,
                    fields=[
                        TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='poggers')
                    ]
                )
            ],
            information_fields=[
                TextInformationField(
                    value='value'
                )
            ]
        )

        form = form_dto.to_entity()

        assert form.form_title == 'form_title'
        assert form.form_id == 'd61dbf66-a10f-11ed-a8fc-0242ac120010'
        assert form.created_by == 'd61dbf66-a10f-11ed-a8fc-0242ac120010'
        assert form.user_id == 'd61dbf66-a10f-11ed-a8fc-0242ac120010'
        assert form.template == 'template'
        assert form.area == 'area'
        assert form.system == 'system'
        assert form.street == 'street'
        assert form.city == 'city'
        assert form.number == 123
        assert form.latitude == 0.0
        assert form.longitude == 0.0
        assert form.description == 'description'
        assert form.priority == PRIORITY.EMERGENCY
        assert form.status == FORM_STATUS.IN_PROGRESS
        assert form.expiration_date == 12345678
        assert form.created_at == 12345678
        assert form.in_progress_at == 12345678
        assert form.completed_at == 12345678
        assert form.justification.options[0].option == 'option'
        assert form.justification.options[0].required_image == True
        assert form.justification.options[0].required_text == True
        assert form.justification.selected_option == 'option'
        assert form.justification.justification_text == 'justification_text'
        assert form.justification.justification_image == 'justification_image'
        assert form.sections[0].section_id == 0
        assert form.sections[0].fields[0].placeholder == 'placeholder'
        assert form.sections[0].fields[0].required == True
        assert form.sections[0].fields[0].key == 'key'
        assert form.sections[0].fields[0].regex == 'regex'
        assert form.sections[0].fields[0].formatting == 'formatting'
        assert form.sections[0].fields[0].max_length == 10
        assert form.sections[0].fields[0].value == 'poggers'
        assert form.information_fields[0].value == 'value'
        
