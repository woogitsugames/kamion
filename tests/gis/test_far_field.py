"""Far-field backdrop generator tests (ADR 0085: tools/worldgen/streetscape/far_field.py)."""

from __future__ import annotations

import hashlib
import json

import numpy as np
import pytest

from conftest import REGION_DIR, REGION_ID, REPO


def test_radial_foreshortening_stays_within_low_far_clip():
    from streetscape import far_field as FF

    assert FF.foreshorten_dist(0.0) == 0.0
    assert FF.foreshorten_dist(100.0) == pytest.approx(100.0)
    d1 = FF.foreshorten_dist(500.0)
    d2 = FF.foreshorten_dist(2000.0)
    d3 = FF.foreshorten_dist(4200.0)
    assert 140.0 < d1 < d2 < d3 <= 660.0  # strictly inside Low cameraFarClip (900 m)

    e_eff, n_eff, d_raw, d_eff = FF.foreshorten_point(712.0, 2500.0, half=1024.0)
    assert d_raw == pytest.approx(1476.0)
    assert d_eff == pytest.approx(FF.foreshorten_dist(1476.0))
    assert e_eff == pytest.approx(712.0)
    assert 1024.0 < n_eff < 1685.0

    s_xy, s_h = FF.foreshorten_scales(1500.0)
    assert 0.30 <= s_xy < 1.0
    assert 0.35 <= s_h < 1.0


def test_sector_partition_matches_four_border_exits():
    from streetscape import far_field as FF

    # North exit: al. Tysiąclecia Państwa Polskiego (E ~ +712, N > +1024)
    assert FF.sector_of(712.0, 1300.0, 1024.0) == "far_north"
    # East exit: ul. Gen. Stanisława Maczka E (E > +1024, N ~ -786)
    assert FF.sector_of(1300.0, -786.0, 1024.0) == "far_east"
    # South exit: al. Tysiąclecia Państwa Polskiego S (E ~ -475, N < -1024)
    assert FF.sector_of(-475.0, -1300.0, 1024.0) == "far_south"
    # West exit: ul. Gen. Stanisława Maczka W (E < -1024, N ~ +298)
    assert FF.sector_of(-1300.0, 298.0, 1024.0) == "far_west"


def test_border_elevation_preserves_local_corridor():
    from streetscape import far_field as FF

    elev = FF.BorderElevation(
        half=1024.0,
        south=[130.0, 134.0, 138.0],
        east=[138.0, 142.0, 146.0],
        north=[146.0, 140.0, 134.0],
        west=[134.0, 132.0, 130.0],
    )
    z_edge = elev.z_at_eff(0.0, 1024.0)
    z_far = elev.z_at_eff(0.0, 1024.0 + FF.APRON_EASE_M + 100.0)
    assert z_edge == pytest.approx(140.0)
    assert abs(z_far - elev.mean) < 3.0


def test_sector_builder_and_building_modes():
    from streetscape import far_field as FF

    elev = FF.BorderElevation(1024.0, [135.0, 135.0], [135.0, 135.0], [135.0, 135.0], [135.0, 135.0])
    sectors = {s: FF.SectorBuilder(s) for s in FF.SECTORS}

    block = {
        "id": "test_block_1",
        "typ": "block",
        "rect": [[-500.0, -1150.0], [-440.0, -1150.0], [-440.0, -1138.0], [-500.0, -1138.0]],
        "area": 720.0,
        "h": 31.0,
        "storeys": 10,
        "func": "budynek wielorodzinny",
    }
    FF._add_building(sectors, block, elev, 1024.0, "High")
    FF._add_chimney(sectors, {"id": "ch1", "e": -380.0, "n": -1250.0, "h": 113.0}, elev, 1024.0, "High")
    FF._add_pylon(sectors, {"id": "py1", "e": 1200.0, "n": -700.0, "h": 28.0}, elev, 1024.0, "High")
    FF._add_forest_stand(
        sectors,
        [[500.0, 1050.0], [700.0, 1050.0], [700.0, 1250.0], [500.0, 1250.0], [500.0, 1050.0]],
        "conifer",
        elev,
        1024.0,
        "Low",
    )

    south_prims = sectors["far_south"].primitives()
    assert len(south_prims) == 1
    assert south_prims[0]["mat"] == "far_field_buildings"
    # Punched window walls have alpha = 1.0, windowless walls/roofs/chimneys have alpha = 0.0
    alphas = set(np.round(south_prims[0]["COL"][:, 3], 2).tolist())
    assert 1.0 in alphas and 0.0 in alphas

    north_prims = sectors["far_north"].primitives()
    # ADR 0330 + farfield-low-s24: one curtain primitive (atlas); the stand mix / haze band select the slot (UV)
    assert {p["mat"] for p in north_prims} == {"far_field_buildings", "forest_edge_mixed_far_atlas"}


