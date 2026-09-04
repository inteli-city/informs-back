import pytest

from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.information_field import FileInformationField
from src.shared.domain.entities.justification import Justification, JustificationOption, SelectedJustification
from src.shared.domain.entities.section import MAX_SECTION_INSTANCE, Section
from src.shared.domain.enums.form_origin_enum import FormOrigin
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.enums.priority_enum import Priority
from src.shared.helpers.errors.domain_errors import EntityError


valid_id = 'd61dbf66-a10f-11ed-a8fc-0242ac120001'
text_field = TextField(label='label', required=True, key='key', order=1, max_length=10, value='value')
section = Section(section_id=1, fields=[text_field])
information_field = FileInformationField(file_path='file')
justification_option = JustificationOption(option='option', required_image=True, required_text=True)
justification = Justification(
    options=[justification_option],
    selected=SelectedJustification(option='option', text='text', image_url='image')
)


def make_form(**overrides):
    base = {
        "id": valid_id,
        "form_title": 'form_title',
        "created_by": valid_id,
        "user_id": valid_id,
        "system": 'system',
        "city": 'city',
        "street": 'street',
        "latitude": 1.0,
        "longitude": 1.0,
        "priority": Priority.LOW,
        "status": FormStatus.PENDING,
        "created_at": 1,
        "updated_at": 1,
        "sections": [section],
    }
    base.update(overrides)
    return Form(**base)


class TestForm:

    def test_form_valid(self):
        make_form(
            template='template',
            area='area',
            number=123,
            observation='obs',
            expiration_date=946407600000,
            justification=justification,
            information_fields=[information_field],
            in_progress_at=None,
            cancelled_at=None,
            completed_at=None,
        )

    def test_invalid_id(self):
        with pytest.raises(EntityError):
            make_form(id='short')

    def test_invalid_priority_type(self):
        with pytest.raises(EntityError):
            make_form(priority='1')  # not enum

    def test_sections_required(self):
        with pytest.raises(EntityError):
            make_form(sections=[])

    def test_sections_empty_list_with_uuid_template(self):
        form = make_form(template=valid_id, justification=justification, sections=[])
        assert form.sections == []

    def test_information_fields_type(self):
        with pytest.raises(EntityError):
            make_form(information_fields=['invalid'])

    def test_information_fields_empty_list(self):
        form = make_form(justification=justification, information_fields=[])
        assert form.information_fields == []

    def test_justification_type(self):
        with pytest.raises(EntityError):
            make_form(justification='not_valid')


