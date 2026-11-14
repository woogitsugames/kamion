"""ADR 0125 (gate 3 recognisability, D51): sign assemblies as data (streetscape.gate3_landmarks), the re-measured
Andersa portal, viaduct noise screen on the outer edge only.

Unit tests need no raw data; the QA tests read the generated reports and are skipped until the world is rebuilt.
"""

from __future__ import annotations

import json
import math

import numpy as np
import pytest

from conftest import REGION_DIR

from roads import meshing, pipeline
from streetscape import gate3_landmarks as G3


def _tris(mesh):
    return sum(len(p["T"]) for p in mesh.out())


def test_assembly_is_one_material_and_small():
    """One sign = one prototype with ONE material (one draw on every tier), far below the 30 k prop budget."""
    for parts, post, lower in (([{"face": "A-30", "plate": "wyjazd\nstraży"}], "galv", 2.0),
                               ([{"face": "U-4a"}], "galv", 0.9),
                               ([{"face": "street_name", "text": "Rondo"}], "teal", 2.6),
                               ([{"face": "D-3"}], "galv", 2.4), ([{"face": "D-6"}], "galv", 2.2),
                               ([{"face": "D-1"}], "galv", 2.0)):
        lod0, lod1, col, im, (w, h), key, top = G3.assembly_mesh(parts, post, lower)
        prims = lod0.out()
        assert [p["mat"] for p in prims] == [f"sign_{key}"]
        assert _tris(lod0) <= 40 and _tris(lod1) <= _tris(lod0)
        uv = prims[0]["UV"]
        assert uv.min() >= 0.0 and uv.max() <= 1.0                  # clamped sign textures: no UV outside the atlas
        assert col is not None and len(col.out()) == 1
        assert im.size[0] / im.size[1] == pytest.approx(w / h, rel=0.02)


def test_assembly_geometry_follows_the_sign_rules():
    """Lower edge at `lower_edge_m` (>= 2.0 m default, Tabl. 1.11), faces look along +y, backs along -y."""
    lod0, _, _, _, _, _, top = G3.assembly_mesh([{"face": "A-30", "plate": "x"}], "galv", 2.0)
    p = lod0.out()[0]
    V, T = p["V"], p["T"]
    n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    front = n[:, 1] > 1e-9
    flat = np.abs(n[:, 0]) + np.abs(n[:, 2]) < 1e-9                 # plate triangles (normal exactly +-y)
    zf = V[np.unique(T[flat & front])][:, 2]
    assert zf.min() == pytest.approx(2.0, abs=1e-6)                 # lower edge of the plate under the triangle
    tri_h = 0.9 * math.sqrt(3) / 2
    assert zf.max() == pytest.approx(2.0 + 0.45 + 0.05 + tri_h, abs=1e-6)
    assert top == pytest.approx(zf.max() + 0.05, abs=1e-6)
    assert (flat & front).sum() == (flat & ~front).sum() == 3       # triangle (1) + plate (2), each with a back
    assert V[np.unique(T[flat & front])][:, 1].min() > V[np.unique(T[flat & ~front])][:, 1].max()


def test_face_uv_is_mirrored_like_the_plates():
    """Seen from the front (+y) local +x is on the viewer's left, so u must fall as x grows (props.plate rule):
    otherwise texts read mirrored."""
    lod0, _, _, im, _, _, _ = G3.assembly_mesh([{"face": "street_name", "text": "Rondo"}], "teal", 2.6)
    p = lod0.out()[0]
    V, T, UV = p["V"], p["T"], p["UV"]
    n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    idx = np.unique(T[(n[:, 1] > 1e-9) & (np.abs(n[:, 0]) + np.abs(n[:, 2]) < 1e-9)])
    left, right = idx[np.argmin(V[idx, 0])], idx[np.argmax(V[idx, 0])]
    assert UV[left, 0] > UV[right, 0]
    top_v, bot_v = idx[np.argmax(V[idx, 2])], idx[np.argmin(V[idx, 2])]
    assert UV[top_v, 1] > UV[bot_v, 1]                              # v = 1 at the image top (props.board rule)


