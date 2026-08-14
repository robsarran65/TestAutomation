"""The agents that run without a browser: generation, validation, analysis, reporting."""

import json

import pytest

from ai_test_engine.agents.agent_base import AgentType, TaskMessage, TaskStatus
from ai_test_engine.agents.ai_generation import AIGenerationAgent
from ai_test_engine.agents.report import ReportAgent, normalize_test_results
from ai_test_engine.agents.specialized import (
    DataValidatorAgent, LocatorRepairAgent, PerformanceAnalyzerAgent,
)

STEPS = [
    {"step_num": 1, "description": "open", "action": "launch_url",
     "status": "PASS", "duration_ms": 120, "error": ""},
    {"step_num": 2, "description": "slow bit", "action": "click",
     "status": "FAIL", "duration_ms": 2500, "error": "not found"},
]
RESULTS = {
    "total_steps": 2, "passed_steps": 1, "failed_steps": 1,
    "success_rate": 50.0, "steps": STEPS, "environment": "TEST",
}


def test_generation_stub_returns_usable_steps():
    agent = AIGenerationAgent()  # defaults to the offline stub provider
    steps = agent.generate_test_from_description("log in as admin")

    assert steps
    assert all({"Description", "XPath", "Action", "Data"} <= set(s) for s in steps)


def test_generation_agent_reports_unknown_action_as_failure():
    result = AIGenerationAgent().execute(TaskMessage(action="not_a_real_action"))

    assert result.status is TaskStatus.FAILED
    assert "not_a_real_action" in result.error


def test_unknown_provider_falls_back_to_stub():
    agent = AIGenerationAgent(llm_provider="no_such_provider")
    with pytest.raises(ValueError):
        agent.generate_test_from_description("anything")


@pytest.mark.parametrize("text,expected_first", [
    ('[{"Description": "a", "XPath": "//x", "Action": "click", "Data": ""}]', "a"),
    ('Sure! Here you go:\n[{"Description": "b", "XPath": "//y", "Action": "click", "Data": ""}]', "b"),
])
def test_parse_steps_extracts_json_even_when_wrapped_in_prose(text, expected_first):
    steps = AIGenerationAgent()._parse_steps(text, "desc")
    assert steps[0]["Description"] == expected_first


def test_parse_steps_falls_back_to_stub_on_garbage():
    steps = AIGenerationAgent()._parse_steps("no json here", "log in")
    assert steps == AIGenerationAgent()._generate_test_stub("log in")


def test_locator_repair_suggests_ranked_alternatives():
    out = LocatorRepairAgent().repair_xpath("//*[@id='login']", "<html/>", "not found")

    assert out["suggestions"]
    assert out["recommended"] == out["suggestions"][0]
    assert 0 < out["self_heal_confidence"] <= 1


def test_data_validator_flags_missing_required_field():
    out = DataValidatorAgent().validate_test_data(
        [{"username": "u1"}], schema={"username": "string", "password": "string"}
    )

    assert out["is_valid"] is False
    assert any("password" in issue for issue in out["issues"])


def test_data_validator_accepts_conforming_rows():
    out = DataValidatorAgent().validate_test_data(
        [{"username": "u1", "password": "p1"}],
        schema={"username": "string", "password": "string"},
    )
    assert out["is_valid"] is True


def test_duplicate_detection():
    row = {"username": "u1", "password": "p1"}
    out = DataValidatorAgent().detect_duplicates([row, dict(row), {"username": "u2"}])

    assert out["duplicate_count"] == 1
    assert out["duplicates"][0]["duplicate_of_index"] == 0


def test_performance_analyzer_computes_metrics():
    out = PerformanceAnalyzerAgent().analyze_test_performance(RESULTS)

    assert out["total_duration_ms"] == 2620
    assert out["max_step_duration_ms"] == 2500
    assert out["total_steps"] == 2


