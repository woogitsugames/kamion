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
    thinning radius keeps its position, species, height, variant, yaw and lean (ADR 0173)."""
    import numpy as np

    free = np.zeros((131, 131), bool)
    edit = free.copy()
    edit[131 - 1 - 25:131 - 1 - 15, 15:25] = True        # rows = north (j = y1 - n), cols = east: e 15..25, n 15..25
    a, b = _place(free), _place(edit)
    far = lambda t: not (12.0 <= t["e"] <= 28.0 and 12.0 <= t["n"] <= 28.0)  # noqa: E731
    key = lambda t: (t["src"], t["e"], t["n"])  # noqa: E731
    fa = sorted((t for t in a if far(t)), key=key)
    fb = sorted((t for t in b if far(t)), key=key)
    assert len(a) > 200 and len(b) < len(a)
    assert fa == fb


def test_vegetation_two_runs_identical():
    import numpy as np

    g = np.zeros((131, 131), bool)
    assert json.dumps(_place(g)) == json.dumps(_place(g))


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
