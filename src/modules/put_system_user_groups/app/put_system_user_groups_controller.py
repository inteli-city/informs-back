from .put_system_user_groups_usecase import PutSystemUserGroupsUsecase
from .put_system_user_groups_viewmodel import PutSystemUserGroupsViewmodel
from src.shared.helpers.contracts.runtime_requests import PutSystemUserGroupsControllerRequestSchema
from src.shared.helpers.access_error_response import HANDLED_ERRORS, access_error_response
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import OK
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class PutSystemUserGroupsController:
    def __init__(self, usecase: PutSystemUserGroupsUsecase):
        self.usecase = usecase

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = PutSystemUserGroupsControllerRequestSchema.model_validate(data)
            requester_user = UserGatewayDTO.from_api_gateway(payload.requester_user.model_dump(by_alias=True))

            result = self.usecase(
                requester_user_id=requester_user.user_id,
                system=payload.system,
                target_user_id=payload.user_id,
                groups=payload.groups,
            )

            viewmodel = PutSystemUserGroupsViewmodel(result)
            return OK(viewmodel.to_dict())

        except HANDLED_ERRORS as err:
            return access_error_response(err)
