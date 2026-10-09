from .get_system_users_usecase import GetSystemUsersUsecase
from .get_system_users_viewmodel import GetSystemUsersViewmodel
from src.shared.helpers.contracts.runtime_requests import GetSystemUsersControllerRequestSchema
from src.shared.helpers.access_error_response import HANDLED_ERRORS, access_error_response
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import OK
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class GetSystemUsersController:
    def __init__(self, usecase: GetSystemUsersUsecase):
        self.usecase = usecase

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = GetSystemUsersControllerRequestSchema.model_validate(data)
            requester_user = UserGatewayDTO.from_api_gateway(payload.requester_user.model_dump(by_alias=True))

            result = self.usecase(
                requester_user_id=requester_user.user_id,
                system=payload.system,
            )

            viewmodel = GetSystemUsersViewmodel(system=payload.system, users=result)
            return OK(viewmodel.to_dict())

        except HANDLED_ERRORS as err:
            return access_error_response(err)
