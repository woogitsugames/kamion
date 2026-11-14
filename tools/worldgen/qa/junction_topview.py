"""ADR 0203 (D63/D64 "roads first"): top view of the GENERATED road geometry next to the GUGiK orthophoto, per junction.

    uv run --project tools/worldgen python tools/worldgen/qa/junction_topview.py --region bialystok-maczka \
        [--out artifacts/<n>/junctions] [--only <id> ...]

Input : Data/Regions/<id>/junction_checks.authored.json  (list of {id, center_2180 [x, y], size_m, note})
        Data/raw/derived/<id>/world/chunk_*.glb (build_world output, High geometry; collision meshes skipped)
        Data/Regions/<id>/ortho.json -> orthophoto GeoTIFF (reference only, docs/05 par. 3; never a texture)
Output: <out>/<id>.jpg  = [orthophoto | top view of the generated meshes], same footprint, north up, 100 m grid ticks.

The top view is drawn straight from the triangles of the world chunks (painter's order by height), so it shows what
the game gets - carriageways, kerbs, pavements, markings, bridge decks - without LOD or draw-distance effects.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from roads import pipeline  # noqa: E402

# ground / road materials by name prefix -> RGB (first match wins). Everything else (buildings, trees, forest canopy,
# fences, collision) is skipped: this is a view of the road layout, and canopies would hide the carriageway.
PALETTE = (
    ("terrain", (96, 122, 78)), ("verge", (110, 138, 86)), ("plot_lawn", (104, 130, 82)),
    ("shoulder", (150, 140, 120)), ("marking_yard", (200, 200, 200)), ("marking", (245, 245, 245)),
    ("curb", (205, 205, 200)), ("bridge_kerb", (205, 205, 200)), ("road_asphalt", (62, 62, 66)),
    ("road_concrete", (150, 150, 146)), ("road_gravel", (150, 132, 104)), ("road_paving", (128, 122, 118)),
    ("path_asphalt", (120, 96, 96)), ("cycle_red", (150, 80, 70)), ("sidewalk", (176, 172, 164)),
    ("apron", (140, 134, 126)), ("yard", (134, 132, 128)), ("bridge_concrete", (120, 130, 150)),
    ("barrier_steel", (230, 120, 40)), ("noise_panel", (40, 150, 150)),
)


def colour(name: str):
    for k, c in PALETTE:
        if name.startswith(k):
            return c
    return None


def read_glb(path: Path):
    """Yield (material_name, tris[n,3,3] in region-local E, N, U) for every primitive of the finest LOD."""
    b = path.read_bytes()
    n = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + n])
    bin0 = 20 + n + 8
    ctype = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
    ncomp = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}

    def acc(i):
        a = j["accessors"][i]
        bv = j["bufferViews"][a["bufferView"]]
        off = bin0 + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        dt = np.dtype(ctype[a["componentType"]])
        nc = ncomp[a["type"]]
        stride = bv.get("byteStride", dt.itemsize * nc)
        if stride == dt.itemsize * nc:
            return np.frombuffer(b, dt, a["count"] * nc, off).reshape(a["count"], nc)
        raw = np.frombuffer(b, np.uint8, a["count"] * stride, off).reshape(a["count"], stride)
        return raw[:, :dt.itemsize * nc].copy().view(dt).reshape(a["count"], nc)

    for node in j["nodes"]:
        if "mesh" not in node or node.get("extras", {}).get("lod", 0) != 0:
            continue
        t = np.array(node.get("translation", [0, 0, 0]), dtype=np.float64)
        for pr in j["meshes"][node["mesh"]]["primitives"]:
            name = j["materials"][pr["material"]]["name"] if "material" in pr else "none"
            if colour(name) is None or pr.get("mode", 4) != 4:
                continue
            p = acc(pr["attributes"]["POSITION"]).astype(np.float64) + t
            idx = acc(pr["indices"]).reshape(-1, 3)
            enu = np.stack([-p[:, 0], p[:, 2], p[:, 1]], axis=1)   # glTF (-E, U, N) -> (E, N, U)
            yield name, enu[idx]


def load_world(region_id: str):
    wdir = pipeline.REPO / "Data" / "raw" / "derived" / region_id / "world"
    out = []
    for f in sorted(wdir.glob("chunk_*.glb")):
        if f.name.endswith(".low.glb"):
            continue
        for name, tris in read_glb(f):
            lo, hi = tris[:, :, :2].min(axis=(0, 1)), tris[:, :, :2].max(axis=(0, 1))
            out.append((name, tris, lo, hi))
    return out


def topview(world, cx, cy, size, px):
    half = size / 2
    img = Image.new("RGB", (px, px), (30, 30, 30))
    d = ImageDraw.Draw(img)
    sel = []
    for name, tris, lo, hi in world:
        if hi[0] < cx - half or lo[0] > cx + half or hi[1] < cy - half or lo[1] > cy + half:
            continue
        c = tris.mean(axis=1)
        m = (np.abs(c[:, 0] - cx) < half + 5) & (np.abs(c[:, 1] - cy) < half + 5)
        if m.any():
            # markings are decals 1-3 cm above the surface: bias them up so that they win over their own carriageway
            bias = 0.25 if name.startswith("marking") else 0.0
            sel.append((np.full(int(m.sum()), len(sel)), tris[m], c[m, 2] + bias, colour(name)))
    if not sel:
        return img, {}
    T = np.concatenate([s[1] for s in sel])
    z = np.concatenate([s[2] for s in sel])
    col = np.concatenate([np.tile(np.array(s[3], dtype=np.uint8), (len(s[1]), 1)) for s in sel])
    k = px / size
    X = (T[:, :, 0] - (cx - half)) * k
    Y = ((cy + half) - T[:, :, 1]) * k
    for i in np.argsort(z, kind="stable"):
        d.polygon([(X[i, 0], Y[i, 0]), (X[i, 1], Y[i, 1]), (X[i, 2], Y[i, 2])], fill=tuple(int(v) for v in col[i]))
    used = {}
    for s in sel:
        used[s[3]] = used.get(s[3], 0) + len(s[1])
    return img, used


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--px", type=int, default=1100)
    a = ap.parse_args()
    import rasterio
    from rasterio.windows import from_bounds
    rdir = pipeline.REGIONS / a.region
    reg = pipeline.load_region(a.region)
    ox, oy = reg["origin"]["x"], reg["origin"]["y"]
    checks = json.loads((rdir / "junction_checks.authored.json").read_text(encoding="utf-8"))["junctions"]
    ortho = json.loads((rdir / "ortho.json").read_text(encoding="utf-8"))
    out = pipeline.REPO / (a.out or f"artifacts/junctions/{a.region}")
    out.mkdir(parents=True, exist_ok=True)
    world = load_world(a.region)
    print(f"[topview] {len(world)} primitives, materials: {sorted({w[0] for w in world})}")
    with rasterio.open(pipeline.REPO / ortho["file"]) as o:
        for c in checks:
            if a.only and c["id"] not in a.only:
                continue
            x, y = c["center_2180"]
            size = float(c["size_m"])
            h = size / 2
            ob = o.read(window=from_bounds(x - h, y - h, x + h, y + h, o.transform), out_shape=(3, a.px, a.px),
                        resampling=rasterio.enums.Resampling.bilinear, boundless=True)
            left = Image.fromarray(np.moveaxis(ob, 0, -1)).convert("RGB")
            right, _ = topview(world, x - ox, y - oy, size, a.px)
            side = Image.new("RGB", (a.px * 2 + 8, a.px + 34), (20, 20, 20))
            side.paste(left, (0, 34))
            side.paste(right, (a.px + 8, 34))
            d = ImageDraw.Draw(side)
            for im_x0 in (0, a.px + 8):     # 100 m ticks on the top edge
                for t in np.arange(0, size + 1, 100.0):
                    xx = im_x0 + t * a.px / size
                    d.line([(xx, 34), (xx, 44)], fill=(255, 255, 0), width=2)
            d.text((8, 10), f"{c['id']}: GUGiK ortho {ortho.get('source_manifest', '')} (reference only) | centre "
                   f"{x:.0f}, {y:.0f} EPSG:2180, {size:.0f} m, N up, ticks 100 m", fill=(230, 230, 230))
            d.text((a.px + 16, 10), "generated world (chunk GLB triangles, top view)", fill=(230, 230, 230))
            f = out / f"{c['id']}.jpg"
            side.resize((side.width * 960 // (a.px * 2 + 8) * 2, side.height * 960 // (a.px * 2 + 8) * 2),
                        Image.LANCZOS).save(f, quality=82, optimize=True)
            print(f)


if __name__ == "__main__":
    main()
