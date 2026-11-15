"""ADR 0219 (a): one parser of road-graph node / edge ids for every region; fidelity `node_arm_check` no longer
crashes on tile-boundary cuts (B<edge>:<k>s|e) and gives byte-identical rows for OSM nodes (region C regression).

Pure Python, no Data/raw: reads only Data/Regions/*/{roads.graph.json, route_start.json} and the committed
Data/Regions/bialystok-industrial-c/generated/fidelity_qa.json."""
import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import roadgraph as RG  # noqa: E402
from fidelity import metrics as Mx  # noqa: E402

REGIONS = REPO / "Data" / "Regions"
GRAPHS = sorted(REGIONS.glob("*/roads.graph.json"))
C = "bialystok-industrial-c"
DOJLIDY = "bialystok-dojlidy"


def _route(rid):
    return json.loads((REGIONS / rid / "route_start.json").read_text(encoding="utf-8"))


def _old_node_arm_check(ctx, node_ids):
    """Verbatim copy of metrics.node_arm_check before ADR 0219 (the reference for the region C regression)."""
    inc = defaultdict(int)
    graph_ways = {int(eid.split(":")[0].lstrip("w")) for eid in ctx.net.sections}
    for w in ctx.osm["ways"]:
        if w["tags"].get("highway") not in Mx.DRIVABLE or w["id"] not in graph_ways:
            continue
        ns = w["nodes"]
        for i, n in enumerate(ns):
            inc[n] += (1 if i in (0, len(ns) - 1) else 2)
    jn = {}
    for j in ctx.g.world.junctions:
        for n in j.nodes:
            jn[n] = j
    out = []
    for n in node_ids:
        nid = int(str(n).lstrip("n"))
        j = jn.get(n) or jn.get(f"n{nid}")
        gen_arms = None
        if j is not None:
            gen_arms = sum(1 for a in j.arms if a.node in (n, f"n{nid}"))
        out.append({"node": n, "osm_degree": inc.get(nid, 0), "gen_arms_at_node": gen_arms,
                    "junction": j.id if j else None})
    return out


def _synthetic_ctx(rid, seed=219):
    """Ctx stub from the committed graph: OSM ways rebuilt from the graph edges (way -> ordered node list), junctions
    on a random subset of the route's OSM nodes with random arm counts. Deterministic (seeded)."""
    g = json.loads((REGIONS / rid / "roads.graph.json").read_text(encoding="utf-8"))
    rnd = random.Random(seed)
    ways = defaultdict(list)
    for e in g["edges"]:
        a, b = e["id"].split(":")[1].split("#")[0].split("-")
        ways[e["osm_way"]] += [int(a), int(b)]
    hw = sorted(Mx.DRIVABLE)
    osm = {"ways": [{"id": w, "tags": {"highway": rnd.choice(hw + ["footway"])}, "nodes": ns}
                    for w, ns in sorted(ways.items())]}
    route_nodes = _route(rid)["graph_nodes"]
    junctions = []
    for k, n in enumerate(route_nodes):
        if n.startswith("n") and rnd.random() < 0.6:
            arms = [SimpleNamespace(node=n if rnd.random() < 0.7 else f"n{k}") for _ in range(rnd.randint(1, 5))]
            junctions.append(SimpleNamespace(id=f"j:{n}", nodes=[n], arms=arms))
    ctx = SimpleNamespace(net=SimpleNamespace(sections={e["id"]: None for e in g["edges"]}), osm=osm,
                          g=SimpleNamespace(world=SimpleNamespace(junctions=junctions)))
    return ctx, route_nodes


@pytest.mark.parametrize("path", GRAPHS, ids=[p.parent.name for p in GRAPHS])
def test_every_node_and_edge_id_of_every_region_parses(path):
    g = json.loads(path.read_text(encoding="utf-8"))
    edges = {e["id"].split("#")[0] for e in g["edges"]}
    for n in g["nodes"]:
        ref = RG.parse_node_id(n["id"])
        if ref.kind == "osm":
            assert n.get("osm_node") == ref.osm_node and not n.get("boundary")
        else:                                   # a tile cut: flagged, no OSM node, on an existing clipped edge
            assert n.get("boundary") is True and "osm_node" not in n and ref.osm_node is None
            assert f"w{ref.osm_way}:{ref.way_nodes[0]}-{ref.way_nodes[1]}" in edges
    for e in g["edges"]:
        assert RG.edge_osm_way(e["id"]) == e["osm_way"]
    route = _route(path.parent.name)
    ids = {n["id"] for n in g["nodes"]}
    assert all(RG.parse_node_id(n).id in ids for n in route["graph_nodes"])
    assert all(RG.edge_osm_way(e) for e in route["edge"])


