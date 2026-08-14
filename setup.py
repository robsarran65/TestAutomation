"""
Setup configuration for AI Test Automation Engine
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="ai-test-automation-engine",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-powered test automation framework for web applications and APIs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/robsarran65/TestAutomation",
    project_urls={
        "Bug Tracker": "https://github.com/robsarran65/TestAutomation/issues",
        "Documentation": "https://github.com/robsarran65/TestAutomation/docs",
        "Source Code": "https://github.com/robsarran65/TestAutomation",
    },
    license="MIT",
    packages=find_packages(exclude=["tests", "docs", "scripts"]),
    python_requires=">=3.8",
    install_requires=[
        "streamlit>=1.28.0",
        "selenium>=4.0.0",
        "webdriver-manager>=4.0.0",
        "pandas>=1.5.0",
        "openpyxl>=3.0.0",
        "requests>=2.28.0",
        "fpdf>=1.7.2",
        "matplotlib>=3.5.0",
        "python-dotenv>=0.20.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "isort>=5.0.0",
        ],
        "ai": [
            "openai>=0.27.0",
            "anthropic>=0.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ai-test-engine=src.app_multiagent:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
    ],
)
