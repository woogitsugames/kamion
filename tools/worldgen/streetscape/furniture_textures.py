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
    concrete = kind in ("concrete", "footing")
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
    # ADR0120: retain concrete scan relief instead of compressing it to nearly white.
    level, grain = (228, 1.05) if kind == "concrete" else ((245, 1.05) if kind == "footing" else (245, 0.3))
    rgb = np.repeat((level * (1 + grain * (ratio - 1)))[..., None], 3, axis=2)
    z = (1 - (np.arange(h) + 0.5) / h)[:, None]
    u = (np.arange(w) + 0.5)[None, :] / w
    height = 0.9 if kind == "bollard" else 9.0
    # Salt / road splash at the foot; asymmetric dirt, no all-over random noise.
    foot = np.clip(1 - z * height / (0.65 if concrete else 0.30), 0, 1)
    foot = foot * (0.65 + 0.35 * np.sin(u * 2 * np.pi + 0.7) ** 2)
    dirt = np.array([133, 126, 109]) if concrete else np.array([157, 112, 77])
    # Galvanised poles get road film, painted steel gets small rust islands at the ground line.
    if kind == "galv":
        dirt = np.array([162, 157, 140])
    islands = np.clip((ratio - 0.94) * 8, 0, 1) if not concrete else np.ones((h, w))
    mask = foot * (0.35 + 0.65 * islands)
    if kind == "footing":
        # A shallow concrete cap is not the salt-soaked bottom of a nine-metre pole (review I3).
        mask *= 0.12
    rgb = rgb * (1 - mask[..., None]) + dirt * mask[..., None]
    if kind in ("grey", "bollard"):
        # One torn, unbranded paper remnant on the rear sector, with no text or invented logo.
        paper = (u > 0.63) & (u < 0.78) & (z * height > 0.63) & (z * height < 0.76)
        rgb[paper] = (211, 207, 184)
    if kind == "concrete":
        # Dirt runs below the two steel arm collars; no uniform all-over noise.
        metres = z * height
        runoff = np.zeros((h, w))
        for collar, sector in ((7.6, 0.22), (8.3, 0.73)):
            below = collar - metres
            streak = np.exp(-((u-sector) / 0.055) ** 2)
            streak = streak * np.clip(below / 0.12, 0, 1) * np.clip(1-below / 2.6, 0, 1)
            runoff = np.maximum(runoff, streak * 0.28)
        rgb = rgb * (1-runoff[..., None]) + np.array([125, 117, 99]) * runoff[..., None]
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")


def textures():
    return {**{f"furniture_{k}": pole_texture(k) for k in ("galv", "grey", "concrete", "bollard", "footing")},
            "furniture_plinth": plinth_texture()}


def plinth_texture():
    """CC0 scan modulation, mean 0.5 linear. The 1 m grain tile is WORKING_VALUE.

    Lighting is removed from the source; the surface shader applies the existing concrete pigment once.
    Dirt height/strength belongs to marked board geometry, never to unmarked gates or noise walls.
    """
    raw = ROOT / "art-source/world/cc0/_raw/brushed_concrete/brushed_concrete_diff_2k.jpg"
    if raw.exists():
        im = np.asarray(Image.open(raw).convert("RGB").resize((256, 256), Image.Resampling.LANCZOS), float)
        lum = im.mean(axis=2)
        ratio = np.clip(lum / np.maximum(gaussian_filter(lum, 16), 1), 0.65, 1.35)
        ratio /= ratio.mean()
    else:
        warnings.warn("ADR0120 concrete scan missing; neutral plinth fallback", stacklevel=2)
        ratio = np.ones((256, 256))
    linear = np.clip(0.5 * ratio, 0, 1)
    srgb = np.where(linear <= 0.0031308, linear * 12.92, 1.055 * linear ** (1/2.4) - 0.055)
    rgb = np.repeat(np.round(srgb * 255).astype(np.uint8)[..., None], 3, axis=2)
    return Image.fromarray(rgb, "RGB")
