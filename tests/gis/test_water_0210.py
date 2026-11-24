"""ADR 0210: surface-water stage (rivers, ponds) - opt-in per region, carve + sheet on a synthetic tile."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import shapely
import yaml

from conftest import REPO

REGIONS_DIR = REPO / "Data" / "Regions"


def test_stage_is_opt_in():
    import regions
    from streetscape import water as WT
    on = sorted(r.id for r in regions.REGIONS.values() if r.water)
    # ADR 0213: + dk65-03; water-tykocin-s24: + tykocin (Narew), DW671 corridor and Knyszyn tiles with water in BDOT/OSM
    assert on == ["dk65-02", "dk65-03", "dw671-tykocin-01", "dw671-tykocin-02", "dw671-tykocin-08", "dw671-tykocin-09", "knyszyn", "knyszyn-s", "tykocin"]
    for rid in ("bialystok-industrial-c", "bialystok-dojlidy"):
        ry = yaml.safe_load((REGIONS_DIR / rid / "region.yaml").read_text(encoding="utf-8"))
        assert "water" not in ry and not WT.enabled(ry)
        assert not (REGIONS_DIR / rid / "generated" / "water_sources.json").exists()
        man = json.loads((REGIONS_DIR / rid / "generated" / "world_manifest.json").read_text(encoding="utf-8"))
        assert "water" not in man["materials"] and "water" not in man["nodes"] and "water" not in man
    ry = yaml.safe_load((REGIONS_DIR / "dk65-02" / "region.yaml").read_text(encoding="utf-8"))
    assert WT.enabled(ry)


def test_stage_hooks_guarded():
    """Without a plan (w.water is None) the streetscape stage and build_world touch no array (determinism of C)."""
    st = (REPO / "tools" / "worldgen" / "streetscape" / "stage.py").read_text(encoding="utf-8")
    assert st.count('getattr(w, "water", None) is not None') == 3      # ADR 0213: + bank vegetation
    bw = (REPO / "tools" / "worldgen" / "roads" / "build_world.py").read_text(encoding="utf-8")
    assert 'mask if w.water is None else (mask | w.water.lod_mask())' in bw
    assert '"materials": MATERIALS if w.water is None else {**MATERIALS, **region_water_materials(w.region)}' in bw      # ADR 0321


class _HF:
    def __init__(self, z):
        self.z = z
        self.x0 = 0.0
        self.y1 = float(z.shape[0] - 1)


def _src(poly_coords, line_coords, pond=None):
    feats = [{"id": "R:0", "props": {"rodzaj": "woda płynąca", "nazwa": "Testowa"},
              "geometry": {"type": "Polygon", "coordinates": [poly_coords]}}]
    lines = [{"id": "L:0", "props": {"rodzaj": "rzeka", "nazwa": "Testowa", "szerokosc": 10.0},
              "geometry": {"type": "LineString", "coordinates": line_coords}}]
    areas = []
    if pond:
        areas.append({"osm_id": 1, "osm_type": "way", "part": 0, "tags": {"natural": "water", "water": "pond"},
                      "geometry": {"type": "Polygon", "coordinates": [pond]}})
        areas.append({"osm_id": 2, "osm_type": "way", "part": 0,
                      "tags": {"natural": "water", "water": "reservoir", "intermittent": "yes"},
                      "geometry": {"type": "Polygon", "coordinates": [[[5, 5], [15, 5], [15, 15], [5, 15], [5, 5]]]}})
    return {"bdot10k": {"OT_PTWP_A": feats, "OT_SWRS_L": lines}, "osm": {"lines": [], "areas": areas}}


def _tile():
    """200 x 200 m valley: river 10 m wide along y = 100 (flows east, falls 0.4 m), banks rising 1:20."""
    n = 201
    x = np.arange(n, dtype=float)
    X, Y = np.meshgrid(x, x[::-1])
    surface = 100.4 - 0.002 * X
    z = surface + np.maximum(np.abs(Y - 100.0) - 5.0, 0.0) / 20.0 + 0.0
    poly = [[0, 95], [200, 95], [200, 105], [0, 105], [0, 95]]
    line = [[200, 100], [0, 100]]                 # BDOT drawn upstream: must be reversed by the level trend
    pond = [[150, 150], [180, 150], [180, 175], [150, 175], [150, 150]]
    z[(X >= 150) & (X <= 180) & (Y >= 150) & (Y <= 175)] = 103.0
    return z, poly, line, pond


@pytest.fixture(scope="module")
def plan():
    from streetscape import water as WT
    z, poly, line, pond = _tile()
    hf = _HF(z)
    road = shapely.box(60, 0, 68, 200)             # a road across the valley (bridge deck is not in this mask)
    p = WT.Plan(_src(poly, line, pond), (0.0, 0.0), hf, shapely.box(0, 0, 200, 200), road)
    mask = np.zeros_like(z, bool)
    mask[:, 60:69] = True
    zc = p.carve(z.copy(), mask, log=lambda *a: None)
    return p, z, zc, mask


def test_levels_fall_downstream(plan):
    p, z, zc, _ = plan
    prof = [x for x in p.report["profiles"] if x["src"].startswith("bdot10k")]
    assert prof and prof[0]["reversed"] is True
    assert prof[0]["level_first_m"] >= prof[0]["level_last_m"]
    row = 200 - 100
    lv = p.level[row, 5:195]
    assert np.all(np.diff(lv[np.isfinite(lv)]) <= 0.02)
    assert abs(p.level[row, 10] - z[row, 10]) < 0.1


def test_intermittent_skipped_and_pond_level(plan):
    p, z, _, _ = plan
    assert any(s["why"] == "intermittent=yes" for s in p.report["skipped"])
    lv = [s["level_m"] for s in p.report["still_levels"]]
    assert len(lv) == 1 and abs(lv[0] - 103.0) < 0.01


def test_carve_bed_bank_lip(plan):
    from scipy import ndimage
    p, z, zc, mask = plan
    keep = ndimage.binary_dilation(mask, iterations=2)          # ROAD_KEEP_M: conformed embankments stay
    W = p.mask & ~keep
    from streetscape import water as WT
    deep = W & (p.d_in > 2.0)                                    # ADR 0324: mud spits may rise within 2 m of the shore
    assert np.all(zc[deep] <= p.level[deep] - 0.1 + 1e-6)        # bed below the water everywhere off the road
    assert np.all(zc[W] <= p.level[W] + WT.SHORE_BAR_M + 1e-6)
    assert (p.level[W] - zc[W]).max() <= max(WT_DEPTHS()) + 1e-6
    lip = ~p.mask & (p.d_out <= 1.5) & ~np.isnan(p.lfill) & ~keep
    # the sheet edge is always under the bank; ADR 0324: bay nodes (next to the water) dip at most SHORE_DIP_M and
    # the sheet gets a patch around each of them (test_sheet)
    dry = lip & ~p.bay_mask
    assert np.all(zc[dry] >= p.lfill[dry] + 0.03)
    assert p.bay_mask.any() and np.all(zc[p.bay_mask] >= p.lfill[p.bay_mask] - WT.SHORE_DIP_M - 1e-6)
    ring = ~p.mask & (p.d_out > 1.5) & (p.d_out <= 2.4) & ~np.isnan(p.lfill) & ~keep
    assert np.all(zc[ring] >= p.lfill[ring] + 0.03)
    assert np.array_equal(zc[mask], z[mask])                     # roads untouched


def WT_DEPTHS():
    from streetscape import water as WT
    return WT.DEPTH_M.values()


def test_sheet(plan):
    from roads.meshing import MeshBuf
    p, z, zc, mask = plan
    buf = MeshBuf()
    ntri = p.sheet(buf, 100.0, log=lambda *a: None)
    assert ntri > 100
    parts = [q for q in buf.parts if q.layer == "water"]
    assert parts and all(q.mat == "water" for q in parts)
    V = np.concatenate([q.V for q in parts])
    C = np.concatenate([q.COL for q in parts])
    assert np.all((C >= 0) & (C <= 1))
    # no water on the ground road; flow points east (+E) on the river
    assert not np.any((V[:, 0] > 60.4) & (V[:, 0] < 67.6))
    # ADR 0324: every bay node (ground below the level) is under the sheet with a margin
    import shapely
    from streetscape import water as WT
    tris = shapely.union_all([shapely.Polygon(q.V[t][:, :2]) for q in parts for t in q.T]).buffer(0.01)
    jb, ib = np.nonzero(p.bay_mask & ~((p.hf.x0 + np.arange(p.mask.shape[1]) > 58.0)
                                       & (p.hf.x0 + np.arange(p.mask.shape[1]) < 70.0))[None, :])
    pts = shapely.points(p.hf.x0 + ib, p.hf.y1 - jb)
    inside = shapely.contains(tris, pts)
    edge = (ib < 2) | (jb < 2) | (ib > p.mask.shape[1] - 3) | (jb > p.mask.shape[0] - 3)
    assert inside[~edge].all()
    river = (np.abs(V[:, 1] - 100) < 3) & (V[:, 0] > 80) & (V[:, 0] < 190)
    assert np.all(C[river, 2] > 0.9)
    # every chunk's triangles stay inside that chunk (assemble() picks the chunk by the centroid)
    for q in parts:
        cen = q.V[q.T].mean(1)
        lo = np.floor(cen[:, :2].min(0) / 100.0)
        hi = np.floor((cen[:, :2].max(0) - 1e-6) / 100.0)
        assert np.array_equal(lo, hi)


def test_bank_colours(plan):
    p, *_ = plan
    col = np.zeros(p.mask.shape + (4,), np.float32)
    c = p.bank_colours(col)
    near = ~p.mask & (p.d_out <= 2.0)
    # ADR 0324: the bank next to the water is long grass OR the wet mud / sand margin
    # ADR 0330: the bed value follows the continuous outline (sd < 0), not the 1 m raster (which reaches 0.7 m out)
    wet = p.sd < -0.3
    assert np.maximum(c[..., 2], c[..., 3])[near].min() > 0.4 and c[..., 3][wet].min() > 0.5
    assert c[..., 3][near].mean() > 0.1


@pytest.mark.skipif(not (REGIONS_DIR / "dk65-02" / "generated" / "water_qa.json").exists(), reason="dk65-02 not built")
def test_dk65_02_supraśl_under_bridge():
    qa = json.loads((REGIONS_DIR / "dk65-02" / "generated" / "water_qa.json").read_text(encoding="utf-8"))
    names = {b["name"] for b in qa["bodies"] if b.get("name")}
    assert {"Supraśl", "Biała"} <= names
    sup = [x for x in qa["profiles"] if x["name"] == "Supraśl" and x["len_m"] > 1000]
    assert sup and 109.5 < sup[0]["level_last_m"] < 111.5
    assert qa["sheet"]["triangles"] > 1000
