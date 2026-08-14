"""
Configuration and settings for the AI Test Automation Engine.
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Directory paths
SRC_DIR = PROJECT_ROOT / "src"
AGENTS_DIR = PROJECT_ROOT / "agents"
CORE_DIR = PROJECT_ROOT / "core"
DATA_DIR = PROJECT_ROOT / "data"
TEST_DATA_DIR = DATA_DIR / "test_data"
UTILS_DIR = PROJECT_ROOT / "utils"
CONFIG_DIR = PROJECT_ROOT / "config"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
LOGS_DIR = OUTPUTS_DIR / "logs"
REPORTS_DIR = OUTPUTS_DIR / "reports"
SCREENSHOTS_DIR = OUTPUTS_DIR / "screenshots"
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"

# Create directories if they don't exist
for directory in [LOGS_DIR, REPORTS_DIR, SCREENSHOTS_DIR, TEST_DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Environment settings
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Test execution settings
DEFAULT_TIMEOUT = 30
RETRY_ATTEMPTS = 3
SCREENSHOT_ON_FAILURE = True

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Report settings
GENERATE_HTML_REPORT = True
GENERATE_PDF_REPORT = False
REPORT_TITLE = "AI Test Automation Engine Report"

# Browser settings
BROWSER_TYPE = "chrome"  # chrome, firefox, edge
HEADLESS_MODE = False
WINDOW_SIZE = (1920, 1080)

# API settings
API_TIMEOUT = 30
VERIFY_SSL = True

# Database settings (if needed)
DATABASE_URL = os.getenv("DATABASE_URL", "")

# AI/LLM settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

# Streamlit settings
STREAMLIT_THEME = "light"
STREAMLIT_WIDE_LAYOUT = True

# Security settings
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
