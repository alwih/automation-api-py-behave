"""DummyJSON login helpers."""

from typing import Any

from requests import Response

from api.client import ApiClient
from config.settings import Settings

LOGIN_PATH = "/auth/login"


def credentials(settings: Settings) -> tuple[str, str]:
    username, password = settings.dummyjson_username, settings.dummyjson_password
    if not (username and password):
        raise RuntimeError(
            "DummyJSON credentials are not set. Copy .env.example to .env, "
            "or set DUMMYJSON_USERNAME and DUMMYJSON_PASSWORD."
        )
    return username, password


def login(client: ApiClient, username: str, password: str, **extra: Any) -> Response:
    body = {"username": username, "password": password, **extra}
    return client.request("POST", LOGIN_PATH, json_body=body)
