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
    assert {p["mat"] for p in north_prims} == {"far_field_buildings", "forest_edge_mixed"}


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
