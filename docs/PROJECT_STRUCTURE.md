# Project Structure

Standard Python **src-layout**: the importable package lives under `src/`, so
tests run against the *installed* package rather than accidentally importing
loose files from the repo root.

```
streamlit-automation-poc/
│
├── src/ai_test_engine/           # The package (everything importable)
│   ├── __init__.py               # Version + UTF-8 stdout setup
│   ├── __main__.py               # `python -m ai_test_engine` -> launches the UI
│   ├── app.py                    # Streamlit UI, single-agent mode
│   ├── app_multiagent.py         # Streamlit UI, multi-agent mode (primary)
│   ├── demo_workflow.py          # End-to-end demo of the agent pipeline
│   ├── prompts.py                # LLM prompt templates (kept out of the code)
│   │
│   ├── agents/                   # Multi-agent architecture
│   │   ├── agent_base.py         # Agent ABC + TaskMessage/TaskResult contract
│   │   ├── coordinator.py        # Routes tasks, resolves dependencies, retries
│   │   ├── executor.py           # Drives Chrome through test steps
│   │   ├── ai_generation.py      # LLM-backed test/data generation
│   │   ├── report.py             # HTML / PDF / summary output
│   │   └── specialized.py        # Locator repair, data validation, perf analysis
│   │
│   ├── core/                     # Single-agent execution engine
│   │   ├── keyword_engine.py     # KEYWORD_MAP: the Action vocabulary
│   │   ├── keyword_library.py    # Human-readable keyword reference
│   │   ├── test_runner.py        # Excel workbook -> browser run -> reports
│   │   └── ai_engine.py          # LLM helper stubs (no API key required)
│   │
│   ├── config/settings.py        # All paths + env-backed settings
│   └── utils/helpers.py          # Small dependency-free helpers
│
├── tests/                        # pytest suite (35 tests, no browser needed)
├── data/test_data/               # Sample .xlsx test workbooks
├── outputs/                      # Generated artifacts — git-ignored
│   ├── reports/                  # HTML + PDF dashboards, charts  <-- reports land HERE
│   ├── logs/                     # Plain run logs
│   └── screenshots/              # Failure screenshots
├── scripts/run_tests.py          # Standalone demo report generator
├── docs/                         # Documentation
├── .github/workflows/ci.yml      # Install package -> pytest -> bandit
├── pyproject.toml                # Single source of packaging + tool config
└── .env.example                  # Copy to .env; see config/settings.py
```

## Where output goes

| Artifact | Location |
|---|---|
| HTML dashboard | `outputs/reports/<name>_report.html` |
| PDF report | `outputs/reports/<name>_report.pdf` |
| Pass/fail chart | `outputs/reports/<name>_chart.png` |
| Screenshots | `outputs/screenshots/` |

All paths come from `config/settings.py` and are anchored to the repo root, so
output lands in the same place regardless of the current working directory.
Never hardcode an output path — import the constant:

```python
from ai_test_engine.config.settings import REPORTS_DIR
```

`outputs/` is git-ignored except for `.gitkeep` placeholders; generated files
are build artifacts, not source.

## Imports

The package is installed (`pip install -e .`), so imports are absolute and
work from anywhere — no `sys.path` manipulation:

```python
from ai_test_engine.agents.coordinator import CoordinatorAgent
from ai_test_engine.core.keyword_engine import KEYWORD_MAP
from ai_test_engine.config.settings import REPORTS_DIR
```

## Setup

```bash
pip install -e ".[dev]"     # installs the package + pytest
pytest                      # run the suite
streamlit run src/ai_test_engine/app_multiagent.py
```

## Extension points

| To add… | Do this |
|---|---|
| A test action/keyword | Add the function to `core/keyword_engine.py`, register it in `KEYWORD_MAP` |
| An agent | Add an `AgentType` member, subclass `Agent`, implement `execute`, register with the Coordinator |
| An LLM provider | Add a branch in `agents/ai_generation.py`; put the prompt in `prompts.py` |
| A setting | Add it to `config/settings.py` and document it in `.env.example` |
