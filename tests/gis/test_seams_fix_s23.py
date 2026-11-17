"""seams-fix-s23 (synthetic data, no Data/raw):

1. roads.seam_p2a: the solid P-2a of a signalised junction approach that a tile seam cuts continues in the neighbouring
   tile for the rest of P2A_MIN_LEN (symmetric rule: the neighbour's graph -> plain network -> junctions -> the marking
   rule markings.approach_ends); nothing when the junction is >= 20 m from the seam or not an approach.
2. roads.meshing.despike_arcs: isolated spikes and steps of the corner (`arc`) heights of a junction outline become
   the running median / a ramp under the kerb-line limit; mouths (`end`) keep their heights; smooth outlines unchanged.
"""
import json
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
from roads import markings as MK  # noqa: E402
from roads import meshing as M  # noqa: E402
from roads import seam_p2a as SP  # noqa: E402
from roads import seam_taper as ST  # noqa: E402
from roads import standards as S  # noqa: E402

ATTR = {"highway": {"v": "secondary", "src": "osm", "conf": "high"}, "lanes": {"v": 2, "src": "osm", "conf": "high"},
        "maxspeed": {"v": 50, "src": "osm", "conf": "high"}, "oneway": {"v": "no", "src": "default", "conf": "medium"}}


def _node(i, x, y, boundary=False, feature=None):
    return {"id": i, "x": x, "y": y, "z_terrain": 120.0, "boundary": boundary, "degree": 1, "feature": feature}


def _edge(way, a, b):
    return {"id": f"w{way}:{a['id']}-{b['id']}", "from": a["id"], "to": b["id"], "osm_way": way, "attrs": ATTR,
            "length_m": float(np.hypot(b["x"] - a["x"], b["y"] - a["y"])),
            "geometry": [[a["x"], a["y"]], [0.5 * (a["x"] + b["x"]), 0.5 * (a["y"] + b["y"])], [b["x"], b["y"]]]}


def _write(root: Path, rid: str, x0: float, nodes, edges):
    d = root / rid
    d.mkdir(parents=True)
    reg = {"bbox": {"xmin": x0, "ymin": 0.0, "xmax": x0 + 200.0, "ymax": 200.0},
           "origin": {"x": x0 + 100.0, "y": 100.0, "z": 120.0}}
    (d / "region.yaml").write_text(yaml.safe_dump(reg), encoding="utf-8")
    (d / "roads.graph.json").write_text(json.dumps({"nodes": nodes, "edges": edges,
                                                   "sources": {"z_terrain": "gugik-nmt-2025-x"}}), encoding="utf-8")
    (d / "overrides.yaml").write_text("overrides: []\n", encoding="utf-8")
    return reg


def _pair(tmp: Path, jx: float, signals=True):
    """Tile A (x 0..200) with a T junction at x = jx on the road y = 100 that crosses the seam x = 200 into tile B
    (x 200..400). Road way 7 from the seam to the junction (A) and on in B; ways 8 / 9 are the other arms in A."""
    seam_a = _node("A:s", 200.0, 100.0, boundary=True)
    j = _node("A:j", jx, 100.0, feature="highway=traffic_signals" if signals else None)
    w = _node("A:w", 0.0, 100.0, boundary=True)
    n = _node("A:n", jx, 200.0, boundary=True)
    _write(tmp, "ta", 0.0, [seam_a, j, w, n], [_edge(7, seam_a, j), _edge(8, j, w), _edge(9, j, n)])
    seam_b = _node("B:s", 200.0, 100.0, boundary=True)
    far = _node("B:e", 400.0, 100.0, boundary=True)
    _write(tmp, "tb", 200.0, [seam_b, far], [_edge(7, seam_b, far)])


def _net(tmp: Path, rid: str):
    reg = yaml.safe_load((tmp / rid / "region.yaml").read_text(encoding="utf-8"))
    g = json.loads((tmp / rid / "roads.graph.json").read_text(encoding="utf-8"))
    return ST.plain_network(g, (reg["origin"]["x"], reg["origin"]["y"]), [])


