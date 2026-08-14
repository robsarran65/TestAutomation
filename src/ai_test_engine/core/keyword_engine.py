"""
The keyword library: the vocabulary available in the ``Action`` column.

Each keyword is one action a test step can perform. Every keyword shares the
same three-argument signature so the runners can dispatch them uniformly
without knowing which one they are calling:

    keyword(driver, locator, value)

    driver  - the Selenium WebDriver (ignored by the API keywords)
    locator - the step's XPath cell, or a JSON field path for API keywords
    value   - the step's Data cell (a URL, text to type, expected value, ...)

Unused positions are named ``_`` by convention. A keyword signals failure by
raising -- usually via ``assert`` -- and the runner records that as a FAIL.

To add a keyword: define a function with this signature, then register it in
``KEYWORD_MAP`` at the bottom. It becomes usable in test workbooks immediately.
"""

import requests
from selenium.webdriver.common.by import By
from ai_test_engine.core.ai_engine import ai_suggest_locator_repair
from ai_test_engine.config.settings import API_TIMEOUT, VERIFY_SSL

# =========================================================
# GLOBAL CONTEXT FOR API + VARIABLES
# =========================================================
# Shared state carried between steps within a run. API keywords are separate
# function calls with no return value, so the response from api_get has to live
# somewhere the later verify/save keywords can reach.
#   last_response - the most recent requests.Response
#   variables     - values captured by api_save_field, keyed by variable name
# NOTE: module-level, therefore process-wide. Fine for sequential runs; it
# would need per-run isolation before tests could execute in parallel.
API_CONTEXT = {
    "last_response": None,
    "variables": {}
}

# =========================================================
# JSON PATH RESOLVER
# =========================================================
def _resolve_json_path(data, path: str):
    """Walk a dotted path into nested JSON, indexing lists by number.

    Example:
        ``nearest_area.0.areaName.0.value`` descends into the ``nearest_area``
        key, takes element 0, then ``areaName``, element 0, then ``value``.

    Returns:
        The value at the path, or None if any segment is missing or the path
        runs into a non-container (so a bad path fails the assertion in the
        calling keyword rather than raising here).
    """
    parts = path.split(".")
    current = data
    for part in parts:
        if isinstance(current, list):
            current = current[int(part)]
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current

# =========================================================
# SELF-HEALING LOCATOR WRAPPER
# =========================================================
def _find_element_with_self_heal(driver, xpath: str):
    """Find an element, asking the AI engine to repair a stale XPath.

    This is the "self-healing" behaviour: when a locator stops matching --
    typically because the UI changed -- the current DOM is handed to
    ``ai_suggest_locator_repair`` for a replacement, which is then retried.

    NOTE: that repair function is currently a stub returning the original
    XPath, so the retry fails the same way. Wiring a real LLM call into
    core/ai_engine.py is what activates this.
    """
    try:
        return driver.find_element(By.XPATH, xpath)
    except Exception:
        dom = driver.page_source
        new_xpath = ai_suggest_locator_repair(xpath, dom)

        # Only retry if the repair actually differs. ai_suggest_locator_repair
        # is a stub that returns its input unchanged, so retrying blindly
        # re-runs a lookup we already know fails -- and with an implicit wait
        # configured, that doubles the cost of every failing step.
        if new_xpath == xpath:
            raise

        return driver.find_element(By.XPATH, new_xpath)

# =========================================================
# UI KEYWORDS
# =========================================================
def launch_url(driver, _, url):
    """Navigate the browser to ``url``. Usually the first step of a test."""
    driver.get(url)

def enter_text(driver, xpath, value):
    """Type ``value`` into the element at ``xpath``, replacing what's there."""
    element = _find_element_with_self_heal(driver, xpath)
    element.clear()  # don't append to an existing value
    element.send_keys(value)

def click(driver, xpath, _):
    """Click the element at ``xpath``."""
    element = _find_element_with_self_heal(driver, xpath)
    element.click()

def verify_text(driver, xpath, expected):
    """Assert the element at ``xpath`` contains ``expected``.

    A substring match, not equality, so a step can check for a phrase inside a
    larger block of text without pinning the whole string.
    """
    element = _find_element_with_self_heal(driver, xpath)
    actual = element.text.strip()
    assert expected in actual, f"Expected '{expected}', got '{actual}'"

