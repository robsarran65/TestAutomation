"""
Entry point for running the AI Test Automation Engine
"""

import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.absolute()

def main():
    """Run the Streamlit application"""
    streamlit_script = PROJECT_ROOT / "src" / "app_multiagent.py"
    
    if not streamlit_script.exists():
        print(f"Error: Streamlit app not found at {streamlit_script}")
        sys.exit(1)
    
    # Run streamlit app
    subprocess.run([
        "streamlit",
        "run",
        str(streamlit_script),
        "--logger.level=info"
    ])

if __name__ == "__main__":
    main()