@pytest.mark.parametrize("east,height,low_visible", [(1300., 10., True), (3000., 10., False), (3000., 40., True)])
def test_low_prunes_only_small_distant_rendered_envelopes(east, height, low_visible):
    from streetscape import far_field as FF
    elev = FF.BorderElevation(1024., [100.] * 2, [100.] * 2, [100.] * 2, [100.] * 2)
    b = {"id": "small-block", "typ": "block", "area": 480., "h": height, "storeys": 4,
         "rect": [[east, -6.], [east + 40., -6.], [east + 40., 6.], [east, 6.]]}
    for tier in ("Low", "High"):
        sectors = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
        FF._add_building(sectors, b, elev, 1024., tier)
        prims = sectors["far_east"].primitives()
        assert bool(prims) == (low_visible or tier == "High")
        if prims:
            # Every retained envelope still has a closed, windowless roof.
            p = prims[0]
            flat_top = np.all(np.isclose(p["V"][p["T"]][:, :, 2], p["V"][:, 2].max()), axis=1)
            assert flat_top.any()
            assert np.all(p["COL"][p["T"]][flat_top, :, 3] == 0.)


def test_low_retains_closed_block_roof_without_penthouse():
    from streetscape import far_field as FF
    elev = FF.BorderElevation(1024., [100.] * 2, [100.] * 2, [100.] * 2, [100.] * 2)
    b = {"id": "tall-block", "typ": "block", "area": 720., "h": 31., "storeys": 10,
         "rect": [[-500., -1150.], [-440., -1150.], [-440., -1138.], [-500., -1138.]]}
    tops = {}
    for tier in ("Low", "High"):
        sectors = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
        FF._add_building(sectors, b, elev, 1024., tier)
        tops[tier] = sectors["far_south"].primitives()[0]["V"][:, 2].max()
    _, scale_h = FF.foreshorten_scales(120.)
    assert tops["Low"] == pytest.approx(elev.z_at_eff(-470., -1144.) + 31. * scale_h)
    assert tops["High"] > tops["Low"]


def test_generated_far_field_qa_and_manifests():
    qa_path = REGION_DIR / "generated" / "far_field_qa.json"
    src_manifest_path = REPO / "Data" / "SourceManifests" / f"{REGION_ID}-far-field.manifest.json"
    wm_path = REGION_DIR / "generated" / "world_manifest.json"

    assert qa_path.exists(), "far_field_qa.json missing"
    assert src_manifest_path.exists(), "far-field source manifest missing"
    assert wm_path.exists(), "world_manifest.json missing"

    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    src_man = json.loads(src_manifest_path.read_text(encoding="utf-8"))
    wm = json.loads(wm_path.read_text(encoding="utf-8"))

    # Source manifest checks
    assert src_man["schema"] == "truck-sim-pl/source-manifest/1"
    assert len(src_man["sources"]) == 3
    fc = qa["feature_counts"]
    assert fc["forest_polygons"] >= 100
    assert fc["buildings"] >= 4000
    assert fc["chimneys"] >= 8
    assert fc["pylons"] >= 150
    assert fc["power_lines"] >= 20
    # Extraction provenance must describe the actual generated feature inventory.
    assert qa["building_height_sources"] == src_man["building_height_sources"]
    assert sum(qa["building_height_sources"].values()) == fc["buildings"]
    assert qa["lod1_height_audit"] == src_man["lod1_height_audit"]
    assert qa["lod1_height_audit"]["usable_ids"] > 0
    assert qa["building_height_sources"]["gugik-lod1-measuredHeight"] > 0

    # Height provenance and an estimated facade finish are different claims.
    appearance = qa["appearance_policy"]
    assert appearance == src_man["appearance_policy"]
    assert appearance["status"] == "WORKING_VALUE"
    assert {"wall_colour", "cladding_modules", "glazing_band", "roof_fascia"} <= set(appearance["not_measured"])
    hall_counts = appearance["source_hall_counts"]
    assert set(hall_counts) == {"industrial", "energy", "other"}
    assert all(isinstance(count, int) and count >= 0 for count in hall_counts.values())
    assert sum(hall_counts.values()) == fc["buildings_by_typology"]["hall"]
    assert 0 < appearance["source_panel_hall_count"] <= hall_counts["industrial"]
    assert appearance["panel_alpha"] == 0.25
    assert appearance["panel_ribbon_alpha"] == 0.65

    # Performance budget & sector structure checks
    low = qa["tiers"]["Low"]
    high = qa["tiers"]["High"]
    assert low["total_triangles"] <= 30_000, f"Low total_triangles {low['total_triangles']} exceeds 30k budget"
    assert high["total_triangles"] > low["total_triangles"]

    for tier_name, tier_data in (("Low", low), ("High", high)):
        assert set(tier_data["sectors"].keys()) == {"far_north", "far_east", "far_south", "far_west"}
        for sec_name, sec in tier_data["sectors"].items():
            assert 1 <= sec["submeshes"] <= 2, f"{tier_name}/{sec_name} has {sec['submeshes']} submeshes (max 2)"
            assert sec["triangles"] > 500, f"{tier_name}/{sec_name} is empty ({sec['triangles']} tris)"

        glb_file = REPO / tier_data["file"]
        if glb_file.exists():
            digest = hashlib.sha256(glb_file.read_bytes()).hexdigest()
            assert digest == tier_data["sha256"]

    assert "far_field_buildings" in wm["materials"]
    assert wm["materials"]["far_field_buildings"].get("vertex_color") is True