# =========================================================
# API KEYWORDS
# =========================================================
# These ignore the driver entirely -- they exercise HTTP endpoints, not a UI.
# api_get must run before any of the verify/save keywords, since they all read
# the response it stores in API_CONTEXT.
def api_get(driver, _, url):
    """Send a GET request and stash the response for later steps.

    The timeout is not optional: without one, an endpoint that accepts the
    connection and then never replies hangs the whole test run indefinitely.
    """
    API_CONTEXT["last_response"] = requests.get(
        url, timeout=API_TIMEOUT, verify=VERIFY_SSL
    )

def api_verify_status(driver, _, expected_status):
    """Assert the last response's HTTP status matches ``expected_status``."""
    resp = API_CONTEXT["last_response"]
    assert resp is not None, "No API response available"
    # Workbook cells arrive as strings; coerce before comparing.
    assert resp.status_code == int(expected_status), \
        f"Expected {expected_status}, got {resp.status_code}"

def api_verify_json_field(driver, field_path, expected_value):
    """Assert a field in the last JSON response equals ``expected_value``.

    ``field_path`` is a dotted path (see ``_resolve_json_path``). Both sides
    are compared as strings, since the workbook has no type information.
    """
    resp = API_CONTEXT["last_response"]
    assert resp is not None, "No API response available"
    data = resp.json()
    actual = _resolve_json_path(data, field_path)
    assert str(actual) == str(expected_value), \
        f"Expected '{expected_value}', got '{actual}'"

def api_save_field(driver, field_path, var_name):
    """Capture a field from the last response into a named variable.

    Lets a later step reuse a value the API generated -- an id, a token -- via
    ``api_verify_variable_exists`` or a ``{{var_name}}`` placeholder.
    """
    resp = API_CONTEXT["last_response"]
    assert resp is not None, "No API response available"
    data = resp.json()
    value = _resolve_json_path(data, field_path)
    API_CONTEXT["variables"][var_name] = value

def api_verify_variable_exists(driver, var_name, _):
    """Assert a variable saved by ``api_save_field`` is present and non-None."""
    value = API_CONTEXT["variables"].get(var_name)
    assert value is not None, f"Variable '{var_name}' not found or is None"

# =========================================================
# KEYWORD MAP
# =========================================================
# The dispatch table. Keys are exactly what a test workbook's Action column
# must contain; an Action missing from here fails the step as "Unknown action".
KEYWORD_MAP = {
    # UI
    "launch_url": launch_url,
    "enter_text": enter_text,
    "click": click,
    "verify_text": verify_text,

    # API
    "api_get": api_get,
    "api_verify_status": api_verify_status,
    "api_verify_json_field": api_verify_json_field,
    "api_save_field": api_save_field,
    "api_verify_variable_exists": api_verify_variable_exists,
}

# =========================================================
# BROWSER REQUIREMENT
# =========================================================
# Which keywords actually need a WebDriver. The api_* family talks plain HTTP
# and ignores the driver argument entirely, so an API-only workbook can run
# with no browser installed at all.
#
# Runners use requires_browser() to decide whether to start Chrome. Add any
# new browser-driving keyword here as well as to KEYWORD_MAP, otherwise a
# workbook using it will run without a driver and fail on a None reference.
BROWSER_KEYWORDS = frozenset({
    "launch_url",
    "enter_text",
    "click",
    "verify_text",
})


def requires_browser(actions) -> bool:
    """Return True if any action in ``actions`` needs a WebDriver.

    Args:
        actions: Iterable of Action cell values. Non-string values (blank
            cells, which pandas reads as NaN) are coerced and simply won't
            match, so they are treated as not needing a browser.

    Unknown actions count as *needing* a browser: a typo should surface as the
    step's own "Unknown action" failure, not as a confusing None-driver crash.
    """
    for action in actions:
        name = str(action).strip()
        if name in BROWSER_KEYWORDS:
            return True
        if name not in KEYWORD_MAP and name not in ("", "nan", "None"):
            return True  # unknown -> assume browser, let the step report it
    return False
