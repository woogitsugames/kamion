"""Fab optional inputs, provenance verification and safe archive processing."""
import hashlib
import json
import os
import subprocess
import struct
from pathlib import Path
from zipfile import ZipFile, ZipInfo

import pytest
from PIL import Image

from fab.prepare import OUTPUT, _meshes, prepare, safe_members, select_maps, sync_glb_textures, validate_crossed_billboard


def setup_source(tmp_path, approved=True):
    archive = tmp_path / "Data/raw/fab/test/source.zip"
    archive.parent.mkdir(parents=True)
    png = tmp_path / "source.png"
    Image.new("RGB", (2048, 1024), (100, 120, 80)).save(png)
    with ZipFile(archive, "w") as zf:
        zf.write(png, "test_4K_BaseColor.png")
        zf.write(png, "test_4K_Normal.png")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    manifest = tmp_path / "Data/SourceManifests/fab-megascans-2026-11-10.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"items": [{"id": "test", "file": archive.relative_to(tmp_path).as_posix(),
                                              "sha256": digest, "kind": "surface"}]}))
    review = tmp_path / "tools/worldgen/fab/review.json"
    review.parent.mkdir(parents=True)
    review.write_text(json.dumps({"items": {"test": {"source_sha256": digest,
                                                    "status": "approved" if approved else "pending"}}}))
    return archive


def test_optional_missing_keeps_fallback(tmp_path, caplog):
    archive = setup_source(tmp_path)
    archive.unlink()
    result = prepare(tmp_path)
    assert result["items"]["test"]["status"] == "missing"
    assert "fallback" in caplog.text


def test_unreviewed_never_produces_usable_asset(tmp_path):
    setup_source(tmp_path, approved=False)
    item = prepare(tmp_path)["items"]["test"]
    assert item["status"] == "pending-review"
    assert not item["textures"]


def test_source_hash_mismatch_fails_closed(tmp_path):
    archive = setup_source(tmp_path)
    archive.write_bytes(archive.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="SHA256"):
        prepare(tmp_path)


def test_texture_budgets_and_reproducibility(tmp_path):
    setup_source(tmp_path)
    first = prepare(tmp_path)
    assert first["items"]["test"]["status"] == "ready"
    for tier, maximum in (("Low", 512), ("High", 1024)):
        for path in first["items"]["test"]["textures"][tier].values():
            assert Path(path).is_relative_to(OUTPUT)
            with Image.open(tmp_path / path) as image:
                assert max(image.size) == maximum
    assert first == prepare(tmp_path)
    for entry in first["items"]["test"]["provenance"]:
        assert hashlib.sha256((tmp_path / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]


@pytest.mark.parametrize("name", ["../escape.fbx", "/absolute.fbx", "C:/drive.fbx", "safe/../../escape.fbx", "safe\\..\\escape.fbx"])
def test_archive_traversal_rejected(tmp_path, name):
    path = tmp_path / "unsafe.zip"
    with ZipFile(path, "w") as zf:
        zf.writestr(name, b"x")
    with ZipFile(path) as zf, pytest.raises(ValueError, match="Unsafe"):
        safe_members(zf)


def test_archive_symlink_rejected(tmp_path):
    path = tmp_path / "unsafe.zip"
    with ZipFile(path, "w") as zf:
        link = ZipInfo("link")
        link.external_attr = 0o120777 << 16
        zf.writestr(link, "target")
    with ZipFile(path) as zf, pytest.raises(ValueError, match="Unsafe"):
        safe_members(zf)


def test_opacity_alpha_and_urp_smoothness(tmp_path):
    archive = setup_source(tmp_path)
    gray = tmp_path / "gray.png"
    Image.new("L", (256, 256), 51).save(gray)
    with ZipFile(archive, "a") as zf:
        zf.write(gray, "test_4K_Opacity.png")
        zf.write(gray, "test_4K_Roughness.png")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    for path in (tmp_path / "Data/SourceManifests/fab-megascans-2026-11-10.json",
                 tmp_path / "tools/worldgen/fab/review.json"):
        data = json.loads(path.read_text())
        if isinstance(data["items"], list):
            data["items"][0]["sha256"] = digest
        else:
            data["items"]["test"]["source_sha256"] = digest
        path.write_text(json.dumps(data))
    textures = prepare(tmp_path)["items"]["test"]["textures"]["Low"]
    with Image.open(tmp_path / textures["basecolor"]) as image:
        assert image.mode == "RGBA" and image.getpixel((1, 1))[3] == 51
    with Image.open(tmp_path / textures["metallic_gloss"]) as image:
        assert image.getpixel((1, 1)) == (0, 0, 0, 204)


def test_mesh_atlas_never_uses_billboard_maps(tmp_path):
    path = tmp_path / "maps.zip"
    with ZipFile(path, "w") as zf:
        zf.writestr("Plant_4K_Billboard_Normal.jpg", b"billboard")
        zf.writestr("Plant_4K_Normal.jpg", b"mesh atlas")
        zf.writestr("Plant_4K_Billboard_Opacity.jpg", b"billboard")
        zf.writestr("Plant_4K_Opacity.jpg", b"mesh atlas")
    with ZipFile(path) as zf:
        maps = select_maps(zf)
        assert maps["normal"].filename == "Plant_4K_Normal.jpg"
        assert maps["opacity"].filename == "Plant_4K_Opacity.jpg"


def test_only_drops_revoked_previous_assets(tmp_path):
    setup_source(tmp_path)
    assert prepare(tmp_path)["items"]["test"]["status"] == "ready"
    path = tmp_path / "tools/worldgen/fab/review.json"
    review = json.loads(path.read_text())
    review["items"]["test"]["status"] = "rejected"
    path.write_text(json.dumps(review))
    result = prepare(tmp_path, only={"other"})["items"]["test"]
    assert result["status"] == "rejected" and not result["textures"] and not result["models"]


def test_only_drops_missing_previous_sources(tmp_path):
    archive = setup_source(tmp_path)
    prepare(tmp_path)
    archive.unlink()
    assert prepare(tmp_path, only={"other"})["items"]["test"]["status"] == "missing"


def test_source_path_outside_fab_rejected(tmp_path):
    setup_source(tmp_path)
    path = tmp_path / "Data/SourceManifests/fab-megascans-2026-11-10.json"
    manifest = json.loads(path.read_text())
    manifest["items"][0]["file"] = "../source.zip"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="inside Data/raw/fab"):
        prepare(tmp_path)


