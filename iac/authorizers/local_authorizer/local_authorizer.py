import base64
import json


def _decode_part(part: str) -> dict:
    padded = part + "=" * (-len(part) % 4)
    decoded = base64.urlsafe_b64decode(padded.encode("utf-8"))
    return json.loads(decoded.decode("utf-8"))


def _parse_token(token: str) -> dict:
    if not token:
        return {}
    if token.startswith("Bearer "):
        token = token.split(" ", 1)[1].strip()
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    return _decode_part(parts[1])


def _normalize_groups(groups) -> str:
    if isinstance(groups, list):
        return ",".join(groups)
    if isinstance(groups, str):
        return groups
    return "FORMULARIOS"


def lambda_handler(event, context):
    token = event.get("authorizationToken") or ""
    method_arn = event.get("methodArn")

    claims = _parse_token(token)
    if not claims:
        return {
            "principalId": "local-deny",
            "policyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "execute-api:Invoke",
                        "Effect": "Deny",
                        "Resource": method_arn,
                    }
                ],
            },
            "context": {
                "claims": json.dumps({}),
            },
        }

    normalized = {
        "sub": claims.get("sub", ""),
        "name": claims.get("name") or claims.get("cognito:username") or "",
        "email": claims.get("email", ""),
        "cognito:groups": _normalize_groups(claims.get("cognito:groups")),
    }

    return {
        "principalId": normalized["sub"] or "local",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": method_arn,
                }
            ],
        },
        "context": {
            "claims": json.dumps(normalized),
        },
    }