def test_minted_ids_round_trip():
    eid = "w443103344:4419538590-4419538591"
    b = RG.boundary_node_id(eid, 0, "s")
    assert b == f"B{eid}:0s"
    r = RG.parse_node_id(b)
    assert (r.kind, r.osm_way, r.way_nodes, r.piece, r.end) == ("boundary", 443103344, (4419538590, 4419538591), 0, "s")
    assert RG.parse_node_id(RG.osm_node_id(1882887381)).osm_node == 1882887381
    assert RG.edge_osm_way(eid + "#2") == 443103344


@pytest.mark.parametrize("bad", ["", "n", "nn12", "w12", "12", "Bw1:2-3", "Bw1:2-3:0x", "n12a"])
def test_unknown_node_formats_fail_loudly(bad):
    with pytest.raises(ValueError):
        RG.parse_node_id(bad)


@pytest.mark.parametrize("bad", ["ww12:1-2", "w12", "12:1-2", "Bw1:2-3:0s", "w1:2"])
def test_unknown_edge_formats_fail_loudly(bad):
    """lstrip('w') used to accept 'ww12:...' as way 12; the parser does not."""
    with pytest.raises(ValueError):
        RG.edge_osm_way(bad)


def test_region_c_route_nodes_parse_exactly_as_before():
    nodes = _route(C)["graph_nodes"]
    assert nodes and all(RG.parse_node_id(n).kind == "osm" for n in nodes)
    assert [RG.parse_node_id(n).osm_node for n in nodes] == [int(n.lstrip("n")) for n in nodes]
    committed = json.loads((REGIONS / C / "generated" / "fidelity_qa.json").read_text(encoding="utf-8"))
    assert [r["node"] for r in committed["route_node_arms"]] == nodes
    assert all("skipped" not in r for r in committed["route_node_arms"])


@pytest.mark.parametrize("seed", [1, 219, 2026])
def test_region_c_node_arm_check_identical_to_old_code(seed):
    ctx, nodes = _synthetic_ctx(C, seed)
    assert Mx.node_arm_check(ctx, nodes) == _old_node_arm_check(ctx, nodes)


def test_dojlidy_boundary_route_nodes_are_skipped_not_crashing():
    ctx, nodes = _synthetic_ctx(DOJLIDY)
    assert any(n.startswith("B") for n in nodes)
    with pytest.raises(ValueError):            # the bug: int('w443103344:...') after lstrip('n')
        _old_node_arm_check(ctx, nodes)
    rows = Mx.node_arm_check(ctx, nodes)
    assert [r["node"] for r in rows] == nodes
    skipped = [r for r in rows if r.get("skipped")]
    assert [r["node"] for r in skipped] == [n for n in nodes if n.startswith("B")]
    assert all(r["skipped"] == "tile_boundary" and r["osm_degree"] is None and r["osm_way"] for r in skipped)
    osm_nodes = [n for n in nodes if n.startswith("n")]
    assert [r for r in rows if not r.get("skipped")] == _old_node_arm_check(ctx, osm_nodes)


@pytest.mark.parametrize("rid", sorted(p.parent.name for p in GRAPHS))
def test_node_arm_check_runs_for_every_region(rid):
    ctx, nodes = _synthetic_ctx(rid)
    rows = Mx.node_arm_check(ctx, nodes)
    assert len(rows) == len(nodes)
    assert sum(1 for r in rows if r.get("skipped")) == sum(1 for n in nodes if n.startswith("B"))


# ================================================================================ (b) powiaty for a bbox (ADR 0219)
import powiaty as PW  # noqa: E402
import regions  # noqa: E402
from shapely.geometry import box  # noqa: E402

# synthetic: powiat "A" west of x = 0, "B" east of it, AOI = both
SYN = {"A": box(-10_000, -10_000, 0, 10_000), "B": box(0, -10_000, 10_000, 10_000)}
SYN_AOI = (-10_000, -10_000, 10_000, 10_000)
# PRG divergence of the hand-kept registry (regions.py) for the TILE bbox, known and reported in ADR 0219;
# knyszyn* is another agent's zone, so the registry is not changed here. Remove the entry when it is fixed.
KNOWN_REGISTRY_GAPS = {"knyszyn-s": {"2002"}}


def test_bbox_across_two_powiaty_gets_both_largest_share_first():
    assert PW.powiaty_for_bbox((-300, 0, 700, 1000), SYN, SYN_AOI) == ("B", "A")
    sh = PW.powiat_shares((-300, 0, 700, 1000), SYN, SYN_AOI)
    assert sh == pytest.approx({"B": 0.7, "A": 0.3})


def test_bbox_in_one_powiat_gets_one():
    assert PW.powiaty_for_bbox((-900, 0, -100, 800), SYN, SYN_AOI) == ("A",)
    assert PW.powiaty_for_bbox((0, 0, 800, 800), SYN, SYN_AOI) == ("B",)   # touching the border is not overlapping