def test_same_parts_share_one_prototype_key():
    a = G3.assembly_key([{"face": "A-30", "plate": "x"}], "galv", 2.0)
    assert a == G3.assembly_key([{"face": "A-30", "plate": "x"}], "galv", 2.0)
    assert a != G3.assembly_key([{"face": "A-30", "plate": "y"}], "galv", 2.0)
    with pytest.raises(KeyError):
        G3.assembly_key([{"face": "Z-99"}], "galv", 2.0)


def test_unknown_face_is_reported_stale_not_dropped():
    class _Pl:
        items = []
        zground = None

        def add(self, *a, **k):
            raise AssertionError("nothing may be placed")
    rep = {}
    G3.build(_Pl(), None, {"nodes": []}, [{"id": "x", "kind": "gate3_sign", "at_en": [0, 0], "travel_bearing_deg": 0,
                                           "parts": [{"face": "Z-99"}]}], (0, 0), {}, rep)
    assert rep["gate3_landmarks"]["signs"] == [] and rep["gate3_landmarks"]["stale"][0].startswith("x:")


def test_bearing_convention():
    """travel_bearing_deg is a compass bearing (0 = north, 90 = east); the face looks against the travel."""
    assert G3._bearing_vec(90) == pytest.approx([1.0, 0.0], abs=1e-9)
    yaw = G3.PP_yaw(-G3._bearing_vec(0))                            # traffic going north: face looks south
    assert [-math.sin(yaw), math.cos(yaw)] == pytest.approx([0.0, -1.0], abs=1e-9)   # local +y rotated by yaw


class _Chain:
    def __init__(self, dirn):
        self.dirn = np.asarray(dirn)


def test_viaduct_screen_side_rule():
    """`screen_side: travel_right` keeps the screen on the right-hand edge of TRAVEL (Mapillary 494288258686575);
    the default stays both edges; no screen style -> no edges."""
    st = dict(meshing.DEFAULT_BRIDGE_STYLE, noise_screen="transparent")
    assert meshing.screen_sides(_Chain([1, 1, 1]), st) == ("L", "R")
    st["screen_side"] = "travel_right"
    assert meshing.screen_sides(_Chain([1, 1, 1]), st) == ("R",)
    assert meshing.screen_sides(_Chain([-1, -1, -1]), st) == ("L",)     # chain drawn against the travel
    assert meshing.screen_sides(_Chain([1, 1]), dict(meshing.DEFAULT_BRIDGE_STYLE)) == ()


def test_overrides_are_data_with_provenance():
    ov = [o for o in pipeline.load_overrides("bialystok-industrial-c") if o.get("kind") == "gate3_sign"]
    assert len(ov) >= 7
    for o in ov:
        assert ("at_en" in o) != ("along" in o), o["id"]
        assert "travel_bearing_deg" in o or "along" in o, o["id"]
        # ADR 0172: a non-Mapillary open photo is named under `photo` ("commons:<id>")
        assert (o.get("mapillary") or o.get("photo")) and o.get("reason") and o.get("confidence") and o.get("verify"), o["id"]
        G3.assembly_key(o["parts"], o.get("post", "galv"), o.get("lower_edge_m", 2.0))


# ------------------------------------------------------------------------------------------- generated world (QA)
@pytest.fixture(scope="module")
def qa():
    p = REGION_DIR / "generated" / "streetscape_qa.json"
    if not p.exists():
        pytest.skip("streetscape_qa.json not built")
    q = json.loads(p.read_text(encoding="utf-8"))
    if "gate3_landmarks" not in q.get("furniture", {}):
        pytest.skip("world not rebuilt with ADR 0125")
    return q


def test_every_gate3_sign_is_placed(qa):
    rep = qa["furniture"]["gate3_landmarks"]
    ids = {o["id"] for o in pipeline.load_overrides("bialystok-industrial-c") if o.get("kind") == "gate3_sign"}
    stale = {x.split(":")[0] for x in rep["stale"]}
    # ADR 0128: the kerbed nose at the northern slip of Rondo Bieżeństwa is an authored traffic island now, D-3 / D-6
    # stand on it (was: carriageway, stale); nothing may be stale.
    assert stale == set()
    assert {s["id"] for s in rep["signs"]} == ids - stale
    assert all(s["snapped_m"] <= G3.SNAP_MAX_M + G3.SNAP_CLEAR_M for s in rep["signs"])


