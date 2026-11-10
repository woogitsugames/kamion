"""Photographic surface crop processing: fallback and output isolation."""
import hashlib
import json
from pathlib import Path
import zipfile

import numpy as np
from PIL import Image
import pytest

import fab_tree_surfaces as fab


def fixture_root(tmp_path, approve=True):
    items, reviews = [], {}
    for aid in {s[0] for r in fab.RECIPES.values() for s in r["sources"]}:
        file = tmp_path / f"Data/raw/fab/{aid}/source.zip"
        file.parent.mkdir(parents=True)
        with zipfile.ZipFile(file, "w") as z:
            for channel, label in fab.CHANNELS.items():
                png = tmp_path / "temp.jpg"
                Image.new("RGB", (32, 32), (120, 100, 80)).save(png)
                z.write(png, "source_4K_" + label + ".jpg")
        sha = hashlib.sha256(file.read_bytes()).hexdigest()
        items.append({"id": aid, "file": file.relative_to(tmp_path).as_posix(), "sha256": sha})
        reviews[aid] = {"status": "approved" if approve else "pending", "source_sha256": sha}
    manifest = tmp_path / fab.SOURCE_MANIFEST
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps({"items": items}))
    review = tmp_path / "tools/worldgen/fab/review.json"
    review.parent.mkdir(parents=True)
    review.write_text(json.dumps({"items": reviews}))
    return items


def test_pending_or_missing_sources_keep_originals(tmp_path, caplog):
    fixture_root(tmp_path, approve=False)
    result = fab.build(tmp_path)
    assert result["materials"] == {}
    assert not list((tmp_path / fab.GENERATED).rglob("*.png"))
    assert "original material retained" in caplog.text


def test_outputs_mobile_sizes_and_generated_only(tmp_path):
    fixture_root(tmp_path)
    result = fab.build(tmp_path)
    assert set(result["materials"]) == {"bark_birch", "bark_linden", "curb_concrete"}
    for material in result["materials"].values():
        for tier, size in (("Low", 512), ("High", 1024)):
            for path in material["textures"][tier].values():
                assert path.startswith(fab.GENERATED.as_posix() + "/")
                with Image.open(tmp_path / path) as image:
                    assert image.size == (size, size)
    assert "linden-leaves" in result["not_used"]
    paths = result["materials"]["curb_concrete"]["textures"]["Low"]
    with Image.open(tmp_path / paths["roughness"]) as image:
        roughness = np.asarray(image)
    with Image.open(tmp_path / paths["metallic_gloss"]) as image:
        packed = np.asarray(image)
    assert packed.shape == (512, 512, 4)
    assert not np.any(packed[..., :3])
    np.testing.assert_array_equal(packed[..., 3], 255 - roughness)


def test_urp_metallic_gloss_encodes_smoothness_endpoints():
    packed = fab.pack_metallic_gloss(np.array([[0, 127, 255]], dtype=np.uint8))
    np.testing.assert_array_equal(packed[..., 3], [[255, 128, 0]])
    assert not np.any(packed[..., :3])


def test_archive_digest_failure(tmp_path):
    items = fixture_root(tmp_path)
    with (tmp_path / items[0]["file"]).open("ab") as f:
        f.write(b"tampered")
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        fab.build(tmp_path)


def test_stitch_preserves_interior_and_matches_boundaries():
    a = np.random.default_rng(1).uniform(size=(128, 128, 3))
    b = fab.stitch_edges(a)
    np.testing.assert_allclose(b[0], b[-1])
    np.testing.assert_allclose(b[:, 0], b[:, -1])
    np.testing.assert_array_equal(b[16:-16, 16:-16], a[16:-16, 16:-16])
