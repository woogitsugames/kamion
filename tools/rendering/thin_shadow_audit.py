"""ADR 0240: audit which instanced prop prototypes are too thin for the main-light shadow map of a tier.

Pomiar z danych (bez Unity): dla LOD0 kazdego prototypu z `street_props.glb` rzutuje geometrie na ziemie wzdluz
kierunku slonca, rasteryzuje sylwetke cienia co 1 cm i liczy
  - bbox [m] (to samo, co `Mesh.bounds.size` w Unity - wejscie reguly `ThinShadowCasterPolicy`),
  - srednia szerokosc cienia w = 2 * pole / obwod [m] (pret: srednica; plyta: mniejszy wymiar),
  - udzial pola, ktory przezywa erozje o `normalBias * texel` z kazdej strony (to robi URP ApplyShadowBias na
    krawedzi sylwetki, gdzie N jest prostopadla do L),
  - udzial pola o lokalnej szerokosci >= 2 texele (otwarcie morfologiczne) = "rozdzielane przez mape cieni".
Mediana po azymutach slonca. Wynik: JSON + tabela; test spojnosci z regula C# w `--check`.

uv run --project tools/worldgen python tools/rendering/thin_shadow_audit.py [--glb <path>] [--out <json>]
"""
import argparse, json, math, struct, sys
from pathlib import Path
import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
CELL = 0.01          # m, raster of the silhouette
SUN_ELEV_DEG = 35.0  # WORKING_VALUE: typical preset elevation; lower sun = longer, not thinner, shadows
AZIMUTHS = [0, 45, 90, 135]
SKIP = ("car_", "van_", "tractor_", "trailer_", "container_")   # bodies, never thin; keep the audit fast

# --- mirror of game/Assets/_Project/Rendering/Runtime/ThinShadowCasterPolicy.cs (keep in sync; EditMode
# ThinShadowCasterTests pins the C# side with bounding boxes copied from this audit) ---
THIN_PREFIXES = ("lamp_", "signal_pole", "sign_post", "sign_g3_", "sign_gantry_", "sign_cantilever_", "bollard", "railing_",
                 "fence_", "sliding_gate", "barrier_arm", "barrier_boom", "chain_", "wire_")
THIN_EXACT = ("pylon",)
MAX_ROD_WIDTH_M = 0.20  # WORKING_VALUE, ~2.5 Low texels
# --check: family members that are individually resolvable but follow their family (one lamp row must not mix).
FAMILY_EXCEPTIONS = ("lamp_old_concrete_9m", "lamp_old_concrete_led_9m", "sign_g3_G3518e7fb6")  # led_9m: ADR 0216b (#120), same pole


def is_thin(name, size):
    """size = bbox (x, y, z), y up. Category first, geometry as the fallback for unknown prototypes."""
    if name.startswith("tree_"):
        return False
    if name in THIN_EXACT or any(name.startswith(p) for p in THIN_PREFIXES):
        return True
    return 0.0 < rod_width(size) < MAX_ROD_WIDTH_M


def rod_width(size):
    """Middle bbox dimension: small for rods / posts / chains (two small dimensions), large for plates and boxes."""
    return sorted(size)[1]


def load_glb(path):
    data = Path(path).read_bytes()
    assert data[:4] == b"glTF", "not a GLB (git lfs pull --include=art-source/world/props/street_props.glb)"
    jl = struct.unpack_from("<I", data, 12)[0]
    js = json.loads(data[20:20 + jl])
    bin0 = data[20 + jl + 8:]
    return js, bin0


def accessor(js, bin0, idx):
    a = js["accessors"][idx]
    bv = js["bufferViews"][a["bufferView"]]
    comp = {5120: "i1", 5121: "u1", 5122: "<i2", 5123: "<u2", 5125: "<u4", 5126: "<f4"}[a["componentType"]]
    n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
    off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = bv.get("byteStride", 0)
    item = np.dtype(comp).itemsize * n
    if stride and stride != item:
        raw = np.frombuffer(bin0, dtype=np.uint8, count=stride * a["count"], offset=off).reshape(a["count"], stride)[:, :item]
        arr = np.frombuffer(raw.tobytes(), dtype=comp)
    else:
        arr = np.frombuffer(bin0, dtype=comp, count=n * a["count"], offset=off)
    arr = arr.reshape(a["count"], n).astype(np.float64 if comp == "<f4" else np.int64)
    if a.get("normalized"):
        arr = arr / {"u1": 255.0, "<u2": 65535.0, "i1": 127.0, "<i2": 32767.0}[comp]
    return arr


def prototypes(js, bin0):
    for node in js["nodes"]:
        name = node.get("name", "")
        if "mesh" not in node or "." in name:
            continue   # .lod1 / .lod2 / .col / .contact
        tris = []
        for prim in js["meshes"][node["mesh"]]["primitives"]:
            pos = accessor(js, bin0, prim["attributes"]["POSITION"])
            idx = accessor(js, bin0, prim["indices"]).reshape(-1, 3) if "indices" in prim else np.arange(len(pos)).reshape(-1, 3)
            tris.append(pos[idx])
        if tris:
            yield name, np.concatenate(tris)


