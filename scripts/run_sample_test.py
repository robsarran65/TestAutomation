#!/usr/bin/env python3
"""
Load a sample test workbook and execute it -- no Streamlit, no file upload.

This is the headless equivalent of the app's upload-and-run flow: it reads an
.xlsx from data/test_data/, submits it to the Coordinator, lets the Test
Executor agent run it for real, and hands the results to the Report agent.

Unlike scripts/run_tests.py (which is a mock with hardcoded results), every
step here actually executes -- real HTTP calls, and a real Chrome browser for
UI workbooks.

Usage:
    python scripts/run_sample_test.py                        # weather API test (no browser)
    python scripts/run_sample_test.py --list                 # show available workbooks
    python scripts/run_sample_test.py -f login_test.xlsx     # UI test (needs Chrome)
    python scripts/run_sample_test.py -f login_data_driven.xlsx -d generated_data.xlsx

Exit code is 0 only if every step passed, so this is CI-usable as-is.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ai_test_engine.agents.agent_base import AgentType, TaskMessage, TaskStatus
from ai_test_engine.agents.coordinator import CoordinatorAgent
from ai_test_engine.agents.executor import TestExecutorAgent
from ai_test_engine.agents.report import ReportAgent, normalize_test_results
from ai_test_engine.config.settings import TEST_DATA_DIR

# The API-only workbook is the default on purpose: it needs no Chrome install
# and no display, so a fresh clone can prove the pipeline works immediately.
DEFAULT_WORKBOOK = "weather_api_test.xlsx"

# Per-task ceiling. A UI workbook waits DEFAULT_TIMEOUT (10s) per failing
# locator, so a 6-step test that fails everything still fits well inside this.
TASK_TIMEOUT_SEC = 300


# =========================================================
# WORKBOOK LOADING
# =========================================================
def list_workbooks() -> List[str]:
    """Return the sample workbook filenames shipped in data/test_data/."""
    return sorted(p.name for p in TEST_DATA_DIR.glob("*.xlsx"))


def _read(name: str) -> "pd.DataFrame":
    """Read a workbook by bare filename (from data/test_data/) or by path."""
    path = TEST_DATA_DIR / name
    if not path.is_file():
        path = Path(name)  # fall back to treating the argument as a real path

    if not path.is_file():
        available = "\n  ".join(list_workbooks())
        raise SystemExit(
            f"Workbook not found: {name}\n"
            f"Available in {TEST_DATA_DIR}:\n  {available}"
        )

    return pd.read_excel(path)


def load_steps(name: str) -> List[Dict[str, Any]]:
    """Read a *test* workbook into the list-of-dicts shape the executor wants.

    The conversion is deliberately identical to what the Streamlit app does on
    upload -- plain ``to_dict(orient="records")``, blank cells left as NaN --
    so this script exercises the same code path the UI does rather than a
    subtly cleaner variant of it.
    """
    df = _read(name)

    missing = {"Description", "Action"} - set(df.columns)
    if missing:
        raise SystemExit(
            f"{name} does not look like a test workbook -- missing column(s): "
            f"{', '.join(sorted(missing))}. Found: {', '.join(df.columns)}\n"
            f"(A data workbook belongs on --data, not --file.)"
        )

    print(f"📂 Loaded {name} ({len(df)} steps)")
    return df.to_dict(orient="records")


def load_data_rows(name: str) -> List[Dict[str, Any]]:
    """Read a *data* workbook: one row per iteration, columns are {{placeholders}}.

    No column schema to enforce here -- the headers are whatever the test
    workbook references, so ``username``/``password`` in generated_data.xlsx
    fills the ``{{username}}``/``{{password}}`` cells in login_data_driven.xlsx.
    """
    df = _read(name)
    print(f"📂 Loaded {name} ({len(df)} data row(s): {', '.join(df.columns)})")
    return df.to_dict(orient="records")


# =========================================================
# COORDINATOR HELPERS
# =========================================================
def wait_for(coordinator: CoordinatorAgent, task_id: str, label: str):
    """Block until a task finishes, then return its TaskResult.

    Polls rather than blocking on a condition because that is the interface
    the Coordinator exposes. Bounded by TASK_TIMEOUT_SEC -- an unbounded wait
    would hang CI forever if an agent died before recording a result.
    """
    deadline = time.time() + TASK_TIMEOUT_SEC

    while time.time() < deadline:
        result = coordinator.task_results.get(task_id)
        if result and result.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            icon = "✅" if result.status == TaskStatus.COMPLETED else "❌"
            print(f"{icon} {label}: {result.status.value} ({result.execution_time_ms}ms)")
            if result.status == TaskStatus.FAILED:
                raise SystemExit(f"{label} failed: {result.error}")
            return result
        time.sleep(0.25)

    raise SystemExit(f"{label} did not finish within {TASK_TIMEOUT_SEC}s")


# =========================================================
# MAIN
# =========================================================
def run(workbook: str, data_file: Optional[str], env: str, want_report: bool) -> int:
    """Execute one workbook end to end. Returns the intended process exit code."""
    test_steps = load_steps(workbook)

    data_rows = None
    if data_file:
        data_rows = load_data_rows(data_file)

    coordinator = CoordinatorAgent()
    coordinator.register_agent(TestExecutorAgent())
    coordinator.register_agent(ReportAgent())
    coordinator.start()

    try:
        # ---- Execute -------------------------------------------------
        if data_rows:
            action = "run_data_driven_test"
            payload = {"test_steps": test_steps, "data_rows": data_rows, "env": env}
        else:
            action = "run_test_cases"
            payload = {"test_steps": test_steps, "data_row": {}, "env": env}

        print(f"\n🧪 Submitting {action} (env: {env})...\n")
        exec_id = coordinator.submit_task(
            TaskMessage(agent_type=AgentType.TEST_EXECUTOR, action=action,
                        payload=payload, priority=1)
        )
        results = wait_for(coordinator, exec_id, "Execution").result

        # ---- Report --------------------------------------------------
        report_path = None
        if want_report:
            # Path().stem, not a string replace: --file may be a full path, and
            # slashes in the report filename would break the open() below it.
            stem = Path(workbook).stem
            report_id = coordinator.submit_task(
                TaskMessage(
                    agent_type=AgentType.REPORT,
                    action="generate_html_report",
                    payload={
                        # Raw: the Report agent normalizes either shape itself.
                        "test_results": results,
                        "filename": f"{stem}_{int(time.time())}",
                        "title": f"Sample Test Run - {workbook}",
                    },
                    priority=1,
                    dependencies=[exec_id],
                )
            )
            report_path = wait_for(coordinator, report_id, "Report").result.get("filepath")

        # ---- Summary -------------------------------------------------
        summary = normalize_test_results(results)
        total = summary.get("total_steps", 0)
        passed = summary.get("passed_steps", 0)
        failed = summary.get("failed_steps", 0)

        print(f"\n{'=' * 60}")
        print(f"  {workbook}: {passed}/{total} steps passed "
              f"({summary.get('success_rate', 0):.1f}%)")
        print(f"{'=' * 60}")

        for step in summary.get("steps", []):
            icon = "✅" if step["status"] == "PASS" else "❌"
            print(f"  {icon} {step['step_num']}. {step['description']} "
                  f"({step['action']}, {step['duration_ms']}ms)")
            if step["error"]:
                print(f"       ↳ {step['error']}")

        if report_path:
            print(f"\n📄 Report: {report_path}")

        return 1 if failed else 0

    finally:
        # Always stop the dispatch thread, including on Ctrl-C -- otherwise the
        # non-daemon thread keeps the interpreter alive after main() returns.
        coordinator.stop()


def main() -> int:
    """Parse arguments and dispatch. Returns the process exit code."""
    parser = argparse.ArgumentParser(
        description="Run a sample test workbook through the multi-agent pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage:")[1] if "Usage:" in __doc__ else None,
    )
    parser.add_argument("-f", "--file", default=DEFAULT_WORKBOOK,
                        help=f"workbook in data/test_data/ (default: {DEFAULT_WORKBOOK})")
    parser.add_argument("-d", "--data",
                        help="data workbook for a data-driven run, e.g. generated_data.xlsx")
    parser.add_argument("-e", "--env", default="DEV", help="environment label (default: DEV)")
    parser.add_argument("--no-report", action="store_true", help="skip HTML report generation")
    parser.add_argument("--list", action="store_true", help="list available workbooks and exit")
    args = parser.parse_args()

    if args.list:
        print(f"Sample workbooks in {TEST_DATA_DIR}:")
        for name in list_workbooks():
            marker = "  (default)" if name == DEFAULT_WORKBOOK else ""
            print(f"  • {name}{marker}")
        return 0

    return run(args.file, args.data, args.env, not args.no_report)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        sys.exit(130)
