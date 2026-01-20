import json
import pytest
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.infra.dtos.user_gateway import UserGatewayDTO

class Test_UserFormulariosApiGatewayDto:

    def test_user_api_gateway_dto_from_api_gateway(self):
        user_data = {
            'sub': 'd61dbf66-a10f-11ed-a8fc-0242ac120002',
            'name': 'Gabriel Godoy',
            'email': 'gabriel@gmail.com',
            'cognito:groups': "GAIA,JUNDIAI,FORMULARIOS"
        }
        
        user_dto = UserGatewayDTO.from_api_gateway(user_data)

        excepted_user_dto = UserGatewayDTO(
            user_id='d61dbf66-a10f-11ed-a8fc-0242ac120002',
            name='Gabriel Godoy',
            email='gabriel@gmail.com',
            systems=['GAIA','JUNDIAI']
        )

        assert user_dto.user_id == excepted_user_dto.user_id
        assert user_dto.name == excepted_user_dto.name
        assert user_dto.email == excepted_user_dto.email
        assert user_dto.systems == ['GAIA','JUNDIAI']

    def test_user_api_gateway_dto_from_api_gateway_json_string(self):
        user_data = {
            'sub': 'd61dbf66-a10f-11ed-a8fc-0242ac120002',
            'name': 'Gabriel Godoy',
            'email': 'gabriel@gmail.com',
            'cognito:groups': "GAIA,JUNDIAI,FORMULARIOS"
        }

        json_str = json.dumps(user_data)

        user_dto = UserGatewayDTO.from_api_gateway(json_str)

        assert user_dto.user_id == user_data["sub"]
        assert user_dto.name == user_data["name"]
        assert user_dto.email == user_data["email"]
        assert user_dto.systems == ['GAIA','JUNDIAI']

    def test_user_gateway_dto_from_api_gateway_not_in_groups(self):
        user_data = {
            'sub': 'd61dbf66-a10f-11ed-a8fc-0242ac120002',
            'name': 'Gabriel Godoy',
            'email': 'gabriel@outlook.com',
            'cognito:groups': "GAIA,JUNDIAI"
        }
        
        with pytest.raises(ForbiddenAction):
            UserGatewayDTO.from_api_gateway(user_data)