def test_skyline_node_flags_and_landmark_stand_ins():
    """ADR 0141: tall ring objects and the stand-ins of region landmark stacks go to the far_skyline builder with the
    TEXCOORD_1.x flag; ordinary sector geometry keeps TEXCOORD_1.x >= 0."""
    from streetscape import far_field as FF

    elev = FF.BorderElevation(1024.0, [135.0, 135.0], [135.0, 135.0], [135.0, 135.0], [135.0, 135.0])
    sectors = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
    skyline = FF.SectorBuilder(FF.SKYLINE, uv1_flag=FF.SKYLINE_FLAG_CLAMP)
    tall = {"id": "tall", "typ": "block", "area": 720.0, "h": 31.0, "storeys": 10, "func": "budynek wielorodzinny",
            "rect": [[-500.0, -1150.0], [-440.0, -1150.0], [-440.0, -1138.0], [-500.0, -1138.0]]}
    low = dict(tall, id="low", h=14.0, storeys=4,
               rect=[[-300.0, -1150.0], [-240.0, -1150.0], [-240.0, -1138.0], [-300.0, -1138.0]])
    FF._add_building(sectors, tall, elev, 1024.0, "Low", skyline=skyline)
    FF._add_building(sectors, low, elev, 1024.0, "Low", skyline=skyline)
    FF._add_chimney(sectors, {"id": "c", "e": -380.0, "n": -1250.0, "h": 113.0}, elev, 1024.0, "Low", skyline=skyline)
    FF._add_chimney(sectors, {"id": "s", "e": -200.0, "n": -1250.0, "h": 20.0}, elev, 1024.0, "Low", skyline=skyline)
    n_clamp = skyline.count0
    stack = {"id": "ec", "e": 624.0, "n": -1084.0, "h": 120.0, "base_d": 7.65, "top_d": 4.8,
             "band_boundaries": [36.0, 48.0, 60.0, 72.0, 84.0, 96.0, 108.0, 120.0]}
    FF._add_landmark_stack_proxy(skyline, stack, elev, "Low")
    skyline.sort_far_to_near()

    south = sectors["far_south"].primitives()[0]
    assert south["UV1"][:, 0].min() >= 0.0, "ordinary far-field geometry carries no skyline flag"
    assert south["V"][:, 2].max() < 135.0 + 25.0, "the 31 m block and the 113 m chimney left the sector mesh"

    sky = skyline.primitives()[0]
    u = sky["UV1"][:, 0]
    assert u.max() <= -FF.SKYLINE_FLAG_CLAMP, "every skyline vertex is flagged"
    beyond = u <= -FF.SKYLINE_FLAG_BEYOND
    assert int(beyond.sum()) == skyline.count0 - n_clamp == 8 * 6 * 4, "shaft + 7 bands, 6 sides: the stack stand-in"
    assert sky["V"][beyond][:, 2].max() == pytest.approx(135.0 + 120.0, abs=1.0), "source height, no foreshortening"
    # Window-grid coordinate survives the flag: -(x + 16) with x >= 0.
    assert (-(u[~beyond]) - FF.SKYLINE_FLAG_CLAMP).min() >= 0.0
    # Painter order: face centroids never get farther from the tile centre along the index buffer.
    tri = sky["T"]
    assert tri.min() == 0 and tri.max() == len(sky["V"]) - 1
    d = np.hypot(*sky["V"][tri].mean(axis=1)[:, :2].T)
    assert d[0] == d.max() and d[-1] <= d.min() + 12.0, "farthest face first, nearest object last"


