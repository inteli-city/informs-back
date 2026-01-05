from src.shared.domain.entities.form import Form
from src.shared.domain.repositories.queue_repository_interface import IQueueRepository
from src.shared.infra.dtos.form_dynamo_dto import FormDynamoDTO


class QueueRepositoryMock(IQueueRepository):

    def __init__(self):
        self.messages = []

    def send_form(self, form: Form) -> None:
        payload = FormDynamoDTO.from_entity(form).to_dynamo()
        self.messages.append({"system": form.system, "payload": payload})
