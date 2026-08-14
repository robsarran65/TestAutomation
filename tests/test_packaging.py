"""Packaging metadata must be correct before this ships to a client site.

The bug these guard against: requirements.txt was missing openpyxl, so anyone
installing with `pip install -r requirements.txt` (including the Dockerfile)
got an app that could not read a single .xlsx test workbook.
"""

import re
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def parse_reqs(text):
    """Map requirement name -> full spec, ignoring comments and blanks."""
    out = {}
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if not line or line.startswith("-"):
            continue
        name = re.split(r"[<>=!~\[]", line)[0].strip().lower()
        out[name] = line
    return out


@pytest.fixture(scope="module")
def pyproject():
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def requirements():
    return parse_reqs((ROOT / "requirements.txt").read_text(encoding="utf-8"))


def test_requirements_and_pyproject_list_the_same_packages(pyproject, requirements):
    declared = parse_reqs("\n".join(pyproject["project"]["dependencies"]))

    assert set(declared) == set(requirements), (
        "requirements.txt and pyproject.toml disagree; "
        f"only in pyproject: {set(declared) - set(requirements)}; "
        f"only in requirements: {set(requirements) - set(declared)}"
    )


def test_requirements_and_pyproject_use_the_same_versions(pyproject, requirements):
    declared = parse_reqs("\n".join(pyproject["project"]["dependencies"]))
    mismatched = {k: (declared[k], requirements[k])
                  for k in declared if declared[k] != requirements[k]}

    assert not mismatched, f"version drift: {mismatched}"


def test_openpyxl_is_declared(pyproject, requirements):
    """pandas.read_excel silently needs this; every workbook depends on it."""
    assert "openpyxl" in requirements
    assert "openpyxl" in parse_reqs("\n".join(pyproject["project"]["dependencies"]))


def test_pytest_is_not_a_runtime_dependency(requirements):
    assert "pytest" not in requirements, "pytest belongs in the dev extra"


def test_declared_python_floor_matches_what_we_run(pyproject):
    floor = pyproject["project"]["requires-python"]
    major, minor = re.search(r"(\d+)\.(\d+)", floor).groups()

    # pandas>=2.2 / matplotlib>=3.8.4 need 3.9+; claiming 3.8 lets pip install
    # on an interpreter where the app cannot start.
    assert (int(major), int(minor)) >= (3, 9)
    assert sys.version_info >= (int(major), int(minor))


def test_console_script_target_is_importable(pyproject):
    """A broken entry point only shows up after install; catch it here."""
    import importlib

    target = pyproject["project"]["scripts"]["ai-test-engine"]
    module, func = target.split(":")

    assert callable(getattr(importlib.import_module(module), func))


def test_package_is_discovered_from_src_layout(pyproject):
    assert pyproject["tool"]["setuptools"]["packages"]["find"]["where"] == ["src"]


def test_every_runtime_dependency_is_installed(requirements):
    """Catches a dependency added to the file but never installed here."""
    import importlib.metadata as md

    missing = []
    for name in requirements:
        try:
            md.version(name)
        except md.PackageNotFoundError:
            missing.append(name)

    assert not missing, f"declared but not installed: {missing}"
