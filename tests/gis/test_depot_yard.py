"""ADR 0071 r10: authored depot yard (override kind `depot_yard`, streetscape.depot_yard), automatic gate booms
(streetscape.gate -> Game.World.DepotBarrier, map audit MA-003), trailers at the hero docks.

Run: uv run --project tools/worldgen pytest tests/gis/test_depot_yard.py -q
"""

from __future__ import annotations

import json
import math

import numpy as np
import pytest
import yaml
from shapely.geometry import Point, Polygon

from conftest import REGION_DIR, REPO

from roads import pipeline
from streetscape import depot_yard as DY
from streetscape import life_props as LP
from streetscape import props as PP

WORLD = REPO / "Data" / "raw" / "derived" / REGION_DIR.name / "world"


class _Placer:
    def __init__(self, items=()):
        self.items = list(items)

    def add(self, proto, p, yaw, z=None, sz=1.0, src="", group=None):
        self.items.append({"p": proto, "e": float(p[0]), "n": float(p[1]), "z": 0.0, "yaw": float(yaw), "src": src})
        return 0.0


def test_apply_synthetic():
    o = {"id": "y", "kind": "depot_yard", "clear_lamps_epsg2180": [[0, 0], [10, 0], [10, 10], [0, 10]],
         "lamps": [{"at": [5.0, 5.0], "face": [5.0, 9.0]}, {"at": [1.0, 1.0], "face": [2.0, 1.0], "proto": "nope"}],
         "props": [{"proto": "container_40_3", "at": [20.0, 0.0], "along": [1.0, 0.0]}],
         "no_parking_epsg2180": [[[0, 0], [4, 0], [4, 4], [0, 4]]]}
    pl = _Placer([{"p": "lamp_8m", "e": 3.0, "n": 3.0}, {"p": "lamp_8m", "e": 30.0, "n": 3.0}, {"p": "bench", "e": 2.0, "n": 2.0}])
    rep = {}
    DY.apply(pl, [o], (0.0, 0.0), {"lamp_arc_9m", "container_40_3"}, rep)
    assert rep["depot_yards"]["applied"] == [{"id": "y", "lamps": 1, "props": 1, "rule_lamps_removed": 1}]
    assert rep["depot_yards"]["stale"] == ["y:nope"]
    lamp = next(i for i in pl.items if i["p"] == "lamp_arc_9m")
    assert lamp["yaw"] == pytest.approx(0.0)                       # arm (+y) toward the face point (north)
    cont = next(i for i in pl.items if i["p"] == "container_40_3")
    assert cont["yaw"] == pytest.approx(-math.pi / 2)             # long axis (+y) along +x
    assert [p.area for p in DY.no_parking([o], (0.0, 0.0))] == [16.0]


def test_prototypes():
    P = PP.build_all(set(), {})
    for name in ("lamp_arc_9m", "lamp_arc_9m_double"):
        m, l1, col = P[name]
        assert col is not None and m is not l1
    base, base1, bcol = LP.barrier_base()
    boom, boom1, _ = LP.barrier_boom()
    assert bcol is not None and LP.BOOM_L == pytest.approx(5.85)
    L = LP.build_all()
    assert {"barrier_base", "barrier_boom", "gatehouse"} <= set(L)


def _instances():
    if not WORLD.exists() or not list(WORLD.glob("instances_*.json")):
        pytest.skip("world not built: run roads/build_world.py")
    out = []
    for f in sorted(WORLD.glob("instances_*.json")):
        out += json.loads(f.read_text(encoding="utf-8"))["instances"]
    return out


def _origin():
    o = yaml.safe_load((REGION_DIR / "region.yaml").read_text(encoding="utf-8"))["origin"]
    return np.array([o["x"], o["y"]])


def test_region_gate_booms_are_automatic():
    inst = _instances()
    booms = [i for i in inst if i["p"] == "barrier_boom"]
    bases = [i for i in inst if i["p"] == "barrier_base"]
    assert len(booms) == 2 and len(bases) == 2
    assert not [i for i in inst if i["p"] in ("barrier_arm", "barrier_arm_raised")]
    lanes = set()
    for b in booms:
        d = b["barrier"]
        assert d["L"] == pytest.approx(LP.BOOM_L) and d["open_deg"] == pytest.approx(LP.BOOM_OPEN_DEG)
        assert d["travel"] in (1.0, -1.0)
        lanes.add(d["lane"])
        # hinge 0.95 m above its housing, BOOM_SIDE beside it
        base = min(bases, key=lambda q: math.hypot(q["e"] - b["e"], q["n"] - b["n"]))
        assert math.hypot(base["e"] - b["e"], base["n"] - b["n"]) == pytest.approx(LP.BOOM_SIDE, abs=0.01)
        assert b["z"] - base["z"] == pytest.approx(LP.BOOM_HINGE[2], abs=0.01)
    assert lanes == {"entry", "exit"}
    # entry and exit run in opposite directions past the island: the two booms point away from each other across it,
    # so their travel signs (relative to their own +y) are equal only if the yaws differ by ~180 deg
    a, b = booms
    dyaw = abs((a["yaw"] - b["yaw"] + math.pi) % (2 * math.pi) - math.pi)
    assert (a["barrier"]["travel"] == b["barrier"]["travel"]) == (dyaw > math.pi / 2)


