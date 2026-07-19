import os
import sys

sys.path.append(os.getcwd())

from src.modules.get_form.app.get_form_viewmodel import GetFormViewmodel
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock


class Test_GetFormViewmodel:
    def test_get_form_viewmodel(self):
        repo = FormRepositoryMock()
        form = repo.forms[0]

        viewmodel = GetFormViewmodel(form).to_dict()

        assert viewmodel['id'] == form.id
        assert viewmodel['status'] == form.status.value
        assert viewmodel['sections'][0]['section_id'] == form.sections[0].section_id
        assert viewmodel['sections'][0]['section_instance'] == 0
        assert viewmodel['sections'][0]['is_duplicable'] is False
        assert viewmodel['justification']['options'][0]['option'] == form.justification.options[0].option
        assert viewmodel['priority'] == form.priority.value
        assert viewmodel['observation'] == form.observation
        assert viewmodel['created_by'] == form.created_by
        assert viewmodel['created_at'] == form.created_at
        assert viewmodel['in_progress_at'] == form.in_progress_at
        assert viewmodel['completed_at'] == form.completed_at
        assert viewmodel['cancelled_at'] == form.cancelled_at

    def test_get_form_viewmodel_with_duplicated_sections(self):
        """Instâncias duplicadas devem sair no GET com seu section_instance real, não o default 0."""
        repo = FormRepositoryMock()
        form = repo.forms[0]

        field = TextField(label='Nome', required=True, key='nome', order=1, max_length=50, value='João')
        field_dup = TextField(label='Nome', required=True, key='nome', order=1, max_length=50, value='Maria')
        form.sections = [
            Section(section_id=1, fields=[field], is_duplicable=True, section_instance=0),
            Section(section_id=1, fields=[field_dup], is_duplicable=True, section_instance=1),
        ]

        viewmodel = GetFormViewmodel(form).to_dict()

        sections = viewmodel['sections']
        assert len(sections) == 2
        assert sections[0]['section_instance'] == 0
        assert sections[1]['section_instance'] == 1
        assert all(s['is_duplicable'] is True for s in sections)
        assert sections[1]['fields'][0]['value'] == 'Maria'