def test_generated_far_field_skyline_budget():
    qa = json.loads((REGION_DIR / "generated" / "far_field_qa.json").read_text(encoding="utf-8"))
    for tier in ("Low", "High"):
        sky = qa["tiers"][tier]["skyline"]
        assert sky["node"] == "far_skyline" and sky["submeshes"] == 1
        assert 0 < sky["triangles"] <= (3000 if tier == "Low" else 8000)
        assert sum(s["triangles"] for s in qa["tiers"][tier]["sectors"].values()) + sky["triangles"] == qa["tiers"][tier]["total_triangles"]
    assert len(qa["tiers"]["Low"]["skyline"]["landmark_stack_proxies"]) == 2


def test_stand_wrapping_a_tile_corner_is_split_by_sector_0308():
    """A forest around the NE corner went whole to the sector of its centroid (east) and stood in the north neighbour."""
    from shapely.geometry import Polygon, Point
    from streetscape import far_field as FF
    half = 1024.0
    reg = FF.sector_regions(half)
    for e, n in ((0, 1500), (1500, 1500), (1500, 0), (1500, -1500), (0, -1500), (-1500, -1500), (-1500, 0), (-1500, 1500),
                 (-1200, 1500)):
        hit = [k for k, r in reg.items() if r.contains(Point(e, n))]
        assert hit == [FF.sector_of(e, n, half)], (e, n, hit)
    # L-shaped stand: an arm east of the tile and an arm north of it, centroid in the east sector
    L = Polygon([(1100, -900), (1500, -900), (1500, 1400), (-600, 1400), (-600, 1150), (1100, 1150)])
    assert FF.sector_of(L.centroid.x, L.centroid.y, half) == "far_east"
    parts = FF.split_by_sector(L, half)
    assert {n for n, _ in parts} == {"far_north", "far_east"}
    assert sum(p.area for _, p in parts) == pytest.approx(L.area, rel=1e-6)
    for name, p in parts:
        assert reg[name].buffer(0.01).contains(p), name


def test_far_field_extra_dist_and_curtain_uv1_0330():
    """ADR 0330 addendum: inverse foreshortening recovers true ring coordinates, extra_dist_eff is 0 within 140 m of
    the tile border, grows monotonically to ~3.55 km, and curtains carry it in TEXCOORD_1.x with sky-tilted normals."""
    from streetscape import far_field as FF

    for e_raw, n_raw in ((500.0, 1100.0), (500.0, 2500.0), (-3200.0, 1800.0), (4100.0, -400.0)):
        ee, ne, d_raw, d_eff = FF.foreshorten_point(e_raw, n_raw, 1024.0)
        er, nr, dt = FF.unforeshorten_xy(np.array([ee]), np.array([ne]), 1024.0)
        assert er[0] == pytest.approx(e_raw, abs=0.5)
        assert nr[0] == pytest.approx(n_raw, abs=0.5)
        assert dt[0] == pytest.approx(d_raw, abs=0.5)
        dex = FF.extra_dist_eff(np.array([ee]), np.array([ne]), 1024.0)[0]
        if d_raw <= FF.FORESHORTEN_FREE_M:
            assert dex == pytest.approx(0.0, abs=1e-6)
        else:
            assert dex == pytest.approx(d_raw - d_eff, abs=0.5)

    elev = FF.BorderElevation(1024.0, [135.0, 135.0], [135.0, 135.0], [135.0, 135.0], [135.0, 135.0])
    sectors = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
    FF._add_forest_stand(
        sectors,
        [[200.0, 2600.0], [800.0, 2600.0], [800.0, 3200.0], [200.0, 3200.0], [200.0, 2600.0]],
        "conifer", elev, 1024.0, "High",
    )
    prims = sectors["far_north"].primitives(1024.0)
    assert len(prims) <= 2
    curtain = next(p for p in prims if p["mat"] == "forest_edge_mixed_far_atlas")
    assert "UV1" in curtain and len(curtain["UV1"]) == len(curtain["V"])
    expected_extra = FF.extra_dist_eff(curtain["V"][:, 0], curtain["V"][:, 1], 1024.0)
    assert np.allclose(curtain["UV1"][:, 0], expected_extra, atol=1e-3)
    assert curtain["UV1"][:, 0].min() > 800.0
    # Top row normals tilt further skyward than bottom row normals (CURTAIN_NORMAL_UP)
    assert curtain["N"][:, 2].max() > 0.75
    assert curtain["N"][:, 2].min() < curtain["N"][:, 2].max() - 0.20


