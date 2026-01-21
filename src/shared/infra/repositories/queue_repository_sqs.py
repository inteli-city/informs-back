import json
from decimal import Decimal
import os

import boto3

from src.shared.domain.entities.form import Form
from src.shared.domain.repositories.queue_repository_interface import IQueueRepository
from src.shared.environments import Environments
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.infra.dtos.form_dynamo_dto import FormDynamoDTO


class QueueRepositorySQS(IQueueRepository):

    def __init__(self):
        client_kwargs = {"region_name": Environments.get_envs().region}
        endpoint_url = Environments.get_envs().sqs_endpoint_url
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url
        self.client = boto3.client("sqs", **client_kwargs)
        self._queue_urls = {}
        self._queue_names = {
            "GAIA": os.environ.get("GAIA_QUEUE_NAME", "FormulariosStackdev-Gaia-Queue"),
            "GIPAV": os.environ.get("GIPAV_QUEUE_NAME", "FormulariosStackdev-GIPAV-Queue"),
        }

    def _get_queue_url(self, queue_name: str) -> str:
        if queue_name in self._queue_urls:
            return self._queue_urls[queue_name]
        response = self.client.get_queue_url(QueueName=queue_name)
        queue_url = response["QueueUrl"]
        self._queue_urls[queue_name] = queue_url
        return queue_url

    def send_form(self, form: Form) -> None:
        queue_name = self._queue_names.get(form.system)
        if queue_name is None:
            raise EntityError("system")

        queue_url = self._get_queue_url(queue_name)
        payload = FormDynamoDTO.from_entity(form).to_dynamo()
        def _json_default(value):
            if isinstance(value, Decimal):
                return int(value) if value % 1 == 0 else float(value)
            raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")
        self.client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(payload, ensure_ascii=True, default=_json_default)
        )
