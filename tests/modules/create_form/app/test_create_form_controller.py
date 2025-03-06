from src.modules.create_form.app.create_form_controller import CreateFormController
from src.modules.create_form.app.create_form_usecase import CreateFormUsecase
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock
from src.shared.infra.repositories.image_repository_mock import ImageRepositoryMock


class Test_CreateFormController:
    def test_create_form_controller(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CreateFormUsecase(repo, image_repo)

        controller = CreateFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
                "name": "Gabriel Godoy",
                "email": "gabriel@gmail.com",
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_title": "FORM TITLE",
            "form_id": "d61dbf66-a10f-11ed-a8fc-0242ac120020",
            "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
            "can_vinculate": True,
            "template": "TEMPLATE",
            "area": "1",
            "system": "GAIA",
            "street": "1",
            "city": "1",
            "number": 1,
            "latitude": 1.0,
            "longitude": 1.0,
            "region": "REGION",
            "priority": "EMERGENCY",
            "expiration_date": 946407600000,
            "justification": {
                "options": [
                    {
                        "option": "option",
                        "required_image": True,
                        "required_text": True
                    }
                ],
                "selected_option": "option",
                "text": "text",
                "image": "image"
            },
            "comments": "123",
            "sections": [
                    {
                        "section_id": "99999",
                        "fields": [
                            {
                                "field_type": "TEXT_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "regex": "regex",
                                "formatting": "formatting",
                                "max_length": 10,
                            },
                            {
                                "field_type": "NUMBER_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "decimal": True,
                                "max_value": 10,
                                "min_value": 1,
                            },
                            {
                                "field_type": "DROPDOWN_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "options": ["option1", "option2"]
                            },
                            {
                                "field_type": "TYPEAHEAD_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "options": ["option1", "option2"],
                                "max_length": 10,
                            },
                            {
                                "field_type": "RADIO_GROUP_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "options": ["option1", "option2"]
                            },
                            {
                                "field_type": "DATE_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "min_date": 946407600000,
                                "max_date": 946407600000
                            },
                            {
                                "field_type": "CHECKBOX_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                            },
                            {
                                "field_type": "CHECKBOX_GROUP_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "options": ["option1", "option2"],
                                "check_limit": 1
                            },
                            {
                                "field_type": "SWITCH_BUTTON_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                            },
                            {
                                "field_type": "FILE_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "file_type": "IMAGE",
                                "min_quantity": 1,
                                "max_quantity": 1
                            }
                        ]
                    },
            ],
            "information_fields": [
                {
                    "information_field_type": "TEXT_INFORMATION_FIELD",
                    "value": "value"
                },
                {
                    "information_field_type": "MAP_INFORMATION_FIELD",
                    "latitude": 1.0,
                    "longitude": 1.0
                },
                {
                    "information_field_type": "IMAGE_INFORMATION_FIELD",
                    "file_path": "file_path"
                }
            ]
        })

        response = controller(data)

        assert response.status_code == 201
        assert response.body['message'] == "Formulário criado com sucesso!"
    
    def test_create_form_controller_missing_request_user(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CreateFormUsecase(repo, image_repo)

        controller = CreateFormController(usecase)

        data = HttpRequest(body={
            "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
            "can_vinculate": True,
            "template": "TEMPLATE",
            "area": "1",
            "system": "GAIA",
            "street": "1",
            "city": "1",
            "number": 1,
            "latitude": 1.0,
            "longitude": 1.0,
            "region": "REGION",
            "priority": "EMERGENCY",
            "expiration_date": 946407600000,
            "comments": "123",
            "sections": [
                    {
                        "section_id": "99999",
                        "fields": [
                            {
                                "field_type": "TEXT_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "regex": "regex",
                                "formatting": "formatting",
                                "max_length": 10,
                                "value": "value"
                            },
                            {
                                "field_type": "TEXT_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "regex": "regex",
                                "formatting": "formatting",
                                "max_length": 10,
                                "value": "value"
                            }
                        ]
                    },
            ],
            "information_fields": [
                {
                    "field_type": "TEXT_FIELD",
                    "placeholder": "placeholder",
                    "required": True,
                    "key": "key",
                    "regex": "regex",
                    "formatting": "formatting",
                    "max_length": 10,
                    "value": "value"
                },
                {
                    "field_type": "TEXT_FIELD",
                    "placeholder": "placeholder",
                    "required": True,
                    "key": "key",
                    "regex": "regex",
                    "formatting": "formatting",
                    "max_length": 10,
                    "value": "value"
                }
            ]
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: requester_user"
    
    def test_create_form_controller_missing_template(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CreateFormUsecase(repo, image_repo)

        controller = CreateFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
                "name": "Gabriel Godoy",
                "email": "gabriel.godoybz@intelicity.com.br",
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_title": "FORM TITLE",
            "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
            "can_vinculate": True,
            "area": "1",
            "system": "GAIA",
            "street": "1",
            "city": "1",
            "number": 1,
            "latitude": 1.0,
            "longitude": 1.0,
            "region": "REGION",
            "priority": "EMERGENCY",
            "expiration_date": 946407600000,
            "comments": "123",
            "sections": [
                    {
                        "section_id": "99999",
                        "fields": [
                            {
                                "field_type": "TEXT_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "regex": "regex",
                                "formatting": "formatting",
                                "max_length": 10,
                                "value": "value"
                            }
                        ]
                    },
            ],
            "information_fields": [
                {
                    "field_type": "TEXT_FIELD",
                    "placeholder": "placeholder",
                    "required": True,
                    "key": "key",
                    "regex": "regex",
                    "formatting": "formatting",
                    "max_length": 10,
                    "value": "value"
                }
            ]
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: template"
    
    def test_create_form_controller_missing_area(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CreateFormUsecase(repo, image_repo)

        controller = CreateFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
                "name": "Gabriel Godoy",
                "email": "gabriel.godoybz@intelicity.com.br",
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_title": "FORM TITLE",
            "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
            "can_vinculate": True,
            "template": "TEMPLATE",
            "system": "GAIA",
            "street": "1",
            "city": "1",
            "number": 1,
            "latitude": 1.0,
            "longitude": 1.0,
            "region": "REGION",
            "priority": "EMERGENCY",
            "expiration_date": 946407600000,
            "comments": "123",
            "sections": [
                    {
                        "section_id": "99999",
                        "fields": [
                            {
                                "field_type": "TEXT_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "regex": "regex",
                                "formatting": "formatting",
                                "max_length": 10,
                                "value": "value"
                            }
                        ]
                    },
            ],
            "information_fields": [
                {
                    "field_type": "TEXT_FIELD",
                    "placeholder": "placeholder",
                    "required": True,
                    "key": "key",
                    "regex": "regex",
                    "formatting": "formatting",
                    "max_length": 10,
                    "value": "value"
                }
            ]
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: area"
    
    def test_create_form_controller_missing_system(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CreateFormUsecase(repo, image_repo)

        controller = CreateFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
                "name": "Gabriel Godoy",
                "email": "gabriel.godoybz@intelicity.com.br",
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_title": "FORM TITLE",
            "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
            "can_vinculate": True,
            "template": "TEMPLATE",
            "area": "1",
            "street": "1",
            "city": "1",
            "number": 1,
            "latitude": 1.0,
            "longitude": 1.0,
            "region": "REGION",
            "priority": "EMERGENCY",
            "expiration_date": 946407600000,
            "comments": "123",
            "sections": [
                    {
                        "section_id": "99999",
                        "fields": [
                            {
                                "field_type": "TEXT_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "regex": "regex",
                                "formatting": "formatting",
                                "max_length": 10,
                                "value": "value"
                            }
                        ]
                    },
            ],
            "information_fields": [
                {
                    "field_type": "TEXT_FIELD",
                    "placeholder": "placeholder",
                    "required": True,
                    "key": "key",
                    "regex": "regex",
                    "formatting": "formatting",
                    "max_length": 10,
                    "value": "value"
                }
            ]
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: system"
    
    def test_create_form_controller_missing_street(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CreateFormUsecase(repo, image_repo)

        controller = CreateFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
                "name": "Gabriel Godoy",
                "email": "gabriel.godoybz@intelicity.com.br",
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_title": "FORM TITLE",
            "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
            "can_vinculate": True,
            "template": "TEMPLATE",
            "area": "1",
            "system": "GAIA",
            "city": "1",
            "number": 1,
            "latitude": 1.0,
            "longitude": 1.0,
            "region": "REGION",
            "priority": "EMERGENCY",
            "expiration_date": 946407600000,
            "comments": "123",
            "sections": [
                    {
                        "section_id": "99999",
                        "fields": [
                            {
                                "field_type": "TEXT_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "regex": "regex",
                                "formatting": "formatting",
                                "max_length": 10,
                                "value": "value"
                            }
                        ]
                    },
            ],
            "information_fields": [
                {
                    "field_type": "TEXT_FIELD",
                    "placeholder": "placeholder",
                    "required": True,
                    "key": "key",
                    "regex": "regex",
                    "formatting": "formatting",
                    "max_length": 10,
                    "value": "value"
                }
            ]
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: street"
    
    def test_create_form_controller_missing_city(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CreateFormUsecase(repo, image_repo)

        controller = CreateFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
                "name": "Gabriel Godoy",
                "email": "gabriel.godoybz@intelicity.com.br",
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_title": "FORM TITLE",
            "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
            "can_vinculate": True,
            "template": "TEMPLATE",
            "area": "1",
            "system": "GAIA",
            "street": "1",
            "number": 1,
            "latitude": 1.0,
            "longitude": 1.0,
            "region": "REGION",
            "priority": "EMERGENCY",
            "expiration_date": 946407600000,
            "comments": "123",
            "sections": [
                    {
                        "section_id": "99999",
                        "fields": [
                            {
                                "field_type": "TEXT_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "regex": "regex",
                                "formatting": "formatting",
                                "max_length": 10,
                                "value": "value"
                            }
                        ]
                    },
            ],
            "information_fields": [
                {
                    "field_type": "TEXT_FIELD",
                    "placeholder": "placeholder",
                    "required": True,
                    "key": "key",
                    "regex": "regex",
                    "formatting": "formatting",
                    "max_length": 10,
                    "value": "value"
                }
            ]
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: city"
    
    def test_create_form_controller_missing_number(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CreateFormUsecase(repo, image_repo)

        controller = CreateFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
                "name": "Gabriel Godoy",
                "email": "gabriel.godoybz@intelicity.com.br",
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_title": "FORM TITLE",
            "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
            "can_vinculate": True,
            "template": "TEMPLATE",
            "area": "1",
            "system": "GAIA",
            "street": "1",
            "city": "1",
            "latitude": 1.0,
            "longitude": 1.0,
            "region": "REGION",
            "priority": "EMERGENCY",
            "expiration_date": 946407600000,
            "comments": "123",
            "sections": [
                    {
                        "section_id": "99999",
                        "fields": [
                            {
                                "field_type": "TEXT_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "regex": "regex",
                                "formatting": "formatting",
                                "max_length": 10,
                                "value": "value"
                            }
                        ]
                    },
            ],
            "information_fields": [
                {
                    "field_type": "TEXT_FIELD",
                    "placeholder": "placeholder",
                    "required": True,
                    "key": "key",
                    "regex": "regex",
                    "formatting": "formatting",
                    "max_length": 10,
                    "value": "value"
                }
            ]
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: number"
    
    def test_create_form_controller_missing_latitude(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CreateFormUsecase(repo, image_repo)

        controller = CreateFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
                "name": "Gabriel Godoy",
                "email": "gabriel.godoybz@intelicity.com.br",
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_title": "FORM TITLE",
            "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
            "can_vinculate": True,
            "template": "TEMPLATE",
            "area": "1",
            "system": "GAIA",
            "street": "1",
            "city": "1",
            "number": 1,
            "longitude": 1.0,
            "region": "REGION",
            "priority": "EMERGENCY",
            "expiration_date": 946407600000,
            "comments": "123",
            "sections": [
                    {
                        "section_id": "99999",
                        "fields": [
                            {
                                "field_type": "TEXT_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "regex": "regex",
                                "formatting": "formatting",
                                "max_length": 10,
                                "value": "value"
                            }
                        ]
                    },
            ],
            "information_fields": [
                {
                    "field_type": "TEXT_FIELD",
                    "placeholder": "placeholder",
                    "required": True,
                    "key": "key",
                    "regex": "regex",
                    "formatting": "formatting",
                    "max_length": 10,
                    "value": "value"
                }
            ]
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: latitude"
    
    def test_create_form_controller_missing_longitude(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CreateFormUsecase(repo, image_repo)

        controller = CreateFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
                "name": "Gabriel Godoy",
                "email": "gabriel.godoybz@intelicity.com.br",
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_title": "FORM TITLE",
            "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
            "can_vinculate": True,
            "template": "TEMPLATE",
            "area": "1",
            "system": "GAIA",
            "street": "1",
            "city": "1",
            "number": 1,
            "latitude": 1.0,
            "region": "REGION",
            "priority": "EMERGENCY",
            "expiration_date": 946407600000,
            "comments": "123",
            "sections": [
                    {
                        "section_id": "99999",
                        "fields": [
                            {
                                "field_type": "TEXT_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "regex": "regex",
                                "formatting": "formatting",
                                "max_length": 10,
                                "value": "value"
                            }
                        ]
                    },
            ],
            "information_fields": [
                {
                    "field_type": "TEXT_FIELD",
                    "placeholder": "placeholder",
                    "required": True,
                    "key": "key",
                    "regex": "regex",
                    "formatting": "formatting",
                    "max_length": 10,
                    "value": "value"
                }
            ]
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: longitude"
    
    def test_create_form_controller_missing_region(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CreateFormUsecase(repo, image_repo)

        controller = CreateFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
                "name": "Gabriel Godoy",
                "email": "gabriel.godoybz@intelicity.com.br",
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_title": "FORM TITLE",
            "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
            "can_vinculate": True,
            "template": "TEMPLATE",
            "area": "1",
            "system": "GAIA",
            "street": "1",
            "city": "1",
            "number": 1,
            "latitude": 1.0,
            "longitude": 1.0,
            "priority": "EMERGENCY",
            "expiration_date": 946407600000,
            "comments": "123",
            "sections": [
                    {
                        "section_id": "99999",
                        "fields": [
                            {
                                "field_type": "TEXT_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "regex": "regex",
                                "formatting": "formatting",
                                "max_length": 10,
                                "value": "value"
                            }
                        ]
                    },
            ],
            "information_fields": [
                {
                    "field_type": "TEXT_FIELD",
                    "placeholder": "placeholder",
                    "required": True,
                    "key": "key",
                    "regex": "regex",
                    "formatting": "formatting",
                    "max_length": 10,
                    "value": "value"
                }
            ]
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: region"
    
    def test_create_form_controller_missing_priority(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CreateFormUsecase(repo, image_repo)

        controller = CreateFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
                "name": "Gabriel Godoy",
                "email": "gabriel.godoybz@intelicity.com.br",
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_title": "FORM TITLE",
            "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
            "can_vinculate": True,
            "template": "TEMPLATE",
            "area": "1",
            "system": "GAIA",
            "street": "1",
            "city": "1",
            "number": 1,
            "latitude": 1.0,
            "longitude": 1.0,
            "region": "REGION",
            "expiration_date": 946407600000,
            "comments": "123",
            "sections": [
                    {
                        "section_id": "99999",
                        "fields": [
                            {
                                "field_type": "TEXT_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "regex": "regex",
                                "formatting": "formatting",
                                "max_length": 10,
                                "value": "value"
                            }
                        ]
                    },
            ],
            "information_fields": [
                {
                    "field_type": "TEXT_FIELD",
                    "placeholder": "placeholder",
                    "required": True,
                    "key": "key",
                    "regex": "regex",
                    "formatting": "formatting",
                    "max_length": 10,
                    "value": "value"
                }
            ]
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: priority"
    
    def test_create_form_controller_priority_not_in_enum(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CreateFormUsecase(repo, image_repo)

        controller = CreateFormController(usecase)

        data = HttpRequest(body={"requester_user": {
                "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
                "name": "Gabriel Godoy",
                "email": "gabriel.godoybz@intelicity.com.br",
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_title": "FORM TITLE",
            "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
            "can_vinculate": True,
            "template": "TEMPLATE",
            "area": "1",
            "system": "GAIA",
            "street": "1",
            "city": "1",
            "number": 1,
            "latitude": 1.0,
            "longitude": 1.0,
            "region": "REGION",
            "priority": "EMERGENCIA",
            "expiration_date": 946407600000,
            "comments": "123",
            "sections": [
                    {
                        "section_id": "99999",
                        "fields": [
                            {
                                "field_type": "TEXT_FIELD",
                                "placeholder": "placeholder",
                                "required": True,
                                "key": "key",
                                "regex": "regex",
                                "formatting": "formatting",
                                "max_length": 10,
                                "value": "value"
                            }
                        ]
                    },
            ],
            "information_fields": [
                {
                    "field_type": "TEXT_FIELD",
                    "placeholder": "placeholder",
                    "required": True,
                    "key": "key",
                    "regex": "regex",
                    "formatting": "formatting",
                    "max_length": 10,
                    "value": "value"
                }
            ]
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == "Parâmetro inválido: priority"
    
    def test_create_form_controller_missing_expiration_date(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CreateFormUsecase(repo, image_repo)

        controller = CreateFormController(usecase)

        data = HttpRequest(body={
            "requester_user": {
                "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
                "name": "Gabriel Godoy",
                "email": "gabriel.godoybz@intelicity.com.br",
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_title": "FORM TITLE",
            "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
            "can_vinculate": True,
            "template": "TEMPLATE",
            "area": "1",
            "system": "GAIA",
            "street": "1",
            "city": "1",
            "number": 1,
            "latitude": 1.0,
            "longitude": 1.0,
            "region": "REGION",
            "priority": "EMERGENCY",
            "comments": "123",
            "sections": [
                {
                    "section_id": "99999",
                    "fields": [
                        {
                            "field_type": "TEXT_FIELD",
                            "placeholder": "placeholder",
                            "required": True,
                            "key": "key",
                            "regex": "regex",
                            "formatting": "formatting",
                            "max_length": 10,
                            "value": "value"
                        }
                    ]
                },
            ],
            "information_fields": [
                {
                    "field_type": "TEXT_FIELD",
                    "placeholder": "placeholder",
                    "required": True,
                    "key": "key",
                    "regex": "regex",
                    "formatting": "formatting",
                    "max_length": 10,
                    "value": "value"
                }
            ]
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: expiration_date"
    
    def test_create_form_controller_missing_sections(self):
        repo = FormRepositoryMock()
        image_repo = ImageRepositoryMock()
        usecase = CreateFormUsecase(repo, image_repo)

        controller = CreateFormController(usecase)

        data = HttpRequest(body={
            "requester_user": {
                "sub": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
                "name": "Gabriel Godoy",
                "email": "gabriel.godoybz@intelicity.com.br",
                "cognito:groups": "GAIA, JUNDIAI,FORMULARIOS"
            },
            "form_title": "FORM TITLE",
            "user_id": "d61dbf66-a10f-11ed-a8fc-0242ac120001",
            "can_vinculate": True,
            "template": "TEMPLATE",
            "area": "1",
            "system": "GAIA",
            "street": "1",
            "city": "1",
            "number": 1,
            "latitude": 1.0,
            "longitude": 1.0,
            "region": "REGION",
            "priority": "EMERGENCY",
            "expiration_date": 946407600000,
            "justification": {
                "options": [
                    {
                        "option": "option",
                        "required_image": True,
                        "required_text": True
                    }
                ],
                "selected_option": "selected_option",
                "text": "text",
                "image": "image"
            },
            "comments": "123",
            "information_fields": [
                {
                    "field_type": "TEXT_FIELD",
                    "placeholder": "placeholder",
                    "required": True,
                    "key": "key",
                    "regex": "regex",
                    "formatting": "formatting",
                    "max_length": 10,
                    "value": "value"
                }
            ]
        })

        response = controller(data)

        assert response.status_code == 400
        assert response.body == "Parâmetro ausente: sections"
    