"""Build all world-C ground PBR sets into art-source/world/materials/<set>/<tier>/ and materials_spec.json.

Run (from the repo root; uses the worldgen venv only for numpy/scipy/pillow, does not touch tools/worldgen):
    uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py
        [--tier High,Medium,Low] [--only set_a,set_b] [--photo <path>]
Outputs are not versioned (art-source/world/materials/.gitignore); see README.md. Deterministic: fixed seeds,
periodic FFT noise, no time-dependent input, numpy/scipy/pillow pinned by tools/worldgen/uv.lock.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pbrkit as K  # noqa: E402
import sets_asphalt as A  # noqa: E402
import sets_other as O  # noqa: E402
import sets_facade as F  # noqa: E402
import sets_scan as SC  # noqa: E402
import sets_viaduct as V  # noqa: E402

OUT = HERE.parent
REPO = OUT.parents[2]
DEFAULT_PHOTO = REPO / "Data" / "photos" / "nowe" / "Worn_cracked_asphalt_pavement.jpg"   # owner set, not versioned

SRC_ALB = ("'Cool Pavements' review, arXiv:2409.12242 (https://arxiv.org/abs/2409.12242), p. 7: new asphalt "
           "concrete ~0.05, rising with ageing and soiling to ~0.15; Portland cement concrete up to 0.35, soiled "
           "~0.2 within weeks/months. Broadband solar albedo, not visible-band: the texture means are "
           "WORKING_VALUE placed inside those ranges")

# ASTC block per tier and map (bits per pixel: 4x4=8, 5x5=5.12, 6x6=3.56, 8x8=2.0)
ASTC = {"High": {"BaseColor": "6x6", "Normal": "5x5", "MaskMap": "6x6", "Var": "8x8"},
        "Medium": {"BaseColor": "6x6", "Normal": "6x6", "MaskMap": "8x8", "Var": "8x8"},
        "Low": {"BaseColor": "8x8", "Normal": "8x8", "MaskMap": "8x8", "Var": "8x8"}}
BPP = {"4x4": 8.0, "5x5": 5.12, "6x6": 3.56, "8x8": 2.0}

SETS = {
    "asphalt_sma_fresh": dict(fn=A.sma_fresh, tile_m=[4.0, 4.0], target=0.075, uv="world_xy_planar",
        slots=["road_asphalt (sections resurfaced recently: proposed material road_asphalt_new)"],
        note="SMA 11 wearing course a few months in service: binder film still on the chips, slight sheen."),
    "asphalt_worn": dict(fn=A.worn, tile_m=[4.0, 4.0], target=0.08, uv="world_xy_planar",
        slots=["road_asphalt", "yard_asphalt", "path_asphalt"],
        note="Aged AC 11 (albedo 0.08, was 0.13; paint/asphalt contrast, ADR 0049 addendum r7): exposed light aggregate, ravelling sockets, dust in voids, low-contrast hairline "
             "micro-cracking only. Distinct cracks come from asphalt_cracks_layer (16 m) so this 4 m base has "
             "no recognisable features."),
    "asphalt_patch": dict(fn=A.patch, tile_m=[4.0, 4.0], target=0.062, uv="world_xy_planar",
        slots=["decal_patch"],
        note="Newer AC 8 patch fill, darker than the road around it (fresh binder, 0.05 class). The decal's "
             "TEXCOORD_1.x (age 0..1) should lerp albedo toward asphalt_worn and smoothness down."),
    "concrete_cast_5m_joints": dict(fn=O.concrete_cast, tile_m=[10.0, 10.0], target=0.30, uv="world_xy_planar",
        slots=["yard_concrete", "road_concrete", "bridge_concrete"],
        note="5 x 5 m cast slabs, 8 mm sawn joints with bitumen sealant (open stretches with dirt), broom "
             "finish, worn exposed sand, one corner break and one transverse crack per 10 m tile. Var.G = "
             "slab id. Joint lines are world-aligned: for road_concrete they need along-road UV (UV1)."),
    "concrete_slab_3x1.5": dict(fn=O.concrete_jomb, tile_m=[6.0, 6.0], target=0.27, uv="world_xy_planar",
        slots=["yard_slabs"],
        note="Precast road plates 3.0 x 1.5 m ('JOMB' type), rows with irregular offsets, 12-32 mm soil "
             "joints (some with grass), worn arrises, settlement steps up to +-6 mm, lifting-socket notches. "
             "Albedo mean measured on plates only (joints excluded)."),
    "kerb_concrete_1m": dict(fn=O.kerb, tile_m=[2.0, 0.5], target=0.28, uv="mesh_uv0_metres (u along, v across)",
        slots=["curb_concrete"],
        note="Precast kerb units 1.0 m (PN-EN 1340 kerb 15x30), mortar joints, chipped arrises. Tile 2 m x "
             "0.5 m, non-square texture (2048x512 High). Aged, grime-darkened kerb (0.28 after photo comparison with Rondo Bieżeństwa; 0.33 read as white lines)."),
    "behaton_i_grey": dict(fn=O.behaton, tile_m=[4.0, 4.0], target=0.23, uv="world_xy_planar",
        slots=["yard_behaton"],
        note="I-shaped (double-T) interlocking 8 cm blocks 200 x 166 mm, waist 120 mm (WORKING_VALUE), rows "
             "offset half a block, 3-4 mm sand joints with moss away from traffic. Var.G = block id: the "
             "shader should add hash(block id + world tile index) tone jitter so the 4 m tile never repeats."),
    "paving_20x10_grey": dict(fn=O.rect_paving, tile_m=[4.0, 4.0], target=0.26, uv="world_xy_planar",
        slots=["sidewalk_paving", "yard_paving", "road_paving"],
        note="Rectangular 200 x 100 mm 'holland' blocks, running bond, 4-shade grey melange. Var.G = block id "
             "(same anti-repeat trick as behaton)."),
    "grass_verge": dict(fn=O.grass_verge, tile_m=[3.0, 3.0], target=0.095, uv="world_xy_planar",
        slots=["verge_grass", "terrain_grass"],
        note="Mown verge from above (z-buffered blades, 2x supersampled): tufts, thatch, bare soil, plantain/"
             "dandelion rosettes, clover. Extra albedo BaseColor_late_autumn (olive-brown; REVIEW r3 W10). "
             "Var.B = bare soil (more mud near kerbs via COLOR_0 masks)."),
    "gravel_compacted": dict(fn=O.gravel, tile_m=[3.0, 3.0], target=0.20, uv="world_xy_planar",
        slots=["shoulder_gravel", "road_gravel", "yard_gravel"],
        note="Compacted crushed stone 0-31.5 mm: two stone sizes half-buried in fines and dust."),
    "oil_stain_alpha": dict(fn=A.oil_atlas, tile_m=[2.0, 2.0], target=None, uv="decal_radial_uv0_atlas_2x2",
        slots=["decal_oil"],
        note="2x2 atlas, one stain per cell in the decal's radial UV (centre 0.5/0.5): 0 drip pool, 1 tyre "
             "smear (elongated, for yards), 2 old faded ring, 3 drip cluster. Cell = floor(seed*4) from "
             "TEXCOORD_1.y; BaseColor.a = opacity; cell borders fade to 0 so mips do not bleed."),
}

SETS.update(V.VIADUCT_SETS)      # hero viaduct strip atlas (ADR 0067)

LAYERS = {
    "asphalt_cracks_layer": dict(tile_m=[16.0, 16.0], uv="world_xy_planar",
        slots=["overlay on road_asphalt / yard_asphalt / path_asphalt (not on asphalt_sma_fresh)"],
        note="Mask: R open crack coverage (crack 1-5 mm, meandering, branched, broken into 2-12 m runs), "
             "G sealant band 25-40 mm (glossy bitumen, smoothness ~0.55, albedo ~0.03), B alligator zone, "
             "A ravelled halo. Normal: crack/sealant relief, blend with RNM/whiteout. Suggested: albedo *= "
             "lerp(1, 0.35, R) then lerp to 0.03 by G; smoothness lerp to 0.55 by G; scale R by a per-road "
             "age factor and by macro B so whole stretches can be crack-free (REVIEW r2 #5, r3 W8)."),
    "macro_variation": dict(tile_m=[64.0, 64.0], uv="world_xy_planar (sample twice: 64 m and 64 m x 4.13 "
                            "rotated, as Kamion/World Surface does)",
        slots=["_MacroMap of every ground material"],
        note="R 8-64 m tone, G 2-16 m tone (both drop-in for the current _MacroMap R/G), B wear/dirt "
             "patches 1.5-24 m, A 0.5-4 m mottling. All centred on 0.5, linear (import sRGB off)."),
    "parapet_runoff": dict(tile_m=[24.0, 4.0], uv="mesh_uv1 (u metres along the wall, v = 1 + metres below the "
                           "attic fascia / length scale; v < 0.5 = no wall-top data)",
        slots=["_RunoffMap of hall_wall_* (keyword _RUNOFF, buildings_mesh.py hall walls)"],
        note="Run-off streaks under the parapet coping of halls (zacieki pod attyka): R soot/dirt, G rust, linear. "
             "Long streaks below coping-sheet joints every 2-3 m, fine drip lines, broad smudges, uneven dirty "
             "band under the drip edge; fades to 0 at 4 m. One RGB sample on wall pixels, all tiers (Low 256x40). "
             "Look WORKING_VALUE (photo-judged, no measurements)."),
    "asphalt_detail_photo": dict(tile_m=[1.0, 1.0], uv="world_xy_planar x1 (close-range detail, fade out "
                                 "beyond ~25 m)",
        slots=["URP-style detail albedo + detail normal on asphalt_worn, asphalt_patch, asphalt_sma_fresh"],
        note="From the public-domain photo Worn_cracked_asphalt_pavement.jpg (John Harvey, Wikimedia "
             "Commons): crack-free crop, luminance high-pass, contrast-normalised, made tileable "
             "(variance-preserving offset blend). DetailAlbedo follows URP: albedo *= tex * "
             "unity_ColorSpaceDouble, so sRGB 128 = neutral (x1.0), range ~x0.75..x1.3. Scale ~0.9 mm/px "
             "estimated from the aggregate size: WORKING_VALUE."),
}


def astc_bytes(res, block):
    return res[0] * res[1] * BPP[block] / 8 * 4 / 3   # with mips


def gpu_estimate(files_info, tier, kind_map=None):
    tot = 0.0
    for f in files_info["files"]:
        kind = next((k for k in ("BaseColor", "Normal", "MaskMap", "Var") if f"_{k}" in f), "Var")
        tot += astc_bytes(files_info["res"], ASTC[tier][kind])
    return tot


TIERS_SEL = list(K.TIERS)


def build_cracks(spec):
    c, mask, h = A.cracks_layer()
    out = OUT / "asphalt_cracks_layer"
    info = {"files": {}}
    n_hi = K.normals_from_height(h, c.px)
    for t, f in K.TIERS.items():
        if t not in TIERS_SEL:
            continue
        d = out / t
        m = K.down(mask, f)
        hh = K.down(h, f)
        K.save_png(d / "T_asphalt_cracks_layer_Mask.png", m, "RGBA")
        K.save_png(d / "T_asphalt_cracks_layer_Normal.png", K.normals_from_height(hh, c.px * f) * 0.5 + 0.5, "RGB")
        files = sorted(p.name for p in d.glob("*.png"))
        info["files"][t] = {"res": [c.nx // f, c.ny // f], "texel_mm": round(c.px * f * 1000, 2),
                            "dir": f"asphalt_cracks_layer/{t}", "files": files,
                            "png_bytes": sum((d / p).stat().st_size for p in files),
                            "astc": {"Mask": ASTC[t]["MaskMap"], "Normal": ASTC[t]["Normal"]}}
        info["files"][t]["gpu_bytes_astc_mips"] = int(
            astc_bytes(info["files"][t]["res"], ASTC[t]["MaskMap"]) + astc_bytes(info["files"][t]["res"], ASTC[t]["Normal"]))
    info["coverage"] = {"open_crack": round(float(mask[..., 0].mean()), 5), "sealant": round(float(mask[..., 1].mean()), 5),
                        "alligator_zone": round(float(mask[..., 2].mean()), 4)}
    return info


def build_macro():
    c, m = O.macro()
    out = OUT / "macro_variation"
    info = {"files": {}}
    for t, f in K.TIERS.items():
        if t not in TIERS_SEL:
            continue
        d = out / t
        mm = K.down(m, f)
        K.save_png(d / "T_macro_variation.png", mm, "RGBA")
        files = ["T_macro_variation.png"]
        res = [c.nx // f, c.ny // f]
        info["files"][t] = {"res": res, "texel_mm": round(c.px * f * 1000, 1), "dir": f"macro_variation/{t}",
                            "files": files, "png_bytes": (d / files[0]).stat().st_size,
                            "gpu_bytes_astc_mips": int(astc_bytes(res, "8x8")), "astc": {"Macro": "8x8"}}
    return info


def build_runoff():
    c, m = F.parapet_runoff()
    out = OUT / "parapet_runoff"
    info = {"files": {}}
    for t, f in K.TIERS.items():
        if t not in TIERS_SEL:
            continue
        d = out / t
        K.save_png(d / "T_parapet_runoff.png", K.down(m, f), "RGB")
        files = ["T_parapet_runoff.png"]
        res = [c.nx // f, c.ny // f]
        info["files"][t] = {"res": res, "texel_mm": round(c.px * f * 1000, 1), "dir": f"parapet_runoff/{t}",
                            "files": files, "png_bytes": (d / files[0]).stat().st_size,
                            "gpu_bytes_astc_mips": int(astc_bytes(res, "6x6")), "astc": {"Macro": "6x6"}}
    info["coverage"] = {"soot_mean": round(float(m[..., 0].mean()), 4), "rust_mean": round(float(m[..., 1].mean()), 4)}
    return info


def build_detail(photo: Path):
    if not photo.exists():
        print(f"  SKIP asphalt_detail_photo: source photo not found ({photo}); pass --photo", flush=True)
        return None
    hp = O.asphalt_detail_photo(photo)
    out = OUT / "asphalt_detail_photo"
    info = {"files": {}, "source_photo": "Data/photos/nowe/Worn_cracked_asphalt_pavement.jpg (public domain)"}
    mult = np.exp(0.13 * np.clip(hp, -2.5, 2.5))
    tex_lin = np.clip(mult / 4.594794, 0, 1)                       # unity_ColorSpaceDouble (linear)
    height = 0.45e-3 * hp                                            # lighter = stone top = higher
    px = 1.0 / hp.shape[0]
    for t, f in (("High", 1), ("Medium", 2)):
        if t not in TIERS_SEL:
            continue
        d = out / t
        K.save_png(d / "T_asphalt_detail_photo_DetailAlbedo.png", K.srgb_encode(K.down(tex_lin, f)), "L")
        K.save_png(d / "T_asphalt_detail_photo_DetailNormal.png",
                   K.normals_from_height(K.down(height, f), px * f) * 0.5 + 0.5, "RGB")
        files = sorted(p.name for p in d.glob("*.png"))
        res = [hp.shape[1] // f, hp.shape[0] // f]
        info["files"][t] = {"res": res, "texel_mm": round(px * f * 1000, 2), "dir": f"asphalt_detail_photo/{t}",
                            "files": files, "png_bytes": sum((d / p).stat().st_size for p in files),
                            "gpu_bytes_astc_mips": int(astc_bytes(res, "6x6") * 2),
                            "astc": {"DetailAlbedo": "6x6", "DetailNormal": "6x6"}}
    info["note_low"] = "Low tier: no detail layer (bandwidth); the base sets alone."
    return info


def _scan_entry(entry: dict, s, scan: bool):
    """Spec fields of a scan-based set: real tile size (scans keep their physical size) and provenance."""
    entry.pop("source", None)
    if not scan:
        return
    if (s.scan_info or {}).get("mode", "").startswith("hybrid"):
        entry["tile_m"] = [round(s.c.Lx, 4), round(s.c.Ly, 4)] if entry.get("tile_m") is None else entry["tile_m"]
    else:
        entry["tile_m"] = [round(s.c.Lx, 4), round(s.c.Ly, 4)]
    entry["source"] = s.scan_info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", type=Path, default=DEFAULT_PHOTO)
    ap.add_argument("--only", default="")
    ap.add_argument("--tier", default="High,Medium,Low", help="comma list of High,Medium,Low")
    ap.add_argument("--procedural", action="store_true",
                    help="ignore the CC0 scans (ADR 0063) and build the purely procedural sets (A/B comparison)")
    a = ap.parse_args()
    import time
    t_all = time.perf_counter()
    TIERS_SEL[:] = [t for t in a.tier.split(",") if t in K.TIERS]
    only = set(filter(None, a.only.split(",")))
    spec_path = OUT / "materials_spec.json"
    old = {}
    if spec_path.exists():
        import json
        old = json.loads(spec_path.read_text(encoding="utf-8"))
    sets = dict(old.get("sets", {}))
    for name, meta in SETS.items():
        if only and name not in only:
            continue
        print("set", name, flush=True)
        t0 = time.perf_counter()
        s = None if a.procedural else SC.build(name)
        scan = s is not None
        s = s or meta["fn"]()
        s.name = name
        info = K.write_set(s, OUT, tiers=TIERS_SEL)
        print(f"  {time.perf_counter() - t0:.1f} s", flush=True)
        for t, fi in info["files"].items():
            fi["astc"] = ASTC[t]
            fi["gpu_bytes_astc_mips"] = int(gpu_estimate(fi, t))
        entry = {k: v for k, v in meta.items() if k != "fn"}
        entry["kind"] = "decal_atlas" if s.alpha is not None else "tiling_set"
        entry["albedo_target_mean_lum_linear"] = meta["target"]
        _scan_entry(entry, s, scan)
        entry.update(info)
        if hasattr(s, "source"):            # sets with an external CC0 base (sets_viaduct)
            entry["source"] = s.source
            entry["concrete_mean_rgb_linear"] = s.concrete_mean
            V.write_layout()
        sets[name] = entry
    for name, meta in F.FACADE_SETS.items():
        if only and name not in only:
            continue
        print("facade set", name, flush=True)
        t0 = time.perf_counter()
        s = None if a.procedural else SC.build(name)
        scan = s is not None
        s = s or meta["fn"]()
        s.name = name
        info = K.write_set(s, OUT, tiers=TIERS_SEL)
        print(f"  {time.perf_counter() - t0:.1f} s", flush=True)
        for t, fi in info["files"].items():
            fi["astc"] = ASTC[t]
            fi["gpu_bytes_astc_mips"] = int(gpu_estimate(fi, t))
        entry = {k: v for k, v in meta.items() if k != "fn"}
        entry["uv"] = "mesh_uv0_metres (u along, v up)"
        entry["kind"] = "modulation_set"
        entry["albedo_target_mean_lum_linear"] = F.MOD_MEAN
        _scan_entry(entry, s, scan)
        entry.update(info)
        sets[name] = entry
    for name, meta in SC.SCAN_ONLY_META.items():
        if a.procedural or (only and name not in only):
            continue
        s = SC.build(name)
        if s is None:
            print(f"  SKIP {name}: scans not fetched (cc0_fetch.py)", flush=True)
            continue
        print("scan-only set", name, flush=True)
        info = K.write_set(s, OUT, tiers=TIERS_SEL)
        for t, fi in info["files"].items():
            fi["astc"] = ASTC[t]
            fi["gpu_bytes_astc_mips"] = int(gpu_estimate(fi, t))
        entry = {"tile_m": None, "slots": meta["slots"], "note": meta["note"], "uv": meta["uv"], "kind": meta["kind"],
                 "albedo_target_mean_lum_linear": meta["target"]}
        _scan_entry(entry, s, True)
        entry.update(info)
        sets[name] = entry
    for name, meta in LAYERS.items():
        if only and name not in only:
            continue
        print("layer", name, flush=True)
        info = {"asphalt_cracks_layer": lambda: build_cracks(None), "macro_variation": build_macro,
                "asphalt_detail_photo": lambda: build_detail(a.photo),
                "parapet_runoff": build_runoff}[name]()
        if info is None:
            continue
        entry = dict(meta)
        entry["kind"] = "layer"
        entry.update(info)
        sets[name] = entry
    spec = {
        "schema": "kamion.world.materials/1",
        "generator": "art-source/world/materials/_src/build_all.py (pbrkit.py, sets_asphalt.py, sets_other.py, sets_facade.py)",
        "conventions": {
            "units": "metres; tile_m = world size of one texture repeat",
            "BaseColor": "sRGB, linear albedo calibrated (Rec.709 luminance mean = albedo_target_mean_lum_linear); "
                         "kind modulation_set: neutral map with mean 0.5, engine albedo = 2 x manifest colour x map",
            "Normal": "tangent space, OpenGL (+Y = +v), Unity/glTF convention; import as Normal map",
            "MaskMap": "URP Lit: R metallic, G occlusion, B detail mask, A smoothness; import sRGB off",
            "Var": "R height normalised over height_range_m, G per-element random id (block/slab/chip; point "
                   "sampled, never averaged), B joint/crack/bare mask (water, dirt, weeds), A convexity/edge "
                   "wear; import sRGB off, mip filter box",
            "tiers": "High = generated resolution (2048 for square sets), Medium = /2, Low = /4, box-filtered "
                     "from High in linear space; smoothness per tier gets the normal variance lost by the "
                     "downsample (Toksvig-style) so distant surfaces do not sparkle",
            "mipmaps": "Unity-generated, Kaiser filter for BaseColor; aniso 4 (Medium) / 8 (High); hf_ratio_"
                       "albedo = share of albedo variance above half Nyquist (shimmer risk; values in each set entry)",
            "anti_tiling": "(1) macro_variation at 64 m and 264 m rotated (existing shader path); (2) Var.G "
                           "element id + world tile index hash -> per-element tone jitter (paving, slabs); "
                           "(3) distinct features (cracks, sealant) only in the 16 m crack layer, faded by "
                           "macro B; (4) optional second base sample at x2.71 scale on High",
            "albedo_source": SRC_ALB,
            "grass_albedo_source": "WORKING_VALUE (visible-band albedo of mown grass; no measured source in "
                                   "repo)",
            "cc0_scans": "ADR 0063: sets with a `source` entry are built from CC0 scans (Poly Haven, manifest "
                         "art-source/world/cc0/cc0_manifest.json, processing _src/sets_scan.py): de-lit, flattened "
                         "above ~1 m, white-balanced to the previous set mean and calibrated to the same target; "
                         "height integrated from the scan normals; isotropic scans re-assembled (texture bombing) "
                         "into 4 m tiles; hybrids keep the procedural layout and take the scan micro-detail",
        },
        "sets": dict(sorted(sets.items())),
    }
    K.dump_json(spec_path, spec)
    print("wrote", spec_path, f"total {time.perf_counter() - t_all:.0f} s")


if __name__ == "__main__":
    main()
