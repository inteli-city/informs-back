from .submit_form_usecase import SubmitFormUsecase
from .submit_form_viewmodel import SubmitFormViewmodel
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import OK, BadRequest, Forbidden, InternalServerError, NotFound
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class SubmitFormController:
    def __init__(self, usecase: SubmitFormUsecase):
        self.submit_form_usecase = usecase

    def _validate_requester_user(self, data: dict) -> UserGatewayDTO:
        requester_user = data.get("requester_user")
        if requester_user is None:
            raise MissingParameters("requester_user")
        return UserGatewayDTO.from_api_gateway(requester_user)

    def _validate_endpoint_parameters(self, data: dict) -> tuple:
        form_id = data.get("form_id")
        if form_id is None:
            raise MissingParameters("form_id")
        if not isinstance(form_id, str):
            raise WrongTypeParameter(fieldName="form_id", fieldTypeExpected="str", fieldTypeReceived=type(form_id))

        completed_at_raw = data.get("completed_at")
        if completed_at_raw is None:
            raise MissingParameters("completed_at")

        if isinstance(completed_at_raw, bool) or not isinstance(completed_at_raw, int):
            raise WrongTypeParameter(fieldName="completed_at", fieldTypeExpected="int", fieldTypeReceived=type(completed_at_raw))

        completed_at = completed_at_raw

        fields_raw = data.get("fields")
        if fields_raw is None:
            raise MissingParameters("fields")
        if not isinstance(fields_raw, list):
            raise WrongTypeParameter(fieldName="fields", fieldTypeExpected="list", fieldTypeReceived=type(fields_raw))
        if len(fields_raw) == 0:
            raise MissingParameters("fields")

        fields = []
        for item in fields_raw:
            if not isinstance(item, dict):
                raise WrongTypeParameter(fieldName="fields", fieldTypeExpected="dict", fieldTypeReceived=type(item))
            section_id = item.get("section_id")
            if section_id is None:
                raise MissingParameters("section_id")
            if isinstance(section_id, bool):
                raise WrongTypeParameter(fieldName="section_id", fieldTypeExpected="int", fieldTypeReceived=type(section_id))
            if isinstance(section_id, str) and section_id.isdigit():
                section_id = int(section_id)
            if not isinstance(section_id, int):
                raise WrongTypeParameter(fieldName="section_id", fieldTypeExpected="int", fieldTypeReceived=type(section_id))

            field_key = item.get("field_key")
            if field_key is None:
                raise MissingParameters("field_key")
            if not isinstance(field_key, str):
                raise WrongTypeParameter(fieldName="field_key", fieldTypeExpected="str", fieldTypeReceived=type(field_key))

            if "value" not in item:
                raise MissingParameters("value")

            fields.append(
                {
                    "section_id": section_id,
                    "field_key": field_key,
                    "value": item.get("value"),
                }
            )

        return form_id, completed_at, fields
    
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            requester_user = self._validate_requester_user(data)
            form_id, completed_at, fields = self._validate_endpoint_parameters(data)
                
            files = self.submit_form_usecase(
                user_id=requester_user.user_id,
                form_id=form_id,
                fields=fields,
                completed_at=completed_at,
            )

            viewmodel = SubmitFormViewmodel(files=files)
            return OK(viewmodel.to_dict())

        except NoItemsFound as err:
            return NotFound(body=err.message)

        except MissingParameters as err:
            return BadRequest(body=err.message)
        
        except WrongTypeParameter as err:
            return BadRequest(body= err.message)

        except ForbiddenAction as err:
            return Forbidden(body=err.message)
        
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
        
        except Exception as err:
            return InternalServerError(body=err.args[0])