def test_bbox_outside_the_data_fails_loudly():
    with pytest.raises(ValueError, match="AOI"):
        PW.powiaty_for_bbox((9_000, 0, 11_000, 100), SYN, SYN_AOI)
    with pytest.raises(ValueError, match="no powiat"):
        PW.powiaty_for_bbox((0, 0, 10, 10), {"A": box(100, 100, 200, 200)}, SYN_AOI)


def test_ring_size_is_the_far_field_ring():
    from streetscape import far_field as FF
    assert PW.RING_MAX_M == FF.RING_MAX_M


def test_committed_prg_boundaries_and_manifest():
    import hashlib
    aoi, geoms = PW.load()
    assert {"2061", "2002", "2008"} <= set(geoms)
    man = json.loads(PW.MANIFEST.read_text(encoding="utf-8"))
    assert man["files"][0]["sha256"] == hashlib.sha256(PW.BOUNDARIES.read_bytes()).hexdigest()
    assert man["aoi_epsg2180"] == list(aoi)
    for r in regions.REGIONS.values():               # every tile and far-field ring lies inside the data
        PW.powiaty_for_bbox(r.bbox)
        PW.powiaty_for_bbox(PW.ring_bbox(r.origin))


def test_region_c_and_single_powiat_tiles_unchanged():
    assert PW.powiaty_for_bbox(regions.get(C).bbox) == ("2061",)
    assert PW.powiaty_for_bbox(regions.get("dk65-02").bbox) == ("2002",)          # the only water region today
    assert PW.powiaty_for_bbox(PW.ring_bbox(regions.get(C).origin)) == ("2061", "2002")  # C ring: 72 % / 28 %


@pytest.mark.parametrize("rid", sorted(regions.REGIONS))
def test_tile_powiaty_match_the_registry_except_known_gaps(rid):
    r = regions.get(rid)
    prg = set(PW.powiaty_for_bbox(r.bbox))
    assert prg - set(r.powiaty) == KNOWN_REGISTRY_GAPS.get(rid, set())
    assert set(r.powiaty) <= prg


def test_knyszynska_tile_is_two_powiaty():
    assert set(PW.powiaty_for_bbox(regions.get("bialystok-knyszynska").bbox)) == {"2061", "2002"}


def test_merge_layers_keeps_first_and_adds_new_ids():
    a = {"L": [{"id": "x:0", "v": 1}, {"id": "y:0", "v": 1}]}
    b = {"L": [{"id": "x:0", "v": 2}, {"id": "a:0", "v": 2}], "M": [{"id": "m:0"}]}
    m = PW.merge_layers(a, b)
    assert m["L"] == [{"id": "a:0", "v": 2}, {"id": "x:0", "v": 1}, {"id": "y:0", "v": 1}]
    assert m["M"] == [{"id": "m:0"}]


def _fake_bdot(root, t, layers):
    for layer in layers:
        f = root / "Data/raw/gugik" / f"bdot10k-{t}" / "gpkg" / f"PL.PZGiK.{t}.BDOT10k.{t}__{layer}.gpkg"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(b"fixture")


def test_far_field_ring_reads_every_ring_powiat(tmp_path, monkeypatch):
    from streetscape import far_field as FF
    _fake_bdot(tmp_path, "2061", FF.BDOT_LAYERS)
    _fake_bdot(tmp_path, "2002", ("OT_PTLZ_A", "OT_BUBD_A"))
    monkeypatch.setattr(FF, "REPO", tmp_path)
    monkeypatch.setattr(PW, "package_files", lambda product, t: None)
    src = FF.ring_sources(*regions.get(C).origin)
    assert src["powiaty"] == ["2061", "2002"]
    assert [p.parent.parent.name for p in src["bdot"]["OT_BUBD_A"]] == ["bdot10k-2061", "bdot10k-2002"]
    assert [p.parent.parent.name for p in src["bdot"]["OT_SULN_L"]] == ["bdot10k-2061"]
    assert src["missing"] == ["lod1-2024-2061", "lod1-2024-2002"]
    src = FF.ring_sources(*regions.get("knyszyn").origin)      # was: only 2061 files -> 0 buildings, 0 forests
    assert src["powiaty"] == ["2008", "2002"] and src["bdot"]["OT_BUBD_A"][0].parent.parent.name == "bdot10k-2002"
    assert "bdot10k-2008" in src["missing"]