def test_region_yard():
    inst = _instances()
    org = _origin()
    ov = next(o for o in pipeline.load_overrides(REGION_DIR.name) if o.get("id") == "kwadrat-park-yard")
    qa = json.loads((REGION_DIR / "generated" / "streetscape_qa.json").read_text(encoding="utf-8"))
    rep = qa["furniture"]["depot_yards"]
    assert rep["stale"] == [] and rep["applied"][0]["lamps"] == len(ov["lamps"]) and rep["applied"][0]["props"] == len(ov["props"])
    # no rule car bay in the truck yard (BDOT "parking" polygon over the manoeuvring yard)
    for ring in ov["no_parking_epsg2180"]:
        poly = Polygon(np.asarray(ring, float) - org).buffer(-2.5)
        cars = [i for i in inst if i["p"].startswith(("car_", "van_")) and poly.contains(Point(i["e"], i["n"]))]
        assert not cars, f"{len(cars)} cars in the truck yard"
    # authored arched columns stand where the override says; no rule lamp left in the cleared polygon
    clear = Polygon(np.asarray(ov["clear_lamps_epsg2180"], float) - org)
    lamps = [i for i in inst if i["p"].startswith("lamp_") and clear.contains(Point(i["e"], i["n"]))]
    assert {i["p"] for i in lamps} == {"lamp_arc_9m"} and len(lamps) >= len(ov["lamps"]) - 1
    # trailers stand at the hero dock row (start clearance does not empty the player's base)
    docks = [i for i in inst if i["p"].startswith("trailer_") and "life:dock" in i.get("src", "") and "9962cca0" in i["src"]]
    assert 3 <= len(docks) <= 11
    # the access road stays open: no gate leaf, no fence return of the kit (CC0 photo 2021, orthophoto 2024)
    assert not [i for i in inst if i["p"] == "cantilever_gate" and "kwadrat-park-gate-kit" in i.get("src", "")]
    assert [i for i in inst if i["p"] == "gatehouse"]


def test_boom_bands_run_along_the_boom():
    """`boom_red_white` stripes follow UV u (WorldPbrMaterials.Stripes, period 1 m): u must be metres along the boom,
    not the circumference (r10a render: near boom all red, far boom all white)."""
    from streetscape import life_props as LP
    for mesh in LP.barrier_boom()[:2]:
        V = np.concatenate(mesh.prims["gate_boom"][0])
        UV = np.concatenate(mesh.prims["gate_boom"][2])
        assert np.ptp(UV[:, 0]) == pytest.approx(np.ptp(V[:, 0]), abs=1e-6)      # u spans the boom length
        # u is constant around each ring (no band change around the profile)
        for x in np.unique(np.round(V[:, 0], 6)):
            assert np.ptp(UV[np.abs(V[:, 0] - x) < 1e-6, 0]) < 1e-9


def test_region_gate_cannot_be_driven_round():
    """ADR 0092 (review 2026-11-11 s9): each boom's rest post stands on a raised kerbed strip on the outer side of its
    lane, and a closure line (posts / panel fence) runs from that strip to the edge of the paved yard; no rule car is
    parked across a closure line."""
    qa = json.loads((REGION_DIR / "generated" / "streetscape_qa.json").read_text(encoding="utf-8"))
    g = qa["furniture"]["gates"]
    assert not [s for s in g["stale"] if "strip" in s or "closure" in s], g["stale"]
    ap = g["applied"][0]
    assert set(ap["side_strips"]) == {"entry", "exit"}
    for name, st in ap["side_strips"].items():
        assert st["rest_on_strip"], name
        assert st["m2"] >= 8.0, (name, st)
    assert set(ap["closure"]) == {"entry", "exit"}
    for name, c in ap["closure"].items():
        assert c["ends"] in ("yard_edge", "building"), (name, c)  # reaches a boundary, not another road / max_m
        assert c["m"] >= 5.0, (name, c)
    assert len(g["closure_lines"]) == 2
    from shapely.geometry import LineString
    lines = [LineString(c) for c in g["closure_lines"]]
    cars = [i for i in _instances() if i["p"].startswith(("car_", "van_", "tractor_", "trailer_"))]
    near = [(i["p"], i["src"]) for i in cars if min(ln.distance(Point(i["e"], i["n"])) for ln in lines) < 1.2]
    assert not near, near
    assert g.get("scuff_tris", 0) > 0


def test_reefer_unit_has_a_grille_on_both_lods():
    """ADR 0092: the refrigeration unit is not a plain white box - the slatted grille is on LOD0 and LOD1, UV v in
    metres (the importer's `louvre_slats` stripes run on it), and the trailer stays inside the LOD budgets."""
    P = LP.build_all()
    m, l1 = P["trailer_reefer_0"][0], P["trailer_reefer_0"][1]
    for mesh in (m, l1):
        uv = np.concatenate(mesh.prims["reefer_grille"][2])
        assert uv[:, 1].max() - uv[:, 1].min() == pytest.approx(0.78, abs=0.01)