def test_bottlenecks_are_sorted_slowest_first():
    out = PerformanceAnalyzerAgent().identify_bottlenecks(RESULTS, threshold_ms=100)
    durations = [b["duration_ms"] for b in out["bottlenecks"]]

    assert out["bottleneck_count"] == 2
    assert durations == sorted(durations, reverse=True)


def test_analyzer_handles_results_with_no_steps():
    assert "error" in PerformanceAnalyzerAgent().analyze_test_performance({})


def test_report_agent_defaults_to_outputs_reports():
    """Reports belong in outputs/reports/, never a cwd-relative folder."""
    from pathlib import Path
    from ai_test_engine.config.settings import REPORTS_DIR

    assert Path(ReportAgent().output_dir) == REPORTS_DIR
    assert REPORTS_DIR.name == "reports"
    assert REPORTS_DIR.is_absolute()  # cwd-independent


def test_report_agent_writes_utf8_html(tmp_path):
    agent = ReportAgent(output_dir=str(tmp_path))
    out = agent.generate_html_report(RESULTS, filename="demo")

    written = tmp_path / "demo_report.html"
    assert written.exists()
    # The template contains non-ASCII glyphs; this is the cp1252 regression guard.
    text = written.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in text
    assert out["filepath"] == str(written)


def test_report_agent_summary_matches_input():
    summary = ReportAgent().generate_summary(RESULTS)

    assert summary["metrics"]["total_steps"] == 2
    assert summary["metrics"]["passed"] == 1
    assert summary["metrics"]["failed"] == 1
    assert "TEST EXECUTION SUMMARY" in summary["summary_text"]


# ---------------------------------------------------------------------------
# Data-driven results use a different key set than a single run. The renderers
# read the single-run keys, so before normalize_test_results() a data-driven
# report claimed 0 steps / 0 passed for a run that really executed several.
# ---------------------------------------------------------------------------
DATA_DRIVEN_RESULTS = {
    "test_type": "data_driven",
    "total_data_rows": 2,
    "total_steps_per_row": 2,
    "total_steps_executed": 4,
    "total_passed": 3,
    "total_failed": 1,
    "overall_success_rate": 75.0,
    "environment": "TEST",
    "iterations": [
        {"data_row_num": 1, "duration_sec": 1.5, "steps": STEPS},
        {"data_row_num": 2, "duration_sec": 2.5, "steps": STEPS},
    ],
}


def test_normalize_maps_data_driven_keys_to_renderer_keys():
    normalized = normalize_test_results(DATA_DRIVEN_RESULTS)

    assert normalized["total_steps"] == 4
    assert normalized["passed_steps"] == 3
    assert normalized["failed_steps"] == 1
    assert normalized["success_rate"] == 75.0
    assert normalized["duration_sec"] == 4.0  # summed across iterations


def test_normalize_flattens_iterations_and_labels_each_row():
    steps = normalize_test_results(DATA_DRIVEN_RESULTS)["steps"]

    assert len(steps) == 4  # 2 steps x 2 rows, not 2
    assert steps[0]["description"].startswith("[row 1]")
    assert steps[2]["description"].startswith("[row 2]")


def test_normalize_leaves_single_run_results_untouched():
    assert normalize_test_results(RESULTS) == RESULTS


def test_report_agent_renders_real_numbers_for_data_driven_runs(tmp_path):
    """The regression guard: a data-driven report must not read 0 steps."""
    agent = ReportAgent(output_dir=str(tmp_path))
    out = agent.generate_html_report(DATA_DRIVEN_RESULTS, filename="dd")

    assert out["summary"] == {"passed": 3, "failed": 1, "total": 4, "success_rate": 75.0}
    assert out["test_count"] == 4

    text = (tmp_path / "dd_report.html").read_text(encoding="utf-8")
    assert "[row 1]" in text and "[row 2]" in text


def test_report_agent_summary_handles_data_driven_shape():
    metrics = ReportAgent().generate_summary(DATA_DRIVEN_RESULTS)["metrics"]

    assert metrics == {"total_steps": 4, "passed": 3, "failed": 1, "success_rate": 75.0}
