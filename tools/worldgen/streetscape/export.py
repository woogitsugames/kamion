"""Export of the street-furniture prototype library and the small generated textures.

art-source/world/props/street_props.glb   prototypes (LOD0, .lod1, .col nodes), sign faces embedded
art-source/world/props/props_meta.json    triangle counts per prototype/LOD (mesh budget table)
art-source/world/signs/<code>.png         our sign-face reproductions (streetscape.signs)
art-source/world/textures/{fence_mesh,dock_digits}.png
All deterministic (same inputs -> same bytes).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from terrain_mesh.gltf import GLB

from . import props as PP
from . import signs as SG
from .materials import M

REPO = Path(__file__).resolve().parents[3]
ART = REPO / "art-source" / "world"



CREASE_DEG = 38.0       # WORKING_VALUE: faces meeting at more than this keep a hard edge (box corners, 6-gon posts)


def crease_normals(prims, angle_deg=CREASE_DEG):
    """Per-corner normals for one prototype (ADR 0041 par. 7): corners are welded by position (0.5 mm) across all
    primitives of the mesh and averaged (area weighted) over the faces within `angle_deg` of the corner's own face,
    so curved shells shade smooth and real creases stay hard. Returns new prims with "N" and re-indexed V / UV / T."""
    if not prims:
        return prims
    cs = float(np.cos(np.radians(angle_deg)))
    P, F, own = [], [], []
    for k, p in enumerate(prims):
        V, T = np.asarray(p["V"], float), np.asarray(p["T"], np.int64).reshape(-1, 3)
        P.append(V[T])                                   # (m, 3, 3)
        own += [k] * len(T)
    C = np.concatenate(P) if P else np.zeros((0, 3, 3))
    if len(C) == 0:
        return prims
    fn = np.cross(C[:, 1] - C[:, 0], C[:, 2] - C[:, 0])
    ln = np.linalg.norm(fn, axis=1)
    fu = fn / np.where(ln > 1e-12, ln, 1.0)[:, None]
    key = np.round(C.reshape(-1, 3) / 0.0005).astype(np.int64)
    _, pid = np.unique(key, axis=0, return_inverse=True)
    pid = pid.reshape(-1)
    face = np.repeat(np.arange(len(C)), 3)
    order = np.argsort(pid, kind="stable")
    bounds = np.flatnonzero(np.diff(pid[order])) + 1
    N = np.zeros((len(C) * 3, 3))
    for grp in np.split(order, bounds):
        f = face[grp]
        if len(grp) == 1:
            N[grp[0]] = fu[f[0]]
            continue
        U = fu[f]
        mask = (U @ U.T) >= cs
        N[grp] = mask.astype(float) @ fn[f]
    nl = np.linalg.norm(N, axis=1)
    bad = nl < 1e-12
    N[bad] = fu[face[bad]]
    nl = np.linalg.norm(N, axis=1)
    N[nl < 1e-12] = [0.0, 0.0, 1.0]
    N /= np.linalg.norm(N, axis=1)[:, None]
    N = N.reshape(-1, 3, 3)
    out, off = [], 0
    for p in prims:
        V, T = np.asarray(p["V"], float), np.asarray(p["T"], np.int64).reshape(-1, 3)
        UV = np.asarray(p["UV"], float) if p.get("UV") is not None else np.zeros((len(V), 2))
        m = len(T)
        rows = np.concatenate([V[T].reshape(-1, 3), np.round(N[off:off + m].reshape(-1, 3), 3), UV[T].reshape(-1, 2)], axis=1)
        off += m
        uniq, inv = np.unique(np.round(rows, 5), axis=0, return_inverse=True)
        q = dict(p)
        q["V"], q["N"], q["UV"], q["T"] = uniq[:, :3], uniq[:, 3:6], uniq[:, 6:8], inv.reshape(-1, 3)
        out.append(q)
    return out


def fence_mesh_png():
    """3D welded panel mesh 50 x 200 mm (vertical wires 50 mm apart, horizontal 200 mm), 1 m tile, alpha."""
    n = 512
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k in range(20):
        x = int(k * n / 20)
        d.rectangle([x, 0, x + 2, n], fill=(255, 255, 255, 255))
    for k in range(5):
        y = int(k * n / 5)
        d.rectangle([0, y, n, y + 3], fill=(255, 255, 255, 255))
    return im


def textures():
    return {"fence_mesh": SG.png_bytes(fence_mesh_png()), "dock_digits": SG.png_bytes(SG.digits_atlas()),
            "plate_back": SG.png_bytes(SG.plate_back())}


def glb_materials():
    tx = textures()
    out = {}
    for k, v in M.items():
        v = dict(v)
        if "texture" in v:
            v["texture_png"] = tx[v.pop("texture")]
        out[k] = v
    return out


def export(codes, boards, out_dir=None):
    out_dir = Path(out_dir) if out_dir else ART / "props"
    sign_dir = (out_dir.parent / "signs") if out_dir != ART / "props" else ART / "signs"
    tex_dir = (out_dir.parent / "textures") if out_dir != ART / "props" else ART / "textures"
    for d in (out_dir, sign_dir, tex_dir):
        d.mkdir(parents=True, exist_ok=True)
    mats = dict(glb_materials())
    sign_png = {}
    for c in sorted(codes):
        _, im = SG.face(c)
        sign_png[c] = SG.png_bytes(SG.weather(im.resize((256, 256), SG.Image.LANCZOS), c))
        mats[f"sign_{c}"] = {"color": [1, 1, 1], "rough": 0.45, "texture_png": sign_png[c], "alpha_cutoff": 0.5}
    for c, (w, h, im) in sorted(boards.items()):
        ww = 512
        hh = max(32, int(round(ww * im.size[1] / im.size[0])))
        sign_png[c] = SG.png_bytes(SG.weather(im.resize((ww, hh), SG.Image.LANCZOS), c, 0.7))
        mats[f"sign_{c}"] = {"color": [1, 1, 1], "rough": 0.45, "texture_png": sign_png[c]}
    from . import life_props as LP
    for c in sorted(LP.SIGNS):
        b = SG.png_bytes(LP.sign_texture(c))
        sign_png[f"facade_{c}"] = b
        mats[f"sign_facade_{c}"] = {"color": [1, 1, 1], "rough": 0.5, "texture_png": b}
    pb = SG.png_bytes(LP.plate_texture())
    tex_extra = {"plate_pl": pb}
    mats["plate_pl"] = {"color": [1, 1, 1], "rough": 0.4, "texture_png": pb}
    for c, b in sign_png.items():
        p = sign_dir / f"{c}.png"
        if not p.exists() or p.read_bytes() != b:
            p.write_bytes(b)
    for k, b in {**textures(), **tex_extra}.items():
        p = tex_dir / f"{k}.png"
        if not p.exists() or p.read_bytes() != b:
            p.write_bytes(b)
    P = PP.build_all(codes, {c: (w, h) for c, (w, h, _) in boards.items()})
    glb = GLB(mats)
    meta = {}
    for name in sorted(P):
        lod0, lod1, col, *more = P[name]
        t0 = glb_tris = 0
        prims = crease_normals(lod0.out())
        glb.add_mesh(name, prims, {"lod": 0})
        t0 = sum(len(p["T"]) for p in prims)
        p1 = crease_normals(lod1.out())
        glb.add_mesh(name + ".lod1", p1, {"lod": 1})
        t1 = sum(len(p["T"]) for p in p1)
        if col is not None:
            glb.add_mesh(name + ".col", col.out(), {"collision": True})
        meta[name] = {"tris_lod0": int(t0), "tris_lod1": int(t1), "materials": sorted({p["mat"] for p in prims})}
        if more and more[0] is not None:          # optional third LOD (cars, vans: far parking rows)
            p2 = crease_normals(more[0].out())
            glb.add_mesh(name + ".lod2", p2, {"lod": 2})
            meta[name]["tris_lod2"] = int(sum(len(p["T"]) for p in p2))
        del glb_tris
    data = glb.bytes({"library": "street_props", "frame": "x right, y front, z up (glTF: x=-x, y=z, z=y)"})
    (out_dir / "street_props.glb").write_bytes(data)
    text = json.dumps({"prototypes": meta, "boards_m": {c: [w, h] for c, (w, h, _) in boards.items()}},
                      indent=1, sort_keys=True) + "\n"
    (out_dir / "props_meta.json").write_text(text, encoding="utf-8", newline="\n")
    return meta
