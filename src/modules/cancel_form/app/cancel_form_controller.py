from pydantic import ValidationError

from .cancel_form_usecase import CancelFormUsecase
from .cancel_form_viewmodel import CancelFormViewmodel
from src.shared.domain.entities.file_upload import FileUploadRequest
from src.shared.helpers.contracts.runtime_requests import CancelFormControllerRequestSchema
from src.shared.helpers.controller_error_handler import controller_error_handler
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import OK, BadRequest, Conflict, Forbidden, NotFound
from src.shared.helpers.functions.pydantic_error_parser import get_validation_error_message
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class CancelFormController:
    def __init__(self, usecase: CancelFormUsecase):
        self.usecase = usecase

    @controller_error_handler
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            payload = CancelFormControllerRequestSchema.model_validate(data)
            requester_user = UserGatewayDTO.from_api_gateway(payload.requester_user.model_dump(by_alias=True))

            justification_image = None
            if payload.file is not None:
                justification_image = FileUploadRequest(
                    filename=payload.file.filename,
                    mimetype=payload.file.mimetype,
                    size_bytes=payload.file.size_bytes,
                    checksum_sha256=payload.file.checksum_sha256,
                )

            file_upload = self.usecase(
                requester_id=requester_user.user_id,
                form_id=payload.form_id,
                selected_option=payload.option,
                justification_text=payload.text,
                justification_image=justification_image,
                cancelled_at=payload.cancelled_at,
            )

            viewmodel = CancelFormViewmodel(file_upload=file_upload)
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

        except DuplicatedItem as err:
            return Conflict(body=err.message)
