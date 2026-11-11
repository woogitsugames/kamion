"""Bake a local Fab grass photobase into the existing world grass material slot.

No download and no runtime geometry/shader change. All pixels stay in ignored
_generated; a missing licence-reviewed source or Blender retains the old grass.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import random
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fab.prepare import ROOT, OUTPUT, MANIFEST, _no_links, _source_path, sha256, read_review

LOG = logging.getLogger("fab.grass_surface")
TARGET = [0.08, 0.105, 0.038]  # WORKING_VALUE: preserve existing grass palette.
TILE_M = 4.0
SEED = 84
CLUMP_COUNT = 256


def periodic_plan(seed=SEED, count=CLUMP_COUNT, tile_m=TILE_M, radius_m=0.5):
    """Deterministic clump positions plus only required wrapped border copies."""
    rng = random.Random(seed)
    result = []
    half = tile_m / 2
    for index in range(count):
        x, y, yaw = rng.uniform(-half, half), rng.uniform(-half, half), rng.uniform(0, 2 * math.pi)
        dx = [0] + ([tile_m] if x - radius_m < -half else []) + ([-tile_m] if x + radius_m > half else [])
        dy = [0] + ([tile_m] if y - radius_m < -half else []) + ([-tile_m] if y + radius_m > half else [])
        for sx in dx:
            for sy in dy:
                result.append({"index": index, "x": x + sx, "y": y + sy, "yaw": yaw,
                               "wrapped": bool(sx or sy)})
    return result


def _linear(rgb):
    rgb = np.asarray(rgb, dtype=np.float64) / 255
    return np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)


def finish_tile(source: Path, destination: Path, maximum: int):
    """Small periodic seam stitch + palette calibration in linear light."""
    with Image.open(source) as original:
        image = original.convert("RGB")
        image.thumbnail((maximum, maximum), Image.Resampling.LANCZOS)
    pixels = _linear(image)
    seam = max(1, maximum // 128)
    for i in range(seam):
        # Same opposite-edge pixels guarantee the 4 m wrap is continuous.
        pair = (pixels[:, i] + pixels[:, -1 - i]) / 2
        pixels[:, i] = pair
        pixels[:, -1 - i] = pair
        pair = (pixels[i] + pixels[-1 - i]) / 2
        pixels[i] = pair
        pixels[-1 - i] = pair
    source_mean = pixels.mean(axis=(0, 1))
    gains = []
    for channel, target in enumerate(TARGET):
        values = pixels[:, :, channel]
        gain = target / max(float(values.mean()), 1e-8)
        if abs(float(np.clip(values * gain, 0, 1).mean()) - target) > 1e-7:
            lo, hi = 0., max(1., gain)
            while np.clip(values * hi, 0, 1).mean() < target:
                hi *= 2
            for _ in range(25):
                mid = (lo + hi) / 2
                if np.clip(values * mid, 0, 1).mean() < target:
                    lo = mid
                else:
                    hi = mid
            gain = (lo + hi) / 2
        gains.append(float(gain))
    scaled = pixels * np.asarray(gains)
    clipped = float(np.any(scaled > 1, axis=2).mean())
    calibrated = np.clip(scaled, 0, 1)
    encoded = np.where(calibrated <= .0031308, calibrated * 12.92,
                       1.055 * calibrated ** (1 / 2.4) - .055)
    rgb = np.clip(np.rint(encoded * 255), 0, 255).astype(np.uint8)
    _no_links(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgb).save(destination)
    return {"source_mean_linear_rgb": source_mean.tolist(), "gain_linear_rgb": gains,
            "target_mean_linear_rgb": TARGET, "target_status": "WORKING_VALUE",
            "achieved_mean_linear_rgb": _linear(rgb).mean(axis=(0, 1)).tolist(),
            "clipped_pixel_fraction": clipped, "seam_stitch_pixels": seam,
            "max_size": maximum, "opaque": True}


def bake(root=ROOT, blender=None):
    root = Path(root).resolve()
    out = root / OUTPUT
    _no_links(out)
    folder = out / "grass_surface"
    _no_links(folder)
    if folder.exists():
        for existing in folder.rglob("*"):
            _no_links(existing)
    manifest_path = out / "grass_surface_manifest.json"
    _no_links(manifest_path)
    report = {"schema": 1, "materials": {}, "status": "fallback"}
    def fallback(reason):
        LOG.warning("Fab grass surface: %s; existing grass fallback retained", reason)
        report["reason"] = reason
        out.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report
    if not blender or not Path(blender).is_file():
        return fallback("Blender unavailable")
    source_manifest = root / MANIFEST
    prepared_path = out / "manifest.json"
    _no_links(prepared_path)
    if not source_manifest.exists() or not prepared_path.exists():
        return fallback("Fab inputs/prepared manifest unavailable")
    item = next((a for a in json.loads(source_manifest.read_text(encoding="utf-8"))["items"] if a["id"] == "grass-clumps"), None)
    if not item:
        return fallback("grass-clumps not in acquisition manifest")
    review = read_review(root).get("grass-clumps", {})
    source = _source_path(root, item["file"])
    if review.get("status") != "approved" or review.get("source_sha256") != item["sha256"]:
        return fallback("grass-clumps review not currently approved")
    if not source.is_file() or sha256(source) != item["sha256"]:
        return fallback("grass-clumps ZIP missing or hash mismatch")
    prepared = json.loads(prepared_path.read_text(encoding="utf-8"))["items"].get("grass-clumps", {})
    if prepared.get("status") != "ready" or prepared.get("source_sha256") != item["sha256"] or not prepared.get("models"):
        return fallback("prepared grass-clumps is not ready/current")
    model = prepared["models"][0]
    relative_model = model["path"]
    basecolor = prepared["textures"]["High"]["basecolor"]
    for relative in (relative_model, basecolor):
        candidate = root / relative
        if not candidate.resolve().is_relative_to(out):
            raise ValueError("Fab grass surface input must stay inside ignored _generated")
        _no_links(candidate)
        if not candidate.is_file():
            return fallback("prepared mesh/basecolor missing")
        expected = next((p["sha256"] for p in prepared.get("provenance", []) if p["path"] == relative), None)
        if not expected or sha256(candidate) != expected:
            return fallback("prepared mesh/basecolor provenance hash mismatch")
    folder.mkdir(parents=True, exist_ok=True)
    plan = periodic_plan()
    raw = folder / "source_topdown.png"
    request = {"mesh": str(root / relative_model), "prototype": "fab_grass_clumps",
               "basecolor": str(root / basecolor), "output": str(raw), "tile_m": TILE_M,
               "resolution": 1024, "floor_linear_rgb": TARGET, "instances": plan}
    request_path = folder / "request.json"
    request_path.write_text(json.dumps(request, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    command = [str(blender), "-b", "--factory-startup", "--python-exit-code", "1", "-P",
               str(root / "tools/blender/world/fab_grass_surface.py"), "--", str(request_path)]
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (folder / "blender.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    if completed.returncode:
        raise subprocess.CalledProcessError(completed.returncode, command, output=completed.stdout, stderr=completed.stderr)
    record = {"sources": [{"id": "grass-clumps", "sha256": item["sha256"]}],
              "textures": {}, "tile_m": [4, 4], "calibration": {}, "provenance": [],
              "method": "Emissive scan baseColor+alpha top-down periodic geometry; no baked lighting/shadows",
              "seed": SEED, "primary_clumps": CLUMP_COUNT, "rendered_clumps_including_wrap": len(plan),
              "prepared_model_sha256": sha256(root / relative_model)}
    for tier, size in (("Low", 512), ("High", 1024)):
        path = folder / tier / "basecolor.png"
        _no_links(path)
        record["calibration"][tier] = finish_tile(raw, path, size)
        rel = path.relative_to(root).as_posix()
        record["textures"][tier] = {"basecolor": rel}
        record["provenance"].append({"path": rel, "sha256": sha256(path)})
    report.update(status="ready", materials={"terrain_grass": record, "verge_grass": record})
    manifest_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blender", type=Path)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(bake(blender=args.blender), sort_keys=True))


if __name__ == "__main__":
    main()
