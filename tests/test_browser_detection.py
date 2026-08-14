"""A browser should only be launched when a test actually drives one.

API-only workbooks talk plain HTTP, so they must run with no Chrome installed.
"""

from pathlib import Path

import pandas as pd
import pytest

from ai_test_engine.config.settings import TEST_DATA_DIR
from ai_test_engine.core.keyword_engine import (
    BROWSER_KEYWORDS, KEYWORD_MAP, requires_browser,
)


def test_api_only_steps_need_no_browser():
    assert requires_browser(["api_get", "api_verify_status"]) is False


def test_any_ui_step_needs_a_browser():
    assert requires_browser(["api_get", "click"]) is True


@pytest.mark.parametrize("action", sorted(BROWSER_KEYWORDS))
def test_every_browser_keyword_is_detected(action):
    assert requires_browser([action]) is True


@pytest.mark.parametrize(
    "action", sorted(set(KEYWORD_MAP) - set(BROWSER_KEYWORDS))
)
def test_no_api_keyword_triggers_a_browser(action):
    assert requires_browser([action]) is False


def test_browser_keywords_are_all_real_keywords():
    """Guards against a typo in BROWSER_KEYWORDS silently disabling detection."""
    assert BROWSER_KEYWORDS <= set(KEYWORD_MAP)


def test_blank_cells_do_not_trigger_a_browser():
    """pandas reads empty Action cells as NaN; those must not count as UI steps."""
    assert requires_browser([float("nan"), "", None, "api_get"]) is False


def test_unknown_action_assumes_browser():
    """A typo should fail as 'Unknown action', not as a None-driver crash."""
    assert requires_browser(["clik"]) is True


def test_empty_step_list_needs_no_browser():
    assert requires_browser([]) is False


# --- against the real sample workbooks -------------------------------------

def test_api_sample_workbook_needs_no_browser():
    df = pd.read_excel(TEST_DATA_DIR / "weather_api_test.xlsx")
    assert requires_browser(df["Action"]) is False


@pytest.mark.parametrize("workbook", [
    "login_test.xlsx",
    "login_test_A.xlsx",
    "login_test_B.xlsx",
    "login_data_driven.xlsx",
])
def test_ui_sample_workbooks_need_a_browser(workbook):
    df = pd.read_excel(TEST_DATA_DIR / workbook)
    assert requires_browser(df["Action"]) is True


def test_executor_skips_browser_for_api_only_steps(monkeypatch):
    """The multi-agent executor must not construct a WebDriver for API steps."""
    from ai_test_engine.agents import executor as executor_mod

    def explode(*args, **kwargs):  # fail loudly if a browser is launched
        raise AssertionError("Chrome was launched for an API-only test")

    monkeypatch.setattr(executor_mod, "create_driver", explode)

    agent = executor_mod.TestExecutorAgent()
    summary = agent._run_test_cases(
        [{"Description": "status", "XPath": "N/A",
          "Action": "api_verify_status", "Data": "200"}]
    )

    assert agent.driver is None
    # The step still ran -- and fails, because no api_get preceded it.
    assert summary["total_steps"] == 1
    assert summary["failed_steps"] == 1


def test_test_runner_skips_browser_for_api_only_workbook(monkeypatch, tmp_path):
    """Same guarantee for the single-agent runner, via the real workbook."""
    from ai_test_engine.core import test_runner as tr

    def explode(*args, **kwargs):
        raise AssertionError("Chrome was launched for an API-only workbook")

    monkeypatch.setattr(tr, "create_driver", explode)
    # Keep generated reports out of outputs/ during the test run.
    monkeypatch.setattr(tr, "REPORTS_DIR", tmp_path)

    class Workbook:
        name = "weather_api_test.xlsx"
        def __fspath__(self):
            return str(TEST_DATA_DIR / "weather_api_test.xlsx")

    runs, html, pdf = tr.run_test_from_excel(Workbook())

    assert len(runs) == 1          # no placeholders -> no data-driven replay
    assert Path(html).parent == tmp_path
