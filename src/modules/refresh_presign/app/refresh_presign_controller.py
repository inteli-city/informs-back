from pydantic import ValidationError

from .refresh_presign_usecase import RefreshPresignUsecase
from .refresh_presign_viewmodel import RefreshPresignViewmodel
from src.shared.helpers.contracts.runtime_requests import RefreshPresignControllerRequestSchema
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import OK, BadRequest, Forbidden, NotFound
from src.shared.helpers.functions.pydantic_error_parser import get_validation_error_message
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class RefreshPresignController:
    def __init__(self, usecase: RefreshPresignUsecase):
        self.usecase = usecase

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = RefreshPresignControllerRequestSchema.model_validate(data)
            requester_user = UserGatewayDTO.from_api_gateway(payload.requester_user.model_dump(by_alias=True))

            files = self.usecase(
                user_id=requester_user.user_id,
                form_id=payload.form_id,
                requested_files=[file.model_dump() for file in payload.files],
            )

            viewmodel = RefreshPresignViewmodel(files=files)
            return OK(viewmodel.to_dict())

        except ValidationError as err:
            return BadRequest(body=get_validation_error_message(err))

        except NoItemsFound as err:
            return NotFound(body=err.message)

        except MissingParameters as err:
            return BadRequest(body=err.message)

        except WrongTypeParameter as err:
            return BadRequest(body=err.message)

        except ForbiddenAction as err:
            return Forbidden(body=err.message)

        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
