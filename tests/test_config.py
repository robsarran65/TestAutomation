"""Configuration must actually reach the code that uses it.

These tests exist because 26 of 33 settings were previously declared and never
read -- config that silently does nothing is worse than no config at all.
"""

import importlib

import pytest

from ai_test_engine.config import settings


def reload_settings(monkeypatch, **env):
    """Re-import settings with the given environment applied."""
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    return importlib.reload(settings)


@pytest.fixture(autouse=True)
def restore_settings():
    """Undo any reload so one test can't leak config into the next."""
    yield
    importlib.reload(settings)


# --- headless: the deployment blocker ---------------------------------------

def test_headless_defaults_on_outside_development(monkeypatch):
    """Servers and containers have no display; headless must be the default."""
    s = reload_settings(monkeypatch, ENVIRONMENT="production")
    monkeypatch.delenv("HEADLESS", raising=False)
    s = importlib.reload(settings)
    assert s.HEADLESS_MODE is True


def test_headless_defaults_off_in_development(monkeypatch):
    monkeypatch.delenv("HEADLESS", raising=False)
    s = reload_settings(monkeypatch, ENVIRONMENT="development")
    assert s.HEADLESS_MODE is False


@pytest.mark.parametrize("raw,expected", [
    ("true", True), ("1", True), ("yes", True), ("on", True), ("TRUE", True),
    ("false", False), ("0", False), ("no", False), ("", False),
])
def test_headless_accepts_common_boolean_spellings(monkeypatch, raw, expected):
    s = reload_settings(monkeypatch, HEADLESS=raw)
    assert s.HEADLESS_MODE is expected


def test_headless_reaches_chrome_options(monkeypatch):
    """The setting must produce a real --headless flag, not just exist."""
    from ai_test_engine.core import browser

    assert "--headless=new" in browser.build_chrome_options(headless=True).arguments
    assert "--headless=new" not in browser.build_chrome_options(headless=False).arguments


def test_container_flags_are_always_present():
    """Without these, Chrome crashes or refuses to start inside Docker."""
    from ai_test_engine.core import browser

    args = browser.build_chrome_options(headless=True).arguments
    assert "--disable-dev-shm-usage" in args   # 64MB /dev/shm in containers
    assert "--no-sandbox" in args              # Chrome won't run as root without it


def test_window_size_reaches_chrome_options(monkeypatch):
    reload_settings(monkeypatch, WINDOW_WIDTH="1280", WINDOW_HEIGHT="720")
    from ai_test_engine.core import browser
    importlib.reload(browser)

    assert "--window-size=1280,720" in browser.build_chrome_options().arguments


# --- numeric settings -------------------------------------------------------

def test_numeric_settings_read_from_environment(monkeypatch):
    s = reload_settings(
        monkeypatch, DEFAULT_TIMEOUT="45", PAGE_LOAD_TIMEOUT="90", API_TIMEOUT="15"
    )
    assert (s.DEFAULT_TIMEOUT, s.PAGE_LOAD_TIMEOUT, s.API_TIMEOUT) == (45, 90, 15)


def test_bad_numeric_value_falls_back_instead_of_crashing(monkeypatch):
    """A typo in a client's .env must not take the whole app down at import."""
    monkeypatch.delenv("DEFAULT_TIMEOUT", raising=False)
    default = importlib.reload(settings).DEFAULT_TIMEOUT

    s = reload_settings(monkeypatch, DEFAULT_TIMEOUT="not-a-number")

    assert s.DEFAULT_TIMEOUT == default
    assert isinstance(s.DEFAULT_TIMEOUT, int)


def test_api_timeout_is_always_set():
    """A request with no timeout hangs the run forever if the endpoint stalls."""
    assert settings.API_TIMEOUT and settings.API_TIMEOUT > 0


def test_api_get_passes_timeout_and_ssl_verification(monkeypatch):
    from ai_test_engine.core import keyword_engine as ke

    captured = {}

    def fake_get(url, **kwargs):
        captured.update(kwargs)
        class R:
            status_code = 200
            def json(self): return {}
        return R()

    monkeypatch.setattr(ke.requests, "get", fake_get)
    ke.api_get(None, None, "https://example.com")

    assert captured["timeout"] == settings.API_TIMEOUT
    assert captured["verify"] == settings.VERIFY_SSL


# --- dead config regression -------------------------------------------------

def test_no_setting_promises_unimplemented_behaviour():
    """Removed settings must stay removed -- they misled operators."""
    for dead in ("BROWSER_TYPE", "SECRET_KEY", "DATABASE_URL", "ALLOWED_HOSTS",
                 "GENERATE_HTML_REPORT", "STREAMLIT_THEME", "RETRY_ATTEMPTS"):
        assert not hasattr(settings, dead), f"{dead} is dead config"


def test_project_root_is_the_repo_in_a_source_checkout():
    """A source checkout must anchor to the repo, not the cwd."""
    assert (settings.PROJECT_ROOT / "pyproject.toml").is_file()


def test_project_root_honours_explicit_override(monkeypatch, tmp_path):
    """Client sites pin a writable data directory with AI_TEST_ENGINE_HOME."""
    s = reload_settings(monkeypatch, AI_TEST_ENGINE_HOME=str(tmp_path))

    assert s.PROJECT_ROOT == tmp_path.resolve()
    assert s.REPORTS_DIR == tmp_path.resolve() / "outputs" / "reports"
    assert s.REPORTS_DIR.is_dir()   # created on import


def test_project_root_never_lands_inside_site_packages(monkeypatch, tmp_path):
    """Regression: installed as a wheel, PROJECT_ROOT resolved to <venv>/Lib,
    so reports were written into site-packages."""
    monkeypatch.delenv("AI_TEST_ENGINE_HOME", raising=False)
    s = importlib.reload(settings)

    parts = {p.lower() for p in s.PROJECT_ROOT.parts}
    assert not parts & {"site-packages", "dist-packages"}


def test_output_directories_exist_after_import():
    """Writers assume these exist; settings creates them on import."""
    for d in (settings.REPORTS_DIR, settings.LOGS_DIR, settings.SCREENSHOTS_DIR):
        assert d.is_dir()
