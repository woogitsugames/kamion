"""Optional Fab photographic detail on our generated tree tubes / Polish kerb geometry.

No downloaded geometry or leaf claim: Linden Branch is a woody branch, Pine Bark is
an atlas of loose bark, and neither is a source of tree foliage. Their existing
foliage / pine-trunk materials remain the fallback. Run before region import:
    uv run --project tools/worldgen tools/worldgen/fab_tree_surfaces.py

All outputs (including the routing manifest) stay in the ignored Fab output root.
Crop coordinates, colour targets and blend weights are reviewed WORKING_VALUEs;
they are not a claim about scan texel density or measured Podlasie bark albedo.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
from pathlib import Path
import zipfile

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
GENERATED = Path("art-source/world/megascans/_generated")
SOURCE_MANIFEST = Path("Data/SourceManifests/fab-megascans-2026-11-10.json")
CHANNELS = {"basecolor": "BaseColor", "normal": "Normal", "roughness": "Roughness", "ao": "AO"}
# Crop coordinates normalised in the actual 4096 maps, chosen after visual review
# to omit atlas gutters, ground litter, cut branch ends and blurred UV padding.
RECIPES = {
    "bark_birch": {"sources": [("silver-birch-bark", (0, 0, 1, 1), .85),
                                 ("birch-tree-trunk", (.07, .10, .39, .83), .15)],
                   "target_srgb": [176, 173, 164]},
    "bark_linden": {"sources": [("linden-branch", (.35, .38, .49, .88), 1.0)],
                    "target_srgb": [84, 78, 70]},
    "curb_concrete": {"sources": [("street-curbs", (.12, .12, .85, .27), .65),
                                    ("modular-curb", (.12, .74, .88, .83), .35)],
                      "target_srgb": [144, 143, 141]},
}


def srgb_to_linear(c):
    return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= .0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - .055)


def pack_metallic_gloss(roughness):
    """URP Lit: nonmetallic RGB, linear smoothness in A (inverse roughness)."""
    roughness = np.clip(np.asarray(roughness), 0, 255).astype(np.uint8)
    packed = np.zeros((*roughness.shape, 4), np.uint8)
    packed[..., 3] = 255 - roughness
    return packed


def stitch_edges(a, width=16):
    """Blend opposite borders symmetrically, preserving the interior scan detail."""
    a = a.copy()
    for axis in (0, 1):
        n = min(width, a.shape[axis] // 4)
        for k in range(n):
            left, right = [slice(None)] * a.ndim, [slice(None)] * a.ndim
            left[axis], right[axis] = k, -1 - k
            left, right = tuple(left), tuple(right)
            x, y = a[left].copy(), a[right].copy()
            w = .5 * (1 - k / n)
            a[left], a[right] = x * (1 - w) + y * w, y * (1 - w) + x * w
    return a


def load_crop(archive: Path, channel: str, crop, size: int):
    """Read only the selected image; never extract an archive to disk."""
    with zipfile.ZipFile(archive) as z:
        suffix = "_" + CHANNELS[channel].lower() + ".jpg"
        names = sorted(n for n in z.namelist() if n.lower().endswith(suffix))
        if len(names) != 1:
            raise ValueError(f"{archive.name}: expected exactly one {channel} map")
        member = z.getinfo(names[0])
        if member.file_size > 128 * 1024 * 1024:
            raise ValueError("oversized source image")
        with Image.open(io.BytesIO(z.read(member))) as image:
            mode = "RGB" if channel in ("basecolor", "normal") else "L"
            w, h = image.size
            bounds = tuple(round(c * (w if k % 2 == 0 else h)) for k, c in enumerate(crop))
            image = image.convert(mode).crop(bounds).resize((size, size), Image.Resampling.LANCZOS)
            return np.asarray(image, np.float32) / 255


def build(root: Path = ROOT):
    root = root.resolve()
    out = root / GENERATED
    # A junction to a tracked art directory must never turn ignored output into
    # overwrites of the original public / CC0 textures.
    if out.resolve() != out.absolute():
        raise ValueError("Fab generated output must not be a symlink or junction")
    source = json.loads((root / SOURCE_MANIFEST).read_text(encoding="utf-8"))
    entries = {i["id"]: i for i in source["items"]}
    review_path = root / "tools/worldgen/fab/review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))["items"] if review_path.exists() else {}
    result = {"schema": 1, "license": "Fab Standard License", "materials": {},
              "not_used": {"pine-bark": "loose bark atlas, not pine trunk",
                           "linden-leaves": "no leaves in Linden Branch source; procedural leaves retained"}}
    verified = {}
    for name, recipe in RECIPES.items():
        ids = [s[0] for s in recipe["sources"]]
        available = True
        for aid in ids:
            item, r = entries[aid], review.get(aid, {})
            p = root / item["file"]
            if r.get("status") != "approved" or r.get("source_sha256") != item["sha256"] or not p.is_file():
                available = False
                break
            if aid not in verified:
                with p.open("rb") as stream:
                    verified[aid] = hashlib.file_digest(stream, "sha256").hexdigest()
            if verified[aid] != item["sha256"]:
                raise ValueError(f"{aid}: archive SHA256 mismatch")
        if not available:
            logging.warning("[Fab] %s unavailable or unreviewed; original material retained", name)
            continue
        record = {"sources": [{"id": aid, "sha256": entries[aid]["sha256"],
                                "crop_uv": list(crop), "weight": weight}
                               for aid, crop, weight in recipe["sources"]],
                  "texture_scale": "WORKING_VALUE; existing procedural UV and kerb mesh retained",
                  "normal_convention": "UNVERIFIED; map retained as supplied, require directional-light review before enabling",
                  "textures": {}}
        for tier, size in (("Low", 512), ("High", 1024)):
            textures = {}
            for channel in CHANNELS:
                arrays = [load_crop(root / entries[aid]["file"], channel, crop, size) * weight
                          for aid, crop, weight in recipe["sources"]]
                a = sum(arrays)
                if channel == "basecolor":
                    a = srgb_to_linear(a)
                    target = srgb_to_linear(np.asarray(recipe["target_srgb"], np.float32) / 255)
                    a *= target / np.maximum(a.mean((0, 1)), .001)
                    a = linear_to_srgb(a)
                a = stitch_edges(a)
                if channel == "normal":
                    n = a * 2 - 1
                    n /= np.maximum(np.linalg.norm(n, axis=2, keepdims=True), .001)
                    a = n * .5 + .5
                path = out / "surfaces" / name / tier / (channel + ".png")
                path.parent.mkdir(parents=True, exist_ok=True)
                Image.fromarray(np.round(np.clip(a, 0, 1) * 255).astype(np.uint8)).save(path, optimize=True)
                textures[channel] = path.relative_to(root).as_posix()
                if channel == "roughness":
                    packed = pack_metallic_gloss(np.round(np.clip(a, 0, 1) * 255))
                    packed_path = path.with_name("metallic_gloss.png")
                    Image.fromarray(packed).save(packed_path, optimize=True)
                    textures["metallic_gloss"] = packed_path.relative_to(root).as_posix()
            record["textures"][tier] = textures
        result["materials"][name] = record
    out.mkdir(parents=True, exist_ok=True)
    (out / "surfaces_manifest.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps({"materials": sorted(build(args.root)["materials"])}))