def test_output_symlink_rejected(tmp_path):
    setup_source(tmp_path)
    target = tmp_path / "outside"
    target.mkdir()
    output = tmp_path / OUTPUT
    output.parent.mkdir(parents=True)
    try:
        output.symlink_to(target, target_is_directory=True)
    except OSError:
        if os.name != "nt":
            pytest.skip("OS requires symlink privilege")
        # A directory junction needs no Developer Mode/admin permission.
        command = "New-Item -ItemType Junction -Path '" + str(output).replace("'", "''") + "' -Target '" + str(target).replace("'", "''") + "' | Out-Null"
        subprocess.run(["powershell", "-NoProfile", "-Command", command], check=True, capture_output=True)
    with pytest.raises(ValueError, match="symlink/junction"):
        prepare(tmp_path)
    assert not list(target.iterdir())


def test_red_only_scalar_source_is_not_luminance(tmp_path):
    archive = setup_source(tmp_path)
    red = tmp_path / "red.png"
    Image.new("RGB", (256, 256), (255, 0, 0)).save(red)
    with ZipFile(archive, "a") as zf:
        for name in ("Opacity", "Roughness", "AO"):
            zf.write(red, f"test_4K_{name}.png")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    for path in (tmp_path / "Data/SourceManifests/fab-megascans-2026-11-10.json",
                 tmp_path / "tools/worldgen/fab/review.json"):
        data = json.loads(path.read_text())
        if isinstance(data["items"], list):
            data["items"][0]["sha256"] = digest
        else:
            data["items"]["test"]["source_sha256"] = digest
        path.write_text(json.dumps(data))
    textures = prepare(tmp_path)["items"]["test"]["textures"]["Low"]
    for name in ("opacity", "roughness", "ao"):
        with Image.open(tmp_path / textures[name]) as image:
            assert image.getextrema() == (255, 255)
    with Image.open(tmp_path / textures["basecolor"]) as image:
        assert image.getextrema()[3] == (255, 255)


def test_plant_source_lods_keep_true_geometry_and_billboard_separate(tmp_path):
    path = tmp_path / "plant.zip"
    with ZipFile(path, "w") as zf:
        for variant in ("VarA", "VarB"):
            for lod in range(4):
                zf.writestr(f"Boxwood_{variant}_LOD{lod}.fbx", f"{variant} sourceLOD{lod}")
    with ZipFile(path) as zf:
        models = _meshes(zf, tmp_path / "generated", "boxwood", first_variant_only=True)
    assert len(models) == 1
    assert models[0]["variant"] == "VarA"
    assert models[0]["source"].read_text() == "VarA sourceLOD2"
    assert models[0]["billboard_source"].read_text() == "VarA sourceLOD3"


def test_exported_glb_parent_transform_fails_before_ready(tmp_path):
    document = {"nodes": [{"mesh": 0, "scale": [0.01, 0.01, 0.01]}]}
    payload = json.dumps(document).encode()
    payload += b" " * (-len(payload) % 4)
    glb = tmp_path / "parent-transform.glb"
    glb.write_bytes(struct.pack("<4sII", b"glTF", 2, 20 + len(payload))
                    + struct.pack("<I4s", len(payload), b"JSON") + payload)
    with pytest.raises(ValueError, match="transforms must be baked"):
        sync_glb_textures(glb, {}, tmp_path)


def test_single_plane_far_foliage_rejected():
    with pytest.raises(ValueError, match="nonzero"):
        validate_crossed_billboard([[-1, 0, 0], [1, 0, 0], [1, 2, 0], [-1, 2, 0]],
                                  [0, 1, 2, 0, 2, 3])


def test_crossed_billboard_covers_both_yaw_directions():
    validate_crossed_billboard([[-1, 0, 0], [1, 0, 0], [1, 2, 0], [-1, 2, 0],
                               [0, 0, -1], [0, 0, 1], [0, 2, 1], [0, 2, -1]],
                              [0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7])


def test_simplified_billboard_cannot_float_above_ground():
    with pytest.raises(ValueError, match="ground base"):
        validate_crossed_billboard([[-1, .02, 0], [1, .02, 0], [1, 2, 0], [-1, 2, 0],
                                   [0, .02, -1], [0, .02, 1], [0, 2, 1], [0, 2, -1]],
                                  [0, 1, 2, 0, 2, 3, 4, 5, 6, 4, 6, 7])
