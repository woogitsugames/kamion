"""Road fidelity ratchet for the start route (ADR 0075).

Reads Data/Regions/<id>/generated/fidelity_qa.json written by
    uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c
Owner targets (docs/11, 2026-11-10: "drogi mają być dosłownie takie same jak na OSM"):
    axis p95 <= 1.0 m, carriageway edge p95 <= 0.75 m, lane count matches on 100 % of verified route segments,
    0 generated islands absent on the orthophoto.
Targets not met yet are xfail(strict=True): when the generator gets there, the xfail turns into XPASS -> fail ->
move the target into the hard asserts. BASELINE is the current state; it may only get better.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from conftest import REGION_DIR, REPO

QA = REGION_DIR / "generated" / "fidelity_qa.json"
TARGET = {"axis_p95": 1.0, "edge_p95": 0.75, "lane_mismatch": 0, "islands_absent": 0}
# Ratchet: never worse than this (+ small tolerance for classifier noise).
# Refreshed 2026-11-11 (ADR 0077) on a full measurement. The fidelity-r9 numbers (axis 0.032, edge 2.04, islands 4,
# lane bug 3) were measured BEFORE ADR 0074 was merged; the same code that is on main (merge base ffcc7b7, gores off:
# artifacts/islands-r10/fidelity_before_qa.json) measures axis p95 0.129 (align_forks of ADR 0074 moves fork arms off
# the OSM way, max 3.25 m), edge p95 2.483, islands 4, lane bug 0 (2 of the 3 were roundabout entries = tool error).
# Now: axis 0.13 (unchanged; authored center_offset placement is excluded from the pooled axis by design), edge p95
# 2.52 (p50 0.76 -> 0.46; the tail is local widenings / bays the generator does not build), islands 1, lane bug 0.
BASELINE = {"axis_p95": 0.13, "edge_p95": 2.31, "lane_mismatch": 0, "islands_absent": 0, "lane_into_island_bug": 0}   # ADR 0095: edge 2.52 -> 2.30, islands 1 -> 0
TOL = {"axis_p95": 0.02, "edge_p95": 0.05}


@pytest.fixture(scope="module")
def qa():
    if not QA.exists():
        pytest.skip("fidelity_qa.json not built (tools/worldgen/fidelity/run.py)")
    return json.loads(QA.read_text(encoding="utf-8"))


def _sha(p):
    # CRLF-normalised, same as tools/worldgen/fidelity/run.py sha_file
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_report_not_stale(qa):
    """The report must describe the current graph, overrides, route and road generator."""
    stale = []
    for k, v in qa["inputs_sha256"].items():
        p = (REGION_DIR / k) if "/" not in k else (REPO / k)
        if not p.exists() or _sha(p) != v:
            stale.append(k)
    assert not stale, f"fidelity_qa.json is stale for {stale}: rerun tools/worldgen/fidelity/run.py"


def test_osm_snapshot_recorded(qa):
    assert qa["summary"]["osm_snapshot"] and len(qa["summary"]["osm_sha256"]) == 64


def _route(qa):
    return qa["summary"]["route"]


def test_ratchet_axis(qa):
    assert _route(qa)["axis_vs_osm_m"]["p95"] <= BASELINE["axis_p95"] + TOL["axis_p95"]


def test_ratchet_edges(qa):
    r = _route(qa)["edge_vs_ortho_m"]
    assert r["valid_sides"] >= 200, "too few ortho edge detections to judge"
    assert r["p95"] <= BASELINE["edge_p95"] + TOL["edge_p95"]


def test_ratchet_lanes(qa):
    ln = _route(qa)["lanes"]
    assert len(ln["mismatch"]) <= BASELINE["lane_mismatch"]
    # 25 of 29 route segments verifiable (OSM lanes tag or marked road on ortho); the 4 unmarked yard roads are not
    assert ln["verified"] >= 25


def test_ratchet_islands(qa):
    assert _route(qa)["gen_islands_absent_on_ortho"] <= BASELINE["islands_absent"]
    assert _route(qa)["lane_into_island_generator_bug"] <= BASELINE["lane_into_island_bug"]


# which owner targets are already met (hard asserts); the rest xfail until met, then this test fails ("promote")
MET = {"axis_p95": True, "edge_p95": False, "lane_mismatch": True, "islands_absent": True}


def _target(name, ok):
    if MET[name]:
        assert ok, f"owner target {name} regressed"
    elif ok:
        pytest.fail(f"owner target {name} is now met: set MET['{name}'] = True (strict ratchet)")
    else:
        pytest.xfail(f"owner target {name} not met yet (ADR 0075, artifacts/fidelity-r9/DIFFS.md)")


def test_target_axis_p95(qa):
    _target("axis_p95", _route(qa)["axis_vs_osm_m"]["p95"] <= TARGET["axis_p95"])


def test_target_edge_p95(qa):
    _target("edge_p95", _route(qa)["edge_vs_ortho_m"]["p95"] <= TARGET["edge_p95"])


def test_target_lane_count(qa):
    _target("lane_mismatch", len(_route(qa)["lanes"]["mismatch"]) <= TARGET["lane_mismatch"])


def test_target_no_phantom_islands(qa):
    _target("islands_absent", _route(qa)["gen_islands_absent_on_ortho"] <= TARGET["islands_absent"])
