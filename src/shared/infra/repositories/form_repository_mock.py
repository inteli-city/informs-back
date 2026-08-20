from copy import deepcopy
from typing import List, Optional, Union
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.information_field import FileInformationField
from src.shared.domain.entities.justification import Justification, JustificationOption, SelectedJustification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction
from src.shared.helpers.functions.pagination_token import encode_pagination_token


class FormRepositoryMock(IFormRepository):
    forms: List[Form]

    def __init__(self):
        text_field = TextField(label='label', required=True, key='key', order=1, regex='regex', max_length=10, value='value')
        text_field_2 = TextField(label='label 2', required=True, key='key_2', order=2, regex='regex', max_length=10, value='value')
        section = Section(section_id=1, fields=[text_field, text_field_2])
        information_field = FileInformationField(
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
                priority=Priority.EMERGENCY,
                status=FormStatus.IN_PROGRESS,
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
                priority=Priority.EMERGENCY,
                status=FormStatus.COMPLETED,
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
                priority=Priority.LOW,
                status=FormStatus.PENDING,
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
    
    def get_form_by_id(self, user_id: str, form_id: str) -> Optional[Form]:
        for form in self.forms:
            if form.id == form_id:
                return deepcopy(form)
        return None
    
    def get_form_by_user_id(self, user_id: str) -> List[Form]:
        filtered_forms = []
        for form in self.forms:
            if form.user_id == user_id:
                filtered_forms.append(deepcopy(form))

        return filtered_forms

    def _parse_start_index(self, forms: List[Form], last_evaluated_key: Optional[dict]) -> int:
        if last_evaluated_key is None:
            return 0

        last_id = last_evaluated_key.get("id")
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
        limit: Optional[int],
        exclusive_start_key: Optional[dict] = None,
        status: Optional[Union[FormStatus, List[FormStatus]]] = None,
        system: Optional[Union[str, List[str]]] = None,
        user_id: Optional[str] = None,
        created_at_start: Optional[int] = None,
        created_at_end: Optional[int] = None,
        updated_at_start: Optional[int] = None,
        updated_at_end: Optional[int] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Form], Optional[str]]:
        forms = self._filter_forms(
            self.forms, user_id, status, system, created_at_start, created_at_end, search,
            updated_at_start, updated_at_end,
        )

        def sort_key(f: Form):
            is_open = f.status not in [FormStatus.COMPLETED, FormStatus.CANCELLED]
            return (is_open, int(f.priority.value), f.created_at)

        forms = sorted(forms, key=sort_key, reverse=True)

        start = self._parse_start_index(forms, exclusive_start_key)
        if limit is None:
            return deepcopy(forms[start:]), None

        end = start + limit
        page = forms[start:end]
        next_key = self._build_next_key(forms, end)
        return deepcopy(page), next_key

    @staticmethod
    def _filter_forms(
        forms, user_id, status, system, created_at_start, created_at_end, search,
        updated_at_start=None, updated_at_end=None,
    ):
        if user_id is not None:
            forms = [form for form in forms if form.user_id == user_id]

        if status is not None:
            statuses = status if isinstance(status, list) else [status]
            forms = [form for form in forms if form.status in statuses]

        if system is not None:
            systems = system if isinstance(system, list) else [system]
            forms = [form for form in forms if form.system in systems]

        if created_at_start is not None:
            forms = [form for form in forms if form.created_at >= created_at_start]
        if created_at_end is not None:
            forms = [form for form in forms if form.created_at <= created_at_end]

        if updated_at_start is not None:
            forms = [form for form in forms if (form.updated_at or 0) >= updated_at_start]
        if updated_at_end is not None:
            forms = [form for form in forms if (form.updated_at or 0) <= updated_at_end]

        if search is not None:
            search_lower = search.lower()
            forms = [
                form for form in forms
                if search_lower in form.form_title.lower() or (form.observation or "").lower().find(search_lower) != -1
            ]
        return forms

    @staticmethod
    def _build_next_key(forms: List[Form], end: int) -> Optional[str]:
        if end >= len(forms):
            return None
        next_form = forms[end - 1]
        next_key = {
            "PK": f"form#{next_form.id}",
            "SK": "METADATA",
            "GSI1PK": f"user#{next_form.user_id}",
            "GSI1SK": f"priority#{next_form.priority.value}#status#{next_form.status.value}#created_at#{next_form.created_at}",
            "id": next_form.id,
        }
        return encode_pagination_token(next_key)
    
    def create_form(self, form: Form) -> Form:
        for item in self.forms:
            if form.id == item.id:
                raise DuplicatedItem('Formulário já existe')
        self.forms.append(deepcopy(form))
        return form

    def update_form(
        self,
        user_id: str,
        form_id: str,
        status: Optional[FormStatus] = None,
        in_progress_at: Optional[int] = None,
        completed_at: Optional[int] = None,
        cancelled_at: Optional[int] = None,
        updated_at: Optional[int] = None,
        sections: Optional[List[Section]] = None,
        justification: Optional[Justification] = None,
        expected_status: Optional[FormStatus] = None,
    ) -> Optional[Form]:
        form = next((f for f in self.forms if f.id == form_id), None)
        if form is None:
            return None
        if expected_status is not None and form.status != expected_status:
            raise ForbiddenAction("Formulário foi atualizado por outra operação")

        updates = {
            "status": status,
            "in_progress_at": in_progress_at,
            "completed_at": completed_at,
            "cancelled_at": cancelled_at,
            "updated_at": updated_at,
            "sections": sections,
            "justification": justification,
        }
        for attr, new_value in updates.items():
            if new_value is not None:
                setattr(form, attr, new_value)
        return form

    def get_forms_updated_since(
        self,
        system: str,
        updated_at_start: int,
        updated_at_end: Optional[int] = None,
        limit: Optional[int] = None,
        exclusive_start_key: Optional[dict] = None,
        status: Optional[Union[FormStatus, List[FormStatus]]] = None,
    ) -> tuple[List[Form], Optional[str]]:
        forms = [form for form in self.forms if form.system == system and form.updated_at >= updated_at_start]
        if updated_at_end is not None:
            forms = [form for form in forms if form.updated_at <= updated_at_end]
        if status is not None:
            statuses = status if isinstance(status, list) else [status]
            forms = [form for form in forms if form.status in statuses]

        forms = sorted(forms, key=lambda form: (form.updated_at, form.id))

        start = self._parse_start_index(forms, exclusive_start_key)
        if limit is None:
            return deepcopy(forms[start:]), None

        end = start + limit
        page = forms[start:end]
        next_key = None
        if end < len(forms):
            next_form = forms[end - 1]
            next_key = {
                "PK": f"form#{next_form.id}",
                "SK": "METADATA",
                "id": next_form.id,
            }
            next_key = encode_pagination_token(next_key)

        return deepcopy(page), next_key
