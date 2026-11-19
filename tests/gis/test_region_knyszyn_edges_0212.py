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
    from roads.markings import EDGE_LINE_MIN_INSET, edge_line_width, edge_lines
    net, _, _, _ = pipeline.build_network(region_id)
    assert not net.overrides_stale
    ways = {f"w{w}" for w in _dk65_override(region_id)["target"]["osm_way"]}
    secs = [s for s in net.sec_list if str(s.edge_id).split(":")[0] in ways and not s.roundabout]
    assert secs
    for s in secs:
        hw = s.width / 2
        lats = sorted(lat for lat, _ in edge_lines(s, hw, 1))
        # ADR 0212: axis 0.20 m inside the 7.5 m edge = 3.55 m (7.1 m line to line, +0.3 m against the orthophoto).
        # ADR 0304: `dk65-edge-line-spacing-0304` puts them 6.8 m apart (orthophoto 0.1 m at the seams: 6.75-6.8 m);
        # way 27718745 (knyszyn-s, width profile 6.6 -> 7.5 m) keeps the 0.20 m inset
        off = hw - S.EDGE_LINE_INSET_MINOR
        if s.edge_line_spacing:
            assert s.edge_line_spacing == 6.8 and str(s.edge_id).split(":")[0] != "w27718745", s.edge_id
            off = min(0.5 * s.edge_line_spacing, hw - EDGE_LINE_MIN_INSET)
        else:
            assert str(s.edge_id).split(":")[0] == "w27718745", s.edge_id
        assert lats == pytest.approx([-off, off]), s.edge_id
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


def _crossings_x(region_id, seam_x):
    g = _graph(region_id)
    nodes = {n["id"]: n for n in g["nodes"]}
    out = {}
    for e in g["edges"]:
        for k in ("from", "to"):
            n = nodes[e[k]]
            if abs(n["x"] - seam_x) < 0.01:
                out.setdefault(e["osm_way"], set()).add(round(n["y"], 1))
    return out


def test_tykocin_tile_on_the_lattice_and_pinned():
    import regions
    c = regions.get("bialystok-industrial-c")
    r = regions.get("dw671-tykocin-01")
    i, j = -9, 7
    assert r.bbox == (c.bbox[0] + 2048 * i, c.bbox[1] + 2048 * j, c.bbox[0] + 2048 * (i + 1), c.bbox[1] + 2048 * (j + 1))
    assert r.bbox[3] == regions.get("knyszyn-w").bbox[1] and r.bbox[2] == regions.get("knyszyn-s").bbox[0]
    assert regions.source_pins("dw671-tykocin-01") == {"nmt_year": "2022"}


def test_tykocin_seams_same_roads_same_points():
    n_t, n_w = _crossings("dw671-tykocin-01", 611583.0), _crossings("knyszyn-w", 611583.0)
    assert 70329870 in n_t and n_t == n_w            # DW671 Tykocka + a service road cross the north seam
    e_t, e_s = _crossings_x("dw671-tykocin-01", 760587.0), _crossings_x("knyszyn-s", 760587.0)
    assert e_t == e_s


def test_tykocin_terrain_seams_identical():
    def load(rid):
        t = json.loads((REGIONS / rid / "terrain.json").read_text(encoding="utf-8"))
        assert t["source_manifest"] == f"gugik-nmt-2022-{rid}"
        f = REPO / t["encoding"]["file"]
        if not f.exists():
            pytest.skip(f"{f} missing (not in git): run build_region.py")
        a = np.fromfile(f, "<u2").reshape(2049, 2049).astype(float)
        return t["encoding"]["offset_m"] + a * t["encoding"]["scale_m_per_unit"]
    t, w, s = load("dw671-tykocin-01"), load("knyszyn-w"), load("knyszyn-s")
    assert np.abs(t[0, :] - w[-1, :]).max() < 0.002       # north edge of (-9,7) = south edge of knyszyn-w
    assert np.abs(t[:, -1] - s[:, 0]).max() < 0.002       # east edge of (-9,7) = west edge of knyszyn-s


def test_knyszyn_roundabout_splitter_legs_stay_without_edge_lines():
    """The only DK65 (primary) sections outside the override: one-way single-lane legs at the splitter islands of the
    DK65/DW671 roundabout in `knyszyn` (ADR 0212 decision 1)."""
    from roads import pipeline
    from roads.markings import edge_lines
    out = {}
    for r in KNYSZYN + ("dk65-monki-01",):
        ways = {f"w{w}" for w in _dk65_override(r)["target"]["osm_way"]}
        net, _, _, _ = pipeline.build_network(r)
        for s in net.sec_list:
            if s.highway == "primary" and not s.roundabout and str(s.edge_id).split(":")[0] not in ways:
                out[s.edge_id] = s
    assert {k.split(":")[0] for k in out} == {"w1464342634", "w1464342635", "w1464342638", "w1464342640"}
    for s in out.values():
        assert s.oneway and s.lanes == 1 and edge_lines(s, s.width / 2, 1) == []


@pytest.mark.parametrize("region_id", ["knyszyn-w", "dk65-monki-01", "dw671-tykocin-01"])
def test_year_pin_selects_the_sheets_of_the_manifest(region_id):
    """The akt_rok grouping (ADR 0212) picks for every pinned region exactly the NMT sheets of its manifest
    (knyszyn-w was ingested with the per-day grouping of ADR 0209: unchanged)."""
    import ingest
    import regions
    av = REPO / "Data" / "SourceManifests" / f"{region_id}.gugik-availability.json"
    mf = REPO / "Data" / "SourceManifests" / f"gugik-nmt-2022-{region_id}.json"
    if not av.exists() or not mf.exists():
        pytest.skip("availability / manifest missing: run ingest.py")
    idx = json.loads(av.read_text(encoding="utf-8"))
    pred = lambda r: (r.get("char_przestrz") == "1.00 m" and r.get("format", "").startswith("ARC/INFO")
                      and r.get("uklad_h") == "PL-EVRF2007-NH" and r.get("akt_rok") == "2022")
    got = sorted(r["url_do_pobrania"] for r in ingest.pick_latest(idx["products"]["NMT"], regions.get(region_id).bbox, pred, key="akt_rok"))
    want = sorted(f["url"] for f in json.loads(mf.read_text(encoding="utf-8"))["files"])
    assert got == want and len(got) == 4
