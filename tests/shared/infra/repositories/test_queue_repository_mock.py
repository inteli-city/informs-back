from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.queue_repository_mock import QueueRepositoryMock


def test_queue_repository_mock_stores_message():
    form_repo = FormRepositoryMock()
    queue_repo = QueueRepositoryMock()

    form = form_repo.forms[0]
    queue_repo.send_form(form)

    assert len(queue_repo.messages) == 1
    message = queue_repo.messages[0]
    assert message["system"] == form.system
    assert message["payload"]["form_id"] == form.form_id
    assert message["payload"]["sections"]
