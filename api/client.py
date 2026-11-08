import json
from http.cookiejar import DefaultCookiePolicy
from typing import Any

import requests


def new_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    # Keep no cookies: DummyJSON's login sets auth cookies that would quietly
    # authenticate later requests and hide whether the Authorization header worked
    session.cookies.set_policy(DefaultCookiePolicy(allowed_domains=[]))
    return session


class ApiClient:
    """Thin wrapper around a requests.Session for one base URL."""

    def __init__(self, session: requests.Session, base_url: str, timeout: float) -> None:
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(
        self, method: str, path: str, json_body: Any = None, headers: dict[str, str] | None = None
    ) -> requests.Response:
        headers = dict(headers or {})
        kwargs: dict[str, Any] = {}
        if json_body is not None:
            # requests' json= escapes non-ASCII as \uXXXX; send real UTF-8 bytes instead
            kwargs["data"] = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"
        return self.session.request(method, self.base_url + path, headers=headers, timeout=self.timeout, **kwargs)
