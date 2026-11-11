"""ADR 0102: CC0 microstructure + authored, height-localised wear; no extra material slots.

Atlas v=0 is the ground contact, v=1 the pole top. Mapillary remains reference-only.
Physical wear heights are WORKING_VALUE. Scans/licences: existing cc0_manifest.json (ADR 0063).
"""
from pathlib import Path
import warnings

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

ROOT = Path(__file__).resolve().parents[3]


def pole_texture(kind):
    concrete = kind == "concrete"
    aid = "brushed_concrete" if concrete else "corrugated_iron_03"
    raw = ROOT / "art-source/world/cc0/_raw" / aid / f"{aid}_diff_2k.jpg"
    w, h = 256, 512
    if raw.exists():
        photo = np.asarray(Image.open(raw).convert("RGB").resize((w, h), Image.Resampling.LANCZOS), float)
        lum = photo.mean(axis=2)
        # Remove large lighting / corrugation: the pole must not acquire sheet-metal ribs.
        ratio = np.clip(lum / np.maximum(gaussian_filter(lum, 12), 1), 0.8, 1.2)
        if not concrete:
            # Corrugation survives a spatial high-pass. Remove its persistent column profile too; a round pole
            # must keep the scan grain without acquiring the source sheet's vertical ribs (close-up review r1).
            ratio = np.clip(ratio / np.maximum(np.median(ratio, axis=0, keepdims=True), 0.01), 0.8, 1.2)
    else:
        warnings.warn(f"ADR0102 scan missing: {aid}; flat furniture texture fallback", stacklevel=2)
        ratio = np.ones((h, w))
    rgb = np.repeat((245 * (1 + 0.3 * (ratio - 1)))[..., None], 3, axis=2)
    z = (1 - (np.arange(h) + 0.5) / h)[:, None]
    u = (np.arange(w) + 0.5)[None, :] / w
    height = 0.9 if kind == "bollard" else 9.0
    # Salt / road splash at the foot; asymmetric dirt, no all-over random noise.
    foot = np.clip(1 - z * height / (0.22 if concrete else 0.30), 0, 1)
    foot = foot * (0.65 + 0.35 * np.sin(u * 2 * np.pi + 0.7) ** 2)
    dirt = np.array([133, 126, 109]) if concrete else np.array([157, 112, 77])
    # Galvanised poles get road film, painted steel gets small rust islands at the ground line.
    if kind == "galv":
        dirt = np.array([162, 157, 140])
    islands = np.clip((ratio - 0.94) * 8, 0, 1) if not concrete else np.ones((h, w))
    mask = foot * (0.35 + 0.65 * islands)
    rgb = rgb * (1 - mask[..., None]) + dirt * mask[..., None]
    if kind in ("grey", "bollard"):
        # One torn, unbranded paper remnant on the rear sector, with no text or invented logo.
        paper = (u > 0.63) & (u < 0.78) & (z * height > 0.63) & (z * height < 0.76)
        rgb[paper] = (211, 207, 184)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")


def textures():
    return {f"furniture_{k}": pole_texture(k) for k in ("galv", "grey", "concrete", "bollard")}