def test_far_field_chm_and_noise_silhouette_0330():
    """ADR 0330 addendum: RingChm drives crown heights where forest_chm.png exists (without the legacy 8.5 m clamp at
    3 km), and multi-scale seeded noise yields a varied, deterministic silhouette where CHM is absent."""
    from streetscape import far_field as FF, forest_chm as FC

    # Synthetic CHM covering east 0..1024, north 1024..2048: western half young (10 m), eastern half mature (28 m)
    top = np.full((64, 64), 10.0, dtype=np.float64)
    top[:, 32:] = 28.0
    cov = np.full((64, 64), 0.9, dtype=np.float64)
    chm = FC.Chm(top, cov, x0=0.0, y1=2048.0, cell_m=16.0)
    ring_chm = FF.RingChm([("synth-tile", chm)])

    e_raw = np.linspace(100.0, 900.0, 20)
    n_raw = np.full_like(e_raw, 1600.0)
    pts_eff = np.array([FF.foreshorten_point(x, y, 1024.0)[:2] for x, y in zip(e_raw, n_raw)])
    ht_chm = FF._crown_height_wave(pts_eff[:, 0], pts_eff[:, 1], 15.0, 1024.0,
                                   rng=np.random.default_rng(7), mix="conifer", ring_chm=ring_chm)
    assert ring_chm.n_chm_verts == len(e_raw)
    # Mature eastern half must stand noticeably taller than young western half
    assert ht_chm[12:].mean() > ht_chm[:8].mean() * 2.0

    # Far stand (d_true ~ 3000 m) without CHM: deterministic, varied, not clamped flat to 8.5 m
    e_far_raw = np.linspace(-800.0, 800.0, 40)
    n_far_raw = np.full_like(e_far_raw, 4000.0)
    pts_far = np.array([FF.foreshorten_point(x, y, 1024.0)[:2] for x, y in zip(e_far_raw, n_far_raw)])
    ht1 = FF._crown_height_wave(pts_far[:, 0], pts_far[:, 1], 8.5, 1024.0, rng=np.random.default_rng(42), mix="mixed")
    ht2 = FF._crown_height_wave(pts_far[:, 0], pts_far[:, 1], 8.5, 1024.0, rng=np.random.default_rng(42), mix="mixed")
    assert np.allclose(ht1, ht2)
    assert ht1.min() < 7.5, "distant low/young parts must not clamp flat to legacy 8.5 m"
    assert ht1.max() / ht1.min() > 1.7, "horizon silhouette must vary across compartments and clumps"


