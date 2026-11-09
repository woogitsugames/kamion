"""Road + terrain mesh generator (tools/worldgen/roads, tools/worldgen/terrain_mesh).

The world is generated once per session into a temp dir (~1 min). Needs the 1 m heightmap
(Data/raw/derived/<region>/heightmap_2049.r16, gitignored) -> skipped when it is missing.
"""

from __future__ import annotations

import hashlib
import json
import struct

import numpy as np
import pytest

from conftest import REGION_DIR, REGION_ID, REPO

HEIGHTMAP = REPO / "Data" / "raw" / "derived" / REGION_ID / "heightmap_2049.r16"
needs_heightmap = pytest.mark.skipif(not HEIGHTMAP.exists(), reason="heightmap not built (Data/raw is gitignored)")


@pytest.fixture(scope="session")
def world(tmp_path_factory):
    if not HEIGHTMAP.exists():
        pytest.skip("heightmap not built")
    from roads import build_world
    out = tmp_path_factory.mktemp("world")
    w, manifest, qa = build_world.build(REGION_ID, out_root=out, verbose=False)
    return {"w": w, "manifest": manifest, "qa": qa, "out": out}


def q(p):
    return tuple(np.round(np.asarray(p, float) * 1000).astype(np.int64).tolist())


# ------------------------------------------------------------------------------------------ seams
@needs_heightmap
def test_junction_seams_are_watertight(world):
    """Every arm end section of a junction patch is shared vertex-for-vertex and edge-for-edge with the
    chain ribbon (no T-junctions, no cracks between ribbons and junction patches)."""
    w = world["w"]
    parts = [p for p in w.buf.parts if p.layer in ("road", "bridge") and p.mat.startswith("road_")]
    by_src = {}
    for p in parts:
        by_src.setdefault(p.src, []).append(p)

    def edge_set(ps):
        es = set()
        for p in ps:
            V = p.V
            for t in p.T:
                for a, b in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                    ka, kb = q(V[a]), q(V[b])
                    es.add((min(ka, kb), max(ka, kb)))
        return es

    repaired = set(w.stats["patch"].get("repaired_ids", [])) | set(w.stats["patch"].get("earclip_ids", []))
    checked = 0
    failures = []
    from roads.meshing import PatchHeight
    for j in w.junctions:
        if j.id in repaired or j.id not in by_src:
            continue
        pe = edge_set(by_src[j.id])
        ph = PatchHeight(j)
        for i, a in enumerate(j.arms):
            c = a.chain
            if c.meta.get("absorbed") or c.length - c.t_a - c.t_b <= 0.05 or c.id not in by_src:
                continue
            pts = [(p, tag) for p, tag in j.boundary if tag[0] == "end" and tag[1] == i]
            pts.sort(key=lambda x: x[1][2])
            keys = [q([p[0], p[1], ph.boundary_z(j, p, tag)]) for p, tag in pts]
            re = edge_set(by_src[c.id])
            for ka, kb in zip(keys, keys[1:]):
                e = (min(ka, kb), max(ka, kb))
                if e not in pe or e not in re:
                    failures.append((j.id, c.id, i))
                    break
            checked += 1
    assert checked > 300, checked
    assert not failures, f"{len(failures)} open seams, first: {failures[:5]}"


