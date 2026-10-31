"""Settings for the APIs under test.

Each setting is looked up in this order; the first non-empty value wins:
  1. behave userdata:       behave -D REQUEST_TIMEOUT=5
  2. environment variables: REQUEST_TIMEOUT=5 behave
  3. the .env file in the repository root (copy .env.example)
  4. DEFAULTS below
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

# Credentials have no default on purpose: they come from .env or the environment
DEFAULTS = {
    "JSONPLACEHOLDER_BASE_URL": "https://jsonplaceholder.typicode.com",
    "DUMMYJSON_BASE_URL": "https://dummyjson.com",
    "REQUEST_TIMEOUT": "10",
}


@dataclass(frozen=True)
class Settings:
    jsonplaceholder_base_url: str
    dummyjson_base_url: str
    request_timeout: float
    dummyjson_username: str | None = None
    dummyjson_password: str | None = field(default=None, repr=False)

    @property
    def base_urls(self):
        return {
            "jsonplaceholder": self.jsonplaceholder_base_url,
            "dummyjson": self.dummyjson_base_url,
        }


def load_settings(userdata=None, environ=None, env_file=ENV_FILE):
    sources = [
        userdata or {},
        os.environ if environ is None else environ,
        dotenv_values(env_file),
        DEFAULTS,
    ]

    def lookup(name):
        for source in sources:
            value = (source.get(name) or "").strip()
            if value:
                return value
        return None

    raw_timeout = lookup("REQUEST_TIMEOUT")
    try:
        timeout = float(raw_timeout)
    except ValueError:
        raise ValueError(f"REQUEST_TIMEOUT must be a number of seconds, got {raw_timeout!r}") from None
    if timeout <= 0:
        raise ValueError(f"REQUEST_TIMEOUT must be greater than 0, got {raw_timeout!r}")

    return Settings(
        jsonplaceholder_base_url=lookup("JSONPLACEHOLDER_BASE_URL"),
        dummyjson_base_url=lookup("DUMMYJSON_BASE_URL"),
        request_timeout=timeout,
        dummyjson_username=lookup("DUMMYJSON_USERNAME"),
        dummyjson_password=lookup("DUMMYJSON_PASSWORD"),
    )
