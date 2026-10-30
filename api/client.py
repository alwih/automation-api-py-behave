import json


class ApiClient:
    """Thin wrapper around a requests.Session for one base URL."""

    def __init__(self, session, base_url, timeout):
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(self, method, path, json_body=None):
        kwargs = {}
        if json_body is not None:
            # requests' json= escapes non-ASCII as \uXXXX; send real UTF-8 bytes instead
            kwargs["data"] = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
            kwargs["headers"] = {"Content-Type": "application/json; charset=utf-8"}
        return self.session.request(method, self.base_url + path, timeout=self.timeout, **kwargs)
