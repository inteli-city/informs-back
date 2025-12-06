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
from boto3.dynamodb.conditions import Key, Attr

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

    def get_all_forms(self, page: int, limit: int, status: Optional[FORM_STATUS] = None, system: Optional[str] = None, user_id: Optional[str] = None, created_at_start: Optional[int] = None, created_at_end: Optional[int] = None, search: Optional[str] = None) -> List[Form]:
        forms: List[Form] = []

        items = []
        filter_expression = None

        if status is not None:
            filter_expression = Attr('status').eq(status.value)
        if system is not None:
            expr = Attr('system').eq(system)
            filter_expression = expr if filter_expression is None else filter_expression & expr
        if created_at_start is not None and created_at_end is not None:
            expr = Attr('created_at').between(Decimal(created_at_start), Decimal(created_at_end))
            filter_expression = expr if filter_expression is None else filter_expression & expr
        elif created_at_start is not None:
            expr = Attr('created_at').gte(Decimal(created_at_start))
            filter_expression = expr if filter_expression is None else filter_expression & expr
        elif created_at_end is not None:
            expr = Attr('created_at').lte(Decimal(created_at_end))
            filter_expression = expr if filter_expression is None else filter_expression & expr

        if user_id is not None:
            query = Key("GSI1PK").eq(self.form_gsi1_partition_key_format(user_id))
            query_kwargs = {
                "key_condition_expression": query,
                "IndexName": "GSI1",
                "Select": 'ALL_ATTRIBUTES'
            }
            if filter_expression is not None:
                query_kwargs["FilterExpression"] = filter_expression
            resp = self.dynamo.query(**query_kwargs)
            items = resp.get('Items', [])
        else:
            if filter_expression is not None:
                resp = self.dynamo.scan_items(filter_expression=filter_expression)
            else:
                resp = self.dynamo.get_all_items()
            items = resp.get('Items', [])

        for item in items:
            forms.append(FormDynamoDTO.from_dynamo(item).to_entity())

        if search is not None:
            search_lower = search.lower()
            forms = [
                form for form in forms
                if search_lower in form.form_title.lower() or (form.observation or "").lower().find(search_lower) != -1
            ]

        def sort_key(f: Form):
            is_open = f.status not in [FORM_STATUS.COMPLETED, FORM_STATUS.CANCELLED]
            return (is_open, int(f.priority.value), f.created_at)

        forms.sort(key=sort_key, reverse=True)

        start = (page - 1) * limit
        end = start + limit
        return forms[start:end]

    def create_form(self, form: Form) -> Form:
        item = FormDynamoDTO.from_entity(form).to_dynamo()

        item["GSI1PK"] = self.form_gsi1_partition_key_format(form.user_id)
        item["GSI1SK"] = self.form_gsi1_sort_key_format(priority=form.priority.value, status=form.status, created_at=form.created_at)

        self.dynamo.put_item(
            item=item,
            partition_key=self.form_partition_key_format(form.id),
            sort_key=self.form_sort_key_format(),
            is_decimal=True
        )
        
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
        update_dict = {}

        def _put(key, value):
            if value is None:
                return
            if isinstance(value, FORM_STATUS):
                update_dict[key] = value.value
            elif isinstance(value, Justification):
                update_dict[key] = JustificationDTO.from_entity(value).to_dynamo()
            elif isinstance(value, list) and value and isinstance(value[0], Section):
                update_dict[key] = [SectionDTO.from_entity(section).to_dynamo() for section in value]
            elif isinstance(value, (int, float)):
                update_dict[key] = Decimal(str(value))
            else:
                update_dict[key] = value

        _put("status", status)
        _put("in_progress_at", in_progress_at)
        _put("completed_at", completed_at)
        _put("cancelled_at", cancelled_at)
        _put("updated_at", updated_at)
        _put("sections", sections)
        _put("justification", justification)

        resp = self.dynamo.update_item(
            partition_key=self.form_partition_key_format(form_id),
            sort_key=self.form_sort_key_format(form_id),
            update_dict=update_dict
        )

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
    
