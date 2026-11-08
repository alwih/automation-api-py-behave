"""Hide secrets, such as the configured password, in failure output."""

_secrets: set[str] = set()


def register_secret(value: str | None) -> None:
    if value:
        _secrets.add(value)


def redact(text: str) -> str:
    for secret in _secrets:
        text = text.replace(secret, "***")
    return text
