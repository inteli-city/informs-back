from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple, Union
from botocore.exceptions import ClientError
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
from src.shared.helpers.functions.pagination_token import encode_pagination_token
from src.shared.helpers.errors.usecase_errors import ForbiddenAction
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

    @staticmethod
    def form_gsi2_partition_key_format(system: str) -> str:
        return f"system#{system}"

    @staticmethod
    def form_gsi2_sort_key_format(updated_at: int, form_id: str) -> str:
        return f"updated_at#{int(updated_at):013d}#form#{form_id}"


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

    def get_all_forms(
        self,
        limit: Optional[int],
        exclusive_start_key: Optional[dict] = None,
        status: Optional[Union[FORM_STATUS, List[FORM_STATUS]]] = None,
        system: Optional[Union[str, List[str]]] = None,
        user_id: Optional[str] = None,
        created_at_start: Optional[int] = None,
        created_at_end: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Form], Optional[str]]:
        forms: List[Form] = []

        items = []
        filter_expression = None

        if status is not None:
            if isinstance(status, list):
                if status:
                    status_filter = None
                    for status_item in status:
                        expr = Attr('status').eq(status_item.value)
                        status_filter = expr if status_filter is None else status_filter | expr
                    filter_expression = status_filter
            else:
                filter_expression = Attr('status').eq(status.value)
        if system is not None:
            if isinstance(system, list):
                if system:
                    system_filter = None
                    for system_item in system:
                        expr = Attr('system').eq(system_item)
                        system_filter = expr if system_filter is None else system_filter | expr
                    if system_filter is not None:
                        filter_expression = system_filter if filter_expression is None else filter_expression & system_filter
            else:
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
                "IndexName": "UserPriorityIndex",
                "Select": "ALL_ATTRIBUTES",
            }
            if filter_expression is not None:
                query_kwargs["FilterExpression"] = filter_expression
            start_key = exclusive_start_key
            while True:
                if limit is not None and search is None:
                    remaining = limit - len(items)
                    if remaining <= 0:
                        break
                    query_kwargs["Limit"] = remaining
                else:
                    query_kwargs.pop("Limit", None)
                if start_key is not None:
                    query_kwargs["ExclusiveStartKey"] = start_key
                else:
                    query_kwargs.pop("ExclusiveStartKey", None)
                resp = self.dynamo.query(**query_kwargs)
                items.extend(resp.get("Items", []))
                start_key = resp.get("LastEvaluatedKey")
                if start_key is None:
                    break
        else:
            scan_kwargs = {
                "Select": "ALL_ATTRIBUTES",
            }
            start_key = exclusive_start_key
            while True:
                if limit is not None and search is None:
                    remaining = limit - len(items)
                    if remaining <= 0:
                        break
                    scan_kwargs["Limit"] = remaining
                else:
                    scan_kwargs.pop("Limit", None)
                if start_key is not None:
                    scan_kwargs["ExclusiveStartKey"] = start_key
                else:
                    scan_kwargs.pop("ExclusiveStartKey", None)
                if filter_expression is not None:
                    resp = self.dynamo.scan_items(filter_expression=filter_expression, **scan_kwargs)
                else:
                    resp = self.dynamo.dynamo_table.scan(**scan_kwargs)
                items.extend(resp.get("Items", []))
                start_key = resp.get("LastEvaluatedKey")
                if start_key is None:
                    break

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
        if limit is not None and search is not None:
            forms = forms[:limit]

        next_key = start_key if limit is not None and search is None else None
        return forms, encode_pagination_token(next_key)

    def create_form(self, form: Form) -> Form:
        item = FormDynamoDTO.from_entity(form).to_dynamo()

        item["GSI1PK"] = self.form_gsi1_partition_key_format(form.user_id)
        item["GSI1SK"] = self.form_gsi1_sort_key_format(priority=form.priority.value, status=form.status, created_at=form.created_at)
        item["GSI2PK"] = self.form_gsi2_partition_key_format(form.system)
        item["GSI2SK"] = self.form_gsi2_sort_key_format(updated_at=form.updated_at, form_id=form.id)

        self.dynamo.put_item(
            item=item,
            partition_key=self.form_partition_key_format(form.id),
            sort_key=self.form_sort_key_format()
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
        expected_status: Optional[FORM_STATUS] = None,
    ) -> Form:
        update_dict = {}
        current_form = self.get_form_by_id(user_id=user_id, form_id=form_id)

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
        if current_form is not None:
            update_dict["GSI2PK"] = self.form_gsi2_partition_key_format(current_form.system)
            if updated_at is not None:
                update_dict["GSI2SK"] = self.form_gsi2_sort_key_format(updated_at=updated_at, form_id=form_id)

        condition_expression = Attr("status").eq(expected_status.value) if expected_status is not None else None
        try:
            resp = self.dynamo.update_item(
                partition_key=self.form_partition_key_format(form_id),
                sort_key=self.form_sort_key_format(form_id),
                update_dict=update_dict,
                condition_expression=condition_expression,
            )
        except ClientError as err:
            error_code = err.response.get("Error", {}).get("Code")
            if error_code == "ConditionalCheckFailedException":
                raise ForbiddenAction("Formulário foi atualizado por outra operação")
            raise

        if "Attributes" not in resp:
            return None
        
        return FormDynamoDTO.from_dynamo(resp['Attributes']).to_entity()

    def get_forms_updated_since(
        self,
        system: str,
        updated_at_start: int,
        updated_at_end: Optional[int] = None,
        limit: Optional[int] = None,
        exclusive_start_key: Optional[dict] = None,
    ) -> Tuple[List[Form], Optional[str]]:
        start_ms = max(0, int(updated_at_start))
        end_ms = int(updated_at_end) if updated_at_end is not None else int(datetime.now(timezone.utc).timestamp() * 1000)

        start_key = self.form_gsi2_sort_key_format(updated_at=start_ms, form_id="")
        end_key = self.form_gsi2_sort_key_format(updated_at=end_ms, form_id="~")
        query_kwargs = {
            "key_condition_expression": Key("GSI2PK").eq(self.form_gsi2_partition_key_format(system))
            & Key("GSI2SK").between(start_key, end_key),
            "IndexName": "SystemUpdatedAtIndex",
            "Select": "ALL_ATTRIBUTES",
            "ScanIndexForward": True,
        }
        if limit is not None:
            query_kwargs["Limit"] = limit
        if exclusive_start_key is not None:
            query_kwargs["ExclusiveStartKey"] = exclusive_start_key

        resp = self.dynamo.query(**query_kwargs)
        items = resp.get("Items", [])
        forms = [FormDynamoDTO.from_dynamo(item).to_entity() for item in items]
        next_key = resp.get("LastEvaluatedKey")
        return forms, encode_pagination_token(next_key)
