from .create_form_usecase import CreateFormUsecase
from .create_form_viewmodel import CreateFormViewmodel
from src.shared.domain.enums.priority_enum import PRIORITY
from src.shared.helpers.errors.controller_errors import MissingParameters, WrongTypeParameter
from src.shared.helpers.errors.domain_errors import EntityError
from src.shared.helpers.errors.usecase_errors import DuplicatedItem, ForbiddenAction, NoItemsFound
from src.shared.helpers.external_interfaces.external_interface import IRequest, IResponse
from src.shared.helpers.external_interfaces.http_codes import BadRequest, Conflict, Created, Forbidden, InternalServerError, NotFound
from src.shared.domain.entities.information_field import ImageInformationField
from src.shared.infra.dtos.information_field_dto import InformationFieldDTO
from src.shared.infra.dtos.justification_dto import JustificationDTO
from src.shared.infra.dtos.section_dto import SectionDTO
from src.shared.infra.dtos.user_gateway import UserGatewayDTO


class CreateFormController:
    def __init__(self, usecase: CreateFormUsecase):
        self.usecase = usecase

    def _validate_requester_user(self, data: dict) -> UserGatewayDTO:
        requester_user = data.get("requester_user")
        if requester_user is None:
            raise MissingParameters("requester_user")

        return UserGatewayDTO.from_api_gateway(requester_user)

    def _validate_endpoint_parameters(self, data: dict) -> tuple:
        def _get_required(field: str):
            value = data.get(field)
            if value is None:
                raise MissingParameters(field)
            return value

        def _require_type(field: str, value, expected_type, expected_label: str = None):
            if not isinstance(value, expected_type):
                label = expected_label or expected_type.__name__
                raise WrongTypeParameter(field, label, type(value))
            return value

        def _parse_optional_int(field: str, value):
            if value is None:
                return None
            if isinstance(value, bool) or not isinstance(value, int):
                raise WrongTypeParameter(field, "int", type(value))
            return value

        def _parse_float(field: str, value):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise WrongTypeParameter(field, "float", type(value))
            return float(value)

        form_title = _get_required("form_title")
        user_id = _get_required("user_id")
        system = _get_required("system")
        street = _get_required("street")
        city = _get_required("city")
        latitude_raw = _get_required("latitude")
        longitude_raw = _get_required("longitude")
        priority_payload = _get_required("priority")
        raw_justifications = _get_required("justifications")
        sessions_raw = _get_required("sessions")
        observation = data.get("observation")
        expiration_date_raw = data.get("expiration_date")
        number_raw = data.get("number")
        template = data.get("template")
        information_fields_raw = data.get("information_fields")
        information_fields_uploads = None

        for field_name, value in [
            ("form_title", form_title),
            ("user_id", user_id),
            ("system", system),
            ("street", street),
            ("city", city),
        ]:
            _require_type(field_name, value, str)

        if observation is not None:
            _require_type("observation", observation, str)
        if template is not None:
            _require_type("template", template, str)

        _require_type("justifications", raw_justifications, list)
        _require_type("sessions", sessions_raw, list)

        if information_fields_raw is not None:
            _require_type("information_fields", information_fields_raw, list)
            information_fields_uploads = [None] * len(information_fields_raw)
            for idx, information_field in enumerate(information_fields_raw):
                if information_field.get("information_field_type") == "IMAGE_INFORMATION_FIELD":
                    mimetype = information_field.get("mimetype")
                    if mimetype is None:
                        raise MissingParameters("mimetype")
                    if not isinstance(mimetype, str):
                        raise WrongTypeParameter("mimetype", "str", type(mimetype))
                    filename = information_field.get("filename")
                    if filename is None:
                        raise MissingParameters("filename")
                    if not isinstance(filename, str):
                        raise WrongTypeParameter("filename", "str", type(filename))
                    information_fields_uploads[idx] = {
                        "mimetype": mimetype,
                        "filename": filename,
                    }

        priority_values = {priority.value for priority in PRIORITY}
        if isinstance(priority_payload, bool) or not isinstance(priority_payload, int):
            raise WrongTypeParameter("priority", "int", type(priority_payload))

        priority_value = str(priority_payload)
        if priority_value in priority_values:
            priority = PRIORITY(priority_value)
        else:
            raise EntityError("priority")

        latitude = _parse_float("latitude", latitude_raw)
        longitude = _parse_float("longitude", longitude_raw)

        expiration_date = _parse_optional_int("expiration_date", expiration_date_raw)
        number = _parse_optional_int("number", number_raw)

        normalized_justifications = []
        for option in raw_justifications:
            required_image = option.get("required_image")
            if required_image is not None and not isinstance(required_image, bool):
                raise WrongTypeParameter("justifications.required_image", "bool", type(required_image))

            required_text = option.get("required_text")
            if required_text is not None and not isinstance(required_text, bool):
                raise WrongTypeParameter("justifications.required_text", "bool", type(required_text))

            normalized_justifications.append(
                {
                    "option": option.get("option"),
                    "required_image": required_image if required_image is not None else False,
                    "required_text": required_text if required_text is not None else False,
                }
            )

        justification_entity = JustificationDTO.from_request({"options": normalized_justifications}).to_entity()
        sections = [SectionDTO.from_request(section).to_entity() for section in sessions_raw]
        information_fields = None
        if information_fields_raw is not None:
            information_fields = []
            for information_field in information_fields_raw:
                if information_field.get("information_field_type") == "IMAGE_INFORMATION_FIELD":
                    information_fields.append(ImageInformationField(file_path=""))
                else:
                    information_fields.append(InformationFieldDTO.from_request(information_field).to_entity())

        return (
            form_title,
            user_id,
            system,
            street,
            city,
            latitude,
            longitude,
            priority,
            sections,
            justification_entity,
            number,
            observation,
            expiration_date,
            template,
            information_fields,
            information_fields_uploads,
        )
    
    def __call__(self, request: IRequest) -> IResponse:
        try:
            data = request.data if isinstance(request.data, dict) else {}
            requester_user = self._validate_requester_user(data)
            (
                form_title,
                user_id,
                system,
                street,
                city,
                latitude,
                longitude,
                priority,
                sections,
                justification_entity,
                number,
                observation,
                expiration_date,
                template,
                information_fields,
                information_fields_uploads,
            ) = self._validate_endpoint_parameters(data)

            form, images = self.usecase(
                form_title=form_title,
                created_by=requester_user.user_id,
                user_id=user_id,
                system=system,
                street=street,
                city=city,
                latitude=latitude,
                longitude=longitude,
                priority=priority,
                sections=sections,
                justification=justification_entity,
                number=number,
                observation=observation,
                expiration_date=expiration_date,
                template=template,
                information_fields=information_fields,
                information_fields_uploads=information_fields_uploads,
            )

            viewmodel = CreateFormViewmodel(form=form, images=images)
            
            return Created(viewmodel.to_dict())
        
        except NoItemsFound as err:
            return NotFound(body=err.message)
        
        except DuplicatedItem as err:
            return Conflict(body=err.message)

        except MissingParameters as err:
            return BadRequest(body= err.message)

        except ForbiddenAction as err:
            return Forbidden(body=err.message)

        except WrongTypeParameter as err:
            return BadRequest(body=err.message)
        
        except EntityError as err:
            return BadRequest(body=f"Parâmetro inválido: {err.message}")
        
        except Exception as err:
            return InternalServerError(body=err.args[0])
