from __future__ import annotations

import datetime
import importlib.machinery
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "bin" / "user-curfew"


@pytest.fixture(scope="session")
def module():
    loader = importlib.machinery.SourceFileLoader("user_curfew", str(SCRIPT_PATH))
    spec = importlib.util.spec_from_loader("user_curfew", loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["user_curfew"] = mod
    loader.exec_module(mod)
    return mod


@pytest.fixture
def sample_entry():
    return {
        "name": "testuser",
        "lock_time": datetime.time(23, 0),
        "unlock_time": datetime.time(5, 0),
        "days": {"mon", "tue", "wed", "thu", "fri"},
        "kill": True,
        "notify": False,
    }


@pytest.fixture
def sample_entries():
    return [
        {
            "name": "alice",
            "lock_time": datetime.time(23, 0),
            "unlock_time": datetime.time(5, 0),
            "days": {"mon", "tue", "wed", "thu", "fri"},
            "kill": True,
            "notify": True,
        },
        {
            "name": "bob",
            "lock_time": datetime.time(22, 0),
            "unlock_time": datetime.time(6, 0),
            "days": {"mon", "tue", "wed", "thu", "fri", "sat", "sun"},
            "kill": False,
            "notify": False,
        },
    ]


@pytest.fixture
def notif_disabled():
    return {"enabled": False, "warnings": 3, "interval": 5}


@pytest.fixture
def notif_enabled():
    return {"enabled": True, "warnings": 3, "interval": 5}
