"""M29 / ADR 0144 pkt 3 + ADR 0141 P2: barrier ends and doubled rows.

Unit tests run on synthetic geometry (no raw data). The region tests audit the data committed in the
repo via `roads.barrier_audit` (guardrail_runs of the generated streetscape_qa.json once the leader
regenerates the world; until then a reconstruction from roads.graph.json + overrides.yaml). No xfail left
(ADR 0159 free ends, ADR 0169 region-edge closures moved to the EditMode test of the importer).
"""

from __future__ import annotations

import numpy as np
import pytest

from conftest import REGION_ID
from roads import barrier_audit as BA
from streetscape import furniture as FU

pytestmark = pytest.mark.unit   # integration r5: no Data/raw needed (graph reconstruction) - run in the -m unit set


# ------------------------------------------------------------------------------------------ units
def test_approach_transition_mask_marks_ground_past_bridge_ends():
    br = np.zeros(60, bool)
    br[20:40] = True
    mask = FU._approach_transition_mask(br, 12.0)
    assert mask[8:20].all() and mask[40:52].all()
    assert not mask[:8].any() and not mask[20:40].any() and not mask[52:].any()


def test_approach_transition_mask_respects_chain_ends():
    br = np.zeros(30, bool)
    br[:10] = True                       # bridge at the chain start: no approach before it
    mask = FU._approach_transition_mask(br, 12.0)
    assert not mask[:10].any() and mask[10:22].all() and not mask[22:].any()
    br2 = np.zeros(30, bool)
    br2[20:] = True                      # bridge at the chain end: no approach past it
    mask2 = FU._approach_transition_mask(br2, 12.0)
    assert mask2[8:20].all() and not mask2[20:].any()


def _run(pts, key, tall=False):
    P = np.asarray(pts, float)
    return {"P": P, "Z": np.zeros(len(P)), "key": key,
            "tall": np.full(len(P), tall), "term": (True, True)}


def test_drop_doubled_rows_removes_the_shorter_parallel_row():
    a = _run(np.column_stack([np.arange(30.0), np.zeros(30)]), "c:x:L:bridge", tall=True)
    b = _run(np.column_stack([np.arange(20.0), np.full(20, 0.3)]), "c:y:R:embankment")  # 0.3 m apart, common 19 m
    q = [a, b]
    m = {}
    FU._drop_doubled_rows(q, m)
    assert [it["key"] for it in q] == ["c:x:L:bridge"]
    assert m["doubled_rows_removed"] == 1 and m["doubled_rows_keys"] == ["c:y:R:embankment"]


def test_drop_doubled_rows_keeps_apart_and_joined_runs():
    # 2 m apart: not a doubling
    a = _run(np.column_stack([np.arange(30.0), np.zeros(30)]), "a")
    b = _run(np.column_stack([np.arange(30.0), np.full(30, 2.0)]), "b")
    q = [a, b]
    FU._drop_doubled_rows(q, {})
    assert len(q) == 2
    # a V join: the runs converge only at the last points (inside the join zone) - both stay
    P1 = np.column_stack([np.arange(30.0), np.zeros(30)])
    P2 = np.column_stack([np.arange(30.0), np.linspace(3.0, 0.2, 30)])
    q = [_run(P1, "a"), _run(P2, "b")]
    FU._drop_doubled_rows(q, {})
    assert len(q) == 2


def test_drop_doubled_rows_never_drops_an_authored_rail():
    a = _run(np.column_stack([np.arange(30.0), np.zeros(30)]), "authored:dk8-ramp-split-barrier")
    b = _run(np.column_stack([np.arange(20.0), np.full(20, 0.3)]), "c:x:L:bridge", tall=True)
    q = [a, b]
    FU._drop_doubled_rows(q, {})
    assert [it["key"] for it in q] == ["authored:dk8-ramp-split-barrier"]


def test_deck_end_continued_by_an_approach_run_is_not_free():
    # M29: with the transition the deck run is one run with the approach; its far (ground) end is the only
    # run end there, so the deck end inside the run is not a free end
    deck = _run(np.column_stack([np.arange(30.0), np.zeros(30)]), "c:x:L:bridge")
    deck["tall"][:] = False
    deck["tall"][10:20] = True          # the deck stretch in the middle, approach (ground) at both run ends
    m = {}
    FU._mark_free_deck_ends([deck], m)
    assert deck["term_tall"] == (False, False)      # neither end of the run is a free DECK end
    assert m["deck_free_ends"] == 0


# ------------------------------------------------------------------------------------------ region (xfail)
@pytest.fixture(scope="module")
def audit():
    return BA.analyze_region(REGION_ID)


# ADR 0159: xfail removed. The last two "free" ends (c:w177895177 L at E 669.4 N -781.9, c:w240542867 R at
# E -739.6 N 74.1) are ends the dedup led onto the BODY of the rail of the merging deck - continued, not free
# (barrier_audit.FREE_END_ON_RAIL_M).
def test_no_free_deck_ends(audit):
    assert audit["deck_run_ends_free"] == 0, audit["free_ends"][:10]


# ADR 0169: xfail removed. The pair it documented (Maczka w257367422 x trunk_link w606396469, 0.20 m apart at
# E -998.5 N 58.5) were region-edge closures recomputed here by a Python copy of WorldEdgeBuilder.ReadExits; the
# importer is their only source now and merges them (EditMode WorldEdgeClosureDuplicateTests). Rail rows: 0.
def test_no_overlapping_barrier_rows(audit):
    assert audit["rail_row_overlaps"] == 0, audit["rail_overlaps"]
