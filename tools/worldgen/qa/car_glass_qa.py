"""Car glass QA (REVIEW r6 W-N8): per-pixel incidence angle on the LOD0 glazing of one parked car, rendered by the
Unity control cameras that `cameras` writes (scripts/visual-qa.ps1 -Gate3 <json>), luma statistics per angle band.

  uv run --project tools/worldgen python tools/worldgen/qa/car_glass_qa.py cameras --region <id> --out <cams.json>
  uv run --project tools/worldgen python tools/worldgen/qa/car_glass_qa.py measure --cams <cams.json> --png-dir <dir>

The glass mask is the projection of the prototype's `car_glass_tint` triangles (streetscape.life_cars, LOD0) with
the instance pose from the world instance files; only triangles facing the camera count, the mask is eroded by
2 px. Luma = Rec.709 on the sRGB PNG (0..100 %). Acceptance (r6): p50 <= 20 % where the incidence < 45 deg,
p50 >= 40 % where it is >= 70 deg.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
REPO = HERE.parents[2]

W, H, FOV = 2340, 1080, 50.0


def _pick_car(region, near, max_d=150.0):
    """Car closest to `near` (local E, N) with one side free of vehicles for 9 m (cameras stand there) and nothing
    within 10 m in front of it. Returns (instance, side sign)."""
    man = json.loads((REPO / "Data/Regions" / region / "generated/world_manifest.json").read_text(encoding="utf-8"))
    allv = []
    for ch in man["chunks"]:
        p = REPO / ch["instances"]["file"]
        allv += [it for it in json.loads(p.read_text(encoding="utf-8"))["instances"]
                 if not it["p"].startswith(("tree_", "sign_", "plate_", "board_", "lamp_"))]
    E = np.array([[v["e"], v["n"]] for v in allv])
    best = None
    for it in allv:
        if not it["p"].startswith("car_"):
            continue
        d = math.hypot(it["e"] - near[0], it["n"] - near[1])
        if d > max_d or (best is not None and d >= best[0]):
            continue
        yaw = it["yaw"]
        fwd = np.array([-math.sin(yaw), math.cos(yaw)])
        right = np.array([math.cos(yaw), math.sin(yaw)])
        rel = E - np.array([it["e"], it["n"]])
        al, ac = rel @ fwd, rel @ right
        own = (np.abs(al) < 0.1) & (np.abs(ac) < 0.1)
        front_free = not np.any(~own & (al > 2.0) & (al < 12.0) & (np.abs(ac) < 2.5))
        for sx in (1.0, -1.0):
            side_free = not np.any(~own & (sx * ac > 0.5) & (sx * ac < 10.0) & (np.abs(al) < 9.0))
            if side_free and front_free:
                best = (d, it, sx)
                break
    return best[1], best[2]


def cameras(region, out, near):
    it, sx = _pick_car(region, near)
    yaw = it["yaw"]
    c = np.array([it["e"], it["n"]])
    fwd = np.array([-math.sin(yaw), math.cos(yaw)])
    right = np.array([math.cos(yaw), math.sin(yaw)]) * sx
    z = it["z"] + 1.7                                         # photo_match kind: 1.7 m above the collision
    zt = it["z"] + 1.15                                       # side glass centre
    cams = []
    # incidence on the side glass ~ angle between the camera ray and the side normal (right); camera ring around
    # the side-window centre (0.3 m behind the car origin), radius 6 m
    tgt = c - fwd * 0.3
    for ang in (0, 25, 40, 70, 78):
        a = math.radians(ang)
        dirv = right * math.cos(a) + fwd * math.sin(a)
        pos = tgt + right * 0.93 + dirv * (6.0 if ang < 60 else 7.5)
        cams.append({"id": f"glass_side_{ang:02d}", "type": "persp", "kind": "photo_match", "fov_deg": FOV,
                     "pos": [float(pos[0]), float(pos[1]), z], "look_at": [float(tgt[0] + right[0] * 0.9),
                                                                         float(tgt[1] + right[1] * 0.9), zt],
                     "note": f"car glass QA, side glass at ~{ang} deg"})
    # windscreen from the front (rake ~ 60 deg: incidence 55-70 deg) and from the rear quarter
    for nm, d, h in (("glass_front", 7.0, 1.7), ("glass_front_low", 9.0, 1.7)):
        pos = c + fwd * d
        cams.append({"id": nm, "type": "persp", "kind": "photo_match", "fov_deg": FOV,
                     "pos": [float(pos[0]), float(pos[1]), it["z"] + h], "look_at": [float(c[0] + fwd[0] * 0.6),
                                                                                    float(c[1] + fwd[1] * 0.6), zt],
                     "note": "car glass QA, windscreen"})
    # r8 N-14: the same car from the front three-quarter at the distances where Low used to switch to LOD1
    # (12.5 m before r8, 16 m now) and beyond; distance = camera to the car origin on the ground plane
    d34 = (right + fwd) / math.sqrt(2.0)
    for dist in (8, 12, 15, 25):
        pos = c + d34 * dist
        cams.append({"id": f"car_lod_{dist:02d}", "type": "persp", "kind": "photo_match", "fov_deg": 40.0,
                     "pos": [float(pos[0]), float(pos[1]), z], "look_at": [float(c[0]), float(c[1]), it["z"] + 0.8],
                     "note": f"car LOD QA, front 3/4 at {dist} m"})
    doc = {"schema": "truck-sim-pl/gate3-cameras/1", "region": region, "car": it, "cameras": cams}
    Path(out).write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print("car", it["p"], "at", round(it["e"], 1), round(it["n"], 1), "->", out)


def _glass_tris(proto):
    from streetscape import life_cars as LC
    parts = proto.split("_")
    m0 = (LC.van(parts[1]) if parts[0] == "van" else LC.car(parts[1], parts[2]))[0]
    V, T = [], []
    for p in m0.out():
        if p["mat"] == "car_glass_tint":
            T.append(np.asarray(p["T"]) + sum(len(v) for v in V))
            V.append(np.asarray(p["V"], float))
    return np.concatenate(V), np.concatenate(T)


def _raster(tris2, depth, w, h):
    """Nearest-triangle index per pixel (z-buffer) of projected triangles (n, 3, 2) with per-vertex depth."""
    idx = np.full((h, w), -1, np.int32)
    zb = np.full((h, w), np.inf)
    for k, (t, dz) in enumerate(zip(tris2, depth)):
        x0, y0 = np.floor(t.min(0)).astype(int)
        x1, y1 = np.ceil(t.max(0)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, w - 1), min(y1, h - 1)
        if x1 < x0 or y1 < y0:
            continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        (ax, ay), (bx, by), (cx, cy) = t
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9:
            continue
        l1 = ((by - cy) * (X - cx) + (cx - bx) * (Y - cy)) / den
        l2 = ((cy - ay) * (X - cx) + (ax - cx) * (Y - cy)) / den
        l3 = 1 - l1 - l2
        ins = (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
        zz = l1 * dz[0] + l2 * dz[1] + l3 * dz[2]
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        upd = ins & (zz < sub)
        sub[upd] = zz[upd]
        idx[y0:y1 + 1, x0:x1 + 1][upd] = k
    return idx


def measure(cams_json, png_dir, out_json=None):
    from PIL import Image
    from scipy import ndimage
    doc = json.loads(Path(cams_json).read_text(encoding="utf-8"))
    it = doc["car"]
    V, T = _glass_tris(it["p"])
    yaw = it["yaw"]
    cy, sy = math.cos(yaw), math.sin(yaw)
    Vw = np.column_stack([it["e"] + V[:, 0] * cy - V[:, 1] * sy, it["n"] + V[:, 0] * sy + V[:, 1] * cy,
                          it["z"] + V[:, 2]])
    res = {}
    bands = {"lt45": [], "ge70": [], "45_70": []}
    for cam in doc["cameras"]:
        png = Path(png_dir) / f"{cam['id']}.png"
        if not png.exists() or not cam["id"].startswith("glass_"):
            continue
        img = np.asarray(Image.open(png).convert("RGB"), np.float64)
        h, w = img.shape[:2]
        luma = (0.2126 * img[..., 0] + 0.7152 * img[..., 1] + 0.0722 * img[..., 2]) / 255.0 * 100.0
        pos = np.array(cam["pos"], float)
        look = np.array(cam["look_at"], float)
        f = look - pos
        f /= np.linalg.norm(f)
        r = np.cross(f, [0, 0, 1.0])
        r /= np.linalg.norm(r)
        u = np.cross(r, f)
        rel = Vw - pos
        xc, yc, zc = rel @ r, rel @ u, rel @ f
        fy = (h / 2) / math.tan(math.radians(cam["fov_deg"]) / 2)
        px = np.column_stack([w / 2 + fy * xc / zc, h / 2 - fy * yc / zc])
        A, B, C = Vw[T[:, 0]], Vw[T[:, 1]], Vw[T[:, 2]]
        nrm = np.cross(B - A, C - A)
        nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-12
        cen = (A + B + C) / 3
        view = pos - cen
        view /= np.linalg.norm(view, axis=1)[:, None]
        facing = np.einsum("ij,ij->i", nrm, view) > 0.02
        ok = facing & (zc[T].min(1) > 0.2)
        idx = _raster(px[T[ok]], zc[T[ok]], w, h)
        keep = ndimage.binary_erosion(idx >= 0, iterations=2)
        tri = np.flatnonzero(ok)[idx[keep]]
        # per-pixel incidence: angle between the pane normal and the ray to the pixel
        ys, xs = np.nonzero(keep)
        rays = (xs[:, None] + 0.5 - w / 2) / fy * r + (h / 2 - ys[:, None] - 0.5) / fy * u + f
        rays /= np.linalg.norm(rays, axis=1)[:, None]
        inc = np.degrees(np.arccos(np.clip(np.abs(np.einsum("ij,ij->i", rays, nrm[tri])), 0, 1)))
        L = luma[keep]
        out = {"pixels": int(keep.sum())}
        for b, sel in (("lt45", inc < 45), ("45_70", (inc >= 45) & (inc < 70)), ("ge70", inc >= 70)):
            if sel.sum() >= 50:
                out[b] = {"n": int(sel.sum()), "p50": round(float(np.median(L[sel])), 1),
                          "p10": round(float(np.percentile(L[sel], 10)), 1),
                          "p90": round(float(np.percentile(L[sel], 90)), 1)}
                bands[b].append(L[sel])
        res[cam["id"]] = out
        # overlay for the visual check
        ov = img.copy()
        ov[keep] = ov[keep] * 0.5 + np.array([255, 0, 255]) * 0.5
        Image.fromarray(ov.astype(np.uint8)).resize((w // 3, h // 3)).save(Path(png_dir) / f"{cam['id']}_mask.png")
    tot = {b: (round(float(np.median(np.concatenate(v))), 1) if v else None) for b, v in bands.items()}
    report = {"car": it["p"], "per_camera": res, "p50_all": tot,
              "pass_lt45_le20": tot["lt45"] is not None and tot["lt45"] <= 20.0,
              "pass_ge70_ge40": tot["ge70"] is not None and tot["ge70"] >= 40.0}
    txt = json.dumps(report, indent=1)
    print(txt)
    if out_json:
        Path(out_json).write_text(txt, encoding="utf-8")
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("cameras")
    a.add_argument("--region", default="bialystok-industrial-c")
    a.add_argument("--out", required=True)
    a.add_argument("--near", type=float, nargs=2, default=None)
    b = sub.add_parser("measure")
    b.add_argument("--cams", required=True)
    b.add_argument("--png-dir", required=True)
    b.add_argument("--out")
    ar = ap.parse_args()
    if ar.cmd == "cameras":
        near = ar.near
        if near is None:
            cc = json.loads((REPO / "Data/Regions" / ar.region / "generated/control_cameras.json").read_text(encoding="utf-8"))
            s1 = next(c for c in cc["cameras"] if c["id"] == "stretch_01")
            near = s1["pos"][:2]
        cameras(ar.region, ar.out, near)
    else:
        measure(ar.cams, ar.png_dir, ar.out)
