import os
import sys

import pytest

sys.path.append(os.getcwd())

from src.modules.delete_profile.app.delete_profile_controller import DeleteProfileController
from src.modules.delete_profile.app.delete_profile_usecase import DeleteProfileUsecase
from src.shared.domain.entities.profile import Profile
from src.shared.domain.enums.profile_role_enum import ProfileRole
from src.shared.helpers.errors.usecase_errors import ForbiddenAction
from src.shared.helpers.external_interfaces.http_models import HttpRequest
from src.shared.infra.repositories.profile_repository_mock import ProfileRepositoryMock


ADMIN_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"
INSPECTOR_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120002"


def _payload(sub: str = ADMIN_USER_ID, groups: str = "FORMULARIOS,GAIA"):
    return {
        "sub": sub,
        "name": "Tester",
        "email": "tester@example.com",
        "cognito:groups": groups,
    }


def _request(target_user_id: str, requester_sub: str = ADMIN_USER_ID):
    return HttpRequest(body={
        "requester_user": _payload(sub=requester_sub),
        "user_id": target_user_id,
    })


class TestDeleteProfileController:
    def setup_method(self):
        self.repo = ProfileRepositoryMock()
        self.usecase = DeleteProfileUsecase(self.repo)
        self.controller = DeleteProfileController(self.usecase)

    def test_admin_soft_deletes_inspector_returns_200(self):
        response = self.controller(_request(target_user_id=INSPECTOR_USER_ID))
        assert response.status_code == 200
        assert response.body["active"] is False
        assert response.body["user_id"] == INSPECTOR_USER_ID
        assert self.repo.get_by_user_id(INSPECTOR_USER_ID).active is False

    def test_admin_soft_deletes_other_admin_when_more_than_one_admin_returns_200(self):
        second_admin = Profile(
            user_id="d61dbf66-a10f-11ed-a8fc-0242ac120020",
            role=ProfileRole.ADMIN,
            name="Second Admin",
            email="admin2@example.com",
            system="GAIA",
            active=True,
            created_at=1, updated_at=1,
        )
        self.repo.create(second_admin)
        # admin original deleta o second admin → OK (sobra 1 ativo: o original)
        response = self.controller(_request(target_user_id=second_admin.user_id))
        assert response.status_code == 200

    def test_inspector_cannot_delete_returns_403(self):
        response = self.controller(_request(
            target_user_id=ADMIN_USER_ID, requester_sub=INSPECTOR_USER_ID
        ))
        assert response.status_code == 403

    def test_admin_cannot_self_delete_returns_403(self):
        response = self.controller(_request(target_user_id=ADMIN_USER_ID))
        assert response.status_code == 403

    def test_target_not_found_returns_404(self):
        response = self.controller(_request(target_user_id="00000000-0000-0000-0000-000000000000"))
        assert response.status_code == 404

    def test_already_inactive_returns_409(self):
        self.repo.soft_delete(user_id=INSPECTOR_USER_ID, updated_at=1)
        response = self.controller(_request(target_user_id=INSPECTOR_USER_ID))
        assert response.status_code == 409

    def test_unknown_requester_returns_403(self):
        response = self.controller(_request(
            target_user_id=INSPECTOR_USER_ID,
            requester_sub="00000000-0000-0000-0000-000000000000",
        ))
        assert response.status_code == 403


class TestDeleteProfileLastAdminGuard:
    """
    Guarda defensiva: mesmo se algum bug/dado anômalo permitir, o usecase
    NUNCA deve remover o último ADMIN ativo. Coberto via repo "trapaceado"
    que reporta 1 admin ativo ao count(), forçando o caminho do guard.
    """

    def test_blocks_delete_of_admin_when_only_one_admin_active(self):
        repo = ProfileRepositoryMock()

        # Adiciona um segundo admin para que o requester exista; e força
        # count_active_by_role(ADMIN) a sempre retornar 1, simulando o caso
        # de borda.
        second_admin = Profile(
            user_id="d61dbf66-a10f-11ed-a8fc-0242ac120020",
            role=ProfileRole.ADMIN,
            name="Second Admin",
            email="admin2@example.com",
            system="GAIA",
            active=True,
            created_at=1, updated_at=1,
        )
        repo.create(second_admin)

        original_count = repo.count_active_by_role
        repo.count_active_by_role = lambda role: 1 if role == ProfileRole.ADMIN else original_count(role)

        usecase = DeleteProfileUsecase(repo)
        with pytest.raises(ForbiddenAction):
            usecase(
                requester_user_id=second_admin.user_id,
                target_user_id=ADMIN_USER_ID,
            )