def test_far_atlas_haze_and_visibility_0330():
    """ADR 0330 addendum: far atlas v2 cools distant bands (higher B/R) and lifts sky visibility (B in _n.png)."""
    from PIL import Image
    from streetscape import forest_hlod as FH

    vdir = REPO / "art-source" / "world" / "vegetation"
    meta = json.loads((vdir / "forest_edge_far_atlas.json").read_text(encoding="utf-8"))
    assert meta["schema"] == "truck-sim-pl/forest-edge-far-atlas/2"
    a_im = np.asarray(Image.open(vdir / f"{FH.FAR_ATLAS_MAT}.png").convert("RGBA"), float) / 255.0
    n_im = np.asarray(Image.open(vdir / f"{FH.FAR_ATLAS_MAT}_n.png").convert("RGBA"), float) / 255.0
    H, Hn = a_im.shape[0], n_im.shape[0]
    br_by_band, vis_by_band = [], []
    for suf in ("", "_haze1", "_haze2"):
        v0, v1 = FH.far_atlas_slot_v("conifer", suf)
        sl = a_im[H - int(round(v1 * H)):H - int(round(v0 * H))]
        m = sl[..., 3] > 0.5
        lin = FH._srgb_to_lin(sl[m, :3]).mean(axis=0)
        br_by_band.append(float(lin[2] / max(lin[0], 1e-6)))
        sn = n_im[Hn - int(round(v1 * Hn)):Hn - int(round(v0 * Hn))]
        vis_by_band.append(float(sn[..., 2].mean()))
    assert br_by_band[0] < br_by_band[1] < br_by_band[2], f"expected cooler B/R with distance: {br_by_band}"
    assert vis_by_band[0] < vis_by_band[1] < vis_by_band[2], f"expected higher sky vis_B with distance: {vis_by_band}"
    assert vis_by_band[2] > 0.85


def test_corridor_treelines_scoped_to_region_c_0330_r2():
    """ADR 0330 r2: Białystok-C's hardcoded corridor treelines and exit tapers must not leak into rural tiles."""
    from streetscape import far_field as FF

    assert len(FF._corridor_treelines(1024.0, "bialystok-industrial-c")) > 0
    assert FF._corridor_treelines(1024.0, "knyszyn-w") == []
    assert FF._corridor_treelines(1024.0, "dk65-05") == []

    e = np.array([-1080.0, -856.0, 1080.0])
    n = np.array([44.0, 1050.0, -980.0])
    assert FF._corridor_taper(e, n, 1024.0, "bialystok-industrial-c").min() < 0.6
    assert np.allclose(FF._corridor_taper(e, n, 1024.0, "knyszyn-w"), 1.0)
    assert np.allclose(FF._corridor_taper(e, n, 1024.0, "dk65-05"), 1.0)


def test_curtain_slope_cap_and_flat_mound_0330_r2():
    """ADR 0330 r2: CHM outliers are capped to Podlasie canopy heights, curtain top slopes stay <= FAR_MAX_TOP_SLOPE,
    and under-canopy mounds stay low (<= 3.6 m) so no forest reads as a conical hill."""
    from streetscape import far_field as FF, forest_chm as FC

    # Extreme 48 m CHM spike next to 8 m trees
    top = np.full((64, 64), 8.0, dtype=np.float64)
    top[:, 30:34] = 48.0
    cov = np.full((64, 64), 0.9, dtype=np.float64)
    chm = FC.Chm(top, cov, x0=0.0, y1=2048.0, cell_m=16.0)
    ring_chm = FF.RingChm([("spike-tile", chm)])

    elev = FF.BorderElevation(1024.0, [130.0, 130.0], [130.0, 130.0], [130.0, 130.0], [130.0, 130.0])
    sectors = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
    # Small 120x120 m stand right over the spike
    FF._add_forest_stand(
        sectors,
        [[420.0, 1200.0], [560.0, 1200.0], [560.0, 1340.0], [420.0, 1340.0], [420.0, 1200.0]],
        "conifer", elev, 1024.0, "High", ring_chm=ring_chm, region_id="knyszyn-w",
    )
    prims = sectors["far_north"].primitives(1024.0)
    assert len(prims) <= 2
    mound = next(p for p in prims if p["mat"] == "far_field_buildings")
    zg_m = np.array([elev.z_at_eff(x, y) for x, y in mound["V"][:, :2]])
    assert (mound["V"][:, 2] - zg_m).max() <= 2.3, "under-canopy mound must stay low and flat"

    curtain = next(p for p in prims if p["mat"] == "forest_edge_mixed_far_atlas")
    cap_quad = FF.FAR_CROWN_CAP_M["conifer"] / 0.888
    zg_c = np.array([elev.z_at_eff(x, y) for x, y in curtain["V"][:, :2]])
    assert (curtain["V"][:, 2] - zg_c).max() <= cap_quad + 1.0, "CHM spike must not exceed Podlasie canopy cap"

    # Check _limit_top_slope directly enforces |dz_top / ds| <= FAR_MAX_TOP_SLOPE
    P = np.column_stack([np.linspace(0.0, 90.0, 11), np.zeros(11)])
    zb = np.full(11, 130.0)
    ht = np.array([8.0, 8.0, 8.0, 35.0, 35.0, 8.0, 8.0, 30.0, 8.0, 8.0, 8.0])
    ht_lim = FF._limit_top_slope(P, zb, ht)
    ds = np.hypot(*np.diff(P, axis=0).T)
    slopes = np.abs(np.diff(zb + ht_lim)) / ds
    assert slopes.max() <= FF.FAR_MAX_TOP_SLOPE + 1e-6


