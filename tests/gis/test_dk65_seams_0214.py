"""ADR 0214: seams of the DK65 corridor tiles dk65-06 ... dk65-11 (+ dk65-05 and knyszyn-s) and the construction_site stage.

File-level tests on region data (no build needed) + unit tests of streetscape.construction_site on a synthetic grid."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import yaml
from shapely.geometry import LineString, box

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "Data" / "Regions"
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
TILES = ["dk65-05", "dk65-06", "dk65-07", "dk65-08", "dk65-09", "dk65-10", "dk65-11", "knyszyn-s"]
SEAMS = list(zip(TILES, TILES[1:]))
# dk65-05 still carries the ADR 0207 Ełcka section (7.6 m); owner D65 p.5 (6.9 m) is applied in dk65-06 here and in
# dk65-02..05 by the separately queued correction task (HANDOVER D65 (b)).
PENDING_0207 = {("dk65-05", "dk65-06")}
# Research K1 (research/dk65-knyszyn-refs): edge lines 6.0-6.4 m apart up to km 25.0 -> dk65-06..11 carry 2 x 3.1 + 2 x 0.2 m
# (`dk65-xsec-k1`). ADR 0233: knyszyn-s keeps that section on its first 484 m through a `width` profile on the seam edge
# (the knyszyn-s set starts at the repaving joint km 25.32), so the set of the overrides differs across that seam while
# the built section is the same - checked on the network and on the meshes in test_dk65_seam_knyszyn_0233.py.
PROFILED_SEAM = {("dk65-11", "knyszyn-s")}
K1_SET = (2, 3.1, 0.2)


def _load(t):
    d = REG / t
    if not (d / "route_start.json").exists():
        pytest.skip(f"{t}: no route_start.json (build_world not run)")
    g = json.loads((d / "roads.graph.json").read_text(encoding="utf-8"))
    r = json.loads((d / "route_start.json").read_text(encoding="utf-8"))
    ov = (yaml.safe_load((d / "overrides.yaml").read_text(encoding="utf-8")) or {}).get("overrides", []) \
        if (d / "overrides.yaml").exists() else []
    return {e["id"]: e for e in g["edges"]}, r["edge"], ov


def _effective(edge, ovs):
    """(width, edge_lines, lanes, lane_width, edge_strip, lamps) after the matching overrides (last wins)."""
    out = {"width": round(float((edge["attrs"].get("width") or {}).get("v") or 0), 2), "edge_lines": None, "lanes": None,
           "lane_width": None, "edge_strip": None, "lamps": None}
    for ov in ovs:
        if ov.get("kind"):
            continue
        tg, st = ov.get("target", {}), ov.get("set", {})
        ways = tg.get("osm_way")
        ways = ways if isinstance(ways, list) else ([ways] if ways is not None else [])
        if tg.get("edge") == edge["id"] or edge["osm_way"] in {int(x) for x in ways}:
            for k in out:
                if k in st and not isinstance(st[k], list):
                    out[k] = st[k]
            if any(k in st for k in ("lanes", "lane_width", "edge_strip")):
                out["width"] = None            # width follows lanes x lane_width + 2 x edge_strip
    return out


@pytest.mark.parametrize("a,b", SEAMS)
def test_seam_cross_section_matches(a, b):
    ea, ra, oa = _load(a)
    eb, rb, ob = _load(b)
    last, first = ea[ra[-1]], eb[rb[0]]
    assert last["osm_way"] == first["osm_way"], f"{a}->{b}: route leaves via way {last['osm_way']}, enters via {first['osm_way']}"
    if (a, b) in PENDING_0207:
        pytest.xfail("dk65-05 Ełcka 7.6 m (ADR 0207) until the D65 p.5 correction of dk65-02..05 lands")
    va, vb = _effective(last, oa), _effective(first, ob)
    if (a, b) in PROFILED_SEAM:
        from test_dk65_seam_knyszyn_0233 import _section_at
        assert (va["lanes"], va["lane_width"], va["edge_strip"]) == K1_SET
        assert va["edge_lines"] == vb["edge_lines"] == "both" and va["lamps"] == vb["lamps"]
        pt = (762635.0, 609811.108)
        sa, sb = _section_at(a, pt), _section_at(b, pt)
        assert sa["width"] == pytest.approx(sb["width"], abs=1e-6) and sa["spacing"] == pytest.approx(sb["spacing"], abs=1e-6)
        return
    if b == "knyszyn-s" and vb["edge_lines"] is None and {k for k in va if va[k] != vb[k]} == {"edge_lines"}:
        pytest.xfail("knyszyn-s DK65 edge lines come with ADR 0212 (branch knyszyn-edges-0212, not merged yet)")
    assert va == vb


def test_dk65_section_k1_06_to_11():
    """Old DK65 (208187096 / 27718745): K1 section through 06..11 (ADR 0233; knyszyn-s: test_dk65_seam_knyszyn_0233)."""
    for t in TILES[1:7]:
        e, r, o = _load(t)
        vals = set()
        for eid in r:
            if e[eid]["osm_way"] in (208187096, 27718745, 1111506754):
                v = _effective(e[eid], o)
                vals.add((v["lanes"], v["lane_width"], v["edge_strip"], v["edge_lines"], v["lamps"]))
        assert vals == {K1_SET + ("both", False)}, (t, vals)


def test_k1_entry_verbatim_06_to_11():
    ent = []
    for t in TILES[1:7]:
        ov = (yaml.safe_load((REG / t / "overrides.yaml").read_text(encoding="utf-8")) or {}).get("overrides", [])
        ent.append(next(o for o in ov if o["id"] == "dk65-xsec-k1"))
        assert not any(o["id"] in ("dk65-carriageway-width", "dk65-old-xsec") for o in ov), t
    assert all(x == ent[0] for x in ent)


@pytest.mark.parametrize("a,b", SEAMS)
def test_seam_route_points_meet(a, b):
    pts = []
    for t, k in ((a, -1), (b, 0)):
        d = REG / t
        if not (d / "route_start.json").exists():
            pytest.skip(f"{t}: no route_start.json")
        r = json.loads((d / "route_start.json").read_text(encoding="utf-8"))
        o = yaml.safe_load((d / "region.yaml").read_text(encoding="utf-8"))["origin"]
        e, n = r["points_en"][k][:2]
        pts.append((e + o["x"], n + o["y"]))
    (x1, y1), (x2, y2) = pts
    assert ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5 < 2.0, pts


def _heights(t):
    tj = json.loads((REG / t / "terrain.json").read_text(encoding="utf-8"))
    f = ROOT / tj["encoding"]["file"]
    if not f.exists():
        pytest.skip(f"{t}: heightmap not on this machine ({f})")
    n = tj["samples"][0]
    z = np.fromfile(f, "<u2").reshape(n, n) * tj["encoding"]["scale_m_per_unit"] + tj["encoding"]["offset_m"]
    return tj["bbox"], z, tj["source_manifest"]


@pytest.mark.parametrize("a,b", SEAMS[1:])
def test_seam_terrain(a, b):
    """Shared tile edges carry the same NMT samples; the one survey-year change (dk65-10 NMT 2025 | dk65-11 NMT 2022,
    pinned to knyszyn-s) stays under 0.5 m."""
    (ba, za, ma), (bb, zb, mb) = _heights(a), _heights(b)
    if ba[0] == bb[2]:
        ea, eb = za[:, 0], zb[:, -1]
    elif ba[2] == bb[0]:
        ea, eb = za[:, -1], zb[:, 0]
    elif ba[3] == bb[1]:
        ea, eb = za[0, :], zb[-1, :]
    else:
        ea, eb = za[-1, :], zb[0, :]
    d = np.abs(ea - eb)
    lim = 0.01 if ma.split("-")[2] == mb.split("-")[2] else 0.5
    assert d.max() < lim, (a, ma, b, mb, float(d.max()))


def _site(t):
    ov = (yaml.safe_load((REG / t / "overrides.yaml").read_text(encoding="utf-8")) or {}).get("overrides", [])
    return [o for o in ov if o.get("kind") == "construction_site"]


@pytest.mark.parametrize("a,b", SEAMS[1:-1])
def test_seam_site_axes_continue(a, b):
    """A construction axis cut by a seam reaches past it in both tiles with the same geometry and half-width, so both
    sides get the same corridor edge (no step in the sand at the seam)."""
    import regions
    ba, bb = box(*regions.get(a).bbox), box(*regions.get(b).bbox)
    seam = ba.intersection(bb)
    if seam.is_empty:
        pytest.skip("no shared edge")
    ax = {t: {(x["osm_way"]): x for s in _site(t) for x in s["axes"]} for t in (a, b)}
    for w in set(ax[a]) & set(ax[b]):
        la, lb = LineString(ax[a][w]["line_epsg2180"]), LineString(ax[b][w]["line_epsg2180"])
        if not la.intersects(seam.buffer(0.1)):
            continue
        assert ax[a][w]["half_width_m"] == ax[b][w]["half_width_m"]
        pa, pb = la.intersection(seam.buffer(0.1)), lb.intersection(seam.buffer(0.1))
        assert pa.distance(pb) < 0.5, (w, a, b)


# ---------------------------------------------------------------- unit tests of streetscape.construction_site
def _grid(n=400):
    return SimpleNamespace(x0=-200.0, y1=200.0, z=np.zeros((n + 1, n + 1)))


def _ras(polys, hf):
    from streetscape import paved as PV
    return PV.rasterize_polys(polys, hf)


def test_construction_site_noop_without_override():
    from streetscape import construction_site as CS
    rep = {}
    assert CS.plan([{"id": "x", "target": {"osm_way": [1]}, "set": {"width": 7.0}}], (0, 0), None, rep) == []
    hf = _grid()
    zc, m = CS.shape_terrain(hf.z.copy(), np.zeros(hf.z.shape, bool), hf, [], _ras, rep)
    CS.fences(None, [], None, rep)
    assert rep == {} and not m.any() and np.array_equal(zc, hf.z)


def test_construction_site_heaps_inside_tile_and_deterministic():
    from streetscape import construction_site as CS
    ov = [{"id": "t", "kind": "construction_site", "platform_m": 0.0, "heaps_per_ha": 6.0,
           "axes": [{"osm_way": 1, "half_width_m": 30.0, "line_epsg2180": [[-250.0, 0.0], [250.0, 0.0]]}]}]
    road = LineString([(-250, -60), (250, -60)]).buffer(4.0)
    tile = box(-150, -150, 150, 150)
    hf = _grid()
    out = []
    for _ in range(2):
        rep = {}
        sites = CS.plan(ov, (0, 0), road, rep, tile=tile)
        zc, m = CS.shape_terrain(hf.z.copy(), _ras([road], hf), hf, sites, _ras, rep)
        out.append(zc)
    assert np.array_equal(out[0], out[1])
    assert rep["construction_sites"]["t"]["heaps"] > 0 and m.any()
    z = out[0]
    # nothing raised outside the tile box shrunk by 2 m (no heap cut by a seam), nothing on the road
    E = hf.x0 + np.arange(z.shape[1]); N = hf.y1 - np.arange(z.shape[0])
    outside = (np.abs(E)[None, :] > 148) | (np.abs(N)[:, None] > 148)
    assert z[outside].max() < 0.05
    assert z[_ras([road], hf)].max() == 0.0
    assert 1.0 < z.max() < 3.5
