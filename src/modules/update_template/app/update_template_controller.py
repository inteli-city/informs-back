from pydantic import ValidationError

from src.modules.update_template.app.update_template_viewmodel import TemplateViewmodel
from src.modules.update_template.app.update_template_usecase import UpdateTemplateUsecase
from src.shared.helpers.contracts.runtime_requests import UpdateTemplateControllerRequestSchema
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Conflict, Forbidden, InternalServerError, NotFound, OK
from src.shared.helpers.functions.pydantic_error_parser import get_validation_error_message
from src.shared.infra.dtos.section_dto import SectionDTO
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class UpdateTemplateController:
    def __init__(self, usecase: UpdateTemplateUsecase):
        self.usecase = usecase

    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = UpdateTemplateControllerRequestSchema.model_validate(data)
            requester = UserGatewayDTO.from_api_gateway(payload.requester_user.model_dump(by_alias=True))
            sections = (
                [SectionDTO.from_request(section.model_dump()).to_entity() for section in payload.sections]
                if payload.sections is not None
                else None
            )

            updated_template = self.usecase(
                template_id=payload.template_id,
                requester_user_id=requester.user_id,
                requester_systems=requester.systems,
                name=payload.name,
                system=payload.system,
                description=payload.description,
                is_active=payload.is_active,
                sections=sections,
            )

            viewmodel = TemplateViewmodel(updated_template)
            return OK(viewmodel.to_dict())

        except ValidationError as err:
            return BadRequest(get_validation_error_message(err))
        except MissingParameters as err:
            return BadRequest(err.message)
        except WrongTypeParameter as err:
            return BadRequest(err.message)
        except EntityError as err:
            return BadRequest(f"Parâmetro inválido: {err.message}")
        except NoItemsFound as err:
            return NotFound(err.message)
        except ForbiddenAction as err:
            return Forbidden(err.message)
        except DuplicatedItem as err:
            return Conflict(err.message)
        except Exception as err:
            return InternalServerError(err.args[0] if err.args else str(err))
