"""Unit test (no Data/raw): the engine material table must not contain duplicate dict keys.

A duplicated key in a dict literal silently wins with the LAST value (the earlier entry is dead code) —
that is how `concrete_pole` was defined twice in streetscape/materials.py. This test parses the module
with `ast` and fails on any dict literal with a repeated string key.

Run: uv run --project tools/worldgen pytest tests/gis -q -m unit
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

MATERIALS_PY = Path(__file__).resolve().parents[2] / "tools" / "worldgen" / "streetscape" / "materials.py"


def _duplicate_keys(node: ast.Dict) -> list[str]:
    seen: set[str] = set()
    dups: list[str] = []
    for key in node.keys:
        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            if key.value in seen and key.value not in dups:
                dups.append(key.value)
            seen.add(key.value)
    return dups


def test_materials_module_has_no_duplicate_dict_keys():
    tree = ast.parse(MATERIALS_PY.read_text(encoding="utf-8"), filename=str(MATERIALS_PY))
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for dup in _duplicate_keys(node):
                offenders.append(f"line {node.lineno}: duplicate key {dup!r}")
    assert not offenders, "duplicate dict keys in materials.py (last one wins, earlier is dead):\n" + "\n".join(offenders)


def test_concrete_pole_kept_value():
    from streetscape import materials as MAT

    # the surviving (later, previously winning) entry — removing the earlier duplicate must not change it
    # (the module post-processing only adds derived keys like sky_occ, so compare the authored fields)
    assert MAT.M["concrete_pole"]["color"] == [0.33, 0.33, 0.31]
    assert MAT.M["concrete_pole"]["rough"] == 0.9
