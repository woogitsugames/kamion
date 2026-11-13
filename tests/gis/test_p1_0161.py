"""ADR 0161 (P1 of the gate 3 frames after s16b): authored lawns (`unpaved_area`), authored signals (`gate3_signal`),
the P-8 arrows of the link to Rondo Putry, the portal station, the D-1 plate, cap coat and pier paint.

Unit tests need no raw data; the QA tests read the generated reports and are skipped until the world is rebuilt.
"""

from __future__ import annotations

import json
import math

import numpy as np
import pytest
from shapely.geometry import Polygon, box

from conftest import REGION_DIR

from roads import pipeline
from streetscape import gate3_landmarks as G3
from streetscape import materials as MT
from streetscape import paved as PV

REGION = "bialystok-industrial-c"


def _src(plac):
    ring = [list(map(list, plac.exterior.coords))]
    return {"osm": {"areas": []},
            "bdot10k": {"OT_PTPL_A": [{"id": "p1", "props": {"materialnawierzchni": "masa bitumiczna"},
                                       "geometry": {"coordinates": ring}}], "OT_KUKO_A": [], "OT_SKRP_L": []}}


def _collect(overrides):
    rep = {}
    out = PV.collect(_src(box(0, 0, 40, 20)), np.zeros(2), overrides, [], Polygon(), None, rep)
    return out, rep


def test_unpaved_area_cuts_data_sources_only():
    """A lawn override removes the BDOT10k yard inside it; an authored footway across the lawn is still laid."""
    lawn = {"id": "lawn", "kind": "unpaved_area", "polygon_en": [[10, 0], [20, 0], [20, 20], [10, 20]]}
    walk = {"id": "walk", "kind": "paved_area", "material": "sidewalk_paving",
            "polygon_epsg2180": [[0, 8], [40, 8], [40, 11], [0, 11]]}
    base, _ = _collect([])
    assert sum(p["poly"].area for p in base) == pytest.approx(800.0, abs=5.0)
    out, rep = _collect([lawn, walk])
    yard = sum(p["poly"].area for p in out if p["source"] == "bdot10k_PTPL")
    path = sum(p["poly"].area for p in out if p["source"] == "authored_override")
    assert path == pytest.approx(120.0, abs=3.0)                       # the footway crosses the lawn uncut
    assert yard == pytest.approx(800.0 - 120.0 - (200.0 - 30.0), abs=10.0)   # yard minus footway minus the rest of the lawn
    assert rep["unpaved_area"]["lawn"] == pytest.approx(170.0, abs=5.0) and rep["unpaved_area_stale"] == []


def test_unpaved_area_that_removes_nothing_is_stale():
    out, rep = _collect([{"id": "far", "kind": "unpaved_area", "polygon_en": [[100, 100], [110, 100], [110, 110]]}])
    assert rep["unpaved_area_stale"] == ["far"]
    assert sum(p["poly"].area for p in out) == pytest.approx(800.0, abs=5.0)


class _Pl:
    def __init__(self):
        self.items = []
        self.zsurf = lambda e, n: np.full(len(e), 140.0)
        self.zground = None

    def add(self, proto, p, yaw, z=None, src=""):
        z = 140.0 if z is None else z
        self.items.append((proto, [round(float(v), 2) for v in p], round(float(yaw), 4), z, src))
        return z


def test_gate3_signal_mast_and_post():
    """A mast = mast + head 5 m out on the arm + low head on the pole; a post = pole + one head. Heads face the traffic."""
    ov = [{"id": "m", "kind": "gate3_signal", "at_en": [10.0, 0.0], "travel_bearing_deg": 0, "arm_bearing_deg": 270},
          {"id": "p", "kind": "gate3_signal", "at_en": [0.0, 0.0], "travel_bearing_deg": 0, "lit": "green"},
          {"id": "bad", "kind": "gate3_signal", "at_en": [0.0, 0.0]}]
    pl, rep = _Pl(), {}
    G3.build(pl, None, {"nodes": []}, ov, (0, 0), {}, rep)
    protos = [i[0] for i in pl.items]
    assert protos == ["signal_mast", "signal_head_red", "signal_head_red", "signal_pole", "signal_head_green"]
    mast, high, low = pl.items[:3]
    assert high[1] == [5.0, 0.0]                                       # 5 m along the arm (west)
    assert high[3] == pytest.approx(140.0 + G3.S.SIGNAL_MAST_H - 1.25) and low[3] == pytest.approx(142.9)
    assert mast[2] == pytest.approx(G3.PP_yaw(G3._bearing_vec(270)), abs=1e-3)
    assert high[2] == low[2] == pytest.approx(G3.PP_yaw(G3._bearing_vec(0)), abs=1e-3)
    g = rep["gate3_landmarks"]
    assert [s["id"] for s in g["signals"]] == ["m", "p"] and g["stale"][0].startswith("bad:")


