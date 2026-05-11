from typing import Any

from pydantic import AliasChoices, Field, StrictBool, field_validator, model_validator

from src.shared.helpers.contracts.base import RequestContractModel
from src.shared.helpers.contracts.endpoints.cancel_form_contract import CancelFormRequestSchema
from src.shared.helpers.contracts.endpoints.create_form_contract import CreateFormRequestSchema
from src.shared.helpers.contracts.endpoints.create_template_contract import CreateTemplateRequestSchema
from src.shared.helpers.contracts.endpoints.plan_route_contract import PlanRouteRequestSchema
from src.shared.helpers.contracts.endpoints.start_form_contract import StartFormRequestSchema
from src.shared.helpers.contracts.endpoints.submit_form_contract import SubmitFormFieldFlatSchema, SubmitFormRequestSchema
from src.shared.helpers.contracts.schemas.template import TemplateSectionSchema


class RequesterUserSchema(RequestContractModel):
    sub: str
    name: str
    email: str
    cognito_groups: str = Field(
        validation_alias=AliasChoices("cognito:groups", "cognito_groups"),
        serialization_alias="cognito:groups",
    )


class CreateFormControllerRequestSchema(CreateFormRequestSchema):
    requester_user: RequesterUserSchema
    number: int | None = None


class CancelFormControllerRequestSchema(CancelFormRequestSchema):
    requester_user: RequesterUserSchema
    form_id: str


class CreateTemplateControllerRequestSchema(CreateTemplateRequestSchema):
    requester_user: RequesterUserSchema


class UpdateTemplateControllerRequestSchema(RequestContractModel):
    requester_user: RequesterUserSchema
    template_id: str
    name: str | None = None
    system: str | None = None
    description: str | None = None
    is_active: StrictBool | None = Field(
        default=None,
        validation_alias=AliasChoices("is_active", "isActive"),
        serialization_alias="is_active",
    )
    sections: list[TemplateSectionSchema] | None = None


class StartFormControllerRequestSchema(StartFormRequestSchema):
    requester_user: RequesterUserSchema
    form_id: str


class SubmitFormFieldFlatControllerSchema(SubmitFormFieldFlatSchema):
    @field_validator("section_id", mode="before")
    @classmethod
    def _ensure_section_id_int(cls, value: Any) -> Any:
        if isinstance(value, bool):
            raise ValueError("section_id")
        if isinstance(value, str) and value.isdigit():
            return int(value)
        if not isinstance(value, int):
            raise ValueError("section_id")
        return value

    @model_validator(mode="before")
    @classmethod
    def _ensure_value_key_is_present(cls, values: Any) -> Any:
        if isinstance(values, dict) and "value" not in values:
            raise ValueError("value")
        return values


class SubmitFormControllerRequestSchema(SubmitFormRequestSchema):
    requester_user: RequesterUserSchema
    form_id: str
    fields: list[SubmitFormFieldFlatControllerSchema]


class PlanRouteControllerRequestSchema(PlanRouteRequestSchema):
    requester_user: RequesterUserSchema


class GetFormControllerRequestSchema(RequestContractModel):
    requester_user: RequesterUserSchema
    form_id: str


class GetTemplateControllerRequestSchema(RequestContractModel):
    requester_user: RequesterUserSchema
    template_id: str


class GetAllFormsControllerRequestSchema(RequestContractModel):
    requester_user: RequesterUserSchema
    limit: int | None = None
    status: str | list[str] | None = None
    system: str | list[str] | None = None
    search: str | None = None
    created_at_start: int | None = None
    created_at_end: int | None = None
    exclusive_start_key: str | None = None

    @field_validator("limit", "created_at_start", "created_at_end", mode="before")
    @classmethod
    def _parse_optional_int(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, bool):
            raise ValueError("int")
        if isinstance(value, str):
            if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
                return int(value)
            raise ValueError("int")
        if not isinstance(value, int):
            raise ValueError("int")
        return value


class GetAllTemplatesControllerRequestSchema(RequestContractModel):
    requester_user: RequesterUserSchema
    limit: int | None = None
    is_active: StrictBool | None = None
    system: str | list[str] | None = None
    name: str | None = None
    exclusive_start_key: str | None = None

    @field_validator("limit", mode="before")
    @classmethod
    def _parse_limit(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, bool):
            raise ValueError("int")
        if isinstance(value, str):
            stripped = value.strip()
            if stripped == "":
                return None
            if stripped.isdigit() or (stripped.startswith("-") and stripped[1:].isdigit()):
                return int(stripped)
            raise ValueError("int")
        if not isinstance(value, int):
            raise ValueError("int")
        return value
