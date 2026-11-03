"""Hide secrets, such as the configured password, in failure output."""

_secrets = set()


def register_secret(value):
    if value:
        _secrets.add(value)


def redact(text):
    for secret in _secrets:
        text = text.replace(secret, "***")
    return text