def test_signal_on_a_carriageway_is_snapped_or_stale():
    ov = [{"id": "near", "kind": "gate3_signal", "at_en": [1.0, 5.0], "travel_bearing_deg": 0},
          {"id": "mid", "kind": "gate3_signal", "at_en": [20.0, 20.0], "travel_bearing_deg": 0}]
    pl, rep = _Pl(), {}
    G3.build(pl, None, {"nodes": []}, ov, (0, 0), {}, rep, carriage=box(0, 0, 40, 40))
    g = rep["gate3_landmarks"]
    assert [s["id"] for s in g["signals"]] == ["near"] and g["signals"][0]["snapped_m"] == pytest.approx(1.6, abs=0.01)
    assert g["stale"][0].startswith("mid:")


def test_authored_overrides_of_0161_are_data():
    ov = {o["id"]: o for o in pipeline.load_overrides(REGION)}
    arrows = [o for i, o in ov.items() if i.startswith("putry-link-p8-")]
    assert len(arrows) == 11 and all(o["kind"] == "painted_arrow" and o["long"] is False for o in arrows)
    left = sorted((o for o in arrows if o["id"].endswith("l")), key=lambda o: o["id"])
    step = [math.dist(a["at_en"], b["at_en"]) for a, b in zip(left, left[1:])]
    assert all(14.5 < d < 15.3 for d in step)                          # pkt 3.2.1: 15 m at <= 70 km/h
    assert ov["andersa-putry-portal-p40"]["distance_m"] == 86.0 and len(ov["andersa-putry-portal-p40"]["columns_en"]) == 2
    d1 = ov["andersa-link-median-d1"]
    assert "along" not in d1 and d1["travel_bearing_deg"] == 295
    assert ov["kwadrat-exit-verge-lawn"]["kind"] == "unpaved_area"


def test_cap_coat_and_pier_paint_are_darker_than_before():
    from roads import build_world as BW
    cap = BW.MATERIALS["bridge_cap_red"]["color"] if hasattr(BW, "MATERIALS") else None
    if cap is not None:
        assert cap[0] < 0.15 and cap[0] / cap[1] > 4.0                 # same red-brown hue, x 0.62
    pier = MT.M["pier_yellow"]["color"]
    assert max(pier) < 0.16 and pier[0] > pier[1] > pier[2]            # ochre kept (CC0 photo), darker


# ------------------------------------------------------------------------------------------- generated world (QA)
@pytest.fixture(scope="module")
def qa():
    p = REGION_DIR / "generated" / "streetscape_qa.json"
    if not p.exists():
        pytest.skip("streetscape_qa.json not built")
    q = json.loads(p.read_text(encoding="utf-8"))
    if "signals" not in q.get("furniture", {}).get("gate3_landmarks", {}):
        pytest.skip("world not rebuilt with ADR 0161")
    return q


def test_ring_signals_are_placed(qa):
    g = qa["furniture"]["gate3_landmarks"]
    sig = {s["id"]: s for s in g["signals"]}
    assert set(sig) == {"putry-ring-s-approach-signal-mast", "putry-ring-s-approach-signal-island"}
    assert sig["putry-ring-s-approach-signal-mast"]["mast"] and all(s["snapped_m"] <= 3.0 for s in sig.values())
    assert g["stale"] == []


def test_lawn_removed_yard_and_is_not_stale(qa):
    by = qa["paved_m2_by_source"]
    assert by["unpaved_area_stale"] == [] and by["unpaved_area"]["kwadrat-exit-verge-lawn"] > 100.0
