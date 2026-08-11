"""Shared fixtures for the hwdesign test suite.

The suite is tiered by what it needs:

* **tier 0** — the build graph is well formed (milliseconds, no tools)
* **tier 1** — the Python golden models are correct (seconds, no Vivado)
* **tier 2** — the full flow including xsim agrees with Python (minutes, Vivado)
* **tier 3** — a rebuild leaves the committed figures untouched

Tier 2 is marked ``vivado`` and skipped automatically when the simulator is not
available, so the suite still passes on a machine without it.
"""
from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DATATYPES_DIR = REPO_ROOT / "demos" / "datatypes"


def _load_module(name: str, path: Path):
    """Import a module by file path — the demos are scripts, not an installed package."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def datatypes():
    """The Unit 1 demo build module, imported directly from demos/datatypes."""
    return _load_module("datatypes_build", DATATYPES_DIR / "datatypes_build.py")


@pytest.fixture(scope="session")
def has_vivado() -> bool:
    from waveflow.scripts.sv_sim import sim_tool
    return shutil.which("xvlog") is not None or sim_tool("xvlog") != "xvlog"


needs_vivado = pytest.mark.skipif(
    shutil.which("xvlog") is None and not Path("C:/Xilinx").exists(),
    reason="Vivado not available",
)
