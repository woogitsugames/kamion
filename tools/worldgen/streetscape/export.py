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

from PIL import Image, ImageDraw

from terrain_mesh.gltf import GLB

from . import props as PP
from . import signs as SG
from .materials import M

REPO = Path(__file__).resolve().parents[3]
ART = REPO / "art-source" / "world"


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
    return {"fence_mesh": SG.png_bytes(fence_mesh_png()), "dock_digits": SG.png_bytes(SG.digits_atlas())}


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
        sign_png[c] = SG.png_bytes(im, (256, 256))
        mats[f"sign_{c}"] = {"color": [1, 1, 1], "rough": 0.45, "texture_png": sign_png[c], "alpha_cutoff": 0.5}
    for c, (w, h, im) in sorted(boards.items()):
        ww = 512
        hh = max(32, int(round(ww * im.size[1] / im.size[0])))
        sign_png[c] = SG.png_bytes(im, (ww, hh))
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
        lod0, lod1, col = P[name]
        t0 = glb_tris = 0
        prims = lod0.out()
        glb.add_mesh(name, prims, {"lod": 0})
        t0 = sum(len(p["T"]) for p in prims)
        p1 = lod1.out()
        glb.add_mesh(name + ".lod1", p1, {"lod": 1})
        t1 = sum(len(p["T"]) for p in p1)
        if col is not None:
            glb.add_mesh(name + ".col", col.out(), {"collision": True})
        meta[name] = {"tris_lod0": int(t0), "tris_lod1": int(t1), "materials": sorted({p["mat"] for p in prims})}
        del glb_tris
    data = glb.bytes({"library": "street_props", "frame": "x right, y front, z up (glTF: x=-x, y=z, z=y)"})
    (out_dir / "street_props.glb").write_bytes(data)
    text = json.dumps({"prototypes": meta, "boards_m": {c: [w, h] for c, (w, h, _) in boards.items()}},
                      indent=1, sort_keys=True) + "\n"
    (out_dir / "props_meta.json").write_text(text, encoding="utf-8", newline="\n")
    return meta
