"""Gaps between carriageways and authored carriageway placement (ADR 0077).

Reads Data/Regions/<id>/generated/roads_qa.json (roads/build_world.py) and overrides.yaml.
"""
from __future__ import annotations

import json

import pytest
import yaml

from conftest import REGION_DIR

QA = REGION_DIR / "generated" / "roads_qa.json"


@pytest.fixture(scope="module")
def qa():
    if not QA.exists():
        pytest.skip("roads_qa.json not built")
    return json.loads(QA.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def overrides():
    return yaml.safe_load((REGION_DIR / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]


def test_gore_stage_reported(qa):
    g = qa["summary"]["gores"]
    assert g["rule"]["status"] == "WORKING_VALUE"
    assert g["gores"], "no paved gores: the stage did not run"
    assert g["kerb_dropped_m"] > 0


def test_every_planned_gore_is_built(qa):
    """A planned gore has its kerbs dropped; without the fill there would be a hole in the road."""
    bad = [x for x in qa["summary"]["gores"]["gores"] if not x["built"]]
    assert not bad, bad


def test_authored_gores_applied(qa, overrides):
    want = {o["id"] for o in overrides if o.get("kind") in ("paved_gore", "traffic_island")}
    applied = {x["id"] for x in qa["summary"]["overrides_applied"]}
    assert want <= applied, f"not applied: {sorted(want - applied)}"
    assert not (want & set(qa["summary"]["overrides_stale"]))
    built = {x["why"].split(":", 1)[1] for x in qa["summary"]["gores"]["gores"] if x["why"].startswith("override:")}
    missing = {o["id"] for o in overrides if o.get("kind") == "paved_gore"} - built
    assert not missing, f"authored paved gores without a fill (rejected for height?): {sorted(missing)}"


def test_no_paint_from_the_gore_rule(qa, overrides):
    """ADR 0093: P-21 comes only from painted_zone polygons traced on the orthophoto; the gore stage paints nothing
    (the rule-based ladders of ADR 0077 did not match the photo) and `hatch:` on a paved_gore is gone."""
    assert not any(o.get("kind") == "paved_gore" and "hatch" in o for o in overrides)
    assert not any(x["hatch"] or "P-21" in x["note"] for x in qa["summary"]["gores"]["gores"])


def test_slivers_obey_rule(qa):
    r = qa["summary"]["gores"]["rule"]
    for x in qa["summary"]["gores"]["gores"]:
        if x["why"] == "hole":
            assert x["area_m2"] < r["min_island_m2"]


def test_center_offset_overrides_applied(qa, overrides):
    want = {o["id"] for o in overrides if "center_offset" in (o.get("set") or {})}
    assert want, "no placement overrides (MA-010 needs putry-ring-s-placement)"
    applied = {x["id"] for x in qa["summary"]["overrides_applied"]}
    assert want <= applied
    for o in overrides:
        st = o.get("set") or {}
        if "center_offset" in st:
            co = st["center_offset"]
            if isinstance(co, list) and co and isinstance(co[0], list):
                # ADR 0095 profile [[t, m], ...]: up to a lane inside the edge; near its ends up to 5.5 m (OSM draws
                # a ramp into the axis of the carriageway it joins, the real lane stays beside it)
                assert all(abs(v) <= (5.5 if (t <= 0.15 or t >= 0.85) else 3.5) for t, v in co), o["id"]
            else:
                vals = co if isinstance(co, list) else [co]
                assert all(abs(v) <= 3.5 for v in vals), "larger than a lane: fix the graph, not the placement"
            assert o.get("reason") and o.get("verify")


def test_generated_axis_still_on_osm(qa, pytestconfig):
    """Authored placement is excluded from the deviation; everything else stays where it was (fork shifts, smoothing)."""
    d = qa["summary"]["axis_smoothing_deviation_m"]
    assert d["p95"] <= 0.5, d


def test_no_kerb_under_a_fill(qa):
    """ADR 0093 (REVIEW 0077 #1): kerbs hidden by a paved gore are removed from the mesh, not sunk under it - zero
    kerb-material triangles inside a built fill (the hero-viaduct re-mesh used to bring 28 of them back)."""
    g = qa["summary"]["gores"]
    assert "kerb_tris_in_fill" in g, "old roads_qa.json: rebuild the region"
    assert g["kerb_tris_in_fill"] == 0
