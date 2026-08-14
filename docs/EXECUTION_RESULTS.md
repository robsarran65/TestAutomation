# Execution Results

Verified results from the current codebase. Every figure below is reproducible
with the commands shown — nothing here is illustrative.

Environment: Python 3.13, Chrome (headless), Windows.

---

## 1. Unit test suite

```bash
pytest
```

```
104 passed in ~7s
```

Requires no browser and no network. Covers the agent contract, coordinator
routing and dependency resolution, keyword engine, browser-requirement
detection, placeholder handling, configuration wiring, and packaging metadata.

---

## 2. Sample workbooks

Run through the real engine against live targets.

| Workbook | Type | Steps | Result |
|---|---|---|---|
| `weather_api_test.xlsx` | API | 5 | 5 passed |
| `login_test.xlsx` | UI | 6 | 6 passed |
| `login_test_A.xlsx` | UI | 5 | 5 passed |
| `login_test_B.xlsx` | UI | 5 | 5 passed |
| `login_data_driven.xlsx` | UI, 2 data rows | 5 × 2 | 10 passed |

UI workbooks target the public practice site
`practicetestautomation.com`; the API workbook targets `wttr.in`. No client
system is involved, so the samples are safe to run anywhere.

**`weather_api_test.xlsx` runs without a browser.** All of its steps are
`api_*` keywords, so the runner skips launching Chrome entirely — it works on
a machine with no browser installed.

---

## 3. Multi-agent demo workflow

```bash
HEADLESS=true python -m ai_test_engine.demo_workflow
```

```
Total execution time:  10.0s
Total tasks submitted: 8
Completed:             8
Failed:                0

Test iterations:       5
Steps per iteration:   5
Total steps passed:    25
Total steps failed:    0
Overall success rate:  100.0%

Agents utilized:
  ai_generation, test_executor, report,
  data_validator, performance_analyzer
```

Phases: AI generation (parallel) → data validation (parallel) → data-driven
execution → analysis and reporting (parallel) → summary.

The coordinator resolves cross-agent dependencies: execution waits on both
test generation and data validation before starting.

---

## 4. Generated artifacts

All output lands in `outputs/reports/`:

| Artifact | Filename |
|---|---|
| HTML dashboard | `<name>_report.html` |
| PDF report | `<name>_report.pdf` |
| Pass/fail chart | `<name>_chart.png` |

Open with any browser:

```bash
start outputs/reports/login_test_report.html     # Windows
open  outputs/reports/login_test_report.html     # macOS
```

`outputs/` is git-ignored — these are build artifacts, regenerated on every
run.

---

## Reproducing

```bash
pip install -e ".[dev]"
pytest                                              # section 1
streamlit run src/ai_test_engine/app_multiagent.py  # section 2, via the UI
HEADLESS=true python -m ai_test_engine.demo_workflow  # section 3
```

Sections 2 and 3 require Chrome and outbound internet access to the public
practice sites.
