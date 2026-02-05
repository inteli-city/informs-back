import base64
import json
from typing import Optional


def encode_pagination_token(last_evaluated_key: Optional[dict]) -> Optional[str]:
    if last_evaluated_key is None:
        return None

    payload = json.dumps(last_evaluated_key, sort_keys=True, separators=(",", ":"))
    token = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")
    return token


def decode_pagination_token(token: Optional[str]) -> Optional[dict]:
    if token is None:
        return None
    if not isinstance(token, str):
        raise ValueError("Pagination token must be a string")

    try:
        decoded_bytes = base64.urlsafe_b64decode(token.encode("ascii"))
        content = json.loads(decoded_bytes.decode("utf-8"))
    except Exception as err:
        raise ValueError("Invalid pagination token") from err

    if not isinstance(content, dict):
        raise ValueError("Invalid pagination token content")

    return content


def try_decode_pagination_token(token: Optional[str]) -> Optional[dict]:
    try:
        return decode_pagination_token(token)
    except ValueError:
        return None
