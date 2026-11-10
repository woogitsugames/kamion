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


def test_border_elevation_eases_to_mean():
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
    assert z_far == pytest.approx(elev.mean)


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
