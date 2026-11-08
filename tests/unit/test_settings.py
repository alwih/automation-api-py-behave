import pytest

from config.settings import load_settings


@pytest.fixture
def env_file(tmp_path):
    path = tmp_path / ".env"
    path.write_text(
        "REQUEST_TIMEOUT=3\nDUMMYJSON_USERNAME=from_file\nDUMMYJSON_PASSWORD=secret\nJSONPLACEHOLDER_BASE_URL=\n"
    )
    return path


def test_defaults_apply_when_nothing_is_set(tmp_path):
    settings = load_settings(environ={}, env_file=tmp_path / "missing.env")
    assert settings.jsonplaceholder_base_url == "https://jsonplaceholder.typicode.com"
    assert settings.dummyjson_base_url == "https://dummyjson.com"
    assert settings.request_timeout == 10.0
    assert settings.dummyjson_username is None
    assert settings.dummyjson_password is None


def test_env_file_beats_defaults_and_blank_values_fall_through(env_file):
    settings = load_settings(environ={}, env_file=env_file)
    assert settings.request_timeout == 3.0
    assert settings.dummyjson_username == "from_file"
    assert settings.jsonplaceholder_base_url == "https://jsonplaceholder.typicode.com"


def test_environment_beats_env_file(env_file):
    assert load_settings(environ={"REQUEST_TIMEOUT": "5"}, env_file=env_file).request_timeout == 5.0


def test_behave_userdata_beats_environment(env_file):
    settings = load_settings(userdata={"REQUEST_TIMEOUT": "7"}, environ={"REQUEST_TIMEOUT": "5"}, env_file=env_file)
    assert settings.request_timeout == 7.0


def test_whitespace_only_values_count_as_unset(tmp_path):
    settings = load_settings(
        userdata={"REQUEST_TIMEOUT": "   "}, environ={"REQUEST_TIMEOUT": " 6 "}, env_file=tmp_path / "missing.env"
    )
    assert settings.request_timeout == 6.0


@pytest.mark.parametrize(
    "raw, message",
    [
        ("abc", "must be a number of seconds"),
        ("0", "must be greater than 0"),
        ("-1", "must be greater than 0"),
    ],
)
def test_invalid_timeout_is_rejected(tmp_path, raw, message):
    with pytest.raises(ValueError, match=message):
        load_settings(environ={"REQUEST_TIMEOUT": raw}, env_file=tmp_path / "missing.env")


def test_password_is_not_shown_in_repr(env_file):
    settings = load_settings(environ={}, env_file=env_file)
    assert settings.dummyjson_password == "secret"
    assert "secret" not in repr(settings)