def test_far_field_read_bdot_single_powiat_is_unchanged_and_merge_dedupes():
    import pandas as pd
    from streetscape import far_field as FF
    frames = {"a": pd.DataFrame({"LOKALNYID": ["1", "2", "2"], "v": [1, 2, 3]}),
              "b": pd.DataFrame({"LOKALNYID": ["2", "9"], "v": [8, 9]})}
    fake = SimpleNamespace(read_dataframe=lambda f, bbox=None: frames[f])
    assert FF._read_bdot(fake, ["a"], None) is frames["a"]          # one powiat: the same frame, duplicates kept
    m = FF._read_bdot(fake, ["a", "b"], None)
    assert m["LOKALNYID"].tolist() == ["1", "2", "2", "9"] and m["v"].tolist() == [1, 2, 3, 9]
    assert FF._read_bdot(fake, [], None) is None


def test_far_field_osm_window_contains_the_old_window_for_c_and_reaches_knyszyn():
    from streetscape import far_field as FF
    lon0, lat0, lon1, lat1 = FF.osm_lonlat_window(*regions.get(C).origin)
    assert lon0 <= 23.08 and lat0 <= 53.10 and lon1 >= 23.30 and lat1 >= 53.24
    lon0, lat0, lon1, lat1 = FF.osm_lonlat_window(*regions.get("knyszyn").origin)
    assert lon0 < 22.90 < lon1 and lat0 < 53.31 < lat1                  # Knyszyn (outside 23.08-23.30 E)


def test_far_field_lod1_merge_single_is_unchanged(monkeypatch):
    from streetscape import far_field as FF
    data = {"a": ({"x": 1.0, "y": 2.0}, {"members": 1, "usable_ids": 2}),
            "b": ({"y": 9.0, "z": 3.0}, {"members": 2, "usable_ids": 2})}

    def fake(z, audit):
        audit.update(data[z][1])
        return dict(data[z][0])
    monkeypatch.setattr(FF, "_extract_lod1_heights", fake)
    a1 = {}
    assert FF._merge_lod1(["a"], a1) == {"x": 1.0, "y": 2.0} and a1 == {"members": 1, "usable_ids": 2}
    a2 = {}
    assert FF._merge_lod1(["a", "b"], a2) == {"x": 1.0, "y": 2.0, "z": 3.0}
    assert a2 == {"members": 3, "usable_ids": 3}


def test_lod2_extract_reads_every_powiat_of_the_window(tmp_path, monkeypatch):
    from streetscape import lod2_extract as L2
    z = {t: tmp_path / f"{t}_lod2_gml.zip" for t in ("2061", "2002")}
    z["2061"].write_bytes(b"x")
    monkeypatch.setattr(PW, "package_files", lambda product, t: [z[t]] if product == "lod2-2017" and t in z else None)
    kb = regions.get("bialystok-knyszynska").bbox
    zips, missing = L2.lod2_zips(kb)
    assert [t for t, _ in zips] == ["2061"] and missing == ["2002"]   # 2002 not on disk -> reported, not silent
    z["2002"].write_bytes(b"x")
    zips, missing = L2.lod2_zips(kb)
    assert sorted(t for t, _ in zips) == ["2002", "2061"] and not missing
    assert [t for t, _ in L2.lod2_zips(regions.get(C).bbox)[0]] == ["2061"]


def test_water_extract_reads_every_tile_powiat_and_single_is_unchanged(monkeypatch):
    import build_region
    import fetch_osm
    from streetscape import water as W
    calls = []
    monkeypatch.setattr(build_region, "manifest_files", lambda ds: [Path(f"/zip/{ds}")])
    monkeypatch.setattr(fetch_osm, "download", lambda: Path("/pbf"))
    monkeypatch.setattr(W, "extract_osm", lambda bbox, pbf: {"ways": []})

    def fake_bdot(bbox, z, gdir):
        calls.append((z.name, gdir.parent.name))
        t = z.name.rsplit("-", 1)[1]
        return {"OT_SWRS_L": [{"id": "shared:0", "t": t}, {"id": f"only{t}:0", "t": t}]}
    monkeypatch.setattr(W, "extract_bdot", fake_bdot)

    def reg(rid):
        x0, y0, x1, y1 = regions.get(rid).bbox
        return {"bbox": {"xmin": x0, "ymin": y0, "xmax": x1, "ymax": y1},
                "teryt_powiat": regions.get(rid).teryt_powiat}
    d = W.extract(reg("dk65-02"))
    assert calls == [("gugik-bdot10k-2002", "bdot10k-2002")]
    assert d["license"]["bdot10k"].startswith("GUGiK BDOT10k (powiat 2002),")
    assert d["bdot10k"] == {"OT_SWRS_L": [{"id": "shared:0", "t": "2002"}, {"id": "only2002:0", "t": "2002"}]}
    calls.clear()
    d = W.extract(reg("bialystok-knyszynska"))
    assert [c[1] for c in calls] == ["bdot10k-2002", "bdot10k-2061"]
    assert [f["id"] for f in d["bdot10k"]["OT_SWRS_L"]] == ["only2002:0", "only2061:0", "shared:0"]
    assert "powiat 2002, 2061" in d["license"]["bdot10k"]
