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
        with Image.open(raw) as original:
            if kind == "concrete":
                # The CC0 tile covers 2.5 m, whereas this atlas spans a complete 9 m shaft.
                # Stretching the full square scan over it turned concrete into long wood-like fibres.
                # Crop/repeat at metric scale; circumference is the mean of our working pole taper.
                circumference_m = np.pi * (.15 + .07)
                tile = original.convert("RGB").resize((512, 512), Image.Resampling.LANCZOS)
                tile_height = int(np.ceil(9 / 2.5 * 512))
                repeated = Image.new("RGB", (512, int(np.ceil(tile_height / 512)) * 512))
                for row in range(0, repeated.height, 512):
                    repeated.paste(tile, (0, row))
                metric = repeated.crop((0, 0, int(round(circumference_m / 2.5 * 512)), tile_height))
                photo = np.asarray(metric.resize((w, h), Image.Resampling.LANCZOS), float)
            else:
                photo = np.asarray(original.convert("RGB").resize((w, h), Image.Resampling.LANCZOS), float)
        lum = photo.mean(axis=2)
        # Remove large lighting / corrugation: the pole must not acquire sheet-metal ribs.
        sigma = (.04 * h / 9, .04 * w / circumference_m) if kind == "concrete" else 12
        ratio = np.clip(lum / np.maximum(gaussian_filter(lum, sigma), 1), 0.8, 1.2)
        if kind == "concrete":
            # Close the cropped cylindrical seam over a small sector, retaining the scan grain.
            for edge in range(8):
                left, right = ratio[:, edge].copy(), ratio[:, -1-edge].copy()
                blend = 1-edge/8
                mean = (left+right)/2
                ratio[:, edge] = left*(1-blend)+mean*blend
                ratio[:, -1-edge] = right*(1-blend)+mean*blend
        if not concrete:
            # Corrugation survives a spatial high-pass. Remove its persistent column profile too; a round pole
            # must keep the scan grain without acquiring the source sheet's vertical ribs (close-up review r1).
            ratio = np.clip(ratio / np.maximum(np.median(ratio, axis=0, keepdims=True), 0.01), 0.8, 1.2)
    else:
        warnings.warn(f"ADR0102 scan missing: {aid}; flat furniture texture fallback", stacklevel=2)
        ratio = np.ones((h, w))
    # ADR0120: retain concrete scan relief instead of compressing it to nearly white.
    level, grain = (228, 0.65) if kind == "concrete" else ((245, 1.05) if kind == "footing" else (245, 0.3))
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
    if kind == "concrete":
        mask *= .5           # translucent road film, avoiding an almost black band around the shaft
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
    out = {**{f"furniture_{k}": pole_texture(k) for k in ("galv", "grey", "concrete", "bollard", "footing")},
           "furniture_plinth": plinth_texture()}
    out["furniture_galv"] = _galv_grey_base(out["furniture_galv"])      # ADR 0162
    out["bus_shelter_atlas"] = shelter_atlas()                          # ADR 0162
    return out


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


# ------------------------------------------------------------------ ADR 0162: BKM shelter atlas
# sRGB of the RAL colours: public conversion tables, approximate (the documents name the RAL codes only, research G5
# section 5) -> WORKING_VALUE. RAL 3020 traffic red, graphite of the older black shelters, light-brown stained bench
# slats ("bejcowane i lakierowane na jasny brąz"), D-15 blue of signs.BLUE.
RAL3020_SRGB = (204, 6, 5)
RAL1012_SRGB = (199, 180, 70)
SHELTER_GRAPHITE_SRGB = (38, 40, 42)
SHELTER_WOOD_SRGB = (150, 104, 62)


