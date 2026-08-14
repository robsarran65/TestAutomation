import requests
from selenium.webdriver.common.by import By
from framework.ai_engine import ai_suggest_locator_repair

# =========================================================
# GLOBAL CONTEXT FOR API + VARIABLES
# =========================================================
API_CONTEXT = {
    "last_response": None,
    "variables": {}
}

# =========================================================
# JSON PATH RESOLVER
# =========================================================
def _resolve_json_path(data, path: str):
    """
    Supports dotted paths with numeric indices, e.g.:
    nearest_area.0.areaName.0.value
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
# SELF‑HEALING LOCATOR WRAPPER
# =========================================================
def _find_element_with_self_heal(driver, xpath: str):
    try:
        return driver.find_element(By.XPATH, xpath)
    except Exception:
        dom = driver.page_source
        new_xpath = ai_suggest_locator_repair(xpath, dom)
        return driver.find_element(By.XPATH, new_xpath)

# =========================================================
# UI KEYWORDS
# =========================================================
def launch_url(driver, _, url):
    driver.get(url)

def enter_text(driver, xpath, value):
    element = _find_element_with_self_heal(driver, xpath)
    element.clear()
    element.send_keys(value)

def click(driver, xpath, _):
    element = _find_element_with_self_heal(driver, xpath)
    element.click()

def verify_text(driver, xpath, expected):
    element = _find_element_with_self_heal(driver, xpath)
    actual = element.text.strip()
    assert expected in actual, f"Expected '{expected}', got '{actual}'"

# =========================================================
# API KEYWORDS
# =========================================================
def api_get(driver, _, url):
    API_CONTEXT["last_response"] = requests.get(url)

def api_verify_status(driver, _, expected_status):
    resp = API_CONTEXT["last_response"]
    assert resp is not None, "No API response available"
    assert resp.status_code == int(expected_status), \
        f"Expected {expected_status}, got {resp.status_code}"

def api_verify_json_field(driver, field_path, expected_value):
    resp = API_CONTEXT["last_response"]
    assert resp is not None, "No API response available"
    data = resp.json()
    actual = _resolve_json_path(data, field_path)
    assert str(actual) == str(expected_value), \
        f"Expected '{expected_value}', got '{actual}'"

def api_save_field(driver, field_path, var_name):
    resp = API_CONTEXT["last_response"]
    assert resp is not None, "No API response available"
    data = resp.json()
    value = _resolve_json_path(data, field_path)
    API_CONTEXT["variables"][var_name] = value

def api_verify_variable_exists(driver, var_name, _):
    value = API_CONTEXT["variables"].get(var_name)
    assert value is not None, f"Variable '{var_name}' not found or is None"

# =========================================================
# KEYWORD MAP
# =========================================================
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
