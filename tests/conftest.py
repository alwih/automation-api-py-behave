import pytest

from api import redaction


@pytest.fixture(autouse=True)
def no_registered_secrets(monkeypatch):
    # Secrets are module-level state; give every test a clean set
    monkeypatch.setattr(redaction, "_secrets", set())
