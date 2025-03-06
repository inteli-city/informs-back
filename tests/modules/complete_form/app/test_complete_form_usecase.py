import pytest
from src.modules.complete_form.app.complete_form_usecase import CompleteFormUsecase
from src.shared.domain.entities.field import TextField
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.image_repository_mock import ImageRepositoryMock


class Test_CompleteFormUsecase:

    def test_complete_form_usecase(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CompleteFormUsecase(repo, image_repo)

        form = repo.forms[0]
        
        text_field = TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='poggers')

        sections = [
            Section(
                section_id='1',
                fields=[text_field]
            )
        ]

        result = usecase(user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001', form_id=form.form_id, sections=sections, vinculation_form_id='d61dbf66-a10f-11ed-a8fc-0242ac120011')

        assert result.status == FORM_STATUS.CONCLUDED
        assert result.vinculation_form_id == 'd61dbf66-a10f-11ed-a8fc-0242ac120011'
        assert result.sections[0].fields[0].value == 'poggers'
    
    def test_complete_form_usecase_vinculation_id_none(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CompleteFormUsecase(repo, image_repo)

        form = repo.forms[0]
        
        text_field = TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='poggers')

        sections = [
            Section(
                section_id='1',
                fields=[text_field]
            )
        ]

        result = usecase(user_id='d61dbf66-a10f-11ed-a8fc-0242ac120001', form_id=form.form_id, sections=sections)

        assert result.status == FORM_STATUS.CONCLUDED
        assert result.vinculation_form_id is None
        assert result.sections[0].fields[0].value == 'poggers'
    
    def test_complete_form_usecase_user_disabled(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CompleteFormUsecase(repo, image_repo)

        form = repo.forms[1]
        
        text_field = TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='poggers')

        sections = [
            Section(
                section_id='1',
                fields=[text_field]
            )
        ]

        with pytest.raises(ForbiddenAction):
            usecase('d61dbf66-a10f-11ed-a8fc-0242ac120001', form.form_id, sections)

    def test_complete_form_usecase_form_not_found(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CompleteFormUsecase(repo, image_repo)

        
        text_field = TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='poggers')

        sections = [
            Section(
                section_id='1',
                fields=[text_field]
            )
        ]

        with pytest.raises(NoItemsFound):
            usecase('d61dbf66-a10f-11ed-a8fc-0242ac120001', '123', sections)
    
    def test_complete_form_usecase_user_not_owner(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CompleteFormUsecase(repo, image_repo)

        form = repo.forms[0]
        
        text_field = TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='poggers')

        sections = [
            Section(
                section_id='1',
                fields=[text_field]
            )
        ]

        with pytest.raises(ForbiddenAction):
            usecase('d61dbf66-a10f-11ed-a8fc-0242ac120002', form.form_id, sections)
    
    def test_complete_form_usecase_form_already_concluded(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CompleteFormUsecase(repo, image_repo)

        form = repo.forms[1]
        
        text_field = TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='poggers')

        sections = [
            Section(
                section_id='1',
                fields=[text_field]
            )
        ]

        with pytest.raises(ForbiddenAction):
            usecase('d61dbf66-a10f-11ed-a8fc-0242ac120001', form.form_id, sections)
    
    def test_complete_form_usecase_required_field_not_filled(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CompleteFormUsecase(repo, image_repo)

        form = repo.forms[0]
        
        text_field = TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value=None)

        sections = [
            Section(
                section_id='1',
                fields=[text_field]
            )
        ]

        with pytest.raises(ForbiddenAction):
            usecase('d61dbf66-a10f-11ed-a8fc-0242ac120001', form.form_id, sections)
    
    def test_complete_form_usecase_vinculation_form_not_found(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CompleteFormUsecase(repo, image_repo)

        form = repo.forms[0]
        
        text_field = TextField(placeholder='placeholder', required=True, key='key', regex='regex', formatting='formatting', max_length=10, value='poggers')

        sections = [
            Section(
                section_id='1',
                fields=[text_field]
            )
        ]

        with pytest.raises(NoItemsFound):
            usecase('d61dbf66-a10f-11ed-a8fc-0242ac120001', form.form_id, sections, '123')
    
