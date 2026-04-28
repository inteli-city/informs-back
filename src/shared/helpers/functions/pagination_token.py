import base64
import json
import logging
from typing import Optional

_TOKEN_MAX_BYTES = 10_240  # 10 KB - prevents DoS via oversized tokens
_TOKEN_MAX_KEYS = 20

logger = logging.getLogger(__name__)


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
    if len(token.encode("ascii", errors="replace")) > _TOKEN_MAX_BYTES:
        raise ValueError("Pagination token exceeds maximum allowed size")

    try:
        decoded_bytes = base64.urlsafe_b64decode(token.encode("ascii"))
        content = json.loads(decoded_bytes.decode("utf-8"))
    except Exception as err:
        raise ValueError("Invalid pagination token") from err

    if not isinstance(content, dict):
        raise ValueError("Invalid pagination token content")
    if len(content) > _TOKEN_MAX_KEYS:
        raise ValueError("Pagination token has too many keys")

    return content


def try_decode_pagination_token(token: Optional[str]) -> Optional[dict]:
    try:
        return decode_pagination_token(token)
    except ValueError:
        logger.warning("Failed to decode pagination token")
        return None
