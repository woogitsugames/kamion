"""M29 / ADR 0144 pkt 3 + ADR 0141 P2: barrier ends and doubled rows.

Unit tests run on synthetic geometry (no raw data). The region tests audit the data committed in the
repo via `roads.barrier_audit` (guardrail_runs of the generated streetscape_qa.json once the leader
regenerates the world; until then a reconstruction from roads.graph.json + overrides.yaml) and are
xfail with the current numbers - the leader regenerates the world with the fix and removes the xfail.
"""

from __future__ import annotations

import numpy as np
import pytest

from conftest import REGION_ID
from roads import barrier_audit as BA
from streetscape import furniture as FU


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


@pytest.mark.xfail(strict=False,
                    reason="M29: wolne końce biegów pomostowych z danych repo - aktualnie 32 wg rekonstrukcji "
                           "z roads.graph.json (pełny build ADR 0144 r7d: 34); przewidywane po poprawce: 0 "
                           "(przejście pomost->dojazd). Lider regeneruje świat i zdejmuje xfail.")
def test_no_free_deck_ends(audit):
    assert audit["deck_run_ends_free"] == 0, audit["free_ends"][:10]


@pytest.mark.xfail(strict=False,
                    reason="M29: nakładające się rzędy z danych repo - aktualnie 1 para zapór na edge-west "
                           "wg kryterium <0,5 m (Maczka w257367422 x trunk_link w606396469, odstęp 0,20 m, "
                           "wspólny odcinek 7,0 m przy E -998,5 N 58,5) + 1 para w paśmie 0,5-1,0 m (0,58 m); "
                           "przewidywane po poprawce: 0. Lider regeneruje świat i zdejmuje xfail.")
def test_no_overlapping_barrier_rows(audit):
    assert audit["rail_row_overlaps"] == 0 and audit["closure_overlaps_lt_0_5m"] == 0, (
        audit["rail_overlaps"], audit["closure_overlaps"])
