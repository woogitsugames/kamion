"""ADR 0198: authored pier rows of the Putry under-deck dressing (estakada A) and their keep-out check.

No Data/raw, no Unity. The unit tests are instant; the `world` tests run the road stage of the generator on a flat
ground model (tools/worldgen/qa/check_piers_vs_roads.py, about 100 s once per session).
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from streetscape import hero_bridge as H

ROOT = Path(__file__).resolve().parents[2]
REGION = "bialystok-industrial-c"
CFG = ROOT / "Data" / "Regions" / REGION / "viaduct_underdeck.json"
NE, SW = "1101181473", "173956078"

sys.path.insert(0, str(ROOT / "tools" / "worldgen" / "qa"))


def _cfg():
    return json.loads(CFG.read_text(encoding="utf-8"))


def _chain(*ways):
    return SimpleNamespace(id="c:w%s:1-2" % ways[0], edges=[(f"w{w}:1-2", 1) for w in ways])


@pytest.mark.unit
def test_column_points_stand_either_side_of_the_deck_centre():
    a, b = H.column_points([0.0, 5.65, 10.0], [0.0, -5.65, 10.0], 2.0)
    np.testing.assert_allclose(a, [0.0, -2.0])
    np.testing.assert_allclose(b, [0.0, 2.0])
    a, b = H.column_points([3.0, 4.0], [-3.0, -4.0], 1.0)             # skewed rail line: unit vector (0.6, 0.8)
    np.testing.assert_allclose(b - a, [1.2, 1.6])


@pytest.mark.unit
def test_keepout_reaches_two_nodes_and_is_free_outside_the_grid():
    hf = SimpleNamespace(x0=0.0, y1=10.0)
    mask = np.zeros((11, 11), bool)
    mask[5, 5] = True                                                  # node E 5, N 5
    blocked = H.keepout(hf, mask)
    assert blocked([5.0, 5.0]) and blocked([7.4, 5.0]) and blocked([5.0, 2.6])
    assert not blocked([7.6, 5.0]) and not blocked([5.0, 8.0])
    assert not blocked([-50.0, 5.0])


@pytest.mark.unit
def test_rows_are_selected_by_the_way_of_the_deck_chain():
    cfg = {"pier_lines_en": {"11": [[1, 2]], "22": [[3, 4], [5, 6]]}, "pier_lines_en_held": {"33": [[9, 9]]}}
    assert H.underdeck_rows(cfg, _chain(11, 44)) == [[1.0, 2.0]]
    assert H.underdeck_rows(cfg, _chain(44, 22)) == [[3.0, 4.0], [5.0, 6.0]]
    assert H.underdeck_rows(cfg, _chain(33)) is None, "held rows are documentation, never built"
    assert H.underdeck_rows({}, _chain(11)) is None, "no authored rows -> span rule"
    with pytest.raises(ValueError):
        H.underdeck_rows(cfg, _chain(11, 22))


@pytest.mark.unit
def test_putry_config_has_rows_for_both_decks_of_estakada_a():
    cfg = _cfg()
    rows = cfg["pier_lines_en"]
    assert set(rows) == {NE, SW} <= {str(x) for x in cfg["target"]["osm_way"]}
    assert len(rows[NE]) == 8, "P13-030: 7-9 rows on the NE deck"
    assert len(rows[SW]) + len(cfg["pier_lines_en_held"][SW]) == 8, "P13-031: 7-9 rows on the SW deck"
    assert "pier_lines_en" not in cfg["set"], "a flat list in `set` would be projected onto both decks"
    note = " ".join(cfg["pier_lines_note"])
    assert "WORKING_VALUE" in note and "CONFLICT" in note
    for pts in list(rows.values()) + list(cfg["pier_lines_en_held"].values()):
        assert all(len(q) == 2 for q in pts)
        e = [q[0] for q in pts]
        assert e == sorted(e), "rows listed from the north-west end"


@pytest.fixture(scope="module")
def report():
    import check_piers_vs_roads as K
    rep, _ = K.check(REGION)
    return rep


def _deck(report, way):
    return next(d for d in report["decks"] if way in d["ways"])


def test_no_column_on_the_generator_keepout_or_the_carriageway(report):
    import check_piers_vs_roads as K
    assert report["ok"], [d["failed"] for d in report["decks"]]
    for d in report["decks"]:
        assert d["authored"] and d["rows_dropped"] == 0 and d["failed"] == []
        for r in d["rows"]:
            assert len(r["cols"]) == 2
            for c in r["cols"]:
                assert not c["keepout"], (d["chain"], r["from_nw_end_m"])        # -> BLOCKED_COLS stays empty
                assert c["carriageway_m"] >= 2.5 > K.CLEAR_M, (d["chain"], r["from_nw_end_m"], c)
                assert c["yard_m"] is None or c["yard_m"] >= K.YARD_CLEAR_M, (d["chain"], r["from_nw_end_m"], c)


def test_rows_stand_at_the_authored_stations(report):
    ne, sw = _deck(report, NE), _deck(report, SW)
    np.testing.assert_allclose([r["from_nw_end_m"] for r in ne["rows"]],
                               [24.39, 48.78, 82.5, 106.0, 133.5, 155.0, 176.5, 198.0], atol=0.05)
    np.testing.assert_allclose([r["from_nw_end_m"] for r in sw["rows"]],
                               [19.5, 40.0, 56.5, 135.5, 161.5, 187.5], atol=0.05)
    assert 219.0 < ne["s_open"][1] - ne["s_open"][0] < 220.0 and 212.5 < sw["s_open"][1] - sw["s_open"][0] < 214.0


def test_ne_deck_has_no_long_span_and_no_short_pair(report):
    spans = _deck(report, NE)["spans_m"]
    assert len(spans) == 9
    assert max(spans) < 35.0, spans           # was 48.8 m
    assert min(spans) > 20.0, spans           # was a 16.4 m pair


def test_sw_deck_conflict_is_explicit(report):
    """The long span of the SW deck is shorter than before (94.8 m) but NOT closed: the two island rows cannot stand
    on the generated ring. They are listed as held and must still be blocked - when the ring geometry is corrected
    this assertion fails on purpose: move the rows to `pier_lines_en` and update ADR 0198."""
    sw = _deck(report, SW)
    assert max(sw["spans_m"]) < 80.0, sw["spans_m"]
    assert sorted(sw["spans_m"])[-2] < 27.0, sw["spans_m"]
    assert len(sw["held"]) == 2
    assert all(h["still_blocked"] for h in sw["held"]), "island rows are free now: activate them (ADR 0198)"
