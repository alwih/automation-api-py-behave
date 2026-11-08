import json
from http.cookiejar import DefaultCookiePolicy

import requests


def new_session():
    session = requests.Session()
    session.headers.update({"Accept": "application/json"})
    # Keep no cookies: DummyJSON's login sets auth cookies that would quietly
    # authenticate later requests and hide whether the Authorization header worked
    session.cookies.set_policy(DefaultCookiePolicy(allowed_domains=[]))
    return session


class ApiClient:
    """Thin wrapper around a requests.Session for one base URL."""

    def __init__(self, session, base_url, timeout):
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(self, method, path, json_body=None, headers=None):
        headers = dict(headers or {})
        kwargs = {}
        if json_body is not None:
            # requests' json= escapes non-ASCII as \uXXXX; send real UTF-8 bytes instead
            kwargs["data"] = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"
        return self.session.request(method, self.base_url + path, headers=headers, timeout=self.timeout, **kwargs)
