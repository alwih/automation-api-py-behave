"""Read JWTs without verifying them; the signing key belongs to the API."""
import base64
import json


def decode_jwt(token):
    """Return (header, payload) of a JWT, or raise ValueError if it isn't one."""
    parts = token.split(".") if isinstance(token, str) else []
    if len(parts) != 3:
        raise ValueError(f"expected 3 dot-separated segments, got {len(parts)}")
    try:
        header, payload = (json.loads(_b64url_decode(part)) for part in parts[:2])
    except ValueError as error:  # bad base64, bad UTF-8 and bad JSON are all ValueErrors
        raise ValueError(f"header or payload is not base64url JSON ({error})") from None
    if not (isinstance(header, dict) and isinstance(payload, dict)):
        raise ValueError("header and payload must be JSON objects")
    return header, payload


def tamper_signature(token):
    """Return the token with the first character of its signature changed."""
    header, payload, signature = token.split(".")
    first = "A" if signature[:1] != "A" else "B"
    return f"{header}.{payload}.{first}{signature[1:]}"


def _b64url_decode(segment):
    return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))
