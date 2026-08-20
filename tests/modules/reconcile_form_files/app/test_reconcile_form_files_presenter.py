import importlib
import os
from urllib.parse import parse_qs, urlsplit

from src.shared.environments import Environments


def _presenter():
    os.environ["STAGE"] = "TEST"
    Environments._reset_instance()
    from src.modules.reconcile_form_files.app import reconcile_form_files_presenter

    return importlib.reload(reconcile_form_files_presenter)


def test_kuma_push_url_replaces_status_and_msg_from_copied_monitor_url():
    presenter = _presenter()

    result = presenter._build_kuma_push_url(
        "https://kuma.example/api/push/token?status=up&msg=OK&ping=",
        status="down",
        msg="2 fotos faltando",
    )
    query = parse_qs(urlsplit(result).query, keep_blank_values=True)

    assert query == {
        "status": ["down"],
        "msg": ["2 fotos faltando"],
        "ping": [""],
    }
