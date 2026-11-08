"""DummyJSON login helpers."""

LOGIN_PATH = "/auth/login"


def credentials(settings):
    username, password = settings.dummyjson_username, settings.dummyjson_password
    if not (username and password):
        raise RuntimeError(
            "DummyJSON credentials are not set. Copy .env.example to .env, "
            "or set DUMMYJSON_USERNAME and DUMMYJSON_PASSWORD."
        )
    return username, password


def login(client, username, password, **extra):
    body = {"username": username, "password": password, **extra}
    return client.request("POST", LOGIN_PATH, json_body=body)
