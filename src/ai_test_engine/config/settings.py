"""
Central configuration for the AI Test Automation Engine.

Every tunable value lives here, so nothing else in the codebase needs to
hardcode a path or read an environment variable directly. Import the constant
you need rather than recomputing it:

    from ai_test_engine.config.settings import REPORTS_DIR

Settings sourced from the environment are read via ``os.getenv`` with a safe
default, so the project runs out of the box with no ``.env`` file present.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env before any os.getenv call below, so a local .env can override the
# defaults. override=False means real environment variables (e.g. those set by
# CI or Docker) always win over the file.
load_dotenv(override=False)

# --------------------------------------------------------------------------
# Directory layout
# --------------------------------------------------------------------------
PACKAGE_DIR = Path(__file__).resolve().parents[1]


def _detect_project_root() -> Path:
    """Locate the directory that outputs/ and data/ hang off.

    This cannot simply walk up a fixed number of levels. In a source checkout
    this file is at ``<root>/src/ai_test_engine/config/settings.py`` (root is
    4 up), but once pip-installed it is at
    ``<venv>/Lib/site-packages/ai_test_engine/config/settings.py``, where 4 up
    is ``<venv>/Lib`` -- so an installed deployment wrote its reports inside
    site-packages, which is the wrong place and is often read-only.

    Resolution order:
        1. ``AI_TEST_ENGINE_HOME`` if set -- an explicit answer always wins,
           and gives client sites a way to pin a writable data directory.
        2. The source checkout, identified by a pyproject.toml 4 levels up.
        3. The current working directory, for installed deployments.
    """
    override = os.getenv("AI_TEST_ENGINE_HOME")
    if override:
        return Path(override).expanduser().resolve()

    candidate = Path(__file__).resolve().parents[3]
    if (candidate / "pyproject.toml").is_file():
        return candidate

    return Path.cwd().resolve()


PROJECT_ROOT = _detect_project_root()

DATA_DIR = PROJECT_ROOT / "data"
TEST_DATA_DIR = DATA_DIR / "test_data"       # sample .xlsx test-case workbooks
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"

# All generated artifacts live under outputs/ and are git-ignored.
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REPORTS_DIR = OUTPUTS_DIR / "reports"        # HTML/PDF dashboards + charts
LOGS_DIR = OUTPUTS_DIR / "logs"              # plain run logs
SCREENSHOTS_DIR = OUTPUTS_DIR / "screenshots"  # failure screenshots

# Created eagerly on import so writers never have to check first.
for directory in [LOGS_DIR, REPORTS_DIR, SCREENSHOTS_DIR, TEST_DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

def _env_bool(name: str, default: bool) -> bool:
    """Read a boolean from the environment. Accepts true/1/yes/on."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    """Read an int from the environment, falling back on a bad value."""
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


# --------------------------------------------------------------------------
# Environment
# --------------------------------------------------------------------------
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# --------------------------------------------------------------------------
# Browser settings  (applied in core/browser.py)
# --------------------------------------------------------------------------
# HEADLESS must be true anywhere without a display -- servers, containers, CI.
# It defaults to true when ENVIRONMENT is anything other than "development",
# so a production deployment is correct without extra configuration.
HEADLESS_MODE = _env_bool("HEADLESS", ENVIRONMENT != "development")

# Viewport. Affects responsive layouts, and therefore which elements a
# locator can see -- a too-small window hides desktop-only navigation.
WINDOW_SIZE = (_env_int("WINDOW_WIDTH", 1920), _env_int("WINDOW_HEIGHT", 1080))

# Seconds Selenium retries a locator before failing the step. The single most
# useful knob for flaky runs on slow client hardware.
#
# Raising this also slows down *failing* tests: every step that cannot find
# its element waits the full timeout before reporting FAIL. 10s is a
# reasonable balance; raise it for slow client environments, but expect a
# suite with many genuine failures to take proportionally longer.
DEFAULT_TIMEOUT = _env_int("DEFAULT_TIMEOUT", 10)

# Seconds to wait for a page to load before raising.
PAGE_LOAD_TIMEOUT = _env_int("PAGE_LOAD_TIMEOUT", 60)

# Capture a screenshot into outputs/screenshots/ when a UI step fails.
SCREENSHOT_ON_FAILURE = _env_bool("SCREENSHOT_ON_FAILURE", True)

# --------------------------------------------------------------------------
# API keyword settings  (applied in core/keyword_engine.py)
# --------------------------------------------------------------------------
# Never leave this unset: a request with no timeout hangs forever if the
# endpoint stops responding, and takes the whole test run with it.
API_TIMEOUT = _env_int("API_TIMEOUT", 30)

# Only disable for a client with an internal CA / self-signed certificate.
VERIFY_SSL = _env_bool("VERIFY_SSL", True)

# --------------------------------------------------------------------------
# AI / LLM settings
# --------------------------------------------------------------------------
# Which backend AIGenerationAgent uses to turn plain-English descriptions into
# test steps. Accepts: "stub" | "openai" | "claude".
#   stub   - offline canned steps; no API key needed. The safe default, so a
#            fresh clone runs with zero configuration.
#   openai - needs OPENAI_API_KEY
#   claude - needs ANTHROPIC_API_KEY
# The agent falls back to "stub" if the chosen provider's SDK isn't installed.
AI_PROVIDER = os.getenv("AI_PROVIDER", "stub")

# Provider SDKs read these directly from the environment; listed here so the
# full set of recognised keys is discoverable in one place.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# NOTE: settings that existed here but were never read by any code have been
# removed (DATABASE_URL, SECRET_KEY, ALLOWED_HOSTS, STREAMLIT_*, LOG_*,
# GENERATE_*_REPORT, REPORT_TITLE, RETRY_ATTEMPTS, DEBUG, BROWSER_TYPE).
# Config that silently does nothing is worse than no config: someone sets
# HEADLESS=true, sees a browser window open anyway, and loses an afternoon.
# Re-add any of them together with the code that honours it.
#
# Browser support is Chrome only. There is no BROWSER_TYPE because Firefox
# and Edge are not implemented.
