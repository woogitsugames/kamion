"""Pack reviewed optional Fab road utilities into one mobile material (ADR 0084).

    uv run --project tools/worldgen tools/worldgen/fab/drainage_atlas.py

Products and routing metadata remain in the ignored licensed generated directory.
Each fixed 2x2 cell has a dilated gutter (8 px Low / 16 px High), omitted
from its UV rect. Proportional gutters preserve shared geometry UVs across tiers.
PNG rows run top-down; exported UV rectangles use glTF's bottom-up mesh UVs.
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fab.prepare import ROOT, OUTPUT, MANIFEST, _no_links, _source_path, read_review, sha256

IDS = ("metal-manhole-cover", "round-drain-cover", "square-rusty-drain")
CHANNELS = {"basecolor": ("RGBA", (0, 0, 0, 0)),
            "metallic_gloss": ("RGBA", (0, 0, 0, 0)), "ao": ("L", 255)}
PADDING = 8


def _input(root, name):
    path = root / name
    _no_links(path)
    if not path.resolve().is_relative_to((root / OUTPUT).resolve()):
        raise ValueError("atlas inputs must be in the ignored Fab output root")
    return path


def uv_rect(slot, maximum, padding=PADDING):
    cell = maximum // 2
    x, y = (slot % 2) * cell, (slot // 2) * cell
    return [(x + padding) / maximum, 1 - (y + cell - padding) / maximum,
            (x + cell - padding) / maximum, 1 - (y + padding) / maximum]


def _tile(image, mode, cell, padding):
    inner = cell - 2 * padding
    image = image.convert(mode)
    # Pillow's RGBA resize premultiplies RGB by A. For packed metal/smoothness
    # channels A is data, and even uniform transparent albedo can shift by a byte.
    # Resize each channel independently to preserve both contracts.
    bands = [band.resize((inner, inner), Image.Resampling.LANCZOS) for band in image.split()]
    image = Image.merge(mode, bands)
    a = np.asarray(image)
    pad_width = ((padding, padding), (padding, padding)) + (((0, 0),) if a.ndim == 3 else ())
    return Image.fromarray(np.pad(a, pad_width, mode="edge"))


def build(root=ROOT):
    root = Path(root).resolve()
    out = root / OUTPUT
    _no_links(out)
    result = {"schema": 1, "license": "Fab Standard License", "materials": {}}
    source = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
    pins = {item["id"]: item for item in source["items"]}
    reviews = read_review(root)
    prepared_path = out / "manifest.json"
    _no_links(prepared_path)
    prepared = json.loads(prepared_path.read_text(encoding="utf-8")) if prepared_path.exists() else {"items": {}}
    selected = {}
    for aid in IDS:
        item, review = pins.get(aid, {}), reviews.get(aid, {})
        asset = prepared.get("items", {}).get(aid, {})
        expected = item.get("sha256")
        if not expected or review.get("status") != "approved" or review.get("source_sha256") != expected:
            continue
        archive = _source_path(root, item["file"])
        if not archive.is_file() or asset.get("status") != "ready" or asset.get("source_sha256") != expected:
            continue
        if sha256(archive) != expected:
            raise ValueError(f"Fab atlas source SHA256 mismatch: {aid}")
        textures = asset.get("textures", {})
        names = [textures.get(tier, {}).get(channel)
                 for tier in ("Low", "High") for channel in CHANNELS]
        if not all(isinstance(name, str) and name and _input(root, name).is_file() for name in names):
            continue
        # Detect changed prepared inputs instead of silently baking unprovenanced maps.
        provenance = {p["path"]: p["sha256"] for p in asset.get("provenance", [])}
        for tier in ("Low", "High"):
            for channel in CHANNELS:
                name = textures[tier][channel]
                if name not in provenance or sha256(_input(root, name)) != provenance[name]:
                    raise ValueError(f"Fab atlas prepared input SHA256 mismatch: {aid}/{tier}/{channel}")
        selected[aid] = textures
    if not selected:
        logging.warning("[Fab] no reviewed drainage maps available; original road utility materials retained")
    else:
        material = {"sources": [{"id": aid, "sha256": pins[aid]["sha256"]} for aid in selected],
                    "textures": {}, "uv_rects": {}, "uv_rects_by_tier": {},
                    "padding_px_by_tier": {"Low": 8, "High": 16}, "provenance": []}
        for tier, maximum in (("Low", 512), ("High", 1024)):
            material["textures"][tier] = {}
            padding = PADDING * maximum // 512
            rects = {aid: uv_rect(IDS.index(aid), maximum, padding) for aid in selected}
            material["uv_rects_by_tier"][tier] = rects
            # World geometry serves Low + High: use the Low-safe rect everywhere.
            # Proportional High gutters retain those same UVs.
            if tier == "Low": material["uv_rects"] = rects
            for channel, (mode, background) in CHANNELS.items():
                atlas = Image.new(mode, (maximum, maximum), background)
                for aid, textures in selected.items():
                    with Image.open(_input(root, textures[tier][channel])) as image:
                        tile = _tile(image, mode, maximum // 2, padding)
                    slot = IDS.index(aid)
                    atlas.paste(tile, ((slot % 2) * maximum // 2, (slot // 2) * maximum // 2))
                path = out / "drainage_atlas" / tier / (channel + ".png")
                _no_links(path)
                path.parent.mkdir(parents=True, exist_ok=True)
                atlas.save(path, optimize=True)
                name = path.relative_to(root).as_posix()
                material["textures"][tier][channel] = name
                material["provenance"].append({"path": name, "sha256": sha256(path)})
        result["materials"]["fab_drainage"] = material
    out.mkdir(parents=True, exist_ok=True)
    path = out / "drainage_atlas_manifest.json"
    _no_links(path)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps({"materials": sorted(build(args.root)["materials"])}))
