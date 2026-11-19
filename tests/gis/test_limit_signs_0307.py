"""ADR 0307 (D91): B-16 / B-18 before bridges with a height / weight limit in the road graph - synthetic data, plus
the real edge of the DW671 bridge over the Narew in Tykocin (roads.graph.json in git)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from streetscape import limit_signs as LS
from streetscape import signs as SG

REPO = Path(__file__).resolve().parents[2]
ORIGIN = (750000.0, 600000.0)


def _net(bridge_attrs, oneway="no"):
    """Straight east-west road 0..600 m in three edges; the middle one (200..400 m) is the bridge."""
    from roads import network
    ox, oy = ORIGIN
    nodes = [{"id": f"n{i}", "x": ox + 200.0 * i, "y": oy} for i in range(4)]

    def edge(i, extra):
        return {"id": f"e{i}", "from": f"n{i}", "to": f"n{i + 1}",
                "geometry": [[ox + 200.0 * i, oy], [ox + 200.0 * (i + 1), oy]],
                "attrs": {"highway": {"v": "secondary"}, "oneway": {"v": oneway}, "lanes": {"v": 2}, **extra}}
    g = {"nodes": nodes, "edges": [edge(0, {}), edge(1, bridge_attrs), edge(2, {})]}
    net = network.load(g, ORIGIN)
    for c in net.chains:
        n = len(c.line.s)
        c.z, c.e = np.zeros(n), np.zeros(n)
    network.assign_sides(net, [], built_up=False)
    return net, {e["id"]: e["attrs"] for e in g["edges"]}


def _placer():
    from streetscape import furniture as FU
    return FU.Placer(lambda e, n: np.zeros(np.shape(e)))


TYKOCIN = {"bridge": {"v": "yes"}, "layer": {"v": 1}, "maxheight": {"v": "3.7"}, "maxweight:hgv": {"v": "12 ton"}}


def test_faces_and_codes():
    assert SG.is_known("B-16_3.7") and SG.is_known("B-16_4") and not SG.is_known("B-16")
    shape, im = SG.face("B-16_3.7")
    assert shape == "disc" and im.size == (SG.S, SG.S)
    a = np.asarray(im)
    assert a[SG.S // 2, 6, 3] > 0 and a[SG.S // 2, 6, 0] > 150 and a[SG.S // 2, 6, 1] < 90      # red ring
    assert LS.plates_for(3.7, 12.0) == ["B-16_3.7", "B-18_12"]
    assert LS.plates_for(None, 7.5) == ["B-18_7.5"] and LS.plates_for(4.0, None) == ["B-16_4"]


def test_edge_limits_only_on_structures():
    assert LS.edge_limits(TYKOCIN) == (3.7, 12.0)
    assert LS.edge_limits({"maxweight": {"v": "12"}}) == (None, None)                 # ordinary street: not this rule
    assert LS.edge_limits({"bridge": {"v": "yes"}, "maxheight": {"v": "default"}}) == (None, None)
    assert LS.edge_limits({"tunnel": {"v": "yes"}, "maxheight": {"v": "3,5 m"}, "maxweight": {"v": "3500 kg"}}) == (3.5, 3.5)


def test_both_entries_signed_right_side_facing_traffic():
    net, attrs = _net(TYKOCIN)
    pl, rep, codes = _placer(), {}, set()
    LS.limit_signs(pl, net, attrs, rep, codes)
    r = rep["limit_signs"]
    assert codes == {"B-16_3.7", "B-18_12"} and r["placed"] == {"B-16_3.7": 2, "B-18_12": 2}
    (st,) = r["structures"]
    assert st["edge"] == "e1" and st["maxheight_m"] == 3.7 and st["maxweight_t"] == 12.0
    ents = {e["dir"]: e for e in st["entries"]}
    assert set(ents) == {"forward", "backward"} and all(e["placed"] for e in ents.values())
    for e in ents.values():
        assert e["before_m"] == pytest.approx(LS.BEFORE_M, abs=1.5)
    c = net.chains[0]
    tang, _ = c.line.frame(ents["forward"]["s"])
    east = float(tang[0]) > 0                      # chain may run either way
    w_entry = ents["forward"] if east else ents["backward"]     # the post met by eastbound traffic
    e_entry = ents["backward"] if east else ents["forward"]
    assert w_entry["e"] == pytest.approx(200.0 - LS.BEFORE_M, abs=1.5) and w_entry["n"] < -3.0   # right of eastbound
    assert e_entry["e"] == pytest.approx(400.0 + LS.BEFORE_M, abs=1.5) and e_entry["n"] > 3.0    # right of westbound
    plates = [it for it in pl.items if it["p"].startswith("plate_B-1")]
    assert len(plates) == 4
    west = sorted((it for it in plates if it["e"] < 300.0), key=lambda it: -it["z"])
    assert [it["p"] for it in west] == ["plate_B-16_3.7", "plate_B-18_12"]                      # B-16 on top


def test_oneway_bridge_gets_one_entry_and_no_limit_no_sign():
    net, attrs = _net(TYKOCIN, oneway="yes")
    pl, rep, codes = _placer(), {}, set()
    LS.limit_signs(pl, net, attrs, rep, codes)
    (st,) = rep["limit_signs"]["structures"]
    assert len(st["entries"]) == 1 and rep["limit_signs"]["placed"] == {"B-16_3.7": 1, "B-18_12": 1}
    net, attrs = _net({"bridge": {"v": "yes"}})
    pl, rep, codes = _placer(), {}, set()
    LS.limit_signs(pl, net, attrs, rep, codes)
    assert rep["limit_signs"]["structures"] == [] and not codes and not pl.items


def test_tykocin_bridge_edge_in_the_graph():
    g = json.loads((REPO / "Data/Regions/tykocin/roads.graph.json").read_text(encoding="utf-8"))
    lim = {e["id"]: LS.edge_limits(e["attrs"]) for e in g["edges"]}
    hit = {k: v for k, v in lim.items() if v != (None, None)}
    assert hit == {"w96942026:1123400724-1123401506": (3.7, 12.0)}