def test_irregular_base_skirt_and_edge_impostors_0330_r2():
    """ADR 0330 r2: High tier emits undergrowth skirt and individual edge tree impostors in the single far-atlas
    submesh (<= 2 submeshes/sector, strictly outside tile); Low tier keeps zero impostors for budget."""
    from streetscape import far_field as FF, forest_hlod as FH

    elev = FF.BorderElevation(1024.0, [135.0, 135.0], [135.0, 135.0], [135.0, 135.0], [135.0, 135.0])
    stand = [[100.0, 1250.0], [600.0, 1250.0], [600.0, 1550.0], [100.0, 1550.0], [100.0, 1250.0]]

    sec_hi = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
    FF._add_forest_stand(sec_hi, stand, "mixed", elev, 1024.0, "High", region_id="knyszyn-w")
    prims_hi = sec_hi["far_north"].primitives(1024.0)
    assert len(prims_hi) <= 2
    curtain_hi = next(p for p in prims_hi if p["mat"] == FH.FAR_ATLAS_MAT)
    # Impostor rows occupy the top 2 slots of the far atlas
    imp_v0, _ = FH.far_atlas_slot_v("impostor", "row0")
    has_impostor_verts = (curtain_hi["UV"][:, 1] >= imp_v0 - 1e-4).any()
    assert has_impostor_verts, "High tier near-edge stand must emit individual edge tree impostors"
    # Every vertex stays outside the tile border
    d_out = np.array([FF.outside_dist(x, y, 1024.0)[4] for x, y in curtain_hi["V"][:, :2]])
    assert d_out.min() >= 8.5

    sec_lo = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
    FF._add_forest_stand(sec_lo, stand, "mixed", elev, 1024.0, "Low", region_id="knyszyn-w")
    prims_lo = sec_lo["far_north"].primitives(1024.0)
    assert len(prims_lo) <= 2
    curtain_lo = next(p for p in prims_lo if p["mat"] == FH.FAR_ATLAS_MAT)
    assert not (curtain_lo["UV"][:, 1] >= imp_v0 - 1e-4).any(), "Low tier must omit extra edge impostors"


def test_far_atlas_impostor_rows_and_padding_0330_r2():
    """ADR 0330 r2: far atlas is 1024x4096 with >= 8 px vertical pad and 8 crisp isolated tree impostors."""
    from PIL import Image
    from streetscape import forest_hlod as FH

    vdir = REPO / "art-source" / "world" / "vegetation"
    meta = json.loads((vdir / "forest_edge_far_atlas.json").read_text(encoding="utf-8"))
    assert meta["size"] == [1024, 4096]
    assert meta["pad"] >= 8
    a_im = np.asarray(Image.open(vdir / f"{FH.FAR_ATLAS_MAT}.png").convert("RGBA"), float) / 255.0
    H, W = a_im.shape[:2]
    assert (W, H) == (1024, 4096)
    for row in FH.FAR_IMPOSTOR_ROWS:
        for tname in row:
            u0, v0, u1, v1, asp, top_frac = FH.far_impostor_uv(tname)
            x0, x1 = int(round(u0 * W)), int(round(u1 * W))
            y0, y1 = H - int(round(v1 * H)), H - int(round(v0 * H))
            cell = a_im[y0:y1, x0:x1]
            assert (cell[..., 3] > 0.5).mean() > 0.05, f"impostor {tname} empty"
            # Left and right borders of each impostor cell are transparent (no bleed between neighbours)
            assert cell[:, :2, 3].max() < 0.05 and cell[:, -2:, 3].max() < 0.05, f"impostor {tname} bleeds horizontally"
