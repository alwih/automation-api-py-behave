import requests
from requests.structures import CaseInsensitiveDict

from api import report
from api.redaction import register_secret

LOGIN_BODY = b'{"username": "u", "password": "hunter2"}'


def make_request(headers=None, body=LOGIN_BODY):
    headers = {"Authorization": "Bearer abc.def.ghi"} if headers is None else headers
    return requests.Request("POST", "https://example.org/auth/login", headers=headers, data=body).prepare()


def make_response(body=b'{"message":"Invalid credentials"}', headers=None):
    response = requests.Response()
    response.status_code = 400
    response.reason = "Bad Request"
    response.headers = CaseInsensitiveDict(
        headers or {"Content-Type": "application/json", "Set-Cookie": "accessToken=abc.def.ghi; Path=/"}
    )
    response._content = body
    response.request = make_request()
    return response


def test_request_shows_method_url_headers_and_pretty_printed_json():
    text = report.describe_request(make_request())
    assert text.startswith("POST https://example.org/auth/login\n")
    assert "\nContent-Length: 40\n" in text
    assert text.endswith('\n\n{\n  "username": "u",\n  "password": "hunter2"\n}')


def test_authorization_keeps_only_its_scheme():
    assert "Authorization: Bearer ***" in report.describe_request(make_request())
    # A token sent without a scheme is hidden completely
    text = report.describe_request(make_request(headers={"Authorization": "abc.def.ghi"}))
    assert "Authorization: ***" in text
    assert "abc.def.ghi" not in text


def test_registered_secrets_are_redacted():
    register_secret("hunter2")
    text = report.describe_request(make_request())
    assert "hunter2" not in text
    assert '"password": "***"' in text


def test_response_shows_status_and_hides_cookies():
    text = report.describe_response(make_response())
    assert text.startswith("HTTP 400 Bad Request\nContent-Type: application/json\nSet-Cookie: ***\n")
    assert "abc.def.ghi" not in text
    assert text.endswith('\n\n{\n  "message": "Invalid credentials"\n}')


def test_a_body_that_is_not_json_is_shown_as_is_and_an_empty_one_is_left_out():
    assert report.describe_response(make_response(body=b"Not Found")).endswith("\n\nNot Found")
    assert "\n\n" not in report.describe_request(make_request(body=None))


def test_attach_exchange_attaches_the_request_then_the_response(monkeypatch):
    attached = []
    monkeypatch.setattr(report.allure, "attach", lambda body, name, attachment_type: attached.append((name, body)))
    report.attach_exchange(make_response())
    assert [name for name, _ in attached] == ["Request", "Response"]
    assert attached[1][1].startswith("HTTP 400 Bad Request")


def test_attach_exchange_does_nothing_without_the_allure_formatter():
    report.attach_exchange(make_response())
