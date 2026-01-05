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
from src.shared.helpers.functions.pagination_token import encode_pagination_token


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

    def _parse_start_index(self, forms: List[Form], last_evaluated_key: Optional[dict]) -> int:
        if last_evaluated_key is None:
            return 0

        last_id = last_evaluated_key.get("id") or last_evaluated_key.get("form_id")
        pk = last_evaluated_key.get("PK") or last_evaluated_key.get("pk")
        if last_id is None and pk and isinstance(pk, str) and pk.startswith("form#"):
            last_id = pk.split("form#", 1)[1]

        if last_id is None:
            return 0

        for idx, form in enumerate(forms):
            if form.id == last_id:
                return idx + 1
        return 0

    def get_all_forms(
        self,
        limit: int,
        exclusive_start_key: Optional[dict] = None,
        status: Optional[FORM_STATUS] = None,
        system: Optional[str] = None,
        user_id: Optional[str] = None,
        created_at_start: Optional[int] = None,
        created_at_end: Optional[int] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Form], Optional[str]]:
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

        start_key_dict = exclusive_start_key
        start = self._parse_start_index(forms, start_key_dict)
        end = start + limit
        page = forms[start:end]

        next_key = None
        if end < len(forms):
            next_form = forms[end - 1]
            next_key = {
                "PK": f"form#{next_form.id}",
                "SK": "METADATA",
                "GSI1PK": f"user#{next_form.user_id}",
                "GSI1SK": f"priority#{next_form.priority.value}#status#{next_form.status.value}#created_at#{next_form.created_at}",
                "id": next_form.id,
                "form_id": next_form.id,
            }
            next_key = encode_pagination_token(next_key)

        return page, next_key
    
    def create_form(self, form: Form) -> Form:
        for item in self.forms:
            if form.id == item.id:
                raise DuplicatedItem('Formulário já existe')
        self.forms.append(form)
        return form

    def update_form(
        self,
        user_id: str,
        form_id: str,
        status: Optional[FORM_STATUS] = None,
        in_progress_at: Optional[int] = None,
        completed_at: Optional[int] = None,
        cancelled_at: Optional[int] = None,
        updated_at: Optional[int] = None,
        sections: Optional[List[Section]] = None,
        justification: Optional[Justification] = None,
    ) -> Form:
        for form in self.forms:
            if form.id == form_id:
                if status is not None:
                    form.status = status
                if in_progress_at is not None:
                    form.in_progress_at = in_progress_at
                if completed_at is not None:
                    form.completed_at = completed_at
                if cancelled_at is not None:
                    form.cancelled_at = cancelled_at
                if updated_at is not None:
                    form.updated_at = updated_at
                if sections is not None:
                    form.sections = sections
                if justification is not None:
                    form.justification = justification
                return form
        return None
