"""ADR 0267: the start-menu region catalog is generated (scripts/export-region-catalog.py) and carries d67-full (D71)."""
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/export-region-catalog.py"
CATALOG = REPO / "game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json"
D71_EXTRA = ["bialystok-dojlidy", "knyszyn-w", "dk65-monki-01", "dw671-tykocin-01"]


def _module():
    spec = importlib.util.spec_from_file_location("export_region_catalog", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sets(cat: dict) -> dict[str, list[str]]:
    return {s["name"]: s["regions"] for s in cat["sets"]}


def test_check_passes_on_the_committed_catalog():
    r = subprocess.run([sys.executable, str(SCRIPT), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_d67_full_is_d67_plus_the_d71_regions():
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    sets = _sets(cat)
    ids = [r["id"] for r in cat["regions"]]
    assert len(sets["d67"]) == 17
    assert sets["d67-full"] == sets["d67"] + D71_EXTRA
    assert len(sets["d67-full"]) == 21 == len(set(sets["d67-full"]))
    assert all(r in ids for r in sets["d67-full"])
    assert all((REPO / "Data/Regions" / r / "route_start.json").exists() for r in D71_EXTRA)


def test_derived_set_is_regenerated_when_missing_or_stale():
    mod = _module()
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))

    missing = copy.deepcopy(cat)
    missing["sets"] = [s for s in missing["sets"] if s["name"] != "d67-full"]
    problems: list[str] = []
    mod.apply_derived_sets(missing, problems)
    assert any("d67-full: missing" in p for p in problems)
    assert missing["sets"] == cat["sets"], "regenerated in the same place (after d67) with the same content"

    stale = copy.deepcopy(cat)
    next(s for s in stale["sets"] if s["name"] == "d67")["regions"].append("dk65-monki-01")
    problems = []
    mod.apply_derived_sets(stale, problems)
    assert any("d67-full: stale" in p for p in problems)
    full = _sets(stale)["d67-full"]
    assert full.count("dk65-monki-01") == 1 and len(full) == 21, "no duplicates when the base set already holds an extra"

    unchanged = copy.deepcopy(cat)
    problems = []
    mod.apply_derived_sets(unchanged, problems)
    assert problems == [] and unchanged == cat
