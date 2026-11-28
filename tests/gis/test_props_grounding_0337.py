"""ADR 0337 (critic build #5 pkt 10): benches with grounded open legs and visible, grounded sign posts."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from roads import standards as S
from streetscape import furniture as F
from streetscape import knyszyn_park_props_0227 as KP
from streetscape import materials as MAT
from streetscape import props as P
from streetscape import signs as SG
from streetscape import tykocin_rynek_0320 as TY
from streetscape.buildings_mesh import Acc

REPO = Path(__file__).resolve().parents[2]


class _Buf:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, V, UV, T, src="", **kw):
        self.parts.append((layer, mat, np.asarray(V, float), np.asarray(T, int), src))


class _Top:
    def __init__(self, fn):
        self.fn = fn

    def top(self, e, n, below=None):
        return float(self.fn(e, n))


# --------------------------------------------------------------------------------------------- benches
def test_authored_bench_has_four_open_legs_and_per_leg_slope_contact():
    """Tykocin / Knyszyn park bench: 4 open legs (no solid end slabs) seated individually on sloped terrain."""
    def slope(xy):
        return 100.0 + 0.14 * float(xy[0]) - 0.10 * float(xy[1])

    row = np.array([1.0, 0.0])
    toward = np.array([0.0, 1.0])
    acc = Acc()
    for layer in ("buildings", "buildings_low"):
        KP._bench(acc, layer, np.array([0.0, 0.0]), slope([0.0, 0.0]), row, toward, z_at=slope)
    buf = _Buf()
    acc.flush(buf, "test")

    lod0_steel = next(v for layer, m, v, t, _ in buf.parts if layer == "buildings" and m == "steel_painted")
    lod0_wood = next(v for layer, m, v, t, _ in buf.parts if layer == "buildings" and m == "bench_wood")
    lod1_tris = sum(len(t) for layer, _, _, t, _ in buf.parts if layer == "buildings_low")
    lod0_tris = sum(len(t) for layer, _, _, t, _ in buf.parts if layer == "buildings")
    assert lod1_tris < 0.5 * lod0_tris

    # Open frame: at mid-shin height (z_local ~ 0.15..0.30) there must be NO steel in the middle y band (-0.12..+0.08)
    shin = lod0_steel[(lod0_steel[:, 2] > 100.12) & (lod0_steel[:, 2] < 100.30)]
    assert len(shin) == 0 or not np.any((shin[:, 1] > -0.12) & (shin[:, 1] < 0.08))

    # Each of the 4 leg feet extends >= 5 cm below the local terrain height at that leg's (e, n)
    for sx in (-1, 1):
        for off_n in (0.17, -0.22):
            xy = np.array([sx * 0.72, off_n])
            near = lod0_steel[(np.abs(lod0_steel[:, 0] - xy[0]) < 0.05) & (np.abs(lod0_steel[:, 1] - xy[1]) < 0.05)]
            assert len(near) > 0, (sx, off_n)
            assert near[:, 2].min() <= slope(xy) - 0.05 + 1e-6

    # Backrest uprights reach at least the top of the backrest wood (backrest is supported)
    assert lod0_steel[:, 2].max() >= lod0_wood[:, 2].max() - 1e-6


def test_prototype_bench_and_bin_are_grounded_with_supported_backrest():
    m0, m1, _ = P.bench()
    p0 = {p["mat"]: p for p in m0.out()}
    p1 = {p["mat"]: p for p in m1.out()}
    assert set(p0) == {"bench_wood", "steel_painted"} == set(p1)
    t0 = sum(len(p["T"]) for p in p0.values())
    t1 = sum(len(p["T"]) for p in p1.values())
    assert t1 < 0.5 * t0

    steel = p0["steel_painted"]["V"]
    wood = p0["bench_wood"]["V"]
    # Buried 8-14 cm (inside ADR 0102's 15 cm contact-audit window) and uprights reach the backrest top
    assert -0.15 < steel[:, 2].min() <= -0.08
    assert steel[:, 2].max() >= wood[:, 2].max() - 1e-6
    # All 4 leg corners present below z = 0
    for x in (-0.72, 0.72):
        for y in (0.17, -0.22):
            sub = steel[(np.abs(steel[:, 0] - x) < 0.05) & (np.abs(steel[:, 1] - y) < 0.05)]
            assert len(sub) > 0 and sub[:, 2].min() <= -0.08

    bm0, bm1, _ = P.waste_bin()
    bp0 = {p["mat"]: p for p in bm0.out()}
    bp1 = {p["mat"]: p for p in bm1.out()}
    assert set(bp0) == {"steel_painted", "steel_galv"} == set(bp1)
    assert sum(len(p["T"]) for p in bp1.values()) < sum(len(p["T"]) for p in bp0.values())
    assert -0.15 < bp0["steel_painted"]["V"][:, 2].min() <= -0.08


def test_placer_seats_benches_and_bins_on_surface_top():
    assert "bench" in F.SEATED_POLES and "waste_bin" in F.SEATED_POLES
    assert "bench" in F.FOOT_R and "waste_bin" in F.FOOT_R
    assert "bench" in F.LOW_SURFACE_PROPS and "waste_bin" in F.LOW_SURFACE_PROPS
    flat = lambda e, n: np.zeros_like(e, dtype=float)
    pl = F.Placer(flat, flat, surf=_Top(lambda e, n: 0.25), col=_Top(lambda e, n: 0.25), zvis=flat)
    zb = pl.add("bench", (1.0, 2.0), 0.0, src="unit")
    zw = pl.add("waste_bin", (3.0, 4.0), 0.0, src="unit")
    assert zb == pytest.approx(0.25)
    assert zw == pytest.approx(0.25)


def test_low_props_use_visible_terrain_not_coarse_collider_on_embankment():
    """ADR 0337 post-wave-8 fix (dk65-01): outside road meshes (`surf.top` is NaN), benches and waste bins (< 1 m
    tall) must seat on the visible 1 m terrain (`zvis`), not the min-filtered 4 m `terrain_lod2` collider
    (`zground_col`) which can dip > 1 m on roadside slopes and bury a 0.94 m bin completely. Tall poles keep
    `zground_col` for collider grounding."""
    zvis = lambda e, n: np.full_like(e, 127.749, dtype=float)
    zcol = lambda e, n: np.full_like(e, 126.720, dtype=float)  # -1.029 m dip as on dk65-01 Warszawska embankment
    nan_top = _Top(lambda e, n: float("nan"))
    pl = F.Placer(zvis, zcol, surf=nan_top, col=nan_top, zvis=zvis)
    zw = pl.add("waste_bin", (-543.171, -984.767), 0.0, src="bus_stop:bin")
    zb = pl.add("bench", (-544.0, -984.0), 0.0, src="osm:bench")
    zp = pl.add("sign_post", (-545.0, -984.0), 0.0, src="rule:sign")
    zl = pl.add("lamp_9m", (-545.62, -984.32), 0.0, src="rule:lamp")
    assert zw == pytest.approx(127.749)
    assert zb == pytest.approx(127.749)
    assert zp == pytest.approx(126.720)
    assert zl == pytest.approx(126.720)
    # On a sidewalk / paved mesh, SurfaceTop still takes precedence over zvis
    walk_top = _Top(lambda e, n: 128.05)
    pl_walk = F.Placer(zvis, zcol, surf=walk_top, col=walk_top, zvis=zvis)
    assert pl_walk.add("waste_bin", (0.0, 0.0), 0.0, src="bus_stop:bin") == pytest.approx(128.05)
    assert pl_walk.add("bench", (1.0, 0.0), 0.0, src="osm:bench") == pytest.approx(128.05)

    # Verify directly on the actual dk65-01 conformed terrain grid at the wave-8 buried bin (-543.171, -984.767)
    tpath = REPO / "Data" / "raw" / "derived" / "dk65-01" / "world" / "terrain_conformed.npy"
    if tpath.exists():
        from roads.profile import Heightfield
        from terrain_mesh import chunks as CH
        rdir = REPO / "Data" / "Regions" / "dk65-01"
        tmeta = json.loads((rdir / "terrain.json").read_text(encoding="utf-8"))
        man = json.loads((rdir / "generated" / "world_manifest.json").read_text(encoding="utf-8"))
        orig = man["origin_epsg2180"]
        ox = float(orig.get("e", orig.get("E", orig.get("x"))) if isinstance(orig, dict) else orig[0])
        oy = float(orig.get("n", orig.get("N", orig.get("y"))) if isinstance(orig, dict) else orig[1])
        zc = np.load(tpath)
        hf = Heightfield(zc, tmeta["bbox"], (ox, oy))
        z4 = CH.lod_grid(zc, np.ones(zc.shape, dtype=bool), 4)

        def zground(e, n):
            return hf.sample(np.asarray(e, float), np.asarray(n, float))

        def zcollider(e, n):
            e, n = np.asarray(e, float), np.asarray(n, float)
            fi = np.clip((e - hf.x0) / 4.0, 0, z4.shape[1] - 1.001)
            fj = np.clip((hf.y1 - n) / 4.0, 0, z4.shape[0] - 1.001)
            i0, j0 = np.floor(fi).astype(int), np.floor(fj).astype(int)
            fx, fy = fi - i0, fj - j0
            za, zb_ = z4[j0, i0], z4[j0, i0 + 1]
            zd, ze = z4[j0 + 1, i0], z4[j0 + 1, i0 + 1]
            return np.where(fx >= fy, za + fx * (zb_ - za) + fy * (ze - zb_), za + fy * (zd - za) + fx * (ze - zd))

        zground_col = lambda e, n: np.minimum(zground(e, n), zcollider(e, n))
        pl_dk = F.Placer(zground, zground_col, surf=nan_top, col=nan_top, zvis=zground)
        pt = (-543.171, -984.767)
        z_bin = pl_dk.add("waste_bin", pt, 0.0, src="bus_stop:bin")
        z_hf = float(hf.sample(np.array([pt[0]]), np.array([pt[1]]))[0])
        z_col_pt = float(zground_col(np.array([pt[0]]), np.array([pt[1]]))[0])
        assert z_col_pt - z_hf < -1.0  # confirms coarse collider dips > 1 m here
        assert z_bin - z_hf == pytest.approx(0.0, abs=1e-3)


# --------------------------------------------------------------------------------------------- sign posts
def test_sign_post_diameter_contrast_grounding_and_lod1():
    m0, m1, col = P.sign_post()
    prims0 = m0.out()
    prims1 = m1.out()
    # Strictly 1 material slot (+0 draws)
    assert len(prims0) == 1 and len(prims1) == 1
    mat = prims0[0]["mat"]
    assert mat == "sign_post_galv" and prims1[0]["mat"] == mat
    spec = MAT.M[mat]
    assert 0.25 <= spec.get("metal", 0.0) <= 0.55
    assert 0.50 <= spec.get("rough", 0.0) <= 0.75

    v0 = prims0[0]["V"]
    # Buried end below 0, within ADR 0102 15 cm probe window even at sz = 3.5
    assert -0.05 <= v0[:, 2].min() <= -0.03
    assert v0[:, 2].max() == pytest.approx(1.0)
    # Shaft diameter = S.SIGN_POST_D (~60.3 mm); ground collar wider near z = 0
    shaft = v0[v0[:, 2] > 0.5]
    r_shaft = np.hypot(shaft[:, 0], shaft[:, 1])
    assert np.median(r_shaft) == pytest.approx(S.SIGN_POST_D / 2, abs=1e-4)
    collar = v0[(v0[:, 2] >= -0.03) & (v0[:, 2] <= 0.03)]
    assert np.hypot(collar[:, 0], collar[:, 1]).max() >= S.SIGN_POST_D / 2 * 1.5

    # LOD1: slightly boosted 6-sided tube so it stays legible at medium distance
    v1 = prims1[0]["V"]
    r_l1 = np.hypot(v1[v1[:, 2] > 0.5, 0], v1[v1[:, 2] > 0.5, 1])
    assert np.median(r_l1) >= S.SIGN_POST_D / 2 * 1.15
    assert len(prims1[0]["T"]) >= 12


@pytest.mark.parametrize("code,sidewalk", [("D-1", False), ("D-1", True), ("A-7", False), ("A-8", False),
                                           ("B-33_70", False), ("D-6", True)])
def test_sign_assembly_post_height_supports_clamps_without_poking_above_tip(code, sidewalk):
    flat = lambda e, n: np.full_like(e, 120.0, dtype=float)
    pl = F.Placer(flat, flat, surf=_Top(lambda e, n: 120.0))
    F.sign_assembly(pl, (10.0, 20.0), (0.0, 1.0), [code], "unit", sidewalk=sidewalk)
    post, plate = pl.items
    assert post["p"] == "sign_post" and plate["p"] == f"plate_{code}"
    assert post["e"] == plate["e"] and post["n"] == plate["n"]
    shape, _ = SG.face(code)
    hh = S.SIGN_SIZE["triangle" if shape == "triangle_up" else shape] * (
        math.sqrt(3) / 2 if shape in ("triangle", "triangle_up") else 1.0
    )
    h_min = S.SIGN_H_SIDEWALK if sidewalk else S.SIGN_H_MIN
    plate_bot = plate["z"] - (2 * hh / 3 if shape == "triangle" else hh / 3 if shape == "triangle_up" else hh / 2)
    plate_top = plate_bot + hh
    assert plate_bot - post["z"] == pytest.approx(h_min, abs=1e-3)
    post_top = post["z"] + post["sz"]
    # Upper clamp (+0.22 * hh) must sit firmly on the post
    assert post_top >= plate["z"] + 0.22 * hh + 0.03
    # Post must never poke above the plate top; pointed shapes inset >= 10 cm
    if shape in ("diamond", "triangle_up"):
        assert post_top <= plate_top - 0.10
    else:
        assert post_top <= plate_top


# --------------------------------------------------------------------------------------------- generated world checks
@pytest.mark.parametrize("region", ["tykocin", "bialystok-knyszynska", "dk65-01"])
def test_generated_region_every_sign_has_post_and_props_finite(region):
    wdir = REPO / "Data" / "raw" / "derived" / region / "world"
    files = sorted(wdir.glob("instances_*.json"))
    if not files:
        pytest.skip(f"{region} instances not generated")
    items = [it for f in files for it in json.loads(f.read_text(encoding="utf-8")).get("instances", [])]
    posts = [it for it in items if it["p"] == "sign_post"]
    rail_masts = [it for it in items if it["p"].startswith(("signal_rail_saltire", "signal_rail_lamps"))]
    assert len(posts) > 0

    for it in items:
        p = it["p"]
        assert math.isfinite(it["e"]) and math.isfinite(it["n"]) and math.isfinite(it["z"])
        if p.startswith("plate_"):
            if p == "plate_G-2":
                supports = posts + rail_masts
            else:
                supports = posts
            near = [s for s in supports if (s["e"] - it["e"]) ** 2 + (s["n"] - it["n"]) ** 2 < 0.15 ** 2]
            assert near, f"{region}: {p} at ({it['e']}, {it['n']}) has no supporting sign_post"
            s = near[0]
            assert s["z"] < it["z"], f"{region}: post above plate at ({it['e']}, {it['n']})"
            if s["p"] == "sign_post":
                assert s["z"] + s.get("sz", 1.0) >= it["z"], f"{region}: short post at ({it['e']}, {it['n']})"
        elif p.startswith("board_") and not p.startswith("board_OB_"):
            near = [s for s in posts if (s["e"] - it["e"]) ** 2 + (s["n"] - it["n"]) ** 2 < 2.5 ** 2]
            assert near, f"{region}: ground board {p} at ({it['e']}, {it['n']}) has no supporting sign_post"


@pytest.mark.parametrize("region", ["tykocin", "bialystok-knyszynska", "dk65-01"])
def test_generated_region_props_ground_contact(region):
    """Every bench, waste_bin and sign_post sits on local terrain/surface (no floating props)."""
    from roads.profile import Heightfield

    wdir = REPO / "Data" / "raw" / "derived" / region / "world"
    tpath = wdir / "terrain_conformed.npy"
    files = sorted(wdir.glob("instances_*.json"))
    if not tpath.exists() or not files:
        pytest.skip(f"{region} terrain/instances not generated")
    rdir = REPO / "Data" / "Regions" / region
    tmeta = json.loads((rdir / "terrain.json").read_text(encoding="utf-8"))
    man = json.loads((rdir / "generated" / "world_manifest.json").read_text(encoding="utf-8"))
    orig = man["origin_epsg2180"]
    ox = float(orig.get("e", orig.get("E", orig.get("x"))) if isinstance(orig, dict) else orig[0])
    oy = float(orig.get("n", orig.get("N", orig.get("y"))) if isinstance(orig, dict) else orig[1])
    hf = Heightfield(np.load(tpath), tmeta["bbox"], (ox, oy))

    items = [it for f in files for it in json.loads(f.read_text(encoding="utf-8")).get("instances", [])]
    qa_path = rdir / "generated" / "streetscape_qa.json"
    qa = json.loads(qa_path.read_text(encoding="utf-8")) if qa_path.exists() else {}
    has_zvis = bool(qa.get("furniture", {}).get("low_props_vis_ground"))
    # Road/sidewalk meshes sit up to ~0.35 m above pushed-down terrain_conformed; roadside ditches can dip ~1.5 m below.
    for kind, lo, hi in (("bench", -1.0, 0.45), ("waste_bin", -1.0, 0.45), ("sign_post", -2.0, 0.65)):
        sub = [it for it in items if it["p"] == kind]
        if not sub:
            continue
        es = np.array([it["e"] for it in sub], dtype=float)
        ns = np.array([it["n"] for it in sub], dtype=float)
        zs = np.array([it["z"] for it in sub], dtype=float)
        dz = zs - hf.sample(es, ns)
        assert float(dz.max()) <= hi, f"{region}: floating {kind}, max dz={dz.max():.3f} m"
        if kind in F.LOW_SURFACE_PROPS and not has_zvis and float(dz.min()) < lo:
            pytest.xfail(
                f"{region}: sunk {kind}, min dz={dz.min():.3f} m — wave-8 data built before ADR 0337 zvis fix "
                "(generator fixed in furniture.py/stage.py; tile to be rebuilt in wave 9)"
            )
        assert float(dz.min()) >= lo, f"{region}: sunk {kind}, min dz={dz.min():.3f} m"


def test_tykocin_rynek_authored_benches_qa():
    qa_path = REPO / "Data" / "Regions" / "tykocin" / "generated" / "streetscape_qa.json"
    if not qa_path.exists():
        pytest.skip("tykocin streetscape_qa.json not generated")
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    rynek = qa["tykocin_rynek_0320"]
    assert rynek["status"] == "applied"
    assert rynek["refused"] == []
    # ADR 0320 (tykocin-plaza-s24): six benches and four edge planters share the ten orthophoto marks.
    assert len(rynek["benches"]) == 6
    edge_planters = [p for p in rynek["planters"] if p["kind"] == "edge planter"]
    assert {tuple(p["at_en"]) for p in edge_planters} == {
        (431.6, -99.25), (452.9, -96.75), (466.6, -95.25), (485.4, -93.0),
    }
    assert len(edge_planters) == 4
    assert len({tuple(b["at_en"]) for b in rynek["benches"]} |
               {tuple(p["at_en"]) for p in edge_planters}) == 10
    assert rynek["tris"]["buildings_low"] < rynek["tris"]["buildings"]
