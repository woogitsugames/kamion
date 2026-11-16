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


def test_report_not_stale(qa):
    """The report must describe the current graph, overrides, route and road generator (ADR 0245: tracked modules
    only, CRLF-normalised, an empty module equals a missing one; a tracked module the report does not list = stale).
    Rebuilding the report needs Data/raw (orthophoto), so a cloud session cannot refresh it - the hashes do not
    depend on Data/raw, only on files in git."""
    from fidelity import inputs as FI
    stale = FI.stale(qa["inputs_sha256"], REGION_DIR, REPO)
    assert not stale, f"fidelity_qa.json is stale for {stale}: rerun tools/worldgen/fidelity/run.py"


def test_stale_check_rules(tmp_path):
    """The staleness rules themselves, on a throw-away tree (no Data/raw needed)."""
    import hashlib

    from fidelity import inputs as FI
    (tmp_path / "a.json").write_bytes(b'{"x":\r\n1}')
    rec = {"a.json": FI.sha_file(tmp_path / "a.json"), "tools/worldgen/roads/gone.py": FI.EMPTY_SHA256}
    assert rec["a.json"] == hashlib.sha256(b'{"x":\n1}').hexdigest()                   # CRLF == LF
    assert FI.stale(rec, tmp_path, tmp_path) == []                       # empty module missing = no change
    bad = {**rec, "tools/worldgen/roads/x.py": "0" * 64}
    assert FI.stale(bad, tmp_path, tmp_path) == ["tools/worldgen/roads/x.py"]     # a real module missing = stale
    (tmp_path / "a.json").write_bytes(b'{"x":2}')
    assert FI.stale(rec, tmp_path, tmp_path) == ["a.json"]


def test_stale_check_ignores_untracked_modules(tmp_path):
    """s21: an untracked WIP module of an unmerged branch (roads/tunnels.py) must not make a committed report stale
    nor leak into a new one; a tracked module missing from the report is stale."""
    import shutil
    import subprocess

    from fidelity import inputs as FI
    if shutil.which("git") is None:
        pytest.skip("git not available")
    roads = tmp_path / FI.ROADS_DIR
    roads.mkdir(parents=True)
    (roads / "a.py").write_text("A = 1\n")
    git = ["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run(git + ["init", "-q"], check=True)
    subprocess.run(git + ["add", "."], check=True)
    for f in FI.REGION_FILES:
        (tmp_path / f).write_text("{}\n")
    rec = FI.compute(tmp_path, tmp_path)
    assert set(rec) == set(FI.REGION_FILES) | {f"{FI.ROADS_DIR}/a.py"}
    (roads / "wip.py").write_text("X = 2\n")                              # untracked: not part of the generator
    assert FI.stale({**rec, f"{FI.ROADS_DIR}/wip.py": FI.EMPTY_SHA256}, tmp_path, tmp_path) == []
    assert FI.compute(tmp_path, tmp_path) == rec
    subprocess.run(git + ["add", "."], check=True)                        # now tracked: report must list it
    assert FI.stale(rec, tmp_path, tmp_path) == [f"{FI.ROADS_DIR}/wip.py"]


def test_report_lists_every_tracked_generator_module():
    """run.py and the test agree on the module set: the writer hashes exactly the tracked modules."""
    from fidelity import inputs as FI
    mods = FI.generator_modules(REPO)
    if mods is None:
        pytest.skip("git not available: tracked generator modules unknown")
    assert "tools/worldgen/roads/build_world.py" in mods and all(m.endswith(".py") for m in mods)
    assert set(FI.compute(REGION_DIR, REPO)) == set(FI.REGION_FILES) | set(mods)


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
