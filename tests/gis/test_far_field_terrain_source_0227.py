"""Far-field edges must follow the current build and the terrain encoding."""
import json

import numpy as np
import pytest

from streetscape import far_field as ff


@pytest.fixture
def sources(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    region = "synthetic"
    regions = tmp_path / "regions"
    (regions / region).mkdir(parents=True)
    raw_file = repo / "terrain.r16"
    raw_file.parent.mkdir(parents=True)
    # Non-square shape catches inverted sample dimensions.
    np.full((3, 5), 12, dtype="<u2").tofile(raw_file)
    metadata = {"samples": [5, 3], "bbox": [0, 0, 4, 2], "encoding": {
        "file": "terrain.r16", "offset_m": 100.0, "scale_m_per_unit": 2.0}}
    (regions / region / "terrain.json").write_text(json.dumps(metadata), encoding="utf8")
    monkeypatch.setattr(ff, "REPO", repo)
    monkeypatch.setattr(ff.pipeline, "REGIONS", regions)
    default = repo / "Data" / "raw" / "derived" / region / "world"
    default.mkdir(parents=True)
    np.save(default / "terrain_conformed.npy", np.full((3, 5), 999.0))
    current = tmp_path / "current"
    current.mkdir()
    return region, current


def assert_border(elev, expected):
    for side in (elev.south, elev.east, elev.north, elev.west):
        np.testing.assert_allclose(side, expected)


def test_current_out_root_wins_over_stale_default(sources):
    region, current = sources
    np.save(current / "terrain_conformed.npy", np.full((3, 5), 150.0))
    assert_border(ff.BorderElevation.from_region(region, half=1, step_m=1, out_root=current), 150.0)


def test_missing_current_conformed_uses_encoded_r16_not_stale_default(sources):
    region, current = sources
    assert_border(ff.BorderElevation.from_region(region, half=1, step_m=1, out_root=current), 124.0)


def test_build_far_field_passes_its_output_root(sources, monkeypatch):
    region, current = sources
    monkeypatch.setattr(ff.pipeline, "load_region", lambda _: {
        "origin": {"x": 0, "y": 0}, "bbox": {"width_m": 2}})
    seen = {}

    def from_region(region_id, **kwargs):
        seen.update(region=region_id, **kwargs)
        return object()

    def stop(*args, **kwargs):
        raise RuntimeError("stop before GIS extraction")

    monkeypatch.setattr(ff.BorderElevation, "from_region", from_region)
    monkeypatch.setattr(ff, "extract_ring_gis", stop)
    with pytest.raises(RuntimeError, match="stop before GIS extraction"):
        ff.build_far_field(region, out_root=current)
    assert seen == {"region": region, "half": 1.0, "out_root": current}
