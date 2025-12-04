from datetime import datetime, timedelta
from typing import List, Optional
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.information_field import ImageInformationField
from src.shared.domain.entities.justification import Justification, JustificationOption, SelectedJustification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.enums.priority_enum import PRIORITY
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.helpers.errors.usecase_errors import DuplicatedItem


class FormRepositoryMock(IFormRepository):
    forms: List[Form]

    def __init__(self):
        def timestamp_yesterday():
            current_date = datetime.now()
            yesterday_date = current_date - timedelta(days=1)

            timestamp_yesterday_seconds = int(yesterday_date.timestamp())
            timestamp_yesterday_milliseconds = timestamp_yesterday_seconds * 1000
            return timestamp_yesterday_milliseconds

        text_field = TextField(label='label', required=True, key='key', order=1, regex='regex', max_length=10, value='value')
        section = Section(section_id=1, fields=[text_field, text_field])
        information_field = ImageInformationField(
            file_path='image'
        )
        justification_option = JustificationOption(
            option='option',
            required_image=True,
            required_text=True
        )

        justification = Justification(
            options=[justification_option],
            selected=SelectedJustification(option='option', text='text', image_url='image')
        )

        self.forms = [
            Form(
                id='d61dbf66-a10f-11ed-a8fc-0242ac120010',
                form_title='FORM_TITLE',
                created_by='d61dbf66-a10f-11ed-a8fc-0242ac120001',
                user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001',
                template='TEMPLATE',
                area='1',
                system='GAIA',
                street='1',
                city='1',
                number=1,
                latitude=1.0,
                longitude=1.0,
                priority=PRIORITY.EMERGENCY,
                status=FORM_STATUS.IN_PROGRESS,
                expiration_date=946407600000,
                observation=None,
                created_at=946407600000,
                updated_at=946407600000,
                in_progress_at=946407600000,
                cancelled_at=None,
                completed_at=None,
                justification=justification,
                sections=[section, section],
                information_fields=[information_field, information_field],
            ),
            Form(
                id='d61dbf66-a10f-11ed-a8fc-0242ac120011',
                form_title='FORM_TITLE2',
                created_by='d61dbf66-a10f-11ed-a8fc-0242ac120001',
                user_id='d61dbf66-a10f-11ed-a8fc-0242ac120002',
                template='TEMPLATE',
                area='1',
                system='GAIA',
                street='1',
                city='1',
                number=1,
                latitude=1.0,
                longitude=1.0,
                priority=PRIORITY.EMERGENCY,
                status=FORM_STATUS.COMPLETED,
                expiration_date=946407600000,
                observation=None,
                created_at=946407600000,
                updated_at=946407600000,
                in_progress_at=946407600000,
                cancelled_at=None,
                completed_at=946407600000,
                justification=justification,
                sections=[section],
                information_fields=[information_field, information_field],
            ),
            Form(
                id='d61dbf66-a10f-11ed-a8fc-0242ac120012',
                form_title='FORM_TITLE',
                created_by='d61dbf66-a10f-11ed-a8fc-0242ac120001',
                user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001',
                template='TEMPLATE',
                area='1',
                system='GAIA',
                street='1',
                city='1',
                number=1,
                latitude=1.0,
                longitude=1.0,
                priority=PRIORITY.LOW,
                status=FORM_STATUS.PENDING,
                expiration_date=946407600000,
                observation=None,
                created_at=946407600000,
                updated_at=946407600000,
                in_progress_at=None,
                cancelled_at=None,
                completed_at=None,
                justification=justification,
                sections=[section, section],
                information_fields=[information_field, information_field],
            ),
        ]
    
    def get_form_by_id(self, user_id: str, form_id: str) -> Form:
        for form in self.forms:
            if form.id == form_id:
                return form
        return None
    
    def get_form_by_user_id(self, user_id: str) -> List[Form]:
        filtered_forms = []
        for form in self.forms:
            if form.user_id == user_id:
                filtered_forms.append(form)

        return filtered_forms

    def get_all_forms(self, page: int, limit: int, status: Optional[FORM_STATUS] = None, system: Optional[str] = None, user_id: Optional[str] = None, created_at_start: Optional[int] = None, created_at_end: Optional[int] = None, search: Optional[str] = None) -> List[Form]:
        forms = self.forms

        if user_id is not None:
            forms = [form for form in forms if form.user_id == user_id]

        if status is not None:
            forms = [form for form in forms if form.status == status]

        if system is not None:
            forms = [form for form in forms if form.system == system]

        if created_at_start is not None:
            forms = [form for form in forms if form.created_at >= created_at_start]
        if created_at_end is not None:
            forms = [form for form in forms if form.created_at <= created_at_end]

        if search is not None:
            search_lower = search.lower()
            forms = [
                form for form in forms
                if search_lower in form.form_title.lower() or (form.observation or "").lower().find(search_lower) != -1
            ]

        def sort_key(f: Form):
            is_open = f.status not in [FORM_STATUS.COMPLETED, FORM_STATUS.CANCELLED]
            return (is_open, int(f.priority.value), f.created_at)

        forms = sorted(forms, key=sort_key, reverse=True)

        start = (page - 1) * limit
        end = start + limit
        return forms[start:end]
    
    def create_form(self, form: Form) -> Form:
        for item in self.forms:
            if form.id == item.id:
                raise DuplicatedItem('Formulário já existe')
        self.forms.append(form)
        return form
    
    def update_form_status(self, user_id: str, form_id: str, status: FORM_STATUS, in_progress_at: Optional[int] = None, updated_at: Optional[int] = None) -> Form:
        for form in self.forms:
            if form.id == form_id:
                form.status = status
                form.in_progress_at = in_progress_at
                form.updated_at = updated_at or form.updated_at
                return form
        return None
    
    def cancel_form(self, user_id: str, form_id: str, justification: Justification, cancelled_at: int, updated_at: int) -> Form:
        for form in self.forms:
            if form.id == form_id:
                form.status = FORM_STATUS.CANCELLED
                form.justification = justification
                form.cancelled_at = cancelled_at
                form.updated_at = updated_at
                return form
        return None

    def complete_form(self, user_id: str, form_id: str, sections: List[Section], completed_at: int, updated_at: int, vinculation_form_id: Optional[str] = None, **kwargs) -> Form:
        for form in self.forms:
            if form.id == form_id:
                form.status = FORM_STATUS.COMPLETED
                form.sections = sections
                form.completed_at = completed_at
                form.updated_at = updated_at
                form.vinculation_form_id = vinculation_form_id
                return form
        return None
