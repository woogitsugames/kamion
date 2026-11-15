"""ADR 0208: region bialystok-knyszynska (third Białystok tile of the D64 route to Knyszyn, lattice -3,0, two powiaty)
and the deck keep-out of walls / fences (bialystok-maczka, wall with railing in the added lane of a low deck)."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import yaml
from shapely.geometry import LineString

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import regions  # noqa: E402
from roads import standards as S  # noqa: E402
from streetscape import furniture as FU  # noqa: E402

RID = "bialystok-knyszynska"
RDIR = REPO / "Data" / "Regions" / RID
PLAN = REPO / "docs" / "reports" / "map" / "dk65_route_plan.json"
EAST, WEST = "bialystok-kleeberga", "dk65-01"


def _graph(rid):
    return json.loads((REPO / "Data" / "Regions" / rid / "roads.graph.json").read_text(encoding="utf-8"))


def _overrides(rid):
    p = REPO / "Data" / "Regions" / rid / "overrides.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8"))["overrides"] or []


def _width(rid, e):
    """Carriageway width the build uses for an edge: authored `set.width` (edge or osm_way target), else the graph."""
    w = (e["attrs"].get("width") or {}).get("v")
    for o in _overrides(rid):
        t, st = o.get("target", {}), o.get("set", {})
        ways = t.get("osm_way", [])
        ways = ways if isinstance(ways, list) else [ways]
        if "width" in st and (t.get("edge") == e["id"] or e["osm_way"] in ways):
            w = st["width"]
    return w


def _boundary(rid, x, width=False):
    g = _graph(rid)
    nodes = {n["id"]: n for n in g["nodes"]}
    out = set()
    for e in g["edges"]:
        for k in ("from", "to"):
            n = nodes[e[k]]
            if n.get("boundary") and abs(n["x"] - x) < 0.01:
                a = e["attrs"]
                row = (round(n["y"], 2), e["osm_way"], a["highway"]["v"], a["lanes"]["v"], a["oneway"]["v"])
                out.add(row + ((_width(rid, e),) if width else ()))
    return out


def test_tile_lies_between_kleeberga_and_dk65_01_and_matches_the_plan():
    k, e, w = regions.get(RID), regions.get(EAST), regions.get(WEST)
    assert k.bbox == (e.bbox[0] - regions.TILE_SIZE_M, e.bbox[1], e.bbox[0], e.bbox[3])
    assert k.bbox[0] == w.bbox[2] and (k.bbox[1], k.bbox[3]) == (w.bbox[1], w.bbox[3])
    assert k.origin == ((k.bbox[0] + k.bbox[2]) / 2, (k.bbox[1] + k.bbox[3]) / 2)
    tiles = json.loads(PLAN.read_text(encoding="utf-8"))["variants"]["A_old_road"]["tiles"]
    t = next(t for t in tiles if tuple(t["ij"]) == (-3, 0))
    assert tuple(t["bbox"]) == k.bbox


def test_two_powiaty_and_single_powiat_regions_are_unchanged():
    k = regions.get(RID)
    assert k.powiaty == ("2061", "2002")
    assert all(r.powiaty == (r.teryt_powiat,) for i, r in regions.REGIONS.items() if i != RID)
    reg = yaml.safe_load((RDIR / "region.yaml").read_text(encoding="utf-8"))
    assert reg["teryt_powiat"] == "2061" and reg["teryt_powiat_extra"] == ["2002"]


def test_both_seams_have_the_same_roads_on_both_sides():
    k = regions.get(RID)
    for x, other, n_min in ((k.bbox[2], EAST, 10), (k.bbox[0], WEST, 5)):
        a, b = _boundary(RID, x), _boundary(other, x)
        assert a == b and len(a) >= n_min, (other, sorted(a ^ b))
    east = _boundary(RID, k.bbox[2])
    assert {r[1] for r in east if r[2] == "trunk"} == {261104557, 301702377}     # both carriageways of Kleeberga
    assert {r[1] for r in _boundary(RID, k.bbox[0]) if r[2] == "secondary"} == {234919333}   # Szosa Knyszyńska


def test_carriageway_widths_agree_across_both_seams_after_overrides():
    k = regions.get(RID)
    for x, other in ((k.bbox[2], EAST), (k.bbox[0], WEST)):
        a, b = _boundary(RID, x, width=True), _boundary(other, x, width=True)
        assert a == b, (other, sorted(a ^ b, key=str))


def test_route_runs_from_the_kleeberga_seam_to_the_dk65_01_seam():
    k = regions.get(RID)
    ep = json.loads((RDIR / "route_endpoints.json").read_text(encoding="utf-8"))
    g = _graph(RID)
    for key, x in (("start_epsg2180", k.bbox[2]), ("end_epsg2180", k.bbox[0])):
        px, py = ep[key]
        assert px == x
        assert min(abs(n["x"] - px) + abs(n["y"] - py) for n in g["nodes"] if n.get("boundary")) < 1.0
    r = json.loads((RDIR / "route_start.json").read_text(encoding="utf-8"))
    P = np.asarray(r["points_en"])[:, :2] + np.asarray(k.origin)
    assert abs(P[0, 0] - k.bbox[2]) < 3.0 and abs(P[-1, 0] - k.bbox[0]) < 3.0
    assert 2900 < r["length_m"] < 3000            # plan: km 5.80-8.76 of variant A


def test_overrides_are_explained_and_target_existing_edges():
    g = _graph(RID)
    ways, edges = {e["osm_way"] for e in g["edges"]}, {e["id"] for e in g["edges"]}
    ov = _overrides(RID)
    assert len(ov) >= 4
    for o in ov:
        assert o["reason"].strip() and o["confidence"] and o["verify"]
        t = o["target"]
        assert all(w in ways for w in t.get("osm_way", [])), o["id"]
        assert "edge" not in t or t["edge"] in edges, o["id"]


def test_junction_checks_and_place_cameras_are_inside_the_tile():
    k = regions.get(RID)
    js = json.loads((RDIR / "junction_checks.authored.json").read_text(encoding="utf-8"))["junctions"]
    assert len(js) >= 9
    for j in js:
        x, y = j["center_2180"]
        assert k.bbox[0] <= x <= k.bbox[2] and k.bbox[1] <= y <= k.bbox[3]
    cams = json.loads((RDIR / "control_cameras_place.authored.json").read_text(encoding="utf-8"))["cameras"]
    want = {"seam_e_into_tile", "seam_e_back_to_edge", "seam_w_to_edge", "seam_w_back_into_tile"}
    assert {c["id"] for c in cams} >= want
    assert all(abs(c["pos_en"][0]) < 1024 and abs(c["pos_en"][1]) < 1024 for c in cams)


# ------------------------------------------------------------------------------------------- deck keep-out
def _deck(z):
    """One 20 x 8 m deck carriageway slab at height z (two triangles), as a bridge-layer road part."""
    V = np.array([[0, 0, z], [20, 0, z], [20, 8, z], [0, 8, z]], float)
    return SimpleNamespace(V=V, T=np.array([[0, 1, 2], [0, 2, 3]]), layer="bridge", mat="road_asphalt")


def _keepout(deck_z, ground_z=129.5):
    lin = FU.Lin(None, lambda x, y: np.full(np.shape(x), ground_z))
    return FU.DeckKeepout(lin, [_deck(deck_z)])


WALL = LineString([(-10.0, 3.0), (30.0, 3.0)])      # crosses the slab from x = 0 to x = 20


def test_wall_whose_railing_comes_up_through_a_low_deck_is_cut_out_of_it():
    # bialystok-maczka r1: wall top 130.54 stayed 0.8 m under the lane (131.31), the railing reached 131.64
    ground, deck = 129.5, 131.4
    wall_top = max(ground + 0.15, ground - 0.4 + 1.0)
    assert wall_top < deck - FU.LANE_FLOOR_M < wall_top + S.RAILING_H        # only the railing is in the lane window
    dk = _keepout(deck, ground)
    parts = dk.cut(WALL, FU._retaining_top)
    assert len(parts) == 2 and abs(dk.cut_m - 20.6) < 0.2                     # the slab + 0.3 m at both ends
    assert all(p.bounds[2] <= -0.29 or p.bounds[0] >= 20.29 for p in parts)


def test_wall_under_a_deck_that_clears_its_railing_stays():
    dk = _keepout(135.0)
    assert dk.cut(WALL, FU._retaining_top) == [WALL] and dk.cut_m == 0.0
    assert dk.cut(WALL, FU._fence_top) == [WALL]


def test_fence_on_a_low_deck_is_cut_and_a_line_off_the_deck_is_untouched():
    dk = _keepout(131.0)
    assert len(dk.cut(WALL, FU._fence_top)) == 2
    off = LineString([(-10.0, 30.0), (30.0, 30.0)])
    assert dk.cut(off, FU._retaining_top) == [off]
    empty = FU.DeckKeepout(FU.Lin(None, lambda x, y: np.zeros(np.shape(x))), [])
    assert empty.cut(WALL, FU._fence_top) == [WALL]
