"""JSON path resolution and the API keyword surface."""

import pytest

from ai_test_engine.core import keyword_engine as ke


@pytest.fixture(autouse=True)
def clean_context():
    """Keyword state is module-global; reset it around every test."""
    ke.API_CONTEXT["last_response"] = None
    ke.API_CONTEXT["variables"] = {}
    yield
    ke.API_CONTEXT["last_response"] = None
    ke.API_CONTEXT["variables"] = {}


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


WEATHER = {"nearest_area": [{"areaName": [{"value": "London"}]}]}


def test_resolves_dotted_path_with_list_indices():
    assert ke._resolve_json_path(WEATHER, "nearest_area.0.areaName.0.value") == "London"


def test_missing_key_resolves_to_none():
    assert ke._resolve_json_path(WEATHER, "nearest_area.0.missing") is None


def test_verify_status_passes_on_match():
    ke.API_CONTEXT["last_response"] = FakeResponse({}, status_code=200)
    ke.api_verify_status(None, None, "200")  # must not raise


def test_verify_status_fails_on_mismatch():
    ke.API_CONTEXT["last_response"] = FakeResponse({}, status_code=500)
    with pytest.raises(AssertionError):
        ke.api_verify_status(None, None, "200")


def test_keywords_require_a_prior_response():
    with pytest.raises(AssertionError, match="No API response"):
        ke.api_verify_status(None, None, "200")


def test_save_field_then_verify_variable_exists():
    ke.API_CONTEXT["last_response"] = FakeResponse(WEATHER)
    ke.api_save_field(None, "nearest_area.0.areaName.0.value", "city")

    assert ke.API_CONTEXT["variables"]["city"] == "London"
    ke.api_verify_variable_exists(None, "city", None)  # must not raise

    with pytest.raises(AssertionError):
        ke.api_verify_variable_exists(None, "absent", None)


def test_keyword_map_exposes_documented_actions():
    expected = {
        "launch_url", "enter_text", "click", "verify_text",
        "api_get", "api_verify_status", "api_verify_json_field",
        "api_save_field", "api_verify_variable_exists",
    }
    assert expected <= set(ke.KEYWORD_MAP)
    assert all(callable(fn) for fn in ke.KEYWORD_MAP.values())
