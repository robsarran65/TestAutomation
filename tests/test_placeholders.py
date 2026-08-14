"""Placeholder detection and substitution.

Data-driven replay should happen only when a workbook has something to
substitute -- otherwise the test is run N times for N identical results.
"""

import pandas as pd
import pytest

from ai_test_engine.config.settings import TEST_DATA_DIR
from ai_test_engine.core.test_runner import has_placeholders, substitute_placeholders


def frame(*cells):
    """One-row workbook with the standard columns."""
    cols = ["Description", "XPath", "Action", "Data"]
    return pd.DataFrame([list(cells)], columns=cols)


# --- detection --------------------------------------------------------------

def test_detects_placeholder_in_data_column():
    assert has_placeholders(frame("Enter user", "//*[@id='u']", "enter_text", "{{username}}"))


def test_detects_placeholder_in_xpath_column():
    assert has_placeholders(frame("Click", "//*[@id='{{target}}']", "click", ""))


def test_no_placeholder_means_no_replay():
    assert not has_placeholders(frame("Enter user", "//*[@id='u']", "enter_text", "student"))


def test_tolerates_inner_whitespace():
    assert has_placeholders(frame("x", "y", "enter_text", "{{ username }}"))


@pytest.mark.parametrize("cell", [
    "{ username }",      # single braces
    "{{}}",              # empty
    "plain text",
    "",
])
def test_non_placeholders_are_not_matched(cell):
    assert not has_placeholders(frame("x", "y", "enter_text", cell))


def test_blank_cells_do_not_crash_detection():
    """pandas reads empty cells as NaN; detection must coerce, not raise."""
    df = frame("Launch", float("nan"), "launch_url", "https://example.com")
    assert has_placeholders(df) is False


# --- the real sample workbooks ---------------------------------------------

def test_data_driven_sample_is_detected():
    df = pd.read_excel(TEST_DATA_DIR / "login_data_driven.xlsx")
    assert has_placeholders(df) is True


@pytest.mark.parametrize("workbook", [
    "login_test.xlsx",
    "login_test_A.xlsx",
    "login_test_B.xlsx",
    "weather_api_test.xlsx",
])
def test_static_samples_are_not_replayed(workbook):
    """These have hardcoded values, so they must run exactly once."""
    df = pd.read_excel(TEST_DATA_DIR / workbook)
    assert has_placeholders(df) is False


# --- substitution round-trip ------------------------------------------------

def test_substitution_fills_the_detected_placeholder():
    row = {"username": "student", "password": "Password123"}

    assert substitute_placeholders("{{username}}", row) == "student"
    assert substitute_placeholders("//*[@id='{{username}}']", row) == "//*[@id='student']"


def test_unknown_placeholder_is_left_alone():
    assert substitute_placeholders("{{missing}}", {"username": "u"}) == "{{missing}}"


def test_non_string_cells_pass_through():
    assert substitute_placeholders(None, {"a": 1}) is None
    assert substitute_placeholders(42, {"a": 1}) == 42
