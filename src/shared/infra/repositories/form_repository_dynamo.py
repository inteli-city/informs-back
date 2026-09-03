from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple, Union
from botocore.exceptions import ClientError

from src.shared.domain.entities.form import Form
from src.shared.domain.entities.justification import Justification
from src.shared.domain.entities.section import Section
from src.shared.domain.enums.form_status_enum import FormStatus
from src.shared.domain.repositories.form_repository_interface import IFormRepository
from src.shared.environments import Environments
from src.shared.infra.dtos.form_dynamo_dto import FormDynamoDTO
from src.shared.infra.dtos.justification_dto import JustificationDTO
from src.shared.infra.dtos.section_dto import SectionDTO
from src.shared.infra.external.dynamo.conditions import Attr, Key
from src.shared.infra.external.dynamo.datasources.dynamo_datasource import DynamoDatasource
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction
from src.shared.helpers.functions.pagination_token import encode_pagination_token

class FormRepositoryDynamo(IFormRepository):

    @staticmethod
    def form_partition_key_format(form_id: str) -> str:
        return f'form#{form_id}'
    
    @staticmethod
    def form_sort_key_format() -> str:
        return 'METADATA'

    @staticmethod 
    def form_gsi1_partition_key_format(user_id: str) -> str:
        return f'user#{user_id}'
    
    @staticmethod
    def form_gsi1_sort_key_format(priority: str, status: FormStatus, created_at: int) -> str:
        return f'priority#{priority}#status#{status.value}#created_at#{created_at}'

    @staticmethod
    def form_gsi2_partition_key_format(system: str) -> str:
        return f"system#{system}"

    @staticmethod
    def form_gsi2_sort_key_format(updated_at: int, form_id: str) -> str:
        return f"updated_at#{int(updated_at):013d}#form#{form_id}"

    @staticmethod
    def form_external_id_lock_partition_key_format(system: str, external_id: str) -> str:
        return f"externalid#{system}#{external_id}"

    @staticmethod
    def form_external_id_lock_sort_key_format() -> str:
        return "LOCK"

    def __init__(self):
        self.dynamo = DynamoDatasource(
            endpoint_url=Environments.get_envs().endpoint_url,
            dynamo_table_name=Environments.get_envs().dynamo_table_name,
            region=Environments.get_envs().region,
            partition_key=Environments.get_envs().dynamo_partition_key,
            sort_key=Environments.get_envs().dynamo_sort_key,
        )
    
    def get_form_by_id(self, user_id: str, form_id: str) -> Optional[Form]:
        form = self.dynamo.get_item(partition_key=self.form_partition_key_format(form_id), sort_key=self.form_sort_key_format())
        if "Item" not in form:
            return None

        return FormDynamoDTO.from_dynamo(form['Item']).to_entity()

    def get_form_by_user_id(self, user_id: str) -> List[Form]:
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
        status: Optional[Union[FormStatus, List[FormStatus]]] = None,
        system: Optional[Union[str, List[str]]] = None,
        user_id: Optional[str] = None,
        created_at_start: Optional[int] = None,
        created_at_end: Optional[int] = None,
        updated_at_start: Optional[int] = None,
        updated_at_end: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Form], Optional[str]]:
        forms: List[Form] = []

        filter_expression = self._build_forms_filter_expression(
            status, system, created_at_start, created_at_end, updated_at_start, updated_at_end
        )
        # limit paginado só se aplica via Dynamo quando não há busca textual
        # (search é filtrado pós-query, então precisamos varrer tudo).
        use_dynamo_limit = limit is not None and search is None

        if user_id is not None:
            items, start_key = self._query_forms_by_user(
                user_id, filter_expression, exclusive_start_key, limit, use_dynamo_limit
            )
        else:
            items, start_key = self._scan_forms(
                filter_expression, exclusive_start_key, limit, use_dynamo_limit
            )

        for item in items:
            forms.append(FormDynamoDTO.from_dynamo(item).to_entity())

        if search is not None:
            search_lower = search.lower()
            forms = [
                form for form in forms
                if search_lower in form.form_title.lower() or search_lower in (form.observation or "").lower()
            ]

        def sort_key(f: Form):
            is_open = f.status not in [FormStatus.COMPLETED, FormStatus.CANCELLED]
            return (is_open, int(f.priority.value), f.created_at)

        forms.sort(key=sort_key, reverse=True)
        if limit is not None and search is not None:
            forms = forms[:limit]

        next_key = start_key if use_dynamo_limit else None
        return forms, encode_pagination_token(next_key)

    @staticmethod
    def _and(base, expr):
        return expr if base is None else base & expr

    @staticmethod
    def _status_filter(status):
        if status is None:
            return None
        if not isinstance(status, list):
            return Attr('status').eq(status.value)
        status_filter = None
        for status_item in status:
            status_filter = FormRepositoryDynamo._or(status_filter, Attr('status').eq(status_item.value))
        return status_filter

    @staticmethod
    def _or(base, expr):
        return expr if base is None else base | expr

    @staticmethod
    def _system_filter(system):
        if system is None:
            return None
        if not isinstance(system, list):
            return Attr('system').eq(system)
        system_filter = None
        for system_item in system:
            system_filter = FormRepositoryDynamo._or(system_filter, Attr('system').eq(system_item))
        return system_filter

    @staticmethod
    def _created_at_filter(created_at_start, created_at_end):
        if created_at_start is not None and created_at_end is not None:
            return Attr('created_at').between(Decimal(created_at_start), Decimal(created_at_end))
        if created_at_start is not None:
            return Attr('created_at').gte(Decimal(created_at_start))
        if created_at_end is not None:
            return Attr('created_at').lte(Decimal(created_at_end))
        return None

    @staticmethod
    def _updated_at_filter(updated_at_start, updated_at_end):
        if updated_at_start is not None and updated_at_end is not None:
            return Attr('updated_at').between(Decimal(updated_at_start), Decimal(updated_at_end))
        if updated_at_start is not None:
            return Attr('updated_at').gte(Decimal(updated_at_start))
        if updated_at_end is not None:
            return Attr('updated_at').lte(Decimal(updated_at_end))
        return None

    @staticmethod
    def _build_forms_filter_expression(
        status, system, created_at_start, created_at_end, updated_at_start=None, updated_at_end=None
    ):
        filter_expression = None
        for part in (
            FormRepositoryDynamo._status_filter(status),
            FormRepositoryDynamo._system_filter(system),
            FormRepositoryDynamo._created_at_filter(created_at_start, created_at_end),
            FormRepositoryDynamo._updated_at_filter(updated_at_start, updated_at_end),
        ):
            if part is not None:
                filter_expression = FormRepositoryDynamo._and(filter_expression, part)
        return filter_expression

    @staticmethod
    def _apply_pagination_kwargs(kwargs: dict, items: list, start_key, limit, use_dynamo_limit) -> bool:
        """Ajusta Limit/ExclusiveStartKey no kwargs. Retorna False se deve parar."""
        if use_dynamo_limit:
            remaining = limit - len(items)
            if remaining <= 0:
                return False
            kwargs["Limit"] = remaining
        else:
            kwargs.pop("Limit", None)
        if start_key is not None:
            kwargs["ExclusiveStartKey"] = start_key
        else:
            kwargs.pop("ExclusiveStartKey", None)
        return True

    def _query_forms_by_user(self, user_id, filter_expression, exclusive_start_key, limit, use_dynamo_limit):
        query = Key("GSI1PK").eq(self.form_gsi1_partition_key_format(user_id))
        query_kwargs = {
            "key_condition_expression": query,
            "IndexName": "UserPriorityIndex",
            "Select": "ALL_ATTRIBUTES",
        }
        if filter_expression is not None:
            query_kwargs["FilterExpression"] = filter_expression

        items = []
        start_key = exclusive_start_key
        while True:
            if not self._apply_pagination_kwargs(query_kwargs, items, start_key, limit, use_dynamo_limit):
                break
            resp = self.dynamo.query(**query_kwargs)
            items.extend(resp.get("Items", []))
            start_key = resp.get("LastEvaluatedKey")
            if start_key is None:
                break
        return items, start_key

    def _scan_forms(self, filter_expression, exclusive_start_key, limit, use_dynamo_limit):
        scan_kwargs = {"Select": "ALL_ATTRIBUTES"}
        items = []
        start_key = exclusive_start_key
        while True:
            if not self._apply_pagination_kwargs(scan_kwargs, items, start_key, limit, use_dynamo_limit):
                break
            if filter_expression is not None:
                resp = self.dynamo.scan_items(filter_expression=filter_expression, **scan_kwargs)
            else:
                resp = self.dynamo.dynamo_table.scan(**scan_kwargs)
            items.extend(resp.get("Items", []))
            start_key = resp.get("LastEvaluatedKey")
            if start_key is None:
                break
        return items, start_key

    def get_form_by_external_id(self, system: str, external_id: str) -> Optional[Form]:
        lock = self.dynamo.get_item(
            partition_key=self.form_external_id_lock_partition_key_format(system, external_id),
            sort_key=self.form_external_id_lock_sort_key_format(),
        )
        form_id = lock.get("Item", {}).get("form_id")
        if not form_id:
            return None
        return self.get_form_by_id(user_id="", form_id=form_id)

    def _claim_external_id(self, form: Form) -> Optional[Form]:
        """Reivindica o par (system, external_id) para este form_id via lock
        atômico. Retorna o form já existente se outra chamada já o criou
        (idempotência de `POST /forms`, especificação Uberlândia §9.1); `None`
        se o lock foi conquistado por este form.
        """
        lock_pk = self.form_external_id_lock_partition_key_format(form.system, form.external_id)
        try:
            self.dynamo.put_item(
                item={"form_id": form.id},
                partition_key=lock_pk,
                sort_key=self.form_external_id_lock_sort_key_format(),
                ConditionExpression="attribute_not_exists(PK)",
            )
            return None
        except ClientError as err:
            if err.response.get("Error", {}).get("Code") != "ConditionalCheckFailedException":
                raise

        existing = self.get_form_by_external_id(form.system, form.external_id)
        if existing is None:
            # Janela rara: o lock foi gravado mas o form correspondente ainda
            # não (crash/timeout entre as duas escritas). Pede retry em vez
            # de duplicar ou travar o external_id para sempre.
            raise DuplicatedItem(
                "Formulário com este external_id está sendo criado por outra requisição; tente novamente em instantes"
            )
        return existing

    def create_form(self, form: Form) -> Form:
        if form.external_id is not None:
            existing = self._claim_external_id(form)
            if existing is not None:
                return existing

        item = FormDynamoDTO.from_entity(form).to_dynamo()

        if form.user_id is not None:
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
        status: Optional[FormStatus] = None,
        in_progress_at: Optional[int] = None,
        completed_at: Optional[int] = None,
        cancelled_at: Optional[int] = None,
        updated_at: Optional[int] = None,
        sections: Optional[List[Section]] = None,
        justification: Optional[Justification] = None,
        expected_status: Optional[FormStatus] = None,
        completed_by: Optional[str] = None,
    ) -> Optional[Form]:
        update_dict = {}
        current_form = self.get_form_by_id(user_id=user_id, form_id=form_id)

        candidate_updates = {
            "status": status,
            "in_progress_at": in_progress_at,
            "completed_at": completed_at,
            "cancelled_at": cancelled_at,
            "updated_at": updated_at,
            "sections": sections,
            "justification": justification,
            "completed_by": completed_by,
        }
        for key, value in candidate_updates.items():
            if value is not None:
                update_dict[key] = self._coerce_update_value(value)
        if current_form is not None:
            update_dict["GSI2PK"] = self.form_gsi2_partition_key_format(current_form.system)
            if updated_at is not None:
                update_dict["GSI2SK"] = self.form_gsi2_sort_key_format(updated_at=updated_at, form_id=form_id)

        condition_expression = Attr("status").eq(expected_status.value) if expected_status is not None else None
        try:
            resp = self.dynamo.update_item(
                partition_key=self.form_partition_key_format(form_id),
                sort_key=self.form_sort_key_format(),
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

    @staticmethod
    def _coerce_update_value(value):
        if isinstance(value, FormStatus):
            return value.value
        if isinstance(value, Justification):
            return JustificationDTO.from_entity(value).to_dynamo()
        if isinstance(value, list) and value and isinstance(value[0], Section):
            return [SectionDTO.from_entity(section).to_dynamo() for section in value]
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        return value

    def get_forms_updated_since(
        self,
        system: str,
        updated_at_start: int,
        updated_at_end: Optional[int] = None,
        limit: Optional[int] = None,
        exclusive_start_key: Optional[dict] = None,
        status: Optional[Union[FormStatus, List[FormStatus]]] = None,
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
        status_filter = self._status_filter(status)
        if status_filter is not None:
            query_kwargs["FilterExpression"] = status_filter

        # Dynamo aplica Limit ANTES do FilterExpression: uma única chamada podia
        # devolver 0 formulários casando o status pedido (mas com
        # LastEvaluatedKey ainda presente), como se a janela tivesse acabado.
        # O loop, igual a _query_forms_by_user/_scan_forms, insiste até juntar
        # `limit` itens já filtrados ou esgotar a janela de verdade.
        use_dynamo_limit = limit is not None
        items: List[dict] = []
        page_start_key = exclusive_start_key
        while True:
            if not self._apply_pagination_kwargs(query_kwargs, items, page_start_key, limit, use_dynamo_limit):
                break
            resp = self.dynamo.query(**query_kwargs)
            items.extend(resp.get("Items", []))
            page_start_key = resp.get("LastEvaluatedKey")
            if page_start_key is None:
                break

        forms = [FormDynamoDTO.from_dynamo(item).to_entity() for item in items]
        return forms, encode_pagination_token(page_start_key)
