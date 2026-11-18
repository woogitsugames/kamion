"""ADR 0207: cross-section continuity on the seams of the DK65 corridor tiles (dk65-01 ... dk65-05).

For every OSM way of the control route that runs through two neighbouring tiles, the authored cross-section
(width, edge_lines) must be the same on both sides of the seam: the effective value = the last matching override in
overrides.yaml (edge- or way-level target), else the road-graph width (BDOT10k) and no edge lines. File-level test
(region data only; no build needed)."""
import json
from pathlib import Path

import pytest
import yaml

REG = Path(__file__).resolve().parents[2] / "Data" / "Regions"
TILES = ["dk65-01", "dk65-02", "dk65-03", "dk65-04", "dk65-05"]
SEAMS = list(zip(TILES, TILES[1:]))


def _load(t):
    d = REG / t
    if not (d / "route_start.json").exists():
        pytest.skip(f"{t}: no route_start.json")
    g = json.loads((d / "roads.graph.json").read_text(encoding="utf-8"))
    r = json.loads((d / "route_start.json").read_text(encoding="utf-8"))
    ov = (yaml.safe_load((d / "overrides.yaml").read_text(encoding="utf-8")) or {}).get("overrides", []) \
        if (d / "overrides.yaml").exists() else []
    return {e["id"]: e for e in g["edges"]}, r["edge"], ov


def _effective(edge, ovs):
    w, el = edge["attrs"]["width"]["v"], None
    for ov in ovs:
        tg, st = ov.get("target", {}), ov.get("set", {})
        ways = tg.get("osm_way")
        ways = ways if isinstance(ways, list) else ([ways] if ways is not None else [])
        if tg.get("edge") == edge["id"] or edge["osm_way"] in {int(x) for x in ways}:
            if "width" in st and not isinstance(st["width"], list):
                w = float(st["width"])
            if "edge_lines" in st:
                el = st["edge_lines"]
    return round(float(w), 2), el


@pytest.mark.parametrize("a,b", SEAMS)
def test_seam_cross_section_matches(a, b):
    ea, ra, oa = _load(a)
    eb, rb, ob = _load(b)
    # the seam = last route edge of tile a and first route edge of tile b (same OSM way, clipped at the tile edge)
    last, first = ea[ra[-1]], eb[rb[0]]
    assert last["osm_way"] == first["osm_way"], f"{a}->{b}: route leaves via way {last['osm_way']}, enters via {first['osm_way']}"
    assert _effective(last, oa) == _effective(first, ob)


def test_elcka_cross_section_same_in_all_tiles():
    """Ełcka/Studzienna (90 km/h) keeps one measured cross-section through dk65-02 ... dk65-05."""
    vals = set()
    for t in TILES[1:]:
        e, r, o = _load(t)
        for eid in r:
            if e[eid]["attrs"].get("name", {}).get("v") in ("Ełcka", "Studzienna"):
                vals.add(_effective(e[eid], o))
    assert vals == {(6.6, "both")}     # D65 p.5 -> D66 (owner): 7.6 -> ~6.9 -> 6.6 m, ADR 0215 r2


@pytest.mark.parametrize("a,b", SEAMS)
def test_seam_route_points_meet(a, b):
    """The control route leaves tile a where it enters tile b (EPSG:2180, < 2 m; both snapped to the shared edge)."""
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
