import importlib.util
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True


@pytest.fixture
def lab_cli(tmp_path, monkeypatch):
    loader = SourceFileLoader("lab_cli", str(ROOT / "lab"))
    spec = importlib.util.spec_from_loader("lab_cli", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    monkeypatch.setattr(module, "STATE_PATH", tmp_path / "state.json")
    return module
