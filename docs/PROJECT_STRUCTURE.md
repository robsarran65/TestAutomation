# Project Structure Documentation

## Directory Layout

This project follows professional AI/ML standards for code organization:

```
ai-test-automation-poc/
│
├── src/                          # Main application code
│   ├── __init__.py
│   ├── __main__.py              # Entry point for python -m
│   ├── app.py                   # Original Streamlit app
│   ├── app_multiagent.py        # Multi-agent Streamlit dashboard
│   └── demo_workflow.py         # Demo workflow example
│
├── agents/                       # Agent implementations
│   ├── __init__.py
│   ├── agent_base.py            # Base agent class
│   ├── coordinator.py           # Task coordinator (was coordinator_agent.py)
│   ├── executor.py              # Test executor (was test_executor_agent.py)
│   ├── ai_generation.py         # AI generation (was ai_generation_agent.py)
│   ├── report.py                # Report generator (was report_agent.py)
│   └── specialized.py           # Specialized agents (was specialized_agents.py)
│
├── core/                        # Core engine modules
│   ├── __init__.py
│   ├── ai_engine.py            # AI engine
│   ├── keyword_engine.py        # Keyword engine
│   ├── keyword_library.py       # Keyword library
│   └── test_runner.py           # Test runner
│
├── utils/                       # Utility modules
│   ├── __init__.py
│   ├── helpers.py              # Helper functions
│   ├── validators.py           # Validation functions
│   └── constants.py            # Constants
│
├── config/                      # Configuration modules
│   ├── __init__.py
│   ├── settings.py             # Project settings and paths
│   └── environment.py          # Environment configuration
│
├── data/                        # Data directory
│   ├── __init__.py
│   └── test_data/              # Test data files
│       ├── __init__.py
│       └── generated_data.xlsx
│
├── tests/                       # Test cases
│   ├── __init__.py
│   ├── ui/                      # UI test cases
│   ├── api/                     # API test cases
│   ├── suites/                  # Test suites
│   │   ├── smoke/
│   │   └── regression/
│   └── conftest.py             # Pytest configuration
│
├── outputs/                     # Generated outputs
│   ├── __init__.py
│   ├── logs/                   # Execution logs
│   ├── reports/                # Generated reports
│   └── screenshots/            # Test screenshots
│
├── docs/                        # Documentation
│   ├── CLOUD_DEPLOYMENT_GUIDE.md
│   ├── MULTIAGENT_ARCHITECTURE.md
│   ├── EXECUTION_RESULTS.md
│   ├── PROJECT_REVIEW.md
│   ├── QUICKSTART.md
│   ├── REPO_RELEASE_CHECKLIST.md
│   └── API.md
│
├── scripts/                     # Utility scripts
│   ├── __init__.py
│   ├── migrate_structure.py    # Structure migration script
│   └── run_tests.py            # Test execution script
│
├── .github/                     # GitHub configuration
│   └── workflows/
│       └── ci.yml              # CI/CD pipeline
│
├── README.md                    # Project README
├── setup.py                     # Package setup (legacy)
├── pyproject.toml              # Modern Python project config
├── requirements.txt            # Dependency list
├── Dockerfile                  # Docker image
├── docker-compose.yml          # Docker compose
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── SECURITY.md                # Security policy
└── LICENSE                    # MIT License
```

## Key Changes from Old Structure

| Old Path | New Path | Reason |
|----------|----------|--------|
| `framework/agent_base.py` | `agents/agent_base.py` | Agents grouped in dedicated directory |
| `framework/coordinator_agent.py` | `agents/coordinator.py` | Simplified naming |
| `framework/test_executor_agent.py` | `agents/executor.py` | Simplified naming |
| `framework/ai_generation_agent.py` | `agents/ai_generation.py` | Simplified naming |
| `framework/report_agent.py` | `agents/report.py` | Simplified naming |
| `framework/specialized_agents.py` | `agents/specialized.py` | Simplified naming |
| `framework/ai_engine.py` | `core/ai_engine.py` | Engine modules in core directory |
| `framework/keyword_engine.py` | `core/keyword_engine.py` | Engine modules in core directory |
| `framework/keyword_library.py` | `core/keyword_library.py` | Engine modules in core directory |
| `framework/test_runner.py` | `core/test_runner.py` | Engine modules in core directory |
| `app.py, app_multiagent.py` | `src/app.py, src/app_multiagent.py` | Source code in src/ |
| `demo_workflow.py` | `src/demo_workflow.py` | Source code in src/ |
| `logs/` | `outputs/logs/` | Unified outputs directory |
| `reports/` | `outputs/reports/` | Unified outputs directory |
| Scattered docs | `docs/` | All documentation centralized |
| `run_tests.py, migrate_structure.py` | `scripts/` | Utility scripts grouped |

## Import Changes

After reorganization, all imports have been updated:

```python
# Old imports
from framework.coordinator_agent import CoordinatorAgent
from framework.test_executor_agent import TestExecutorAgent
from framework.ai_engine import ai_generate_test_from_description

# New imports
from agents.coordinator import CoordinatorAgent
from agents.executor import TestExecutorAgent
from core.ai_engine import ai_generate_test_from_description
```

## Running the Application

### Option 1: Using setuptools
```bash
pip install -e .
ai-test-engine
```

### Option 2: Using Streamlit directly
```bash
streamlit run src/app_multiagent.py
```

### Option 3: Using Python module
```bash
python -m src
```

## Installing Dependencies

```bash
# Basic installation
pip install -r requirements.txt

# With AI support
pip install -r requirements.txt[ai]

# Development setup
pip install -e ".[dev,ai]"
```

## Configuration

- **Settings**: Defined in `config/settings.py`
- **Environment Variables**: Use `.env` file (template: `.env.example`)
- **Paths**: Auto-configured relative to project root

## Testing

```bash
pytest tests/
pytest tests/ -v --cov
```

## Building Distribution Packages

```bash
python setup.py sdist bdist_wheel
# or
pip install build
python -m build
```

## Best Practices

1. **Imports**: Use absolute imports from project root
   ```python
   from agents.coordinator import CoordinatorAgent
   from config.settings import PROJECT_ROOT
   ```

2. **Logging**: Use standard Python logging with module names
   ```python
   import logging
   logger = logging.getLogger(__name__)
   ```

3. **Configuration**: Use `config.settings` for project-wide settings
   ```python
   from config.settings import OUTPUTS_DIR, DEBUG
   ```

4. **Data Files**: Store in `data/test_data/` directory
   ```python
   from config.settings import TEST_DATA_DIR
   test_file = TEST_DATA_DIR / "login_test.xlsx"
   ```

5. **Reports**: Generate to `outputs/reports/` directory
   ```python
   from config.settings import REPORTS_DIR
   report_path = REPORTS_DIR / "test_report.html"
   ```
