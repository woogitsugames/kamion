"""Unit test (no Data/raw): brand filter for OSM text printed on direction boards (BRAND-SWEEP-S20 #6).

Run: uv run --project tools/worldgen pytest tests/gis -q -m unit
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from streetscape import brand_filter as BF

pytestmark = pytest.mark.unit

REPO = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("text", [
    "stacja paliw BP", "Circle K", "Orlen", "Biedronka", "McDonald's", "Kwadrat Park", "Browar Dojlidy",
    "Biazet S.A.", "Galeria Jurowiecka", "Lidl", "Żabka", "DHL Parcel",
])
def test_branded_destinations_are_dropped(text):
    assert BF.is_branded(text)
    kept, dropped = BF.neutral_destinations(["Warszawa", text])
    assert kept == ["Warszawa"] and dropped == [text]


@pytest.mark.parametrize("text", [
    "Centrum handlowe", "Lotnisko", "Warszawa", "Augustów", "Centrum", "Dojlidy", "Fasty", "Krywlany",
    "Białostoczek", "stacja paliw", "browar", "Rondo Putry", "Andersa", "Bielsk Podlaski", "Manifest",
])
def test_generic_places_pass(text):
    assert not BF.is_branded(text)


# Branded destinations found in the tracked route graphs (s21): the filter drops them on the next build_world.
# bialystok-maczka: OSM `destination=...;Orlen` on a service road into a fuel station (not in BRAND-SWEEP-S20,
# region ingested after the sweep).
KNOWN_BRANDED = {("bialystok-maczka", "Orlen")}


def _graph_destinations():
    for g in sorted((REPO / "Data" / "Regions").glob("*/roads.graph.json")):
        data = json.loads(g.read_text(encoding="utf-8"))
        for e in data.get("edges") or []:
            d = (e.get("attrs") or {}).get("destination")
            v = d.get("v") if isinstance(d, dict) else d
            for x in str(v or "").split(";"):
                if x.strip():
                    yield g.parent.name, x.strip()


def test_route_graph_destinations_are_reviewed():
    """Every branded destination in the tracked graphs is a reviewed one (and the filter drops it)."""
    found = {(r, x) for r, x in _graph_destinations() if BF.is_branded(x)}
    assert found <= KNOWN_BRANDED, f"new branded destination(s) {sorted(found - KNOWN_BRANDED)}: the filter drops " \
        "them from the boards; review and add to KNOWN_BRANDED"
    for _, x in found:
        assert BF.neutral_destinations([x]) == ([], [x])