def silhouette(tris, az_deg):
    """Ground-plane shadow mask (bool raster, CELL) of triangles (n, 3, 3), y up."""
    el, az = math.radians(SUN_ELEV_DEG), math.radians(az_deg)
    k = 1.0 / math.tan(el)
    dx, dz = math.cos(az) * k, math.sin(az) * k
    p = np.stack([tris[..., 0] + tris[..., 1] * dx, tris[..., 2] + tris[..., 1] * dz], axis=-1)   # (n, 3, 2)
    lo = p.reshape(-1, 2).min(0) - 4 * CELL
    hi = p.reshape(-1, 2).max(0) + 4 * CELL
    w, h = np.ceil((hi - lo) / CELL).astype(int) + 1
    mask = np.zeros((h, w), dtype=bool)
    q = (p - lo) / CELL
    for a, b, c in q:
        x0, y0 = np.floor(np.minimum(np.minimum(a, b), c)).astype(int)
        x1, y1 = np.ceil(np.maximum(np.maximum(a, b), c)).astype(int) + 1
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-9:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        l1 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
        l2 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
        inside = (l1 >= -1e-6) & (l2 >= -1e-6) & (l1 + l2 <= 1 + 1e-6)
        mask[y0:y1, x0:x1] |= inside
    return mask


def measure(tris, texel_m, normal_bias):
    out = {"width": [], "survive_bias": [], "resolved": []}
    r_bias = normal_bias * texel_m / CELL
    r_open = texel_m / CELL          # opening radius 1 texel = features >= 2 texels wide survive
    for az in AZIMUTHS:
        m = silhouette(tris, az)
        area = m.sum()
        if area == 0:
            continue
        dt = ndimage.distance_transform_edt(m)
        perim = (m & ~ndimage.binary_erosion(m)).sum()
        out["width"].append(2.0 * area * CELL / max(perim, 1))
        out["survive_bias"].append(float((dt > r_bias).sum()) / area)
        opened = ndimage.distance_transform_edt(~(dt > r_open)) <= r_open
        out["resolved"].append(float((opened & m).sum()) / area)
    return {k: float(np.median(v)) if v else 0.0 for k, v in out.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--glb", default=str(ROOT / "art-source/world/props/street_props.glb"))
    ap.add_argument("--out", default=str(ROOT / "artifacts/shadows-0240/thin_shadow_audit.json"))
    ap.add_argument("--texel", type=float, default=0.078, help="Low main-light shadow texel [m] (ESTIMATED, ADR 0240)")
    ap.add_argument("--normal-bias", type=float, default=1.0, help="tier shadowNormalBias [texels]")
    ap.add_argument("--only", default="")
    ap.add_argument("--check", action="store_true", help="exit 1 when the rule disagrees with the measurement")
    a = ap.parse_args()
    js, bin0 = load_glb(a.glb)
    rows = []
    for name, tris in prototypes(js, bin0):
        if name.startswith(SKIP) or (a.only and not name.startswith(a.only)):
            continue
        size = (tris.reshape(-1, 3).max(0) - tris.reshape(-1, 3).min(0)).tolist()
        m = measure(tris, a.texel, a.normal_bias)
        rows.append({"name": name, "tris": int(len(tris)), "bbox_m": [round(s, 3) for s in size], "rod_width_m": round(rod_width(size), 3),
                     "shadow_width_m": round(m["width"], 3), "survive_bias": round(m["survive_bias"], 3),
                     "resolved": round(m["resolved"], 3), "thin": bool(is_thin(name, size))})
        r = rows[-1]
        print(f"{r['name']:28s} tris {r['tris']:5d} bbox {r['bbox_m'][0]:6.2f} {r['bbox_m'][1]:6.2f} {r['bbox_m'][2]:6.2f} rod {r['rod_width_m']:5.2f} "
              f"w {r['shadow_width_m']:5.3f} bias {r['survive_bias']:4.2f} res {r['resolved']:4.2f} {'THIN' if r['thin'] else ''}", flush=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({"schema": "kamion/thin-shadow-audit/1", "texel_m": a.texel, "normal_bias": a.normal_bias,
                                       "sun_elev_deg": SUN_ELEV_DEG, "cell_m": CELL, "prototypes": rows}, indent=1), encoding="utf-8")


    if a.check:
        # A: unresolvable (< 70 % of the shadow is >= 2 texels wide) must be thin; B: clearly resolvable and wide must cast.
        bad = [r["name"] for r in rows if r["resolved"] < 0.70 and not r["thin"]]
        bad += [r["name"] for r in rows if r["resolved"] >= 0.90 and r["shadow_width_m"] >= 0.20 and r["thin"]
                and r["name"] not in FAMILY_EXCEPTIONS]
        n_thin = sum(r["thin"] for r in rows)
        print(f"CHECK: {len(rows)} prototypes, {n_thin} thin, {len(bad)} disagreements {bad}")
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