def test_p2a_rest_carried_into_the_neighbour(tmp_path):
    SP._neighbour_approaches.cache_clear()
    _pair(tmp_path, jx=190.0)                    # junction 10 m from the seam
    net_a = _net(tmp_path, "ta")
    from roads import junctions as J
    juncs = J.build_junctions(net_a, None)
    info = MK.arm_infos(juncs, net_a.sec_list)
    c7 = next(c for c in net_a.chains if "w7:" in c.id)
    appr = MK.approach_ends(c7, info, net_a.sec_list)
    assert appr, "signalised junction: the w7 arm is a P-2a approach"
    end = next(iter(appr))
    s_seam = 0.0 if end == "b" else c7.length
    painted_in_a = abs(appr[end] - s_seam)
    carry = SP.plan(_net(tmp_path, "tb"), "tb", tmp_path)
    assert len(carry) == 1
    (cid, cend), L = next(iter(carry.items()))
    assert "w7:" in cid
    assert abs(L - (S.P2A_MIN_LEN - painted_in_a)) < 1e-6
    assert 5.0 < L < S.P2A_MIN_LEN
    # tile A gets nothing back from B (no junction there)
    SP._neighbour_approaches.cache_clear()
    assert SP.plan(net_a, "ta", tmp_path) == {}


def test_no_carry_when_far_or_not_an_approach(tmp_path):
    SP._neighbour_approaches.cache_clear()
    _pair(tmp_path / "far", jx=150.0)            # 50 m from the seam: the whole P-2a lies in A
    assert SP.plan(_net(tmp_path / "far", "tb"), "tb", tmp_path / "far") == {}
    SP._neighbour_approaches.cache_clear()
    _pair(tmp_path / "nosig", jx=190.0, signals=False)   # no signals, no turn lanes: dashed up to the junction
    assert SP.plan(_net(tmp_path / "nosig", "tb"), "tb", tmp_path / "nosig") == {}


def test_despike_arcs_spike_step_and_smooth():
    n = 40
    t = np.linspace(0.0, 1.0, n, endpoint=False)
    pts = np.column_stack([np.cos(2 * np.pi * t), np.sin(2 * np.pi * t)]) * 6.0      # ~0.94 m between points
    z = 120.0 + 0.02 * np.arange(n) * (np.arange(n) < 20) + 0.02 * (40 - np.arange(n)) * (np.arange(n) >= 20)
    tags = [("arc", 0, 0.0)] * n
    assert np.allclose(M.despike_arcs(z, tags, pts), z)                             # smooth: unchanged
    zs = z.copy()
    zs[10] -= 0.15
    zs[11] -= 0.13
    out = M.despike_arcs(zs, tags, pts)
    assert np.max(np.abs(out - z)) < 0.03                                            # 2-point dip removed
    tags_end = list(tags)
    tags_end[10] = ("end", 0, 1.0)
    out = M.despike_arcs(zs, tags_end, pts)
    assert out[10] == zs[10]                                                         # a mouth keeps its height
    zt = z.copy()
    zt[25:] += 0.16                                                                  # step between points 24 and 25
    out = M.despike_arcs(zt, tags, pts)
    ds = np.hypot(*(np.roll(pts, -1, 0) - pts).T)
    grad = np.abs(np.roll(out, -1) - out) / np.maximum(ds, 0.25)
    assert grad[20:30].max() <= M.ARC_GRADE_MAX
    assert np.allclose(out[8:18], zt[8:18])     # away from the steps (24|25 and the wrap 39|0): unchanged


def test_despike_arcs_interpolates_by_distance_on_uneven_outline():
    """Codex review s24 (ADR 0289 'Recenzja s24'): flagged heights are interpolated by distance along the outline, not
    by station index. Good points 10.1 m apart differing by 0.2 m, a spike 0.1 m after the first good point and two more
    stations evenly spread in between: the repaired point must sit on the 0.02 m/m line, not half way (1 m/m)."""
    # straight-ish outline: dense cluster near a mouth, then long gap (a corner arc sampled unevenly)
    xs = [0.0, 0.1, 5.0, 10.1]
    tail = list(np.linspace(11.0, 60.0, 30))
    x = np.array(xs + tail + list(np.linspace(59.0, 1.0, 30)))
    y = np.concatenate([np.zeros(4 + 30), np.full(30, 3.0)])
    pts = np.column_stack([x, y])
    n = len(pts)
    z = np.full(n, 100.0)
    # good line 0.2 m over 10.1 m on the first span, flat elsewhere
    z[0], z[2], z[3] = 100.0, 100.0 + 0.2 * 5.0 / 10.1, 100.2
    z[4:34] = 100.2
    zs = z.copy()
    zs[1] = 100.0 - 0.3                                   # spike 0.1 m from point 0
    tags = [("arc", 0, 0.0)] * n
    out = M.despike_arcs(zs, tags, pts)
    expect = 100.0 + 0.2 * 0.1 / 10.1
    assert abs(out[1] - expect) < 0.01, out[1]
    assert abs(out[1] - out[0]) / 0.1 <= M.ARC_GRADE_MAX  # grade to the near neighbour stays a kerb-able slope
    # by index the old code gave point 1 a third of (z[2]-z[0]) ~ 0.033 m, i.e. 0.33 m/m over 0.1 m