class TestFormApplyFieldValues:

    def _make_duplicable_form(self):
        field_a = TextField(label='Nome', required=True, key='nome', order=1, max_length=50)
        field_b = TextField(label='Obs', required=False, key='obs', order=2, max_length=50)
        sec = Section(section_id=1, fields=[field_a, field_b], is_duplicable=True)
        return make_form(sections=[sec], justification=justification)

    def test_apply_field_values_single_instance(self):
        form = self._make_duplicable_form()
        form.status = FormStatus.IN_PROGRESS
        form.apply_field_values([
            {"section_id": 1, "section_instance": 0, "field_key": "nome", "value": "João"},
            {"section_id": 1, "section_instance": 0, "field_key": "obs", "value": "ok"},
        ])
        assert len(form.sections) == 1
        assert form.sections[0].fields[0].value == "João"

    def test_apply_field_values_duplicate_instance_created(self):
        form = self._make_duplicable_form()
        form.status = FormStatus.IN_PROGRESS
        form.apply_field_values([
            {"section_id": 1, "section_instance": 0, "field_key": "nome", "value": "João"},
            {"section_id": 1, "section_instance": 0, "field_key": "obs", "value": "ok"},
            {"section_id": 1, "section_instance": 1, "field_key": "nome", "value": "Maria"},
            {"section_id": 1, "section_instance": 1, "field_key": "obs", "value": "tb ok"},
        ])
        assert len(form.sections) == 2
        instance_0 = next(s for s in form.sections if s.section_instance == 0)
        instance_1 = next(s for s in form.sections if s.section_instance == 1)
        assert instance_0.fields[0].value == "João"
        assert instance_1.fields[0].value == "Maria"

    def test_apply_field_values_duplicate_base_not_mutated(self):
        """O snapshot da instância 0 deve ser limpo, mesmo se os campos de instance=0 chegarem antes."""
        form = self._make_duplicable_form()
        form.status = FormStatus.IN_PROGRESS
        form.apply_field_values([
            {"section_id": 1, "section_instance": 0, "field_key": "nome", "value": "João"},
            {"section_id": 1, "section_instance": 0, "field_key": "obs", "value": "ok"},
            {"section_id": 1, "section_instance": 1, "field_key": "nome", "value": "Maria"},
            {"section_id": 1, "section_instance": 1, "field_key": "obs", "value": "tb ok"},
        ])
        instance_1 = next(s for s in form.sections if s.section_instance == 1)
        assert instance_1.section_id == 1
        assert instance_1.is_duplicable is True

    def test_apply_field_values_not_duplicable_raises(self):
        field_a = TextField(label='Nome', required=True, key='nome', order=1, max_length=50)
        sec = Section(section_id=1, fields=[field_a], is_duplicable=False)
        form = make_form(sections=[sec], justification=justification)
        form.status = FormStatus.IN_PROGRESS
        with pytest.raises(EntityError):
            form.apply_field_values([
                {"section_id": 1, "section_instance": 0, "field_key": "nome", "value": "João"},
                {"section_id": 1, "section_instance": 1, "field_key": "nome", "value": "Maria"},
            ])

    def test_apply_field_values_duplicate_key_same_instance_raises(self):
        form = self._make_duplicable_form()
        form.status = FormStatus.IN_PROGRESS
        with pytest.raises(EntityError):
            form.apply_field_values([
                {"section_id": 1, "section_instance": 0, "field_key": "nome", "value": "João"},
                {"section_id": 1, "section_instance": 0, "field_key": "nome", "value": "duplicado"},
            ])

    def test_apply_field_values_section_instance_negative_raises(self):
        form = self._make_duplicable_form()
        form.status = FormStatus.IN_PROGRESS
        with pytest.raises(EntityError):
            form.apply_field_values([
                {"section_id": 1, "section_instance": -1, "field_key": "nome", "value": "João"},
            ])

    def test_apply_field_values_section_instance_not_int_raises(self):
        form = self._make_duplicable_form()
        form.status = FormStatus.IN_PROGRESS
        with pytest.raises(EntityError):
            form.apply_field_values([
                {"section_id": 1, "section_instance": "1", "field_key": "nome", "value": "João"},
            ])

    def test_apply_field_values_section_instance_above_max_raises(self):
        """Defesa no domínio (além do contrato): teto evita deepcopies em série e
        item do DynamoDB inflado além do limite de 400KB."""
        form = self._make_duplicable_form()
        form.status = FormStatus.IN_PROGRESS
        with pytest.raises(EntityError):
            form.apply_field_values([
                {"section_id": 1, "section_instance": MAX_SECTION_INSTANCE + 1, "field_key": "nome", "value": "João"},
            ])

    def test_apply_field_values_duplicate_instance_missing_required_raises(self):
        """Instância duplicada deve ser validada como um adicional: obrigatórios preenchidos."""
        form = self._make_duplicable_form()
        form.status = FormStatus.IN_PROGRESS
        with pytest.raises(EntityError):
            form.apply_field_values([
                {"section_id": 1, "section_instance": 0, "field_key": "nome", "value": "João"},
                {"section_id": 1, "section_instance": 0, "field_key": "obs", "value": "ok"},
                # instância 1 criada, mas campo obrigatório 'nome' não enviado
                {"section_id": 1, "section_instance": 1, "field_key": "obs", "value": "tb ok"},
            ])

    def test_apply_field_values_duplicate_instance_does_not_inherit_base_value(self):
        """Instância nova não deve herdar valor que a seção base já tinha antes deste submit
        (ex.: default gravado na criação) — senão o obrigatório passaria sem o cliente
        ter preenchido nada para esta instância específica."""
        field_a = TextField(label='Nome', required=True, key='nome', order=1, max_length=50, value='Default')
        field_b = TextField(label='Obs', required=False, key='obs', order=2, max_length=50)
        sec = Section(section_id=1, fields=[field_a, field_b], is_duplicable=True)
        form = make_form(sections=[sec], justification=justification)
        form.status = FormStatus.IN_PROGRESS
        with pytest.raises(EntityError):
            form.apply_field_values([
                # instância 1 criada, mas 'nome' (obrigatório, com valor 'Default' herdado
                # da base) não é enviado para esta instância
                {"section_id": 1, "section_instance": 1, "field_key": "obs", "value": "tb ok"},
            ])

    def test_apply_field_values_duplicate_instance_clears_inherited_value(self):
        """Confirma que o clone realmente zera o valor herdado (não só que a validação falha).
        'nome' não é enviado para a instância 1 — sem o fix, ficaria com 'Default' herdado."""
        field_a = TextField(label='Nome', required=False, key='nome', order=1, max_length=50, value='Default')
        field_b = TextField(label='Obs', required=False, key='obs', order=2, max_length=50)
        sec = Section(section_id=1, fields=[field_a, field_b], is_duplicable=True)
        form = make_form(sections=[sec], justification=justification)
        form.status = FormStatus.IN_PROGRESS
        form.apply_field_values([
            {"section_id": 1, "section_instance": 1, "field_key": "obs", "value": "novo"},
        ])
        instance_0 = next(s for s in form.sections if s.section_instance == 0)
        instance_1 = next(s for s in form.sections if s.section_instance == 1)
        assert instance_0.fields[0].value == "Default"
        assert instance_1.fields[0].value is None

    def test_apply_field_values_section_instance_default_zero(self):
        """Campos sem section_instance devem usar instância 0 (retrocompatibilidade)."""
        form = self._make_duplicable_form()
        form.status = FormStatus.IN_PROGRESS
        form.apply_field_values([
            {"section_id": 1, "field_key": "nome", "value": "João"},
            {"section_id": 1, "field_key": "obs", "value": "ok"},
        ])
        assert form.sections[0].fields[0].value == "João"


