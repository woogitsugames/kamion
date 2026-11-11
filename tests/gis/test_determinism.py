"""Determinism of the world generator across processes (ADR 0096).

Python randomises str hashes per process (PYTHONHASHSEED), so anything that depends on the iteration order of a
set of strings changes from run to run. `max(set(mats), key=mats.count)` in roads.meshing._emit_strip did: on a tie
the strip material (kerb / sidewalk) followed the hash order, and parking bays, cars and kerb triangles of the whole
region changed between two runs of the same code (1526 / 1500 bays, 84 942 / 84 705 kerb triangles).
"""

import os
import re
import subprocess
import sys

import pytest

from conftest import REGION_ID, REPO

HEIGHTMAP = REPO / "Data" / "raw" / "derived" / REGION_ID / "heightmap_2049.r16"
WORLDGEN = REPO / "tools" / "worldgen"
# seeds that gave three different road meshes before the fix (artifacts/determinism, probe_seed{0,4,9}.json)
SEEDS = ("0", "4", "9")


@pytest.mark.skipif(not HEIGHTMAP.exists(), reason="heightmap not built (Data/raw is gitignored)")
def test_road_stage_independent_of_hash_seed():
    procs = []
    for seed in SEEDS:
        env = {**os.environ, "PYTHONHASHSEED": seed}
        procs.append(subprocess.Popen([sys.executable, str(WORLDGEN / "qa" / "determinism.py"), "--region", REGION_ID],
                                      cwd=REPO, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
    totals = {}
    for seed, p in zip(SEEDS, procs):
        out, err = p.communicate(timeout=1500)
        assert p.returncode == 0, err[-2000:]
        line = [ln for ln in out.splitlines() if ln.startswith("TOTAL ")][-1]
        totals[seed] = line.split()[1:]
    assert len({tuple(v) for v in totals.values()}) == 1, totals


def test_strip_material_tie_is_first_along_the_strip():
    """The rule itself: majority material, a tie goes to the material met first (not to the hash order)."""
    src = (WORLDGEN / "roads" / "meshing.py").read_text(encoding="utf-8")
    assert "mat = max(dict.fromkeys(mats), key=mats.count)" in src
    for mats in (["curb_concrete", "sidewalk_paving"], ["sidewalk_paving", "curb_concrete"],
                 ["verge_grass", "curb_concrete", "curb_concrete", "verge_grass"]):
        assert max(dict.fromkeys(mats), key=mats.count) == mats[0]
    assert max(dict.fromkeys(["a", "b", "b"]), key=["a", "b", "b"].count) == "b"


# a set fed straight into an order-sensitive consumer; `sorted(set(...))` / `sorted({...})` is the fixed form
ORDER_FROM_SET = re.compile(r"\b(?:max|min|next|list|tuple|enumerate)\(\s*(?:iter\(\s*)?set\(|\bfor\s+[\w, ()]+\s+in\s+set\(")


def test_no_order_taken_from_a_set_in_the_generator():
    bad = []
    for d in ("roads", "streetscape", "terrain_mesh"):
        for p in sorted((WORLDGEN / d).rglob("*.py")):
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                code = line.split("#", 1)[0]
                if ORDER_FROM_SET.search(code):
                    bad.append(f"{p.relative_to(REPO).as_posix()}:{n}: {line.strip()}")
    assert not bad, "iteration order of a set decides the result (PYTHONHASHSEED):\n" + "\n".join(bad)
