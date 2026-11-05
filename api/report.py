"""Readable copies of a request and its response for the Allure report, with credentials hidden."""
import json

import allure

from api.redaction import redact

# Credentials that aren't registered secrets: tokens and session cookies
MASKED_HEADERS = {"authorization", "cookie", "set-cookie"}


def _mask(name, value):
    name = name.lower()
    if name == "authorization" and " " in value:
        return value.split(" ", 1)[0] + " ***"  # keep the scheme, so a wrong "Bearer" prefix still shows
    return "***" if name in MASKED_HEADERS else value


def _body(raw):
    text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
    try:
        return json.dumps(json.loads(text), indent=2, ensure_ascii=False)
    except ValueError:
        return text


def _describe(first_line, headers, body):
    lines = [first_line, *(f"{name}: {_mask(name, value)}" for name, value in headers.items())]
    if body:
        lines += ["", _body(body)]
    return redact("\n".join(lines))


def describe_request(request):
    return _describe(f"{request.method} {request.url}", request.headers, request.body)


def describe_response(response):
    return _describe(f"HTTP {response.status_code} {response.reason}", response.headers, response.content)


def attach_exchange(response):
    """Attach the request and response to the running Allure step; does nothing without -f allure."""
    allure.attach(describe_request(response.request), name="Request", attachment_type=allure.attachment_type.TEXT)
    allure.attach(describe_response(response), name="Response", attachment_type=allure.attachment_type.TEXT)
