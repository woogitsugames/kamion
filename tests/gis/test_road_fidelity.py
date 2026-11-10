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
# measured 2026-11-11 (roads-p0-r10, ADR 0076 section "Ratchety fidelity"); ratchet: never worse than this.
#   axis_p95        0.032 (r9) -> 0.129: network.align_forks (ADR 0074, lane continuity at forks whose lanes add up) moves
#                   the Andersa -> Rondo Putry link w606396463 3.25 m off its OSM axis (and tapers w173956083 back);
#                   every other route edge has p95 <= 0.11 m. ADR 0076 r1 (carriageways pushed abreast) raised it to
#                   1.745 and was withdrawn after the orthophoto check; the merge layout is on the OSM axes again.
#   edge_p95        2.04 -> 2.50: the same link is now measured (18 stations, 3.9 m) + classifier noise on 3 edges.
#   islands_absent  4 -> 6: both new ones come with the ADR 0074 fork shifts - (336, -563) 14 m2 in the S-bend of the
#                   slip w282244180, (-366, -119) 373 m2 between the viaduct ramp and the link (road fraction 0.69).
#                   Owner: ADR 0077 (gores / junction corners); target there <= 4, here it must not grow.
#   lane_into_island_bug 3 -> 2.
# main's fidelity_qa.json was older than ADR 0074 (test_report_not_stale red on main), so these are the first
# measured values of the ADR 0074 generator; ADR 0076 r2 itself changes none of them.
BASELINE = {"axis_p95": 0.129, "edge_p95": 2.50, "lane_mismatch": 0, "islands_absent": 6, "lane_into_island_bug": 2}
TOL = {"axis_p95": 0.001, "edge_p95": 0.05}      # the axis is deterministic; edges carry classifier noise


@pytest.fixture(scope="module")
def qa():
    if not QA.exists():
        pytest.skip("fidelity_qa.json not built (tools/worldgen/fidelity/run.py)")
    return json.loads(QA.read_text(encoding="utf-8"))


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


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
MET = {"axis_p95": True, "edge_p95": False, "lane_mismatch": True, "islands_absent": False}


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
