"""Scan grass photobase: deterministic layout, palette, wrapping and fallback."""
import hashlib
import json
import subprocess
import sys
import os
from pathlib import Path

import numpy as np
from PIL import Image
import pytest

from fab.grass_surface import OUTPUT, TARGET, bake, finish_tile, periodic_plan, _linear


def test_deterministic_periodic_clump_plan():
    plan = periodic_plan()
    assert plan == periodic_plan()
    assert plan != periodic_plan(seed=85)
    primary = [i for i in plan if not i["wrapped"]]
    assert len(primary) == 256
    assert all(-2 <= i["x"] <= 2 and -2 <= i["y"] <= 2 for i in primary)
    by_index = {i["index"]: i for i in primary}
    for copy in plan:
        original = by_index[copy["index"]]
        assert copy["yaw"] == original["yaw"]
        assert abs((copy["x"] - original["x"]) / 4 - round((copy["x"] - original["x"]) / 4)) < 1e-8
        assert abs((copy["y"] - original["y"]) / 4 - round((copy["y"] - original["y"]) / 4)) < 1e-8


def test_tile_palette_size_edges_and_reproducible_bytes(tmp_path):
    rng = np.random.default_rng(84)
    source = tmp_path / "raw.png"
    Image.fromarray(rng.integers(20, 160, (1300, 1300, 3), dtype=np.uint8)).save(source)
    path = tmp_path / "Low/basecolor.png"
    result = finish_tile(source, path, 512)
    first = path.read_bytes()
    pixels = np.asarray(Image.open(path))
    assert pixels.shape == (512, 512, 3)
    assert np.array_equal(pixels[0], pixels[-1])
    assert np.array_equal(pixels[:, 0], pixels[:, -1])
    assert np.max(np.abs(_linear(pixels).mean(axis=(0, 1)) - TARGET)) < .001
    assert result["target_status"] == "WORKING_VALUE"
    assert finish_tile(source, path, 512) == result
    assert path.read_bytes() == first
    high = tmp_path / "High/basecolor.png"
    finish_tile(source, high, 1024)
    assert Image.open(high).size == (1024, 1024)


def test_missing_blender_is_empty_warned_fallback(tmp_path, caplog):
    result = bake(tmp_path, blender=None)
    assert result["materials"] == {} and result["status"] == "fallback"
    assert "existing grass fallback" in caplog.text
    assert json.loads((tmp_path / OUTPUT / "grass_surface_manifest.json").read_text())["materials"] == {}


def _inputs(root):
    source = root / "Data/raw/fab/grass-clumps/source.zip"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"locally acquired fixture")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    path = root / "Data/SourceManifests/fab-megascans-2026-11-10.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"items": [{"id": "grass-clumps", "file": source.relative_to(root).as_posix(), "sha256": digest}]}))
    review = root / "tools/worldgen/fab/review.json"
    review.parent.mkdir(parents=True)
    review.write_text(json.dumps({"items": {"grass-clumps": {"status": "approved", "source_sha256": digest}}}))
    folder = root / OUTPUT
    folder.mkdir(parents=True)
    model = folder / "grass.glb"
    model.write_bytes(b"prepared fixture")
    image = folder / "basecolor.png"
    Image.new("RGBA", (32, 32), (80, 100, 40, 255)).save(image)
    item = {"status": "ready", "source_sha256": digest, "models": [{"path": model.relative_to(root).as_posix()}],
            "textures": {"High": {"basecolor": image.relative_to(root).as_posix()}},
            "provenance": [{"path": p.relative_to(root).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in (model, image)]}
    (folder / "manifest.json").write_text(json.dumps({"items": {"grass-clumps": item}}))
    return source, model, review


def test_missing_or_changed_source_is_fallback_without_blender_execution(tmp_path, monkeypatch):
    source, _, _ = _inputs(tmp_path)
    source.write_bytes(b"changed")
    def forbidden(*args, **kwargs):
        pytest.fail("Blender must not execute for an unverified source")
    monkeypatch.setattr(subprocess, "run", forbidden)
    assert bake(tmp_path, blender=sys.executable)["materials"] == {}


def test_revoked_review_is_fallback(tmp_path):
    _, _, review = _inputs(tmp_path)
    data = json.loads(review.read_text())
    data["items"]["grass-clumps"]["status"] = "rejected"
    review.write_text(json.dumps(data))
    assert bake(tmp_path, blender=sys.executable)["materials"] == {}


def test_prepared_input_cannot_escape_ignored_output(tmp_path):
    _inputs(tmp_path)
    path = tmp_path / OUTPUT / "manifest.json"
    data = json.loads(path.read_text())
    data["items"]["grass-clumps"]["models"][0]["path"] = "outside.glb"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="inside ignored"):
        bake(tmp_path, blender=sys.executable)


def test_success_manifest_has_opaque_tiers_and_shared_material_record(tmp_path, monkeypatch):
    _inputs(tmp_path)
    def fake_blender(command, **kwargs):
        request = json.loads(Path(command[-1]).read_text())
        Image.new("RGB", (1024, 1024), (80, 100, 40)).save(request["output"])
        return subprocess.CompletedProcess(command, 0, "fixture render", "")
    monkeypatch.setattr(subprocess, "run", fake_blender)
    result = bake(tmp_path, blender=sys.executable)
    assert result["status"] == "ready"
    a, b = (result["materials"][key] for key in ("terrain_grass", "verge_grass"))
    assert a == b and a["tile_m"] == [4, 4]
    for tier, maximum in (("Low", 512), ("High", 1024)):
        path = tmp_path / a["textures"][tier]["basecolor"]
        assert path.resolve().is_relative_to(tmp_path / OUTPUT)
        with Image.open(path) as image:
            assert image.mode == "RGB" and max(image.size) <= maximum


def test_changed_prepared_mesh_does_not_bake(tmp_path):
    _, model, _ = _inputs(tmp_path)
    model.write_bytes(b"changed after provenance recording")
    result = bake(tmp_path, blender=sys.executable)
    assert result["materials"] == {} and "provenance" in result["reason"]


def test_output_junction_cannot_write_outside_ignored_tree(tmp_path):
    output = tmp_path / OUTPUT
    outside = tmp_path / "outside"
    outside.mkdir()
    output.parent.mkdir(parents=True)
    try:
        output.symlink_to(outside, target_is_directory=True)
    except OSError:
        if os.name != "nt":
            pytest.skip("OS requires symlink permission")
        command = "New-Item -ItemType Junction -Path '" + str(output).replace("'", "''") + "' -Target '" + str(outside).replace("'", "''") + "' | Out-Null"
        subprocess.run(["powershell", "-NoProfile", "-Command", command], capture_output=True, check=True)
    with pytest.raises(ValueError, match="symlink/junction"):
        bake(tmp_path)
    assert not list(outside.iterdir())
