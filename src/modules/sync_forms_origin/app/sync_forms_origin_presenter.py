import json
import os
from typing import List

from src.shared.environments import Environments
from .sync_forms_origin_usecase import SyncFormsOriginUsecase


SYSTEM_TO_ORIGIN = {
    "GAIA": "gaia",
    "GIPAV": "servicos_poa",
}


def _parse_systems() -> List[str]:
    raw = os.environ.get("SYNC_ORIGIN_SYSTEMS", "GAIA,GIPAV")
    return [item.strip().upper() for item in raw.split(",") if item.strip()]


def lambda_handler(event, context):
    limit = int(os.environ.get("SYNC_FORMS_PAGE_LIMIT", "100"))
    window_minutes = int(os.environ.get("SYNC_FORMS_WINDOW_MINUTES", "10"))

    form_repo = Environments.get_form_repo()
    origin_repo = Environments.get_origin_repo()
    usecase = SyncFormsOriginUsecase(form_repo=form_repo, origin_repo=origin_repo)

    systems = _parse_systems()
    results = usecase(
        systems=systems,
        system_mapping=SYSTEM_TO_ORIGIN,
        window_minutes=window_minutes,
        limit=limit,
    )

    payload = {
        "results": [result.__dict__ for result in results],
        "requested_systems": systems,
        "window_minutes": window_minutes,
    }

    return {
        "statusCode": 200,
        "body": json.dumps(payload, ensure_ascii=False),
        "headers": {"Content-Type": "application/json"},
    }
