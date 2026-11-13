"""ADR 0166: build_world of a region other than C must not rewrite the shared art-source library and must not use the
C-specific control cameras (Andersa / Rondo Putry); region C keeps both unchanged."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))


def test_shared_library_only_for_reference_region():
    from roads import build_world as BW
    c = BW.SHARED_LIBRARY_REGION
    assert c == "bialystok-industrial-c"
    assert BW.props_library_dir(c, BW.DEFAULT_OUT(c)) is None                       # shared art-source (unchanged)
    assert BW.props_meta_path(c) == REPO / "art-source/world/props/props_meta.json"
    d = "bialystok-dojlidy"
    lib = BW.props_library_dir(d, BW.DEFAULT_OUT(d))
    assert lib == REPO / "Data" / "raw" / "derived" / d / "props"
    assert "art-source" not in lib.parts
    # a non-default output of C (tests, scratch builds) never writes the shared library either
    assert BW.props_library_dir(c, Path("scratch") / "world") == Path("scratch") / "props"


def test_camera_dispatch():
    from roads import build_world as BW
    import inspect
    src = inspect.getsource(BW.cameras)
    assert "cameras_industrial_c" in src and "cameras_generic" in src
    assert "Andersa" not in inspect.getsource(BW.cameras_generic)


@pytest.mark.parametrize("region_id", ["bialystok-dojlidy"])
def test_generated_cameras_generic(region_id):
    p = REPO / "Data/Regions" / region_id / "generated/control_cameras.json"
    if not p.exists():
        pytest.skip("control_cameras.json missing: run roads/build_world.py")
    cams = json.loads(p.read_text(encoding="utf-8"))["cameras"]
    ids = [c["id"] for c in cams]
    assert len(ids) == len(set(ids))
    assert not any("putry" in i or "andersa" in i for i in ids)
    assert any(c["type"] == "ortho" for c in cams)
    assert sum(1 for i in ids if i.startswith("route_s")) >= 3