def shelter_atlas():
    """512 x 512 sRGB atlas of the BKM shelter (props.SHELTER_UV*; v up = image rows from the bottom):
    top band: flat swatches red / graphite / wood / grey with low-contrast powder-coat grain; below it the blue
    information board (a plain field with a white keyline - no operator logo, no invented stop text); left middle a
    printed timetable sheet (columns of fine grey rows, our own pattern); right middle the D-15 rack face after BKM
    zał. 07c typ A/B (white name field, D-15 bus symbol, number slots) - our own drawing."""
    from PIL import ImageDraw
    from . import signs as SG
    n = 512
    rng = np.random.default_rng(162)
    im = Image.new("RGB", (n, n), RAL3020_SRGB)
    a = np.asarray(im, float).copy()
    grain = gaussian_filter(rng.normal(0, 1, (n, n)), 1.2)
    for k, c in enumerate((RAL3020_SRGB, SHELTER_GRAPHITE_SRGB, SHELTER_WOOD_SRGB, (150, 152, 152))):
        x0, x1 = k * n // 4, (k + 1) * n // 4
        amp = 10.0 if k == 2 else 4.0
        a[: n // 8, x0:x1] = np.clip(np.array(c, float)[None, None, :] * (1 + grain[: n // 8, x0:x1, None] * amp / 255 * 3),
                                     0, 255)
    # spare area below the pictures keeps the red swatch (filtered borders of the red never bleed into another colour)
    im = Image.fromarray(a.astype(np.uint8), "RGB")
    d = ImageDraw.Draw(im)

    def rows(v0, v1):
        return int(round((1 - v1) * n)), int(round((1 - v0) * n))

    # information board (v 0.76 .. 0.86)
    r0, r1 = rows(0.76, 0.86)
    d.rectangle([0, r0, n - 1, r1], fill=SG.BLUE)
    d.rectangle([3, r0 + 4, n - 4, r1 - 4], outline=SG.WHITE, width=2)
    # timetable sheet (u 0.02 .. 0.48, v 0.27 .. 0.73)
    t0, t1 = rows(0.27, 0.73)
    c0, c1 = int(0.02 * n), int(0.48 * n)
    d.rectangle([c0, t0, c1, t1], fill=(236, 236, 230))
    d.rectangle([c0 + 6, t0 + 8, c1 - 6, t0 + 22], fill=(60, 60, 64))          # header bar
    cols = 3
    cw = (c1 - c0 - 16) / cols
    for ci in range(cols):
        x0 = c0 + 8 + ci * cw
        y = t0 + 30
        while y < t1 - 10:
            w = cw * (0.55 + 0.35 * rng.random())
            d.line([(x0 + 2, y), (x0 + w, y)], fill=(120, 120, 124), width=2)
            y += 6 if rng.random() > 0.15 else 11
    d.rectangle([c0, t0, c1, t1], outline=(205, 205, 200), width=2)
    # D-15 rack face (u 0.53 .. 0.87, v 0.25 .. 0.75)
    f0, f1 = rows(0.25, 0.75)
    u0, u1 = int(0.53 * n), int(0.87 * n)
    d.rectangle([u0, f0, u1, f1], fill=RAL3020_SRGB)
    inner = [u0 + 6, f0 + 6, u1 - 6, f1 - 6]
    d.rectangle(inner, fill=SG.BLUE)
    hname = int((f1 - f0) * 0.2)
    d.rectangle([inner[0] + 4, inner[1] + 4, inner[2] - 4, inner[1] + hname], fill=SG.WHITE)
    d.line([(inner[0] + 4, inner[1] + hname * 0.55), (inner[2] - 4, inner[1] + hname * 0.55)], fill=SG.BLUE, width=2)
    sym = SG.face("D-15")[1].resize((int((inner[2] - inner[0]) * 0.66),) * 2, Image.LANCZOS)
    im.paste(sym.convert("RGB"), (inner[0] + 4, inner[1] + hname + 10), sym.split()[3])
    sx = inner[0] + 8 + sym.size[0]
    for k in range(5):
        y = inner[1] + hname + 12 + k * (sym.size[1] / 5)
        d.rounded_rectangle([sx, y, inner[2] - 6, y + sym.size[1] / 5 - 6], radius=3, fill=SG.WHITE)
    return im


def _galv_grey_base(im):
    """ADR 0162: ZDM PFU - the lowest ~0.3 m of a lighting column painted grey (research G5-010, SOURCED; shade of
    grey UNVERIFIED). Drawn into the galv atlas (v = metres / 9): an even matt band with a crisp top edge, the road
    film of the foot stays on top of it."""
    a = np.asarray(im, float).copy()
    h = a.shape[0]
    z = (1 - (np.arange(h) + 0.5) / h) * 9.0
    band = (z <= 0.30)[:, None]
    grey = np.array([112.0, 114.0, 114.0])
    foot = np.clip(1 - z / 0.30, 0, 1)[:, None, None] * 0.25
    paint = grey * (1 - foot) + np.array([150.0, 140.0, 120.0]) * foot
    a = np.where(band[..., None], paint * (0.97 + 0.03 * (a / 255.0)), a)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")
