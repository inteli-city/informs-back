from copy import deepcopy

import pytest

from src.modules.plan_route.app.plan_route_usecase import PlanRouteUsecase
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.enums.priority_enum import PRIORITY
from src.shared.infra.repositories.form_repository_mock import FormRepositoryMock


REQUESTER_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120001"
OTHER_USER_ID = "d61dbf66-a10f-11ed-a8fc-0242ac120002"


def _build_pending_form(
    repo: FormRepositoryMock,
    *,
    suffix: str,
    user_id: str,
    latitude: float,
    longitude: float,
    priority: PRIORITY,
    created_at: int,
):
    """Clona o form PENDING existente do mock e troca os atributos relevantes."""
    template = repo.forms[2]  # form 2 do mock já é PENDING para REQUESTER_USER_ID
    form = deepcopy(template)
    # IDs precisam ter 36 chars (validação no construtor); manter o mesmo prefixo + suffix.
    form.id = f"d61dbf66-a10f-11ed-a8fc-0242ac120{suffix}"
    form.user_id = user_id
    form.latitude = latitude
    form.longitude = longitude
    form.priority = priority
    form.status = FORM_STATUS.PENDING
    form.created_at = created_at
    return form


class TestPlanRouteUsecase:
    def test_returns_empty_list_and_zero_distance_when_no_pending_forms(self):
        repo = FormRepositoryMock()
        # OTHER_USER_ID só tem 1 form e está COMPLETED.
        usecase = PlanRouteUsecase(repo)

        ordered_forms, total_km = usecase(
            requester_user_id=OTHER_USER_ID,
            start_latitude=-23.56,
            start_longitude=-46.65,
            n=10,
        )

        assert ordered_forms == []
        assert total_km == pytest.approx(0.0, abs=1e-9)

    def test_returns_only_what_is_available_when_less_than_n(self):
        # REQUESTER_USER_ID tem apenas 1 PENDING no mock default.
        repo = FormRepositoryMock()
        usecase = PlanRouteUsecase(repo)

        ordered_forms, _ = usecase(
            requester_user_id=REQUESTER_USER_ID,
            start_latitude=0.0,
            start_longitude=0.0,
            n=10,
        )

        assert len(ordered_forms) == 1

    def test_only_picks_pending_of_requester_user(self):
        # Adiciona um PENDING para outro user — não pode aparecer no resultado.
        repo = FormRepositoryMock()
        intruder = _build_pending_form(
            repo, suffix="100", user_id=OTHER_USER_ID,
            latitude=-23.0, longitude=-46.0,
            priority=PRIORITY.HIGH, created_at=946407600000,
        )
        repo.forms.append(intruder)
        usecase = PlanRouteUsecase(repo)

        ordered_forms, _ = usecase(
            requester_user_id=REQUESTER_USER_ID,
            start_latitude=0.0, start_longitude=0.0,
            n=10,
        )

        assert all(form.user_id == REQUESTER_USER_ID for form in ordered_forms)
        assert intruder.id not in {f.id for f in ordered_forms}

    def test_orders_by_priority_desc_then_created_at_asc_before_picking_n(self):
        # 4 PENDING para o mesmo user com prioridades e datas distintas.
        # Esperamos n=2 pegar: primeiro EMERGENCY mais antigo, depois HIGH mais antigo.
        repo = FormRepositoryMock()
        repo.forms = [
            _build_pending_form(repo, suffix="200", user_id=REQUESTER_USER_ID,
                                latitude=0.0, longitude=0.0,
                                priority=PRIORITY.HIGH, created_at=200),
            _build_pending_form(repo, suffix="201", user_id=REQUESTER_USER_ID,
                                latitude=0.0, longitude=0.0,
                                priority=PRIORITY.HIGH, created_at=100),
            _build_pending_form(repo, suffix="202", user_id=REQUESTER_USER_ID,
                                latitude=0.0, longitude=0.0,
                                priority=PRIORITY.EMERGENCY, created_at=300),
            _build_pending_form(repo, suffix="203", user_id=REQUESTER_USER_ID,
                                latitude=0.0, longitude=0.0,
                                priority=PRIORITY.EMERGENCY, created_at=200),
        ]
        usecase = PlanRouteUsecase(repo)

        ordered_forms, _ = usecase(
            requester_user_id=REQUESTER_USER_ID,
            start_latitude=0.0, start_longitude=0.0,
            n=2,
        )

        # Antes do nearest-neighbor, deveriam ter sido pegos os 2 EMERGENCY
        # (mais antigos primeiro). Como ambos estão na mesma coord, a ordem
        # do nearest-neighbor é estável e mantém a ordem de chegada.
        assert len(ordered_forms) == 2
        priorities = [int(f.priority.value) for f in ordered_forms]
        assert all(p == int(PRIORITY.EMERGENCY.value) for p in priorities)
        # E entre os dois, esperamos created_at ASC primeiro (200 antes de 300)
        assert ordered_forms[0].created_at == 200
        assert ordered_forms[1].created_at == 300

    def test_applies_nearest_neighbor_seeded_at_start(self):
        # 3 PENDING todos com mesma prioridade — ordem determinada pelo
        # nearest-neighbor. Start em (0,0); pontos a 0.1°, 5°, 10° de longitude.
        # Ordem esperada de visita: 0.1° → 5° → 10°.
        repo = FormRepositoryMock()
        repo.forms = [
            _build_pending_form(repo, suffix="300", user_id=REQUESTER_USER_ID,
                                latitude=0.0, longitude=10.0,
                                priority=PRIORITY.MEDIUM, created_at=100),
            _build_pending_form(repo, suffix="301", user_id=REQUESTER_USER_ID,
                                latitude=0.0, longitude=0.1,
                                priority=PRIORITY.MEDIUM, created_at=100),
            _build_pending_form(repo, suffix="302", user_id=REQUESTER_USER_ID,
                                latitude=0.0, longitude=5.0,
                                priority=PRIORITY.MEDIUM, created_at=100),
        ]
        usecase = PlanRouteUsecase(repo)

        ordered_forms, _ = usecase(
            requester_user_id=REQUESTER_USER_ID,
            start_latitude=0.0, start_longitude=0.0,
            n=3,
        )

        longitudes = [f.longitude for f in ordered_forms]
        assert longitudes == [0.1, 5.0, 10.0]

    def test_total_distance_includes_end_when_provided(self):
        # 1 PENDING em (0, 1°). Start em (0,0), end em (0, 2°).
        # Distância: start→form (~111 km) + form→end (~111 km) = ~222 km.
        repo = FormRepositoryMock()
        repo.forms = [
            _build_pending_form(repo, suffix="400", user_id=REQUESTER_USER_ID,
                                latitude=0.0, longitude=1.0,
                                priority=PRIORITY.MEDIUM, created_at=100),
        ]
        usecase = PlanRouteUsecase(repo)

        _, total_km = usecase(
            requester_user_id=REQUESTER_USER_ID,
            start_latitude=0.0, start_longitude=0.0,
            n=1,
            end_latitude=0.0, end_longitude=2.0,
        )

        assert 220.0 < total_km < 224.0

    def test_total_distance_excludes_end_when_omitted(self):
        # 1 PENDING em (0, 1°). Start em (0,0), sem end.
        # Distância: start→form (~111 km).
        repo = FormRepositoryMock()
        repo.forms = [
            _build_pending_form(repo, suffix="500", user_id=REQUESTER_USER_ID,
                                latitude=0.0, longitude=1.0,
                                priority=PRIORITY.MEDIUM, created_at=100),
        ]
        usecase = PlanRouteUsecase(repo)

        _, total_km = usecase(
            requester_user_id=REQUESTER_USER_ID,
            start_latitude=0.0, start_longitude=0.0,
            n=1,
        )

        assert 110.0 < total_km < 112.0
