"""ADR 0133: authored median lamp row (DK8 over Rondo Putry) - console on the deck fascia, rule lamps replaced."""
import json
import math

import numpy as np
import pytest

from roads.meshing import Part
from streetscape import furniture as F, props as P

REGION = __import__("pathlib").Path(__file__).resolve().parents[2] / "Data/Regions/bialystok-industrial-c"


def _deck(y0, y1, z, x0=-50.0, x1=50.0):
    V = np.array([[x0, y0, z], [x1, y0, z], [x1, y1, z], [x0, y1, z]], float)
    return Part("bridge", "bridge_concrete", V, np.zeros((4, 2)), np.array([[0, 1, 2], [0, 2, 3]]))


def _row(tmp_path, pts, snap=2.6):
    f = tmp_path / "lamp_rows.json"
    f.write_text(json.dumps({"rows": [{"id": "t", "proto": "lamp_double_12m", "proto_console": "lamp_double_console_12m",
                                       "suppress_rule_lamps": {"osm_way": [1], "within_m": 18.0},
                                       "deck_snap_m": snap, "points_en": pts}]}), encoding="utf-8")
    return f


def test_console_on_the_nearest_deck_edge_rule_lamps_replaced(tmp_path):
    flat = lambda e, n: np.zeros_like(e, dtype=float)
    pl = F.Placer(flat, flat)
    # two decks 10 m wide at 8 m, a 4.2 m gap between y = 0 and y = 4.2
    parts = [_deck(-10.0, 0.0, 8.0), _deck(4.2, 14.2, 8.0)]
    pl.add("lamp_12m", (0.0, 13.5), 0.0, z=8.2, src="rule:c:w1:a-b", group="lamp")      # outer edge: replaced
    pl.add("lamp_12m", (0.0, 40.0), 0.0, z=8.2, src="rule:c:w1:a-b", group="lamp")      # far away: kept
    pl.add("lamp_12m", (0.0, 13.0), 0.0, z=8.2, src="rule:c:w2:a-b", group="lamp")      # other way: kept
    rep = {}
    F.lamp_rows(pl, parts, _row(tmp_path, [[-20.0, 2.8], [20.0, 2.8]]), rep)
    r = rep["lamp_rows"]["t"]
    assert r["rule_lamps_removed"] == 1 and r["placed"] == 2 and r["console"] == 2
    new = [it for it in pl.items if it["src"].startswith("authored:")]
    for it in new:
        assert it["p"] == "lamp_double_console_12m"
        assert it["n"] == pytest.approx(4.2 - F.CONSOLE_OUT_M, abs=0.03)      # gap side of the nearer deck
        assert it["z"] == pytest.approx(8.0, abs=1e-6)                        # cap top, not the ground under the gap
        # +y (console, arm) points across the road toward that deck
        assert math.cos(it["yaw"] + math.pi / 2) == pytest.approx(0.0, abs=1e-6)
        assert math.sin(it["yaw"] + math.pi / 2) == pytest.approx(1.0, abs=1e-6)
    assert sum(1 for it in pl.items if it["src"].startswith("rule:")) == 2


def test_ground_column_where_no_deck_is_near(tmp_path):
    flat = lambda e, n: np.zeros_like(e, dtype=float)
    pl = F.Placer(flat, flat)
    rep = {}
    F.lamp_rows(pl, [_deck(20.0, 30.0, 8.0)], _row(tmp_path, [[-20.0, 0.0], [20.0, 0.0]]), rep)
    assert {it["p"] for it in pl.items} == {"lamp_double_12m"}
    assert all(it["z"] == 0.0 for it in pl.items)


def test_double_arm_prototype():
    for console in (False, True):
        m = P.lamp_y(12.0, console=console)[0].out()
        V = np.concatenate([p["V"] for p in m])
        assert V[:, 2].max() == pytest.approx(12.0, abs=0.06)
        assert V[:, 1].max() == pytest.approx(-V[:, 1].min(), abs=0.4)       # symmetric arms (console only adds y > 0)
        assert V[:, 1].max() > 2.9                                              # reach 2.4 m + housing
        mats = {p["mat"] for p in m}
        assert ("furniture_footing" in mats) != console


def test_authored_row_file():
    d = json.loads((REGION / "lamp_rows.json").read_text(encoding="utf-8"))
    row = d["rows"][0]
    P_ = np.asarray(row["points_en"], float)
    gaps = np.hypot(*np.diff(P_, axis=0).T)
    assert len(P_) == 14 and 30.0 < gaps.min() and gaps.max() < 38.0           # measured spacing 32-37 m
