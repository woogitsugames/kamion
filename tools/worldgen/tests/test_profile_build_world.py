"""D22: the build_world stage profiler wraps existing generator functions and restores them (no Data/raw needed)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qa import profile_build_world as PB  # noqa: E402


def _get(mod, attr):
    owner = importlib.import_module(mod)
    for part in attr.split("."):
        owner = getattr(owner, part)
    return owner


def test_every_stage_resolves_and_is_restored():
    before = {(m, a): _get(m, a) for m, a in PB.STAGES}
    undo, missing = PB.install(PB.STAGES)
    try:
        assert missing == [], missing                         # a renamed generator function shows up here
        assert all(getattr(_get(m, a), "__wrapped_stage__", None) is before[(m, a)] for m, a in PB.STAGES)
    finally:
        for owner, name, fn in undo:
            setattr(owner, name, fn)
    assert all(_get(m, a) is before[(m, a)] for m, a in PB.STAGES)


def test_timer_counts_calls():
    PB.TIMES.clear()
    f = PB._wrap("k", lambda x: x + 1)
    assert f(1) == 2 and f(2) == 3
    assert PB.TIMES["k"][0] == 2 and PB.TIMES["k"][1] >= 0.0
