"""
Entry point for running the AI Test Automation Engine.
"""

import subprocess
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent / "app_multiagent.py"


def main():
    """Run the Streamlit application."""
    if not APP.exists():
        print(f"Error: Streamlit app not found at {APP}")
        sys.exit(1)

    sys.exit(subprocess.call(
        ["streamlit", "run", str(APP), "--logger.level=info"]
    ))


if __name__ == "__main__":
    main()
