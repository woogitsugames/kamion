"""ADR 0212: DK65 edge lines in knyszyn / knyszyn-w / knyszyn-s (one set across both seams), the year-pinned NMT
series of ingest.py, and tile dk65-monki-01 (lattice (-9,9), north of knyszyn-w towards Monki)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
REGIONS = REPO / "Data" / "Regions"
KNYSZYN = ("knyszyn", "knyszyn-w", "knyszyn-s")
DK65_SET = {"lanes": 2, "lane_width": 3.4, "edge_strip": 0.35, "edge_lines": "both"}


def _dk65_override(region_id):
    ov = yaml.safe_load((REGIONS / region_id / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    return next(o for o in ov if o["id"] == "dk65-carriageway-width")


def test_same_dk65_set_in_all_knyszyn_tiles():
    for r in KNYSZYN:
        assert _dk65_override(r)["set"] == DK65_SET, r
    # the ways that cross the seams carry the override on both sides
    assert 232511646 in _dk65_override("knyszyn")["target"]["osm_way"]
    assert 232511646 in _dk65_override("knyszyn-w")["target"]["osm_way"]
    assert 286990127 in _dk65_override("knyszyn")["target"]["osm_way"]
    assert 286990127 in _dk65_override("knyszyn-s")["target"]["osm_way"]


@pytest.mark.parametrize("region_id", KNYSZYN)
def test_dk65_sections_paint_narrow_edge_lines_at_measured_offset(region_id):
    from roads import pipeline
    from roads import standards as S
    from roads.markings import edge_line_width, edge_lines
    net, _, _, _ = pipeline.build_network(region_id)
    assert not net.overrides_stale
    ways = {f"w{w}" for w in _dk65_override(region_id)["target"]["osm_way"]}
    secs = [s for s in net.sec_list if str(s.edge_id).split(":")[0] in ways and not s.roundabout]
    assert secs
    for s in secs:
        hw = s.width / 2
        lats = sorted(lat for lat, _ in edge_lines(s, hw, 1))
        # orthophoto 0.1 m 2025: line peaks 3.0-4.0 m off the OSM axis, median ~3.55 m
        assert lats == pytest.approx([-(hw - S.EDGE_LINE_INSET_MINOR), hw - S.EDGE_LINE_INSET_MINOR]), s.edge_id
        assert 3.3 <= lats[1] <= 3.8
        assert edge_line_width(s) == S.LINE_W_NARROW


def test_year_pin_joins_flight_days_of_one_year():
    import ingest

    def row(godlo, date, x0):
        return {"godlo": godlo, "akt_data": date, "akt_rok": date[:4], "url_do_pobrania": f"u/{godlo}-{date}",
                "ring": [[x0, 0], [x0 + 1, 0], [x0 + 1, 1], [x0, 1], [x0, 0]]}
    rows = [row("a", "2022-07-29", 0), row("b", "2022-08-27", 1), row("a", "2025-05-27", 0)]
    bbox = (0, 0, 2, 1)
    assert ingest.pick_latest(rows, bbox, lambda r: r["akt_rok"] == "2022") == []      # per day: no full cover
    got = ingest.pick_latest(rows, bbox, lambda r: r["akt_rok"] == "2022", key="akt_rok")
    assert [r["godlo"] for r in got] == ["a", "b"]
    # a repeated sheet in the pinned year keeps its latest flight day
    rows.append(row("a", "2022-09-01", 0))
    got = ingest.pick_latest(rows, bbox, lambda r: r["akt_rok"] == "2022", key="akt_rok")
    assert {r["akt_data"] for r in got} == {"2022-09-01", "2022-08-27"}


def test_monki_tile_on_the_lattice_north_of_knyszyn_w():
    import regions
    c = regions.get("bialystok-industrial-c")
    r = regions.get("dk65-monki-01")
    i, j = -9, 9
    assert r.bbox == (c.bbox[0] + 2048 * i, c.bbox[1] + 2048 * j, c.bbox[0] + 2048 * (i + 1), c.bbox[1] + 2048 * (j + 1))
    assert r.bbox[1] == regions.get("knyszyn-w").bbox[3]
    assert r.teryt_powiat == "2008"
    assert regions.source_pins("dk65-monki-01") == {"nmt_year": "2022"}


def _graph(region_id):
    p = REGIONS / region_id / "roads.graph.json"
    if not p.exists():
        pytest.skip(f"{p} missing: run build_region.py")
    return json.loads(p.read_text(encoding="utf-8"))


def _crossings(region_id, seam_y):
    g = _graph(region_id)
    nodes = {n["id"]: n for n in g["nodes"]}
    out = {}
    for e in g["edges"]:
        for k in ("from", "to"):
            n = nodes[e[k]]
            if abs(n["y"] - seam_y) < 0.01:
                out.setdefault(e["osm_way"], set()).add(round(n["x"], 1))
    return out


def test_monki_seam_same_roads_same_points():
    seam = 613631.0
    m, w = _crossings("dk65-monki-01", seam), _crossings("knyszyn-w", seam)
    assert 232511647 in m          # DK65 crosses into the new tile
    assert set(m) == set(w)
    for way in m:
        assert m[way] == w[way], way


def test_monki_dk65_carries_the_knyszyn_w_cross_section():
    ov = _dk65_override("dk65-monki-01")
    assert ov["set"] == DK65_SET
    from roads import pipeline
    net, _, _, _ = pipeline.build_network("dk65-monki-01")
    assert not net.overrides_stale
    dk = [s for s in net.sec_list if s.highway == "primary"]
    assert dk and all(s.lanes == 2 and abs(s.width - 7.5) < 1e-6 for s in dk)


def test_monki_terrain_seam_identical():
    rows = []
    for rid, row in (("dk65-monki-01", 0), ("knyszyn-w", -1)):
        t = json.loads((REGIONS / rid / "terrain.json").read_text(encoding="utf-8")) if (REGIONS / rid / "terrain.json").exists() else None
        if t is None:
            pytest.skip("terrain.json missing: run build_region.py")
        assert t["source_manifest"] == f"gugik-nmt-2022-{rid}"
        f = REPO / t["encoding"]["file"]
        if not f.exists():
            pytest.skip(f"{f} missing (not in git): run build_region.py")
        a = np.fromfile(f, "<u2").reshape(2049, 2049).astype(float)
        rows.append((t, a))
    # heightmap_2049.r16: row 0 = north edge (build_region.py)
    (tm, am), (tw, aw) = rows
    hm = lambda t, a, r: t["encoding"]["offset_m"] + a[r, :] * t["encoding"]["scale_m_per_unit"]
    assert np.abs(hm(tm, am, -1) - hm(tw, aw, 0)).max() < 0.002
