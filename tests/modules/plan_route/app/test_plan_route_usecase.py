from copy import deepcopy

import pytest

from src.modules.plan_route.app.plan_route_usecase import PlanRouteUsecase
from src.shared.domain.enums.form_status_enum import FORM_STATUS
from src.shared.domain.enums.priority_enum import PRIORITY
from src.shared.helpers.errors.usecase_errors import FormsNotFound
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
        assert total_km == 0.0

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


class TestPlanRouteUsecaseModoFormIds:
    """
    Modo `form_ids`: cliente passa lista explícita. Backend valida que cada
    form pertence ao requester (independente de status), aplica nearest-neighbor,
    e retorna 404 com missing_form_ids se algum não bater.
    """

    def test_orders_supplied_form_ids_via_nearest_neighbor(self):
        repo = FormRepositoryMock()
        # 3 forms do requester com longitudes 10, 0.1, 5 (qualquer status).
        repo.forms = [
            _build_pending_form(repo, suffix="600", user_id=REQUESTER_USER_ID,
                                latitude=0.0, longitude=10.0,
                                priority=PRIORITY.LOW, created_at=100),
            _build_pending_form(repo, suffix="601", user_id=REQUESTER_USER_ID,
                                latitude=0.0, longitude=0.1,
                                priority=PRIORITY.LOW, created_at=100),
            _build_pending_form(repo, suffix="602", user_id=REQUESTER_USER_ID,
                                latitude=0.0, longitude=5.0,
                                priority=PRIORITY.LOW, created_at=100),
        ]
        # Coloca status diferentes só pra provar que o modo form_ids ignora status.
        repo.forms[0].status = FORM_STATUS.COMPLETED
        repo.forms[1].status = FORM_STATUS.IN_PROGRESS
        repo.forms[2].status = FORM_STATUS.CANCELLED
        usecase = PlanRouteUsecase(repo)

        ordered_forms, _ = usecase(
            requester_user_id=REQUESTER_USER_ID,
            start_latitude=0.0, start_longitude=0.0,
            form_ids=[repo.forms[0].id, repo.forms[1].id, repo.forms[2].id],
        )

        # Mesmo com IDs vindos em ordem (10, 0.1, 5), deve ordenar por proximidade.
        longitudes = [f.longitude for f in ordered_forms]
        assert longitudes == [0.1, 5.0, 10.0]

    def test_form_ids_mode_accepts_any_status(self):
        # COMPLETED também deve ser aceito; o modo n filtraria, este não.
        repo = FormRepositoryMock()
        completed_form_id = repo.forms[1].id  # form 1 do mock é COMPLETED do user 002
        # Troca dono pra ser do requester.
        repo.forms[1].user_id = REQUESTER_USER_ID
        usecase = PlanRouteUsecase(repo)

        ordered_forms, _ = usecase(
            requester_user_id=REQUESTER_USER_ID,
            start_latitude=0.0, start_longitude=0.0,
            form_ids=[completed_form_id],
        )

        assert len(ordered_forms) == 1
        assert ordered_forms[0].id == completed_form_id

    def test_raises_forms_not_found_when_any_id_missing(self):
        repo = FormRepositoryMock()
        usecase = PlanRouteUsecase(repo)

        valid_id = repo.forms[2].id  # PENDING do REQUESTER_USER_ID
        invalid_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(FormsNotFound) as exc_info:
            usecase(
                requester_user_id=REQUESTER_USER_ID,
                start_latitude=0.0, start_longitude=0.0,
                form_ids=[valid_id, invalid_id],
            )

        assert exc_info.value.missing_form_ids == [invalid_id]

    def test_raises_forms_not_found_when_id_belongs_to_other_user(self):
        # Form do user 002 — passar como requester 001 deve resultar em 404.
        repo = FormRepositoryMock()
        other_user_form_id = repo.forms[1].id  # user 002
        usecase = PlanRouteUsecase(repo)

        with pytest.raises(FormsNotFound) as exc_info:
            usecase(
                requester_user_id=REQUESTER_USER_ID,
                start_latitude=0.0, start_longitude=0.0,
                form_ids=[other_user_form_id],
            )

        assert exc_info.value.missing_form_ids == [other_user_form_id]

    def test_total_distance_with_end_in_form_ids_mode(self):
        repo = FormRepositoryMock()
        repo.forms = [
            _build_pending_form(repo, suffix="700", user_id=REQUESTER_USER_ID,
                                latitude=0.0, longitude=1.0,
                                priority=PRIORITY.MEDIUM, created_at=100),
        ]
        usecase = PlanRouteUsecase(repo)

        _, total_km = usecase(
            requester_user_id=REQUESTER_USER_ID,
            start_latitude=0.0, start_longitude=0.0,
            form_ids=[repo.forms[0].id],
            end_latitude=0.0, end_longitude=2.0,
        )

        # Mesmo cálculo do teste anterior do modo n: ~222 km
        assert 220.0 < total_km < 224.0
