"""Settings for the APIs under test.

Each setting is looked up in this order; the first non-empty value wins:
  1. behave userdata:       behave -D REQUEST_TIMEOUT=5
  2. environment variables: REQUEST_TIMEOUT=5 behave
  3. the .env file in the repository root (copy .env.example)
  4. DEFAULTS below
"""

import os
from collections.abc import Mapping
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
    def base_urls(self) -> dict[str, str]:
        return {
            "jsonplaceholder": self.jsonplaceholder_base_url,
            "dummyjson": self.dummyjson_base_url,
        }


def load_settings(
    userdata: Mapping[str, str] | None = None,
    environ: Mapping[str, str] | None = None,
    env_file: Path = ENV_FILE,
) -> Settings:
    sources: list[Mapping[str, str | None]] = [
        userdata or {},
        os.environ if environ is None else environ,
        dotenv_values(env_file),
        DEFAULTS,
    ]

    def lookup(name: str) -> str | None:
        for source in sources:
            value = (source.get(name) or "").strip()
            if value:
                return value
        return None

    def required(name: str) -> str:
        # Only credentials lack a default, so this fails only if a name is dropped from DEFAULTS
        value = lookup(name)
        if value is None:
            raise ValueError(f"{name} is not set and has no default")
        return value

    raw_timeout = required("REQUEST_TIMEOUT")
    try:
        timeout = float(raw_timeout)
    except ValueError:
        raise ValueError(f"REQUEST_TIMEOUT must be a number of seconds, got {raw_timeout!r}") from None
    if timeout <= 0:
        raise ValueError(f"REQUEST_TIMEOUT must be greater than 0, got {raw_timeout!r}")

    return Settings(
        jsonplaceholder_base_url=required("JSONPLACEHOLDER_BASE_URL"),
        dummyjson_base_url=required("DUMMYJSON_BASE_URL"),
        request_timeout=timeout,
        dummyjson_username=lookup("DUMMYJSON_USERNAME"),
        dummyjson_password=lookup("DUMMYJSON_PASSWORD"),
    )
