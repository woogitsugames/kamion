"""ADR 0173: two runs of the world generator give identical output.

Fast checks on a slice: source hashes do not depend on the checkout line endings, and the compare tool reports
identical / order-only / content differences correctly.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qa.compare_world import compare  # noqa: E402
from streetscape.far_field import _sha256  # noqa: E402


def test_source_hash_ignores_crlf(tmp_path):
    lf, crlf = tmp_path / "a.yaml", tmp_path / "b.yaml"
    lf.write_bytes(b"x: 1\ny: [2, 3]\n")
    crlf.write_bytes(b"x: 1\r\ny: [2, 3]\r\n")
    assert _sha256(lf) == _sha256(crlf)
    g1, g2 = tmp_path / "a.geojson", tmp_path / "b.geojson"
    g1.write_bytes(b'{"a":\n1}')
    g2.write_bytes(b'{"a":\r\n1}')
    assert _sha256(g1) == _sha256(g2)


def test_build_world_hashes_lf_normalised():
    src = (Path(__file__).resolve().parents[1] / "roads" / "build_world.py").read_text(encoding="utf-8")
    assert 'sha(p.read_bytes().replace(b"\\r\\n", b"\\n"))' in src


def _place(blocked):
    from types import SimpleNamespace

    import numpy as np

    from streetscape import vegetation as VG
    sq = [[[0, 0], [120, 0], [120, 120], [0, 120], [0, 0]]]
    feat = lambda i, **p: {"id": i, "props": p, "geometry": {"coordinates": sq}}  # noqa: E731
    src = {"bdot10k": {"OT_PTLZ_A": [feat("PL.TEST.LAS.1", kategoria="mieszany", rodzaj="las")],
                       "OT_PTRK_A": [], "OT_OIPR_P": [], "OT_OIPR_L": [], "OT_PTNZ_A": [feat("PL.TEST.NZ.1")],
                       "OT_PTTR_A": []},
           "osm": {"nodes": []}}
    hf = SimpleNamespace(x0=0.0, y1=float(blocked.shape[0] - 1))
    zc = np.zeros(blocked.shape, np.float32)
    trees, _ = VG.place(src, (0.0, 0.0), hf, zc, blocked, {}, overrides=[])
    return trees


def test_vegetation_local_edit_stays_local():
    """A small new blocked patch (kerb / paved area) only removes the trees on it: every tree further than the
    thinning radius keeps its position, species, height, variant, yaw and lean (ADR 0173).

    ADR 0245: the High-only forest floor (ADR 0187) is by design laid where the floor is seen from a road, i.e.
    within FLOOR_ROAD_M of a blocked cell, so a new paved patch may ADD floor plants up to that radius - and nowhere
    else. Every floor plant present in both runs is identical, and no tree of any other layer changes far away
    (before ADR 0245 the floor filter shifted the random stream of the stand mantle drawn after it)."""
    import numpy as np

    from streetscape.vegetation import FLOOR_ROAD_M

    free = np.zeros((131, 131), bool)
    free[:, 100:103] = True                               # a road along e 100..102 in both runs: floor exists in both
    edit = free.copy()
    edit[131 - 1 - 25:131 - 1 - 15, 15:25] = True        # rows = north (j = y1 - n), cols = east: e 15..25, n 15..25
    a, b = _place(free), _place(edit)
    is_floor = lambda t: t["src"].endswith(":floor")  # noqa: E731
    far = lambda t: not (12.0 <= t["e"] <= 28.0 and 12.0 <= t["n"] <= 28.0)  # noqa: E731
    key = lambda t: (t["src"], t["e"], t["n"])  # noqa: E731
    ta, tb = [t for t in a if not is_floor(t)], [t for t in b if not is_floor(t)]
    assert len(ta) > 200 and len(tb) < len(ta)
    assert sorted((t for t in ta if far(t)), key=key) == sorted((t for t in tb if far(t)), key=key)
    fa = {key(t): t for t in a if is_floor(t)}
    fb = {key(t): t for t in b if is_floor(t)}
    assert len(fa.keys() & fb.keys()) > 20 and all(fa[k] == fb[k] for k in fa.keys() & fb.keys())
    assert all(not far(fa[k]) for k in fa.keys() - fb.keys()), "a floor plant vanished far from the patch"

    def dist_to_patch(t):                                  # metres from the blocked nodes e, n in 15..24
        return float(np.hypot(max(15.0 - t["e"], 0.0, t["e"] - 24.0), max(15.0 - t["n"], 0.0, t["n"] - 24.0)))
    new_floor = [fb[k] for k in fb.keys() - fa.keys()]
    assert new_floor and max(dist_to_patch(t) for t in new_floor) <= FLOOR_ROAD_M + 1.5


def test_vegetation_two_runs_identical():
    import numpy as np

    g = np.zeros((131, 131), bool)
    assert json.dumps(_place(g)) == json.dumps(_place(g))


def test_vegetation_with_floor_identical_across_processes():
    """ADR 0245 after the merge with ADR 0222 (one `keep=` mask in `emit`): a forest with a road (floor + mantle
    active) is identical in two fresh interpreters with different hash seeds, and identical to an in-process run."""
    import hashlib
    import os
    import subprocess

    import numpy as np

    g = np.zeros((131, 131), bool)
    g[:, 100:103] = True
    here = _place(g)
    assert sum(t["src"].endswith(":floor") for t in here) > 20 and sum(t["src"].endswith(":edge") for t in here) > 20
    want = hashlib.sha256(json.dumps(here).encode()).hexdigest()
    code = ("import hashlib, json, sys, numpy as np; sys.path.insert(0, sys.argv[1]); "
            "import test_determinism_0173 as T; g = np.zeros((131, 131), bool); g[:, 100:103] = True; "
            "print(hashlib.sha256(json.dumps(T._place(g)).encode()).hexdigest())")
    for seed in ("0", "12345"):
        out = subprocess.run([sys.executable, "-c", code, str(Path(__file__).resolve().parent)], check=True,
                             capture_output=True, text=True, env={**os.environ, "PYTHONHASHSEED": seed})
        assert out.stdout.strip() == want, f"PYTHONHASHSEED={seed}"


def test_compare_world_classifies(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    i1 = [{"p": "tree", "e": 1.0, "n": 2.0}, {"p": "lamp", "e": 3.0, "n": 4.0}]
    (a / "instances_0_0.json").write_text(json.dumps({"instances": i1}))
    (b / "instances_0_0.json").write_text(json.dumps({"instances": i1}))
    assert compare(a, b) == []
    (b / "instances_0_0.json").write_text(json.dumps({"instances": i1[::-1]}))
    assert "ORDER ONLY" in compare(a, b)[0]
    (b / "instances_0_0.json").write_text(json.dumps({"instances": i1[:1]}))
    assert "CONTENT" in compare(a, b)[0]
