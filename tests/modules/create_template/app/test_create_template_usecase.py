import os
import sys

import pytest

sys.path.append(os.getcwd())

from src.modules.create_template.app.create_template_usecase import CreateTemplateUsecase
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.section import Section
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.infra.repositories.template_repository_mock import TemplateRepositoryMock


class TestCreateTemplateUsecase:
    def _make_section(self):
        field = TextField(label="Name", required=True, key="name", order=0)
        return Section(section_id=1, fields=[field])

    def test_create_template_usecase_success(self):
        repo = TemplateRepositoryMock()
        usecase = CreateTemplateUsecase(repo)

        template = usecase(
            created_by="user-123",
            name="Template X",
            system="GAIA",
            description="Description",
            is_active=True,
            sessions=[self._make_section()],
        )

        assert template.name == "Template X"
        assert template.created_by == "user-123"
        assert len(repo.templates) == 2
        assert repo.templates[-1].id == template.id

    def test_create_template_usecase_empty_sessions(self):
        repo = TemplateRepositoryMock()
        usecase = CreateTemplateUsecase(repo)

        with pytest.raises(EntityError):
            usecase(
                created_by="user-123",
                name="Template X",
                system="GAIA",
                description=None,
                is_active=True,
                sessions=[],
            )

    def test_create_template_usecase_section_without_fields(self):
        repo = TemplateRepositoryMock()
        usecase = CreateTemplateUsecase(repo)

        class SectionWithoutFields:
            def __init__(self):
                self.fields = []

        with pytest.raises(EntityError):
            usecase(
                created_by="user-123",
                name="Template X",
                system="GAIA",
                description=None,
                is_active=True,
                sessions=[SectionWithoutFields()],
            )
