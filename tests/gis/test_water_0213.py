"""ADR 0213: water in dk65-03 (level continuous on the dk65-02 seam), bank vegetation (reed belt ribbons + shrubs from
the orthophoto product water_banks.json), stage isolation for regions without water."""

from __future__ import annotations

import json

import numpy as np
import shapely

from conftest import REPO

REGIONS_DIR = REPO / "Data" / "Regions"


class _HF:
    def __init__(self, z, x0=0.0):
        self.z = z
        self.x0 = x0
        self.y1 = float(z.shape[0] - 1)


def _src(x0, x1):
    poly = [[x0 - 60, 95], [x1 + 60, 95], [x1 + 60, 105], [x0 - 60, 105], [x0 - 60, 95]]
    line = [[x1 + 60, 100], [x0 - 60, 100]]          # flows west (like the Supraśl), drawn downstream
    return {"bdot10k": {"OT_PTWP_A": [{"id": "R:0", "props": {"rodzaj": "woda płynąca"},
                                       "geometry": {"type": "Polygon", "coordinates": [poly]}}],
                        "OT_SWRS_L": []},
            "osm": {"lines": [{"osm_way": 1, "part": 0, "tags": {"waterway": "river", "width": "10"},
                               "geometry": {"type": "LineString", "coordinates": line}}], "areas": []}}


def _valley(x0, seed):
    """201 x 201 m tile starting at local E x0; river along N = 100 falling westward; tile-specific noise inside the
    water (the two tiles' NMT agree on the shared column only, like two neighbouring heightmaps)."""
    n = 201
    X, Y = np.meshgrid(np.arange(n, dtype=float) + x0, np.arange(n, dtype=float)[::-1])
    z = 100.0 + 0.003 * X + np.maximum(np.abs(Y - 100.0) - 5.0, 0.0) / 20.0
    rng = np.random.default_rng(seed)
    wet = np.abs(Y - 100.0) <= 5.0
    z[wet] += rng.normal(0.0, 0.05, wet.sum())
    return z


def test_seam_levels_equal_on_shared_edge():
    from streetscape import water as WT
    zw = _valley(0.0, 1)       # west tile E 0..200
    ze = _valley(200.0, 2)     # east tile E 200..400, column 0 = west tile's column 200
    ze[:, 0] = zw[:, -1]
    pw = WT.Plan(_src(0, 200), (0.0, 0.0), _HF(zw, 0.0), shapely.box(0, 0, 200, 200), shapely.Polygon())
    pe = WT.Plan(_src(200, 400), (0.0, 0.0), _HF(ze, 200.0), shapely.box(200, 0, 400, 200), shapely.Polygon())
    a, b = pw.level[:, -1], pe.level[:, 0]
    m = np.isfinite(a) & np.isfinite(b)
    assert m.sum() >= 8
    assert np.max(np.abs(a[m] - b[m])) < 1e-6
    assert any(s["edge"] == "E" for s in pw.report["seams"]) and any(s["edge"] == "W" for s in pe.report["seams"])
    # away from the edge (> SEAM_BLEND_M) a tile keeps its own levels
    assert np.isfinite(pw.level[100, 40])


def _doc():
    run = [[float(x), 106.0, 0.0, 1.0, 6.0] for x in range(10, 190, 2)]        # north shore of the valley river
    return {"runs": [run], "crowns": [[50.0, 112.0, 1.4], [120.0, 115.0, 3.0], [60.5, 112.0, 1.2]]}


def test_reed_ribbons_high_low():
    from roads.meshing import MeshBuf as Buffer
    from streetscape import reeds as RD
    buf = Buffer()
    keep = shapely.box(80, 90, 90, 130)                                       # a road across the bank
    rep = {}
    zg = lambda e, n: np.full(np.shape(e), 101.0)
    zl = lambda e, n: np.where(np.asarray(n) < 105.0, 100.2, np.nan)
    th = RD.build(buf, _doc(), zg, zl, keep, rep, layer="banks", low=False)
    tl = RD.build(buf, _doc(), zg, zl, keep, rep, layer="banks_low", low=True)
    assert th > 0 and 0 < tl < th
    for p in buf.parts:
        assert p.mat == "water_reeds" and p.COL is not None and np.all(p.COL[:, 3] == 1.0)
        used = np.unique(p.T)
        V = p.V[used]
        tall = V[:, 2] > 101.0
        # no standing ribbon vertex inside the keep-out (vertices there are collapsed to the foot)
        assert not shapely.contains_xy(keep, V[tall, 0], V[tall, 1]).any()
        assert V[:, 2].min() >= 100.2 - 0.25 - 0.12 - 1e-6 and V[:, 2].max() <= 101.0 + max(RD.HEIGHT_M) * 1.4
    assert rep["banks"]["ribbons"] >= 2 and rep["banks_low"]["triangles"] == tl


def test_shrubs_from_crowns():
    from streetscape import reeds as RD
    rep = {}
    trees = [{"e": 60.0, "n": 112.5}]
    out = RD.shrubs(_doc(), lambda e, n: np.full(np.shape(e), 101.0), trees, lambda e, n: False, rep)
    assert [t["p"] for t in out] == ["tree_shrub", "tree_alder"]        # 60.5 / 112 is within 2.5 m of a tree
    assert rep["bank_shrubs"]["skipped"]["near_tree"] == 1
    assert out == RD.shrubs(_doc(), lambda e, n: np.full(np.shape(e), 101.0), trees, lambda e, n: False, {})


def test_reed_texture_tiles_and_clips():
    from streetscape import reeds as RD
    a = np.asarray(RD.texture()).astype(float)
    assert a.shape == (RD.TEX_H, RD.TEX_W, 4)
    alpha = a[..., 3] > 127
    assert alpha[-20:].mean() > 0.9                     # foot of the belt is a closed mass
    assert alpha[:20].mean() < 0.35                     # ragged top
    # u wraps: the first and last columns carry the same strokes (drawn at x - W, x, x + W)
    assert np.abs(alpha[:, 0].astype(float) - alpha[:, -1].astype(float)).mean() < 0.25


def test_regions_and_isolation():
    import regions
    on = sorted(r.id for r in regions.REGIONS.values() if r.water)
    assert on == ["dk65-02", "dk65-03"]
    bw = (REPO / "tools" / "worldgen" / "roads" / "build_world.py").read_text(encoding="utf-8")
    assert '"water_reeds"' in bw and '"banks", "banks_low"' in bw
    assert "if w.water is not None:            # ADR 0213" in bw
    for rid in ("bialystok-industrial-c", "bialystok-dojlidy"):
        man = json.loads((REGIONS_DIR / rid / "generated" / "world_manifest.json").read_text(encoding="utf-8"))
        assert "water_reeds" not in man["materials"] and "banks" not in man["nodes"]
        assert not (REGIONS_DIR / rid / "water_banks.json").exists()


def test_water_banks_products():
    for rid in ("dk65-02", "dk65-03"):
        d = json.loads((REGIONS_DIR / rid / "water_banks.json").read_text(encoding="utf-8"))
        c = d["counts"]
        assert 0.2 < c["belt_share"] < 0.95 and c["runs"] > 20 and c["crowns"] > 50
        for run in d["runs"][:20]:
            a = np.asarray(run, float)
            assert np.allclose(np.hypot(a[:, 2], a[:, 3]), 1.0, atol=0.01)
            assert np.all(a[:, 4] >= 1.5)