@needs_heightmap
def test_terrain_chunk_borders_match(world):
    """Neighbouring terrain chunks (LOD0) share identical border vertices (no cracks between chunks)."""
    from terrain_mesh import chunks as CH
    w = world["w"]
    zc = np.load(world["out"] / "terrain_conformed.npy")
    # the chunk builder samples the same global grid: border column of chunk i == first column of i+1
    per = CH.CHUNK_M
    for k in range(1, zc.shape[1] // per):
        col = k * per
        assert np.isfinite(zc[:, col]).all()
    # and the exported GLBs carry the same heights on a shared edge
    a = _glb_positions(world["out"] / "chunk_3_3.glb", "terrain_lod0")
    b = _glb_positions(world["out"] / "chunk_4_3.glb", "terrain_lod0")
    ea = {tuple(np.round(v, 3)) for v in a if abs(-v[0] - 0.0) < 1e-3}      # glTF x = -E; E = 0 border
    eb = {tuple(np.round(v, 3)) for v in b if abs(-v[0] - 0.0) < 1e-3}
    assert len(ea) > 200 and ea == eb


def _glb_positions(path, node_name):
    data = path.read_bytes()
    jlen, = struct.unpack("<I", data[12:16])
    doc = json.loads(data[20:20 + jlen])
    binoff = 20 + jlen + 8
    node = next(n for n in doc["nodes"] if n["name"] == node_name)
    out = []
    for prim in doc["meshes"][node["mesh"]]["primitives"]:
        acc = doc["accessors"][prim["attributes"]["POSITION"]]
        bv = doc["bufferViews"][acc["bufferView"]]
        arr = np.frombuffer(data, "<f4", acc["count"] * 3, binoff + bv["byteOffset"]).reshape(-1, 3)
        out.append(arr)
    return np.vstack(out)


# ------------------------------------------------------------------------------------------ profile
@needs_heightmap
def test_max_grade_within_regulation(world):
    """Smoothed vertical profiles respect PTB2022 §20 ust.2 / §62 ust.2 (difficult-conditions limit)."""
    qa = world["qa"]
    over = [(c["id"], c["max_grade"], c["grade_limit"]) for c in qa["chains"] if c["max_grade"] > c["grade_limit"] + 1e-6]
    assert not over, over
    trunk = [c["max_grade"] for c in qa["chains"] if "trunk" in c["highway"]]
    assert max(trunk) <= 0.08


@needs_heightmap
def test_profile_follows_nmt_without_noise(world):
    w = world["w"]
    for c in w.net.chains:
        if c.bridge.any() or c.length < 50:
            continue
        st = w.profiles["chains"][c.id]
        assert st["rms_vs_nmt_m"] < 0.35, (c.id, st)
        # no NMT noise: second differences bounded by the class vertical curvature limit
        k = np.abs(np.diff(c.z, 2)) / 0.5 ** 2
        assert k.max() <= 1 / 150 + 1e-6, (c.id, k.max())


# ------------------------------------------------------------------------------------------ alignment
@needs_heightmap
def test_mesh_matches_generated_centreline(world):
    """Carriageway vertices lie on the generated cross-section: |lateral| <= half width + 0.2 m from the
    generated centre line, and crown vertices are within 0.2 m of it."""
    w = world["w"]
    chains = {c.id: c for c in w.net.chains}
    worst = 0.0
    n = 0
    for p in w.buf.parts:
        if p.layer not in ("road", "bridge") or not p.mat.startswith("road_") or p.src not in chains:
            continue
        c = chains[p.src]
        for v in p.V[:: max(1, len(p.V) // 60)]:
            s, lat = c.line.project(v[:2])
            excess = abs(lat) - float(c.hw_at(s))
            worst = max(worst, excess)
            n += 1
    assert n > 5000
    assert worst <= 0.2, worst


@needs_heightmap
def test_centreline_vs_osm_axis(world):
    """Horizontal smoothing of OSM polylines moves the axis by <= 0.5 m (p95) — the rest of the
    alignment budget (docs/05 §5: <= 1-2 m) belongs to the source data."""
    d = world["qa"]["summary"]["axis_smoothing_deviation_m"]
    assert d["p95"] <= 0.5, d


# ------------------------------------------------------------------------------------------ terrain
@needs_heightmap
def test_terrain_stays_below_road(world):
    from terrain_mesh import conform as CF
    w = world["w"]
    road_z, mask = CF.rasterise([p for p in w.buf.parts if p.layer == "road"], w.hf)
    zc = np.load(world["out"] / "terrain_conformed.npy").astype(np.float64)
    gap = road_z[mask] - zc[mask]
    assert gap.min() >= 0.30 - 1e-3


# ------------------------------------------------------------------------------------------ export
@needs_heightmap
def test_export_is_deterministic(world):
    """Same inputs -> byte-identical GLBs: the in-process build equals the committed manifest (written
    by an earlier CLI run, different process / hash seed)."""
    committed = json.loads((REGION_DIR / "generated" / "world_manifest.json").read_text(encoding="utf-8"))
    built = world["manifest"]
    assert [c["id"] for c in committed["chunks"]] == [c["id"] for c in built["chunks"]]
    for a, b in zip(committed["chunks"], built["chunks"]):
        assert a["sha256"] == b["sha256"], a["id"]
        p = world["out"] / f"chunk_{a['id']}.glb"
        assert hashlib.sha256(p.read_bytes()).hexdigest() == b["sha256"]


@needs_heightmap
def test_glb_structure(world):
    p = world["out"] / "chunk_2_3.glb"
    data = p.read_bytes()
    magic, ver, total = struct.unpack("<III", data[:12])
    assert magic == 0x46546C67 and ver == 2 and total == len(data)
    jlen, = struct.unpack("<I", data[12:16])
    doc = json.loads(data[20:20 + jlen])
    names = {n["name"] for n in doc["nodes"]}
    assert {"terrain_lod0", "terrain_lod1", "terrain_lod2", "terrain_lod3", "road", "road_collision"} <= names
    for acc in doc["accessors"]:
        if acc["componentType"] == 5123:
            assert acc["count"] % 3 == 0 or acc["type"] == "SCALAR"
    mats = {m["name"] for m in doc["materials"]}
    assert "road_asphalt" in mats and "terrain_grass" in mats


@needs_heightmap
def test_overrides_applied_and_not_stale(world):
    m = world["manifest"]
    ids = {o["id"] for o in m["overrides_applied"]}
    assert {"kwadrat-park-yard-access-width", "kwadrat-park-yard-flush-edges",
            "kwadrat-park-access-junction-radius"} <= ids
    assert m["overrides_stale"] == []
    w = world["w"]
    sec = w.net.sections["w1090234575:8722811971-9986085571"]
    assert sec.width == pytest.approx(7.0) and sec.width_src.startswith("authored_override")


# ------------------------------------------------------------------------------------------ standards
def test_marking_dimensions_from_regulation():
    from roads import standards as S
    from roads.markings import arrow_glyph
    assert S.DASH["P-1a"] == (4.0, 8.0) and S.DASH["P-1b"] == (2.0, 4.0)
    assert S.LINE_W_NARROW == 0.12 and S.LINE_W_WIDE == 0.24
    assert (S.P10_STRIPE, S.P10_GAP, S.P10_WIDTH) == (0.5, 0.5, 4.0)
    g = arrow_glyph(["through"], long=False)
    x0, y0, x1, y1 = g.bounds
    assert x1 - x0 == pytest.approx(5.0, abs=0.02) and y1 - y0 == pytest.approx(0.75, abs=0.02)


def test_lane_widths_from_regulation():
    from roads import standards as S
    assert S.LANE_WIDTH["GP"] == (3.50, 3.25) and S.LANE_WIDTH["Z"] == (3.00, 2.75)
    assert S.SINGLE_LANE_MIN == 3.50


def test_cross_section_from_tags():
    from roads.network import edge_section

    def e(**tags):
        attrs = {k: {"v": v, "src": "osm", "conf": "high"} for k, v in tags.items()}
        return {"id": "x", "attrs": attrs}
    trunk = edge_section(e(highway="trunk", oneway="yes", lanes=2, width=8.0))
    assert trunk.lane_w == pytest.approx(3.5) and trunk.width == pytest.approx(8.0)
    # BDOT width implausible for 3 lanes (2.33 m/lane): rejected, class standard used, rejection recorded
    wide = edge_section(e(highway="trunk", oneway="yes", lanes=3, width=8.0))
    assert wide.lane_w == pytest.approx(3.5) and wide.width == pytest.approx(3 * 3.5 + 1.0)
    assert wide.provenance["width_rejected"]["bdot_width"] == 8.0
    narrow = edge_section(e(highway="trunk", oneway="yes", lanes=2, width=7.0))  # 3.0 m/lane -> clamp 3.25
    assert narrow.lane_w == pytest.approx(3.25)
    res = edge_section(e(highway="residential", oneway="no", lanes=2))
    assert res.width == pytest.approx(2 * 2.75) and res.lanes_fwd == 1 and res.lanes_bwd == 1
    ramp = edge_section(e(highway="trunk_link", oneway="yes", lanes=1))
    assert ramp.width >= 3.5


def test_side_profile_kerb_height():
    from roads import standards as S
    from roads.network import URBAN, side_profile
    prof = side_profile(URBAN, S.KERB_HEIGHT, S.SIDEWALK_W, S.FLANGE_DEPTH, 1)
    face = prof[0]
    assert face[0] == face[2] == 0.0 and 0.12 <= face[3] - face[1] <= 0.15
