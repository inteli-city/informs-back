import os
import sys

import pytest

sys.path.append(os.getcwd())

from src.modules.update_profile.app.update_profile_usecase import UpdateProfileUsecase
from src.shared.domain.enums.profile_role_enum import ProfileRole
from src.shared.helpers.errors.usecase_errors import ForbiddenAction, NoItemsFound
from src.shared.infra.repositories.profile_repository_mock import ProfileRepositoryMock


ADMIN_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"
INSPECTOR_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120002"


class TestUpdateProfileUsecase:
    def setup_method(self):
        self.repo = ProfileRepositoryMock()
        self.usecase = UpdateProfileUsecase(self.repo)

    def test_admin_updates_role_and_scope(self):
        profile = self.usecase(
            requester_user_id=ADMIN_USER_ID,
            target_user_id=INSPECTOR_USER_ID,
            role=ProfileRole.MANAGER,
            scope={"bairro": ["Santa Mônica"]},
        )
        assert profile.role == ProfileRole.MANAGER
        assert profile.scope == {"bairro": ["Santa Mônica"]}

    def test_inspector_cannot_update_raises_forbidden(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(
                requester_user_id=INSPECTOR_USER_ID,
                target_user_id=ADMIN_USER_ID,
                role=ProfileRole.MANAGER,
                scope={},
            )

    def test_unknown_requester_raises_forbidden(self):
        with pytest.raises(ForbiddenAction):
            self.usecase(
                requester_user_id="00000000-0000-0000-0000-000000000000",
                target_user_id=INSPECTOR_USER_ID,
                role=ProfileRole.MANAGER,
                scope={},
            )

    def test_unknown_target_raises_not_found(self):
        with pytest.raises(NoItemsFound):
            self.usecase(
                requester_user_id=ADMIN_USER_ID,
                target_user_id="00000000-0000-0000-0000-000000000000",
                role=ProfileRole.MANAGER,
                scope={},
            )
