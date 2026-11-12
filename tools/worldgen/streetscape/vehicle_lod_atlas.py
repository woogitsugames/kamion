"""ADR 0153: two-submesh parked vehicles; geometry and near paint remain unchanged.

The second submesh uses an authored material palette atlas with the baseline
linear albedo and effective metallic/smoothness, including fictional plates
and the existing refrigeration-grille stripe pattern.
No external images, brands or scan assets are introduced.
"""
from pathlib import Path

import numpy as np
from PIL import Image

PREFIXES = ("car_", "van_", "tractor_", "trailer_")
NAME = "vehicle_lod_details"
SIZE = (1024, 512)
# Stable layout independent of prototype iteration order; 64 px padded solid cells.
DETAILS = (
    "car_glass", "car_lamp", "car_light_head", "car_light_tail", "car_sill", "car_trim",
    "reefer_grille", "reefer_unit", "rim", "rim_dark", "rim_dusty", "rim_steel",
    "trailer_alu", "trailer_chassis", "trailer_doors", "trailer_front", "trailer_front_dark",
    "tyre", "tyre_dusty",
)


def primary(name):
    if name.startswith("car_"):
        return "car_paint_" + name.rsplit("_", 1)[1]
    if name.startswith("van_"):
        return "car_paint_" + name.split("_", 1)[1]
    if name.startswith("tractor_"):
        return "tractor_paint_" + name.split("_", 1)[1]
    if name.startswith("trailer_curtain_"):
        from .life_props import CURTAIN_COLOURS
        return "trailer_curtain_" + CURTAIN_COLOURS[int(name.rsplit("_", 1)[1])]
    if name.startswith(("trailer_box_", "trailer_reefer_")):
        return "trailer_box_white"
    raise ValueError(name)


def center(material):
    k = DETAILS.index(material)
    return np.array([(k % 16 * 64 + 32) / SIZE[0], (k // 16 * 64 + 32) / SIZE[1]])


def consolidate(prims, name):
    if not name.startswith(PREFIXES):
        return prims
    keep = primary(name)
    out, parts = [], []
    for p in prims:
        if p["mat"] == keep:
            out.append(p)
            continue
        q = dict(p)
        if p["mat"] == "car_plate":
            uv = np.asarray(p["UV"], float)
            # Plate rectangle, with 8 px of edge extension. v=0 is image bottom.
            q["UV"] = np.column_stack([(8 + uv[:, 0] * 1008) / 1024,
                                         (264 + uv[:, 1] * 240) / 512])
        elif p["mat"] == "reefer_grille":
            # Source physical rectangle: life_props.trailer, 1.68 x .78 m.
            uv = np.asarray(p["UV"], float)
            q["UV"] = np.column_stack([(8 + uv[:, 0] / 1.68 * 1008) / 1024,
                                         (136 + uv[:, 1] / .78 * 112) / 512])
        else:
            q["UV"] = np.broadcast_to(center(p["mat"]), (len(p["V"]), 2)).copy()
        parts.append(q)
    if parts:
        merged = {"mat": NAME}
        for attr in ("V", "N", "UV"):
            merged[attr] = np.concatenate([p[attr] for p in parts])
        offsets = np.cumsum([0] + [len(p["V"]) for p in parts[:-1]])
        merged["T"] = np.concatenate([p["T"] + off for p, off in zip(parts, offsets)])
        out.append(merged)
    return out


def generate(root=None, texture_dir=None):
    from .materials import M
    from .life_cars import plate_atlas
    root = Path(root) if root else Path(__file__).resolve().parents[3]
    dest = Path(texture_dir) if texture_dir is not None else root / "art-source/world/textures"
    dest.mkdir(parents=True, exist_ok=True)
    base = np.zeros((512, 1024, 3), np.uint8)
    mask = np.zeros((512, 1024, 4), np.uint8)
    mask[:, :, 1] = 255
    for k, material in enumerate(DETAILS):
        definition = M[material]
        linear = np.asarray(definition["color"], float)
        srgb = np.where(linear <= .0031308, 12.92 * linear, 1.055 * linear ** (1 / 2.4) - .055)
        x, y = k % 16 * 64, 512 - (k // 16 + 1) * 64
        base[y:y + 64, x:x + 64] = np.round(srgb * 255).astype(np.uint8)
        # Preserve the *effective* baseline: LookDevAssets.WorldMaterial uses
        # dielectric World Surface for ordinary materials with metal <= .5.
        metal = definition.get("metal", 0)
        mask[y:y + 64, x:x + 64] = [round((metal if metal > .5 else 0) * 255), 255, 0,
                                         round((1 - definition["rough"]) * 255)]
    # Extend the plate border into the padding so filtering never reaches a black texel.
    plates = np.asarray(plate_atlas().resize((1008, 240), Image.Resampling.LANCZOS))
    base[:256] = np.pad(plates, ((8, 8), (8, 8), (0, 0)), mode="edge")
    mask[:256] = [0, 255, 0, round((1 - M["car_plate"]["rough"]) * 255)]
    # WorldPbrMaterials.Stripes(louvre_slats), WorldPBR _STRIPES: 60 mm pitch,
    # half dark gap / half light slat; source shader overrides smoothness to .45.
    v = .78 * (1 - (np.arange(112) + .5) / 112)
    phase = np.mod(v / .06, 1)
    bright = np.abs(phase - .5) >= .25
    linear = np.where(bright[:, None], [.085, .088, .09], [.012, .012, .012])
    srgb = np.where(linear <= .0031308, 12.92 * linear, 1.055 * linear ** (1 / 2.4) - .055)
    grille = np.broadcast_to(np.round(srgb * 255).astype(np.uint8)[:, None, :], (112, 1008, 3))
    base[256:384] = np.pad(grille, ((8, 8), (8, 8), (0, 0)), mode="edge")
    mask[256:384] = [0, 255, 0, round(.45 * 255)]
    Image.fromarray(base).save(dest / f"{NAME}_BaseColor.png")
    Image.fromarray(mask).save(dest / f"{NAME}_MaskMap.png")
    return dest
