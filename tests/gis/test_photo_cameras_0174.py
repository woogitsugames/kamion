"""ADR 0174: authored photo-matched control cameras (control_cameras_photo.authored.json) reach generated/control_cameras.json
with the authored position, a level look direction along the authored heading and an eye above the surface."""
import json
import math
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("region_id", ["bialystok-dojlidy"])
def test_photo_cameras_generated(region_id):
    rdir = REPO / "Data/Regions" / region_id
    src = rdir / "control_cameras_photo.authored.json"
    gen = rdir / "generated/control_cameras.json"
    if not src.exists() or not gen.exists():
        pytest.skip("no authored photo cameras or control_cameras.json missing")
    cams = {c["id"]: c for c in json.loads(gen.read_text(encoding="utf-8"))["cameras"]}
    for e in json.loads(src.read_text(encoding="utf-8"))["cameras"]:
        c = cams[e["id"]]
        assert c["type"] == "persp" and c["fov_deg"] == pytest.approx(e["fov_deg"])
        assert c["pos"][0] == pytest.approx(e["pos_en"][0], abs=1e-3) and c["pos"][1] == pytest.approx(e["pos_en"][1], abs=1e-3)
        de, dn = c["look_at"][0] - c["pos"][0], c["look_at"][1] - c["pos"][1]
        hd = math.degrees(math.atan2(de, dn)) % 360.0
        assert abs((hd - e["heading_deg"] + 180.0) % 360.0 - 180.0) < 0.1
        assert c["look_at"][2] == pytest.approx(c["pos"][2])
        assert 100.0 < c["pos"][2] < 250.0     # EVRF2007 heights of the tile + eye


def test_reference_region_has_no_photo_file():
    # region C keeps its authored cameras_industrial_c set; a photo file there would be silently ignored
    assert not (REPO / "Data/Regions/bialystok-industrial-c/control_cameras_photo.authored.json").exists()
