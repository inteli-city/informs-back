from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from src.shared.domain.entities.form import Form
from src.shared.domain.entities.justification import Justification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.environments import Environments
from src.shared.infra.dtos.form_dynamo_dto import FormDynamoDTO
from src.shared.infra.dtos.justification_dto import JustificationDTO
from src.shared.infra.dtos.section_dto import SectionDTO
from src.shared.infra.external.dynamo.datasources.dynamo_datasource import DynamoDatasource
from boto3.dynamodb.conditions import Key

class FormRepositoryDynamo(IFormRepository):

    @staticmethod
    def form_partition_key_format(form_id: str) -> str:
        return f'form#{form_id}'
    
    @staticmethod
    def form_sort_key_format(form_id: str = None) -> str:
        return 'METADATA'

    @staticmethod 
    def form_gsi1_partition_key_format(user_id: str) -> str:
        return f'user#{user_id}'
    
    @staticmethod
    def form_gsi1_sort_key_format(priority: str, status: FORM_STATUS, created_at: int) -> str:
        return f'priority#{priority}#status#{status.value}#created_at#{created_at}'

    def __init__(self):
        self.dynamo = DynamoDatasource(
            endpoint_url=Environments.get_envs().endpoint_url,
            dynamo_table_name=Environments.get_envs().dynamo_table_name,
            region=Environments.get_envs().region,
            partition_key=Environments.get_envs().dynamo_partition_key,
            sort_key=Environments.get_envs().dynamo_sort_key,
        )
    
    def get_form_by_id(self, user_id: str, form_id: str) -> Form:
        form = self.dynamo.get_item(partition_key=self.form_partition_key_format(form_id), sort_key=self.form_sort_key_format(form_id))
        if "Item" not in form:
            return None

        return FormDynamoDTO.from_dynamo(form['Item']).to_entity()

    def get_form_by_user_id(self, user_id: str) -> dict:
        query_string = Key(self.dynamo.partition_key).eq(self.form_partition_key_format(user_id))
        resp = self.dynamo.query(key_condition_expression=query_string, Select='ALL_ATTRIBUTES')
        forms = []

        for item in resp['Items']:
            forms.append(FormDynamoDTO.from_dynamo(item).to_entity())
        
        return forms

    def create_form(self, form: Form) -> Form:
        item = FormDynamoDTO.from_entity(form).to_dynamo()

        self.dynamo.put_item(item=item, partition_key=self.form_partition_key_format(form.id), sort_key=self.form_sort_key_format(form.id), is_decimal=True)
        
        return form
    
    def update_form_status(self, user_id: str, form_id: str, status: FORM_STATUS, in_progress_at: Optional[int] = None, updated_at: Optional[int] = None) -> Form:
        update_dict = {
            "status": status.value,
            "in_progress_at": Decimal(in_progress_at) if in_progress_at is not None else None,
            "updated_at": Decimal(updated_at) if updated_at is not None else None
        }

        resp = self.dynamo.update_item(partition_key=self.form_partition_key_format(form_id), sort_key=self.form_sort_key_format(form_id), update_dict=update_dict)
        
        if "Attributes" not in resp:
            return None
        
        return FormDynamoDTO.from_dynamo(resp['Attributes']).to_entity()
    
    def cancel_form(self, user_id: str, form_id: str, justification: Justification, cancelled_at: int, updated_at: int) -> Form:
        
        update_dict = {
            "status": FORM_STATUS.CANCELLED.value,
            "justification": JustificationDTO.from_entity(justification).to_dynamo(),
            "cancelled_at": Decimal(cancelled_at),
            "updated_at": Decimal(updated_at)
        }

        resp = self.dynamo.update_item(partition_key=self.form_partition_key_format(form_id), sort_key=self.form_sort_key_format(form_id), update_dict=update_dict)
        
        if "Attributes" not in resp:
            return None
        
        return FormDynamoDTO.from_dynamo(resp['Attributes']).to_entity()
    
    def complete_form(self, user_id: str, form_id: str, sections: List[Section], completed_at: int, updated_at: int) -> Form:
        update_dict = {
            "status": FORM_STATUS.COMPLETED.value,
            "sections": [
                SectionDTO.from_entity(section).to_dynamo() for section in sections
            ],
            "completed_at": Decimal(completed_at),
            "updated_at": Decimal(updated_at)
        }

        resp = self.dynamo.update_item(partition_key=self.form_partition_key_format(form_id), sort_key=self.form_sort_key_format(form_id), update_dict=update_dict)
        
        if "Attributes" not in resp:
            return None
        
        return FormDynamoDTO.from_dynamo(resp['Attributes']).to_entity()

    def start_form(self, user_id: str, form_id: str, in_progress_at: int, updated_at: int) -> Form:
        update_dict = {
            "status": FORM_STATUS.IN_PROGRESS.value,
            "in_progress_at": Decimal(in_progress_at),
            "updated_at": Decimal(updated_at)
        }

        resp = self.dynamo.update_item(partition_key=self.form_partition_key_format(form_id), sort_key=self.form_sort_key_format(form_id), update_dict=update_dict)
        
        if "Attributes" not in resp:
            return None
        
        return FormDynamoDTO.from_dynamo(resp['Attributes']).to_entity()