def test_signs_on_authored_islands_stand_where_authored(qa):
    """ADR 0128: a sign authored on a traffic island (islands lie on the carriageway footprint) is not snapped away."""
    signs = {s["id"]: s for s in qa["furniture"]["gate3_landmarks"]["signs"]}
    want = {"biezenstwa-n-slip-d6": "biezenstwa-n-slip-nose", "biezenstwa-n-slip-d3": "biezenstwa-n-slip-nose",
            "andersa-elewatorska-island-u4a": "n10015785253-island"}
    for sid, isl in want.items():
        assert signs[sid].get("island") == isl and signs[sid]["snapped_m"] == 0.0, sid
    # orthophoto 0.08 m: nose of the Andersa island at E -219.6 N -235.3; the board stands within 1 m of it
    u = signs["andersa-elewatorska-island-u4a"]["at"]
    assert math.hypot(u[0] + 219.6, u[1] + 235.3) <= 1.0
    d6, d3 = signs["biezenstwa-n-slip-d6"]["at"], signs["biezenstwa-n-slip-d3"]["at"]
    assert 2.0 <= math.hypot(d6[0] - d3[0], d6[1] - d3[1]) <= 3.0          # 2.4 m apart on the orthophoto / photo


def test_portal_stands_where_the_orthophoto_has_it(qa):
    """GUGiK orthophoto 2024 + Mapillary bracket: portal centre at E,N = (-261, -208) +- 3 m (was 59 m further)."""
    g = {x["id"]: x for x in qa["furniture"]["landmarks"]["gantries"]}["andersa-putry-approach-gantry"]
    assert math.hypot(g["at"][0] + 261.0, g["at"][1] + 208.0) <= 6.0
    assert g["form"] == "portal" and len(g["boards"]) == 2
    signs = {s["id"]: s for s in qa["furniture"]["gate3_landmarks"]["signs"]}
    for sid in ("andersa-gantry-warning-right", "andersa-gantry-warning-left"):
        s = signs[sid]
        d = math.hypot(s["at"][0] - g["at"][0], s["at"][1] - g["at"][1])
        assert 5.0 <= d <= 16.0, (sid, d)                           # a few metres before the portal, beside the road
        assert abs((s["travel_bearing_deg"] - 312 + 180) % 360 - 180) < 15
    r, l = signs["andersa-gantry-warning-right"]["at"], signs["andersa-gantry-warning-left"]["at"]
    t = np.array([math.sin(math.radians(312)), math.cos(math.radians(312))])
    cross = t[0] * (r[1] - l[1]) - t[1] * (r[0] - l[0])
    assert cross < 0                                                # "R" really is on the right of the travel


def test_snap_off_the_carriageway():
    """An authored point up to SNAP_MAX_M inside the carriageway moves SNAP_CLEAR_M behind its nearest edge; deeper
    points are refused (reported stale by build)."""
    from shapely.geometry import box
    road = box(0, -3.5, 100, 3.5)
    assert G3.off_carriageway(road, np.array([50.0, 5.0])) == pytest.approx([50.0, 5.0])
    assert G3.off_carriageway(road, np.array([50.0, 2.0])) == pytest.approx([50.0, 3.5 + G3.SNAP_CLEAR_M])
    assert G3.off_carriageway(box(0, -30, 100, 30), np.array([50.0, 0.0])) is None


def test_sign_under_a_deck_stands_on_the_ground():
    """The top surface under a viaduct is the deck (first build: name plates at z = deck); the sign must take the
    terrain height unless the entry says on_deck."""
    class _Pl:
        def __init__(self):
            self.items = []
            self.zsurf = lambda e, n: np.full(len(e), 140.0)
            self.zground = lambda e, n: np.full(len(e), 132.0)

        def add(self, proto, p, yaw, z=None, src=""):
            self.items.append((proto, z))
            return z
    ov = {"id": "x", "kind": "gate3_sign", "at_en": [1.0, 2.0], "travel_bearing_deg": 90, "parts": [{"face": "D-3"}],
          "mapillary": ["1"]}
    pl, rep = _Pl(), {}
    G3.build(pl, None, {"nodes": []}, [ov, dict(ov, id="y", on_deck=True)], (0, 0), {}, rep)
    assert [z for _, z in pl.items] == [132.0, 140.0]
    assert [s["under_deck"] for s in rep["gate3_landmarks"]["signs"]] == [True, False]