class TestFormUberlandiaFields:
    """Especificação Uberlândia §6/§8: `user_id` opcional (pool) + campos novos."""

    def test_accepts_user_id_none(self):
        form = make_form(user_id=None, justification=justification)
        assert form.user_id is None

    def test_rejects_invalid_user_id_when_not_none(self):
        with pytest.raises(EntityError):
            make_form(user_id="not-a-valid-uuid", justification=justification)

    def test_new_fields_default_to_none_or_empty(self):
        form = make_form(justification=justification)
        assert form.external_id is None
        assert form.origin is None
        assert form.service_type is None
        assert form.occurred_at is None
        assert form.scheduled_start_at is None
        assert form.scheduled_end_at is None
        assert form.attributes == {}
        assert form.completed_by is None

    def test_accepts_all_new_fields_set(self):
        form = make_form(
            external_id="OS-7514",
            origin=FormOrigin.CITIZEN,
            service_type="tapa-buraco",
            occurred_at=1,
            scheduled_start_at=2,
            scheduled_end_at=3,
            attributes={"bairro": ["Santa Mônica"]},
            justification=justification,
        )
        assert form.external_id == "OS-7514"
        assert form.origin == FormOrigin.CITIZEN
        assert form.attributes == {"bairro": ["Santa Mônica"]}

    def test_rejects_malformed_attributes(self):
        with pytest.raises(EntityError):
            make_form(attributes={"bairro": "Santa Mônica"}, justification=justification)

    def test_rejects_origin_not_enum(self):
        with pytest.raises(EntityError):
            make_form(origin="CITIZEN", justification=justification)

    def test_complete_sets_completed_by(self):
        form = make_form(status=FormStatus.IN_PROGRESS, justification=justification)
        form.complete(completed_at=1, updated_at=1, completed_by=valid_id)
        assert form.completed_by == valid_id

    def test_complete_without_completed_by_keeps_none(self):
        form = make_form(status=FormStatus.IN_PROGRESS, justification=justification)
        form.complete(completed_at=1, updated_at=1)
        assert form.completed_by is None

    def test_complete_rejects_invalid_completed_by(self):
        form = make_form(status=FormStatus.IN_PROGRESS, justification=justification)
        with pytest.raises(EntityError):
            form.complete(completed_at=1, updated_at=1, completed_by="not-a-valid-uuid")
