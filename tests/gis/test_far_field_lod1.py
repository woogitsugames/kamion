"""LoD1 archive regressions: real GUGiK layout, scoped joins and unusable data."""
import zipfile

import pytest

from streetscape.far_field import _extract_lod1_heights


def archive(tmp_path, members):
    path = tmp_path / "lod1.zip"
    with zipfile.ZipFile(path, "w") as zf:
        for name, body in members.items():
            zf.writestr(name, body)
    return path


def city(body):
    return ('<c:CityModel xmlns:c="http://www.opengis.net/citygml/2.0" '
            'xmlns:b="http://www.opengis.net/citygml/building/2.0" '
            'xmlns:g="http://www.opengis.net/citygml/generics/2.0">'
            + body + '</c:CityModel>')


def building(bid, height):
    return ('<b:Building><b:measuredHeight uom="meter">' + height + '</b:measuredHeight>'
            '<g:stringAttribute name="buildingId"><g:value>' + bid +
            '</g:value></g:stringAttribute></b:Building>')


def test_reads_all_gml_and_xml_members_with_generic_ids_and_arbitrary_prefixes(tmp_path):
    path = archive(tmp_path, {
        "tile-b.GML": city(building(" B ", "31.25")),
        "tile-a.xml": city(building("A", "9.5")),
        "readme.txt": "not XML",
    })
    audit = {}
    assert _extract_lod1_heights(path, audit) == {"A": 9.5, "B": 31.25}
    assert audit == dict(members=2, buildings=2, invalid_or_missing=0,
                         duplicate_records=0, conflicting_ids=0, usable_ids=2)


def test_missing_values_never_join_across_buildings_or_building_parts(tmp_path):
    body = ('<b:Building><b:buildingId>no-height</b:buildingId>'
            '<b:consistsOfBuildingPart><b:BuildingPart><b:measuredHeight>99</b:measuredHeight>'
            '</b:BuildingPart></b:consistsOfBuildingPart></b:Building>'
            '<b:Building><b:measuredHeight>44</b:measuredHeight></b:Building>'
            '<b:Building><b:measuredHeight>12</b:measuredHeight>'
            '<b:buildingId>legacy</b:buildingId></b:Building>')
    assert _extract_lod1_heights(archive(tmp_path, {"tile.gml": city(body)})) == {"legacy": 12}


@pytest.mark.parametrize("value", ["nan", "inf", "-inf", "-2", "0", "invalid", ""])
def test_rejects_nonfinite_nonpositive_and_invalid_heights(tmp_path, value):
    assert _extract_lod1_heights(archive(tmp_path, {"tile.gml": city(building("bad", value))})) == {}


def test_conflicting_duplicate_ids_are_excluded_independently_of_member_order(tmp_path):
    a = city(building("conflict", "12") + building("same", "20"))
    b = city(building("conflict", "13") + building("same", "20"))
    for first, second in ((a, b), (b, a)):
        audit = {}
        assert _extract_lod1_heights(archive(tmp_path, {"a.gml": first, "b.gml": second}), audit) == {"same": 20}
        assert audit["conflicting_ids"] == 1
        assert audit["duplicate_records"] == 2


def test_missing_archive_and_unsupported_height_units(tmp_path):
    assert _extract_lod1_heights(tmp_path / "missing.zip") == {}
    body = building("feet", "40").replace('uom="meter"', 'uom="ft"')
    assert _extract_lod1_heights(archive(tmp_path, {"tile.gml": city(body)})) == {}


@pytest.mark.parametrize("unit", ["m", "#m", "meter", "metre"])
def test_supported_meter_units(tmp_path, unit):
    body = building("valid", "12.5").replace('uom="meter"', f'uom="{unit}"')
    assert _extract_lod1_heights(archive(tmp_path, {"tile.gml": city(body)})) == {"valid": 12.5}
