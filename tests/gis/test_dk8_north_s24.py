"""s8-north-s24 (ADR 0315): DK8 north out of Bialystok -> Wasilkow -> towards Korycin.

Checks the committed plan (docs/reports/map/dk8_north_plan.json, tools/worldgen/qa/dk8_north_plan.py) against the region
registry, the authored files and the streaming corridor - no network, no Data/raw.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import regions  # noqa: E402

PLAN = json.loads((REPO / "docs/reports/map/dk8_north_plan.json").read_text(encoding="utf-8"))
IDS = [t["id"] for t in PLAN["tiles"]]


def test_tiles_sit_on_the_lattice_of_tile_c():
    c = regions.REGIONS["bialystok-industrial-c"]
    for t in PLAN["tiles"]:
        r = regions.REGIONS[t["id"]]
        i, j = t["ij"]
        assert r.bbox == (c.bbox[0] + i * 2048.0, c.bbox[1] + j * 2048.0, c.bbox[0] + (i + 1) * 2048.0,
                          c.bbox[1] + (j + 1) * 2048.0)
        assert r.origin == ((r.bbox[0] + r.bbox[2]) / 2, (r.bbox[1] + r.bbox[3]) / 2)
        assert list(r.powiaty) == t["powiaty"]


def test_route_chain_is_continuous_and_starts_on_the_c_seam():
    first = PLAN["tiles"][0]["entry"]["crossing"]
    assert first["y"] == regions.REGIONS["bialystok-industrial-c"].bbox[3]
    for a, b in zip(PLAN["tiles"], PLAN["tiles"][1:]):
        assert a["exit"]["joins_next"], (a["id"], b["id"])
    for t in PLAN["tiles"]:
        ep = json.loads((REPO / "Data/Regions" / t["id"] / "route_endpoints.json").read_text(encoding="utf-8"))
        assert ep["start_epsg2180"] == [t["entry"]["crossing"]["x"], t["entry"]["crossing"]["y"]]
        assert ep["end_epsg2180"] == [t["exit"]["crossing"]["x"], t["exit"]["crossing"]["y"]]


def test_nmt_pin_matches_tile_c():
    for rid in IDS:
        assert regions.source_pins(rid).get("nmt_year") == PLAN["nmt_pin"] == "2025"
    assert (REPO / "Data/SourceManifests/gugik-nmt-2025-bialystok-industrial-c.json").exists()


def test_corridor_link_and_catalog():
    cfg = yaml.safe_load((REPO / "Data/Streaming/route_links.yaml").read_text(encoding="utf-8"))
    cor = next(c for c in cfg["corridors"] if c["id"] == "bialystok-wasilkow")
    assert cor["tiles"] == ["bialystok-industrial-c", *IDS] and cor["destination"] == "wasilkow"
    link = next(L for L in cfg["links"] if L["id"] == "c-dk8-north-to-wasilkow")
    first = PLAN["tiles"][0]["entry"]["crossing"]
    assert link["replaces_route"] == "bialystok-industrial-c" and link["destination"] == "wasilkow"
    assert abs(link["end_epsg2180"][0] - first["x"]) < 0.1 and link["end_epsg2180"][1] == first["y"]
    cat = json.loads((REPO / "game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json").read_text("utf-8"))
    assert set(IDS) <= {r["id"] for r in cat["regions"]}
