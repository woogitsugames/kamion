"""The drainage atlas keeps licensed inputs local and preserves alpha / data."""
import json

import numpy as np
from PIL import Image
import pytest

from fab import drainage_atlas as atlas


def make_root(root):
    sources, reviews, prepared = [], {}, {}
    for k, aid in enumerate(atlas.IDS):
        archive = root / f"Data/raw/fab/{aid}/source.zip"
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_bytes((aid + "synthetic archive pin").encode())
        digest = atlas.sha256(archive)
        sources.append({"id": aid, "file": archive.relative_to(root).as_posix(), "sha256": digest})
        reviews[aid] = {"status": "approved", "source_sha256": digest}
        item = {"status": "ready", "source_sha256": digest, "textures": {}, "provenance": []}
        prepared[aid] = item
        for tier in ("Low", "High"):
            item["textures"][tier] = {}
            for channel, (mode, _) in atlas.CHANNELS.items():
                path = root / atlas.OUTPUT / aid / tier / (channel + ".png")
                path.parent.mkdir(parents=True, exist_ok=True)
                color = (40 + k * 30, 50 + k * 30, 60 + k * 30, 100 + k * 30) if mode == "RGBA" else 50 + k * 30
                Image.new(mode, (64, 64), color).save(path)
                name = path.relative_to(root).as_posix()
                item["textures"][tier][channel] = name
                item["provenance"].append({"path": name, "sha256": atlas.sha256(path)})
    for path, data in ((root / atlas.MANIFEST, {"items": sources}),
                       (root / "tools/worldgen/fab/review.json", {"items": reviews}),
                       (root / atlas.OUTPUT / "manifest.json", {"items": prepared})):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
    return prepared


def test_atlas_uses_one_material_and_same_uv_all_tiers(tmp_path):
    make_root(tmp_path)
    result = atlas.build(tmp_path)
    assert list(result["materials"]) == ["fab_drainage"]
    material = result["materials"]["fab_drainage"]
    assert material["uv_rects"] == material["uv_rects_by_tier"]["Low"] == material["uv_rects_by_tier"]["High"]
    # The first image is in the upper left, expressed in bottom-up UV coordinates.
    assert material["uv_rects"][atlas.IDS[0]] == [8/512, 264/512, 248/512, 504/512]
    for tier, size in (("Low", 512), ("High", 1024)):
        paths = material["textures"][tier]
        for channel, path in paths.items():
            assert path.startswith(atlas.OUTPUT.as_posix() + "/")
            with Image.open(tmp_path / path) as image:
                assert image.size == (size, size)
                if channel == "basecolor":
                    assert image.mode == "RGBA"
                    a = np.asarray(image)
                    for k in range(3):
                        x, y = k % 2 * size // 2, k // 2 * size // 2
                        # Dilated gutter and cell interior keep source RGBA.
                        np.testing.assert_array_equal(a[y, x], [40+k*30, 50+k*30, 60+k*30, 100+k*30])
                    assert not a[-1, -1].any()


def test_revoked_approval_is_excluded_and_empty_clone_falls_back(tmp_path, caplog):
    make_root(tmp_path)
    review_path = tmp_path / "tools/worldgen/fab/review.json"
    reviews = json.loads(review_path.read_text())
    for item in reviews["items"].values(): item["status"] = "rejected"
    review_path.write_text(json.dumps(reviews))
    assert atlas.build(tmp_path)["materials"] == {}
    assert "original road utility materials retained" in caplog.text
    (tmp_path / atlas.OUTPUT / "manifest.json").unlink()
    assert atlas.build(tmp_path)["materials"] == {}


def test_atlas_rejects_modified_prepared_input(tmp_path):
    prepared = make_root(tmp_path)
    path = tmp_path / prepared[atlas.IDS[0]]["textures"]["Low"]["basecolor"]
    Image.new("RGBA", (64, 64), (255, 0, 0, 255)).save(path)
    with pytest.raises(ValueError, match="prepared input SHA256 mismatch"):
        atlas.build(tmp_path)


def test_partial_prepared_maps_are_skipped(tmp_path):
    make_root(tmp_path)
    path = tmp_path / atlas.OUTPUT / "manifest.json"
    data = json.loads(path.read_text())
    for item in data["items"].values(): del item["textures"]["Low"]["ao"]
    path.write_text(json.dumps(data))
    assert atlas.build(tmp_path)["materials"] == {}


def test_atlas_rejects_input_outside_generated(tmp_path):
    make_root(tmp_path)
    path = tmp_path / atlas.OUTPUT / "manifest.json"
    data = json.loads(path.read_text())
    data["items"][atlas.IDS[0]]["textures"]["Low"]["basecolor"] = "docs/LICENSES.md"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="ignored Fab output root"):
        atlas.build(tmp_path)
