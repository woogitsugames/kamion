"""ADR 0085 r2: a centroid outside the tile must not duplicate a tile building."""

import json

import numpy as np
import pytest
from shapely.geometry import MultiPolygon, Polygon, box

from conftest import REGION_ID, REPO
from streetscape import far_field as FF


@pytest.mark.parametrize("footprint", [
    box(-250, -1100, -180, -1000),  # edge-south regression; centroid outside
    box(-250, 1000, -180, 1100),
    box(-1100, -250, -1000, -180),
    box(1000, -250, 1100, -180),
    box(-50, -50, 50, 50),
    box(1024, -50, 1100, 50),  # boundary contact belongs to the region too
    MultiPolygon([box(1400, 0, 1500, 100), box(1000, 0, 1030, 10)]),
])
def test_whole_source_footprint_must_be_disjoint(footprint):
    assert not FF.building_outside_region(footprint, 1024)


def test_rectangle_can_overlap_even_when_source_does_not():
    # Concave building bends around the NE tile corner; its LoD rectangle fills the gap.
    source = Polygon([(1000, 1040), (1040, 1040), (1040, 1000),
                      (1080, 1000), (1080, 1080), (1000, 1080)])
    assert FF.building_outside_region(source, 1024)
    assert not FF.building_outside_region(source.minimum_rotated_rectangle, 1024)


def test_bdot_extraction_excludes_crossing_source_and_lod_rectangle(tmp_path, monkeypatch):
    import pyogrio

    source_file = (tmp_path / "Data/raw/gugik/bdot10k-2061/gpkg/"
                   "PL.PZGiK.335.BDOT10k.2061__OT_BUBD_A.gpkg")
    source_file.parent.mkdir(parents=True)
    source_file.write_bytes(b"fixture")

    class Row(dict):
        @property
        def geometry(self):
            return self["geometry"]

    footprints = {
        "crossing-hall": box(-250, -1100, -180, -1000),
        "external-hall": box(-250, -1300, -180, -1200),
        "multipart": MultiPolygon([box(1400, 0, 1500, 100), box(1000, 0, 1030, 10)]),
        "concave-corner": Polygon([(1000, 1040), (1040, 1040), (1040, 1000),
                                   (1080, 1000), (1080, 1080), (1000, 1080)]),
    }

    class Frame:
        def iterrows(self):
            return enumerate(Row(geometry=geom, LOKALNYID=key,
                                 FUNKCJAOGOLNABUDYNKU="magazyn", LICZBAKONDYGNACJI=3)
                             for key, geom in footprints.items())

    monkeypatch.setattr(FF, "REPO", tmp_path)
    monkeypatch.setattr(pyogrio, "read_dataframe", lambda *args, **kwargs: Frame())
    gis = FF.extract_ring_gis("fixture", 0, 0)
    assert [b["id"] for b in gis["buildings"]] == ["external-hall"]
    assert gis["boundary_exclusions"]["bdot_source"] == 2
    assert gis["boundary_exclusions"]["bdot_rectangle"] == 1
    # A regional building continues past the boundary; an alternate source rectangle
    # can overlap that continuation without intersecting the tile itself.
    region_file = tmp_path / "Data/Regions/fixture/buildings.geojson"
    region_file.parent.mkdir(parents=True)
    region_file.write_text(json.dumps({"features": [{
        "geometry": box(-230, -1270, -190, -1000).__geo_interface__,
        "properties": {},
    }]}), encoding="utf-8")
    refreshed = FF.extract_ring_gis("fixture", 0, 0)
    assert not refreshed["buildings"], "regional footprint change must invalidate the cache"


@pytest.mark.parametrize("tier", ["Low", "High"])
def test_crossing_building_emits_no_geometry(tier):
    elev = FF.BorderElevation(1024, *([[135, 135]] * 4))
    sectors = {name: FF.SectorBuilder(name) for name in FF.SECTORS}
    building = dict(id="edge-south-regression", typ="hall", area=7000,
                    h=12, rect=[[-250, -1100], [-180, -1100],
                                [-180, -1000], [-250, -1000]])
    FF._add_building(sectors, building, elev, 1024, tier)
    assert all(not sec.primitives() for sec in sectors.values())
    building["rect"] = [[e, n - 150] for e, n in building["rect"]]
    FF._add_building(sectors, building, elev, 1024, tier)
    assert sectors["far_south"].primitives(), "retain genuinely external buildings"


def test_regenerated_building_rectangles_do_not_intersect_region():
    path = REPO / "Data/raw/derived" / REGION_ID / "world/far_field_gis_cache.json"
    if not path.exists():
        pytest.skip("far-field raw extraction cache unavailable")
    gis = json.loads(path.read_text(encoding="utf-8"))
    assert gis["schema"] == FF.GIS_CACHE_SCHEMA
    tile = FF.region_building_exclusion(REGION_ID, *gis["origin_epsg2180"], gis["half_m"])
    for building in gis["buildings"]:
        rect = np.asarray(building["rect"])
        assert not Polygon(rect).intersects(tile), building["id"]
        cx, cy = rect.mean(axis=0)
        ce, cn, distance, _ = FF.foreshorten_point(cx, cy, gis["half_m"])
        scale, _ = FF.foreshorten_scales(distance)
        mapped = (rect - [cx, cy]) * scale + [ce, cn]
        assert not Polygon(mapped).intersects(tile), building["id"]
