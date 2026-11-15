"""Night data of the building atlases (ADR 0192): which pixels of a window cell let room light out, how much, and
which window a pixel belongs to.

Outputs (game/Assets/_Project/Rendering/Resources/Night/, versioned, small; regenerate after any change of the cell
layout in tools/worldgen/streetscape/facade_atlas.py or of the window painting in sets_buildings.py):
  T_NightAtlasId.png   facade_atlas (16 x 16 m), 512 px, point sampled: R, G = centre of the cell the texel belongs
                       to (u / 16, v / 16; the 5 cm gutter belongs to its cell), A = window class x 32 / 255
                       (0 not a window, 1 flat, 2 stairwell / entrance, 3 office, 4 hall), B unused.
  T_NightAtlasT.png    facade_atlas, 1024 px, bilinear + mips: R = room-light transmission of the glass pane
                       (0 frame / sash / wall, clear glass 0.55-1.0 by height in the room, net curtain ~0.7,
                       drapes 0.08, roller blind 0.25 ...), G = fabric coverage (curtain / blind tints the light).
  T_NightFarId.png / T_NightFarT.png  the same for the LOD1 storey rows facade_far (24 x FAR_H m, 256 x 512 / 512 x 1024).
The transmission is painted from the SAME calls that paint the albedo: sets_buildings.interior() is wrapped and every
call (kind, rectangle, blind fraction) is replayed into a transmission layer; the glass mask is the painter's height
(-4 cm = glass, frames / sashes at 0 / -1.2 cm). WORKING_VALUE transmissions (no photometric source; judged on renders).

    uv run --project tools/worldgen python art-source/world/materials/_src/night_facade.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sets_buildings as B  # noqa: E402

A = B.A
F32 = np.float32
REPO = HERE.parents[3]
OUT = REPO / "game" / "Assets" / "_Project" / "Rendering" / "Resources" / "Night"

# window class per atlas kind (shader: probability / colour temperature of a lit window)
CLASS = {"w1": 1, "w2": 1, "w3": 1, "bdoor": 1, "bwin": 1, "balg": 1, "house": 1,
         "stair": 2, "door_block": 2, "off": 3, "hallw": 4, "indw": 4}

_orig_interior = B.interior


def _trn_layer(p):
    if not hasattr(p, "trn"):
        p.trn = np.zeros((p.ny, p.nx), F32)
        p.cov = np.zeros((p.ny, p.nx), F32)
    return p.trn, p.cov


def _interior_rec(p, R, kind, col=None, frac=1.0, plants=0, k=0):
    """interior() + the matching room-light transmission (what a lit room shows through this pane)."""
    _orig_interior(p, R, kind, col=col, frac=frac, plants=plants, k=k)
    trn, cov = _trn_layer(p)
    x0, x1, y0, y1 = R
    m = p.rect(x0, x1, y0, y1)
    u = np.clip((p.X - x0) / (x1 - x0), 0, 1)
    v = np.clip((p.Y - y0) / (y1 - y0), 0, 1)
    t = 0.55 + 0.45 * v                       # clear glass: the room, ceiling / lamp side brighter
    c = np.zeros_like(t)

    def fabric(mask, tf, cf):
        nonlocal t, c
        t = t * (1 - mask) + tf * mask
        c = c * (1 - mask) + cf * mask

    if kind in ("net", "lit"):
        fabric(np.ones_like(u), 0.72 if kind == "net" else 0.8, 0.8 if kind == "net" else 0.55)
    elif kind == "net_gap":
        gap = 0.03 + 0.22 * (1 - v) ** 1.8
        fabric(np.clip((np.abs(u - 0.5) - gap) / 0.01, 0, 1), 0.72, 0.8)
    elif kind == "cafe":
        fabric((v < 0.50 + 0.06 * frac).astype(F32), 0.6, 0.9)
    elif kind == "drapes":
        a = 0.20 + 0.10 * frac + 0.03 * np.sin(v * 5 + 1.0)
        b = 0.17 + 0.08 * frac + 0.03 * np.sin(v * 4 + 2.0)
        fabric(((u > a) & (u < 1 - b)).astype(F32), 0.72, 0.8)
        dm = np.clip(np.clip((a - u) / 0.01, 0, 1) + np.clip((u - (1 - b)) / 0.01, 0, 1), 0, 1)
        fabric(dm, 0.08, 1.0)                 # lined drapes: a faint coloured glow
    elif kind in ("roller", "daynight", "venetian", "vertical"):
        bm = np.clip((v - (1 - frac)) / 0.004, 0, 1)
        tf, cf = {"roller": (0.25, 1.0), "daynight": (0.38, 0.8), "venetian": (0.12, 1.0), "vertical": (0.3, 1.0)}[kind]
        fabric(bm, tf, cf)
    elif kind == "frosted":
        fabric(np.ones_like(u), 0.6, 0.0)     # obscure glass glows evenly, not tinted
    elif kind == "office":
        t = np.full_like(u, 0.9)
    trn += (t - trn) * m
    cov += (c - cov) * m


B.interior = _interior_rec


def cell_layers(kind, i, px):
    """(transmission, coverage) of one painted cell, glass mask applied."""
    p = B.paint_cell(kind, i, px)
    if not hasattr(p, "trn"):                 # no interior painted (steel door, garage, AC ...)
        z = np.zeros((p.ny, p.nx), F32)
        return z, z
    glass = np.clip((-0.03 - p.hgt) / 0.006, 0, 1)       # -4 cm glass; frame 0, sash -1.2 cm
    return (p.trn * glass).astype(F32), (p.cov * glass).astype(F32)


def _put(dst, img, r0, c0):
    r1, c1 = r0 + img.shape[0], c0 + img.shape[1]
    rr0, cc0 = max(r0, 0), max(c0, 0)
    rr1, cc1 = min(r1, dst.shape[0]), min(c1, dst.shape[1])
    if rr1 > rr0 and cc1 > cc0:
        dst[rr0:rr1, cc0:cc1] = img[rr0 - r0:rr1 - r0, cc0 - c0:cc1 - c0]


def atlas(n_t=1024, n_id=512):
    L = A.ATLAS_M[0]
    px = L / n_t
    T = np.zeros((n_t, n_t, 3), F32)
    ID = np.zeros((n_id, n_id, 4), np.uint8)
    pid = L / n_id
    g = A.GUTTER
    for (kind, i), (u0, v0, w, h) in A.CELLS.items():
        if kind.startswith("sw_"):
            continue
        cls = CLASS.get(kind, 0)
        if cls:
            t, c = cell_layers(kind, i, px)
            col = int(round(u0 / px))
            row = n_t - int(round((v0 + h) / px))
            _put(T[..., 0], t, row, col)
            _put(T[..., 1], c, row, col)
        # id: the cell and its own gutter
        c0, c1 = int(np.floor((u0 - g) / pid)), int(np.ceil((u0 + w + g) / pid))
        r0, r1 = n_id - int(np.ceil((v0 + h + g) / pid)), n_id - int(np.floor((v0 - g) / pid))
        cu, cv = (u0 + w / 2) / L, (v0 + h / 2) / L
        ID[max(r0, 0):r1, max(c0, 0):c1] = (round(cu * 255), round(cv * 255), 0, cls * 32)
    return T, ID


def far(n_tx=512, n_ty=1024, n_idx=256, n_idy=512):
    Lx, Ly = A.FAR_M
    pxx, pxy = Lx / n_tx, Ly / n_ty
    px = min(pxx, pxy)
    T = np.zeros((n_ty, n_tx, 3), F32)
    ID = np.zeros((n_idy, n_idx, 4), np.uint8)

    def paste(kind, var, x, y):
        cls = CLASS.get(kind, 0)
        p = B.paint_cell(kind, var, px)
        w, h = p.w, p.h
        t, c = cell_layers(kind, var, px) if cls else (np.zeros((p.ny, p.nx), F32),) * 2
        # resample the cell (painted at px) onto the far grid (pxx, pxy): nearest
        ny_, nx_ = max(1, int(round(h / pxy))), max(1, int(round(w / pxx)))
        ri = np.clip(((np.arange(ny_) + 0.5) * pxy / px).astype(int), 0, p.ny - 1)
        ci = np.clip(((np.arange(nx_) + 0.5) * pxx / px).astype(int), 0, p.nx - 1)
        r0, c0 = n_ty - int(round((y + h) / pxy)), int(round(x / pxx))
        _put(T[..., 0], t[np.ix_(ri, ci)], r0, c0)
        _put(T[..., 1], c[np.ix_(ri, ci)], r0, c0)
        sx, sy = Lx / n_idx, Ly / n_idy
        a0, a1 = int(round(x / sx)), int(round((x + w) / sx))
        b0, b1 = n_idy - int(round((y + h) / sy)), n_idy - int(round(y / sy))
        cu, cv = (x + w / 2) / Lx, (y + h / 2) / Ly
        ID[max(b0, 0):b1, max(a0, 0):a1] = (round(cu * 255), round(cv * 255), 0, cls * 32)

    for group, row in A.FAR_ORDER:
        vf = A.far_row_v(group, row)
        sill = A.FAR_SILL[group]
        for bay in range(A.FAR_BAYS):
            kind, var = A.FAR_ROWS[group][row][bay]
            xc = (bay + 0.5) * A.FAR_PITCH
            if kind == "bal":                  # same placement as sets_buildings.facade_far
                x0 = xc - 1.05
                paste("bdoor", var, x0, vf + 0.05)
                paste("bwin", var, x0 + 0.9, vf + 0.05 + 0.85)
                paste("balf", A.bal_type(group), xc - 1.3, vf + 0.02)     # balustrade blocks the door's lower part
            elif kind == "rib":
                for j in range(2):
                    paste("off", var, bay * A.FAR_PITCH + j * 1.5, vf + sill)
            else:
                w = A.KINDS[kind][0]
                paste(kind, var, xc - w / 2, vf + sill)
    return T, ID


def save(T, ID, stem):
    OUT.mkdir(parents=True, exist_ok=True)
    t8 = np.clip(np.round(T * 255), 0, 255).astype(np.uint8)
    Image.fromarray(t8, "RGB").save(OUT / f"T_Night{stem}T.png", optimize=True)
    Image.fromarray(ID, "RGBA").save(OUT / f"T_Night{stem}Id.png", optimize=True)
    lit = T[..., 0] > 0.05
    print(f"{stem}: T {T.shape[1]}x{T.shape[0]} glass {lit.mean() * 100:.1f} % mean T {T[..., 0][lit].mean():.2f}; "
          f"id {ID.shape[1]}x{ID.shape[0]} window texels {(ID[..., 3] > 0).mean() * 100:.1f} %")


if __name__ == "__main__":
    save(*atlas(), "Atlas")
    save(*far(), "Far")
