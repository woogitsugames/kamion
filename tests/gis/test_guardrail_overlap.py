"""ADR 0144 (REVIEW s14-0123 P1-1): one rail system per edge, no rail end left in the air, no white foot plates.

Unit tests run without raw data; the region tests read `furniture.guardrail_runs` of the generated
streetscape_qa.json (every built W-beam run: 1 m points E, N, foot z, deck flag).
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from conftest import REGION_DIR

from roads import standards as S
from roads.meshing import MeshBuf
from streetscape import furniture as FU

# two W-beams of one separator are traced 1.5 m apart and meet in a V before the nose (ADR 0123): rails may come
# closer than OVERLAP_M only within JOIN_ZONE_M of an end of one of them
OVERLAP_M = 1.0
JOIN_ZONE_M = 12.0
LEVEL_DZ = 1.0


def _lin():
    return FU.Lin(MeshBuf(), lambda e, n: np.zeros(len(np.atleast_1d(e))))


def _straight(n, e0=0.0, north=0.0):
    return np.column_stack([e0 + np.arange(n, dtype=float), np.full(n, north)])


# ------------------------------------------------------------------------------------------ units
def test_free_deck_end_is_marked_and_turned_down():
    deck = {"P": _straight(30), "Z": np.full(30, 5.0), "key": "deck", "tall": np.ones(30, bool), "term": (True, True)}
    # a ground rail led onto the start of the deck barrier: that end carries on, the far end is free
    lead = {"P": _straight(20, e0=-20.5, north=0.3), "Z": np.full(20, 4.8), "key": "lead", "tall": np.zeros(20, bool),
            "term": (True, False)}
    m = {}
    FU._mark_free_deck_ends([deck, lead], m)
    assert deck["term_tall"] == (False, True)
    assert lead["term_tall"] == (False, False)
    assert m["deck_free_ends"] == 1
    lin = _lin()
    FU.guardrail(lin, deck["P"], deck["Z"], "deck", deck["tall"], deck["term"], deck["term_tall"])
    V = np.concatenate([p.V for p in lin.buf.parts if p.mat == "barrier_steel" and p.layer != "collision"])
    end = V[V[:, 0] > 28.5]
    start = V[V[:, 0] < 0.5]
    # free end: the beam comes down to the ground terminal height; the continued end keeps the full barrier height
    assert end[:, 2].max() <= 5.0 + 0.45
    assert start[:, 2].max() >= 5.0 + S.GUARDRAIL_H - 0.05


def test_cancelled_terminal_is_not_a_free_deck_end():
    deck = {"P": _straight(30), "Z": np.full(30, 5.0), "key": "deck", "tall": np.ones(30, bool), "term": (False, False)}
    FU._mark_free_deck_ends([deck])
    assert deck["term_tall"] == (False, False)


def test_deck_posts_have_no_foot_plate():
    lin = _lin()
    P, Z = _straight(24), np.full(24, 5.0)
    FU.guardrail(lin, P, Z, "deck", np.ones(24, bool), (False, False))
    for p in lin.buf.parts:
        if p.layer == "collision":
            continue
        A = p.V[p.T]
        nrm = np.cross(A[:, 1] - A[:, 0], A[:, 2] - A[:, 0])
        up = np.abs(nrm[:, 2]) > 0.99 * np.maximum(np.linalg.norm(nrm, axis=1), 1e-12)
        at_foot = np.abs(A[:, :, 2].mean(1) - 5.0) < 0.06
        assert not (up & at_foot).any(), "horizontal quad at the foot of a deck post (white plate)"


def test_parapet_is_dropped_only_beside_a_deck_barrier():
    buf = MeshBuf()
    # two balustrade strips: one 0.25 m beside the deck barrier, one 3 m away (another edge)
    for north, src in ((0.25, "c:a:parapet"), (3.0, "c:b:parapet")):
        V = np.array([[e, north, z] for e in range(0, 21) for z in (6.0, 6.1)], float)
        T = np.array([[2 * k, 2 * k + 2, 2 * k + 3] for k in range(20)] + [[2 * k, 2 * k + 3, 2 * k + 1] for k in range(20)])
        buf.add("bridge", "barrier_steel", V, V[:, :2], T, src=src)
    runs = [{"P": _straight(21), "Z": np.full(21, 5.0), "tall": np.ones(21, bool)},
            {"P": _straight(21, north=3.2), "Z": np.full(21, 5.0), "tall": np.zeros(21, bool)}]   # ground rail: ignored
    m = {}
    n = FU.drop_parapets_at_barriers(buf, runs, m)
    assert n == 40 and m["parapet_tris_dropped"] == 40
    assert len(buf.parts[0].T) == 0 and len(buf.parts[1].T) == 40


def test_bridge_dips():
    Z = np.array([10.0, 10.0, 10.0, 9.2, 9.1, 9.3, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0])
    assert np.allclose(FU._bridge_dips(Z), 10.0)
    # a dip at the end of the run (rail carried over the grass before a deck joint)
    Z = np.concatenate([np.full(20, 10.0), [9.5, 9.0, 8.8]])
    assert FU._bridge_dips(Z).min() >= 10.0 - 1e-9
    # a real, long descent is kept
    Z = np.linspace(10.0, 6.0, 40)
    assert np.allclose(FU._bridge_dips(Z), Z)


# ------------------------------------------------------------------------------------------ region
@pytest.fixture(scope="module")
def runs():
    p = REGION_DIR / "generated" / "streetscape_qa.json"
    if not p.exists():
        pytest.skip("streetscape_qa.json not generated")
    r = json.loads(p.read_text(encoding="utf-8")).get("furniture", {}).get("guardrail_runs")
    if not r:
        pytest.skip("streetscape_qa.json has no guardrail_runs (generated before ADR 0144)")
    return [{**x, "A": np.asarray(x["pts"], float)} for x in r]


def overlaps(runs):
    """[(key a, key b, metres, E, N)] of stretches where two runs at one level are closer than OVERLAP_M outside the
    join zone at the ends of either run."""
    from scipy.spatial import cKDTree
    out = []
    trees = [cKDTree(r["A"][:, :2]) for r in runs]
    for i, a in enumerate(runs):
        A = a["A"]
        sa = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(A[:, :2], axis=0).T))])
        for j in range(i + 1, len(runs)):
            B = runs[j]["A"]
            if (A[:, 0].min() > B[:, 0].max() + 2 or B[:, 0].min() > A[:, 0].max() + 2
                    or A[:, 1].min() > B[:, 1].max() + 2 or B[:, 1].min() > A[:, 1].max() + 2):
                continue
            d, k = trees[j].query(A[:, :2])
            sb = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(B[:, :2], axis=0).T))])
            near = (d < OVERLAP_M) & (np.abs(A[:, 2] - B[k, 2]) < LEVEL_DZ)
            inner = (sa > JOIN_ZONE_M) & (sa < sa[-1] - JOIN_ZONE_M) & (sb[k] > JOIN_ZONE_M) & (sb[k] < sb[-1] - JOIN_ZONE_M)
            bad = near & inner
            if bad.any():
                q = A[np.where(bad)[0][0]]
                out.append((a["key"], runs[j]["key"], int(bad.sum()), round(float(q[0]), 1), round(float(q[1]), 1)))
    return out


def test_no_two_barriers_side_by_side(runs):
    bad = overlaps(runs)
    assert not bad, f"W-beam runs closer than {OVERLAP_M} m outside a join: {bad[:8]}"


def test_no_deck_barrier_end_in_the_air(runs):
    ends = [(i, r["A"][e][:3]) for i, r in enumerate(runs) for e in (0, -1)]
    hanging = []
    for i, r in enumerate(runs):
        for e, name in ((0, "start"), (-1, "end")):
            if not r["A"][e][3] or not r["term"][0 if e == 0 else 1]:
                continue                                   # ground end, or a terminal cancelled on purpose (join / authored)
            p = r["A"][e][:3]
            cont = any(j != i and np.hypot(*(q[:2] - p[:2])) <= FU.RAIL_CONTINUE_M and abs(q[2] - p[2]) <= FU.RAIL_CONTINUE_DZ
                       for j, q in ends)
            if not cont and not r["term_tall"][0 if e == 0 else 1]:
                hanging.append((r["key"], name, [round(float(v), 1) for v in p[:2]]))
    assert not hanging, hanging


def test_rails_of_the_dk8_separator_reach_the_deck_barriers(runs):
    """p0_kerb_merge_eye: both authored rails of dk8-ramp-split-island end at the first post of a deck barrier, at its
    height (they used to end 2.4 m short / 0.75 m low)."""
    deck_ends = [r["A"][e][:3] for r in runs for e in (0, -1) if r["A"][e][3]]
    for key in ("authored:dk8-ramp-split-barrier", "authored:dk8-ramp-split-barrier-n"):
        mine = [r for r in runs if r["key"] == key]
        assert mine, key
        east = max((r["A"][e][:3] for r in mine for e in (0, -1)), key=lambda p: p[0])
        d = min((float(np.hypot(*(q[:2] - east[:2]))), abs(float(q[2] - east[2]))) for q in deck_ends)
        assert d[0] <= 1.0 and d[1] <= 0.45, (key, east.tolist(), d)
