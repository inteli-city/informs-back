"""Testes do GetLocationHistoryUsecase.

Cobre RBAC (super admin, ou tracking.view num sistema da pessoa alvo), validação de range (since <= until),
filter por user_id + range temporal e ordenação cronológica.
"""

import pytest

from src.modules.get_location_history.app.get_location_history_usecase import (
    GetLocationHistoryUsecase,
)
from src.shared.domain.entities.location_ping import LocationPing
from src.shared.domain.entities.system_membership import SystemMembership
from src.shared.domain.services.access_control import AccessControl
from src.shared.infra.repositories.system_role_repository_mock import SystemRoleRepositoryMock
from src.shared.helpers.errors.controller_errors import WrongTypeParameter
from src.shared.helpers.errors.usecase_errors import ForbiddenAction
from src.shared.infra.repositories.location_repository_mock import (
    LocationRepositoryMock,
)
from src.shared.infra.repositories.profile_repository_mock import (
    ProfileRepositoryMock,
)
from src.shared.infra.repositories.system_role_repository_mock import MOCK_GESTOR_ROLE_ID


ADMIN_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"
INSPECTOR_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120002"
TARGET_INSPECTOR = "fake-inspector-id"  # esse user é o que tem pings no LocationRepositoryMock


class TestGetLocationHistoryUsecase:
    def _build(self):
        return GetLocationHistoryUsecase(
            location_repo=LocationRepositoryMock(),
            access_control=AccessControl(ProfileRepositoryMock(), SystemRoleRepositoryMock()),
        )

    @staticmethod
    def _join(usecase, user_id, system, role_id):
        usecase.access_control.profile_repo.put_membership(
            SystemMembership(user_id=user_id, system=system, role_id=role_id, created_at=1, updated_at=1)
        )

    def test_admin_reads_full_range(self):
        usecase = self._build()
        pings = usecase(
            requester_user_id=ADMIN_ID,
            target_user_id=TARGET_INSPECTOR,
            since_ms=0,
            until_ms=10_000,
        )
        # Mock pré-popula 5 pings (ts 1000..5000).
        assert len(pings) == 5
        assert all(isinstance(p, LocationPing) for p in pings)

    def test_returns_in_chronological_order(self):
        usecase = self._build()
        pings = usecase(
            requester_user_id=ADMIN_ID,
            target_user_id=TARGET_INSPECTOR,
            since_ms=0,
            until_ms=10_000,
        )
        timestamps = [p.ts for p in pings]
        assert timestamps == sorted(timestamps)

    def test_filters_by_range(self):
        usecase = self._build()
        pings = usecase(
            requester_user_id=ADMIN_ID,
            target_user_id=TARGET_INSPECTOR,
            since_ms=2000,
            until_ms=4000,
        )
        assert [p.ts for p in pings] == [2000, 3000, 4000]

    def test_returns_empty_when_no_pings_in_range(self):
        usecase = self._build()
        pings = usecase(
            requester_user_id=ADMIN_ID,
            target_user_id=TARGET_INSPECTOR,
            since_ms=10_000,
            until_ms=20_000,
        )
        assert pings == []

    def test_returns_empty_for_unknown_user(self):
        usecase = self._build()
        pings = usecase(
            requester_user_id=ADMIN_ID,
            target_user_id="ghost",
            since_ms=0,
            until_ms=10_000,
        )
        assert pings == []

    def test_tracking_view_in_a_shared_system_reads_history(self):
        usecase = self._build()
        self._join(usecase, INSPECTOR_ID, "GAIA", MOCK_GESTOR_ROLE_ID)
        self._join(usecase, TARGET_INSPECTOR, "GAIA", "r-tecnico-gaia")

        pings = usecase(requester_user_id=INSPECTOR_ID, target_user_id=TARGET_INSPECTOR, since_ms=0, until_ms=10_000)

        assert len(pings) == 5

    def test_tracking_view_in_another_system_is_forbidden(self):
        usecase = self._build()
        self._join(usecase, INSPECTOR_ID, "GAIA", MOCK_GESTOR_ROLE_ID)
        self._join(usecase, TARGET_INSPECTOR, "UBERLANDIA", "r-tecnico-uberlandia")

        with pytest.raises(ForbiddenAction):
            usecase(requester_user_id=INSPECTOR_ID, target_user_id=TARGET_INSPECTOR, since_ms=0, until_ms=10_000)

    def test_inspector_role_is_forbidden(self):
        usecase = self._build()
        with pytest.raises(ForbiddenAction):
            usecase(
                requester_user_id=INSPECTOR_ID,
                target_user_id=TARGET_INSPECTOR,
                since_ms=0,
                until_ms=10_000,
            )

    def test_unknown_requester_is_forbidden(self):
        usecase = self._build()
        with pytest.raises(ForbiddenAction):
            usecase(
                requester_user_id="ghost",
                target_user_id=TARGET_INSPECTOR,
                since_ms=0,
                until_ms=10_000,
            )

    def test_inactive_admin_is_forbidden(self):
        usecase = self._build()
        # Marca o admin como inativo direto na lista do mock (atalho:
        # soft_delete formal exigiria outro admin ativo pra não bater no
        # guard de "último admin").
        for p in usecase.access_control.profile_repo.profiles:
            if p.user_id == ADMIN_ID:
                p.active = False
        with pytest.raises(ForbiddenAction):
            usecase(
                requester_user_id=ADMIN_ID,
                target_user_id=TARGET_INSPECTOR,
                since_ms=0,
                until_ms=10_000,
            )

    def test_inverted_range_raises(self):
        usecase = self._build()
        with pytest.raises(WrongTypeParameter):
            usecase(
                requester_user_id=ADMIN_ID,
                target_user_id=TARGET_INSPECTOR,
                since_ms=5000,
                until_ms=1000,
            )
