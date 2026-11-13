"""Masonry gate kit (authored override `kind: masonry_gate`, ADR 0189): the brick entrance of an older institution
that neither OSM nor BDOT10k describes - a sand-lime brick wall with pillars and name plaques on one side of the
drive, a brick porch (piers under a flat concrete canopy) on the other, and the signs that hang on them.

Everything is data in Data/Regions/<id>/overrides.yaml and survives a re-import. Coordinates of the kit are given in
the GATE FRAME: origin `anchor.at_en` (region-local E/N, on the drive axis at the gate line), `l` = metres to the
RIGHT of a vehicle driving in (`anchor.enter_bearing_deg`, compass), `a` = metres from the gate line toward the
street. Faces look along +a (toward the street) unless `facing_deg` (compass) is given.

  walls    [{line_la: [[l, a], ...], height_m, thick_m, coping_m, pillars_la: [[l, a], ...], pillar_m, pillar_h_m,
             plaques: {at_la, facing_deg?, cols, rows, count, size_m: [w, h], z_m, texts: [...]}}]
  piers    [{at_la, size_m: [w along the gate line, d], height_m, cap: true|false}]
  canopy   {rect_la: [l0, a0, l1, a1], z_m, thick_m}        flat painted concrete slab + dark sheet roof
  platform {rect_la, height_m}                              concrete step under the porch
  faces    [{face: B-20 | C-2 | B-33_<n> | B-2, at_la, z_m (centre), size_m, facing_deg?, fade?}]   plate on masonry
  boards   [{board: <name of BOARDS>, at_la, z_m, size_m: [w, h], facing_deg?}]
  posts    [{at_la, height_m, lantern: true|false, faces: [{face, z_m, size_m}], plate: {z_m, size_m}}]
  fence_cut_m   the rule fence (furniture.fences) is cut within this distance of the walls (default 1.2 m)

The whole kit is ONE prototype with ONE material (own 1024 px atlas: brick, coping, concrete, plaques, sign faces):
one draw on every tier. The brick, the plaques and the boards are our own drawings (PIL / numpy); plaque and board
texts are neutral words, never the name of a real institution (CLAUDE.md rule 8). Sign faces are the project's own
vector faces (streetscape.signs) + C-2 drawn here. Sizes are WORKING_VALUE read off the reference photo unless the
entry says otherwise. A kit whose anchor is on a carriageway or whose pier / pillar stands on one is reported in the
streetscape QA (`masonry_gates.stale` / `on_carriageway`), never dropped silently.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from . import props as PP
from . import signs as SG

KIND = "masonry_gate"
ATLAS = 1024
BRICK_PX_M = 128.0            # brick band: 8.0 m x 2.6 m
BRICK_BAND_M = (8.0, 2.6)
BRICK_BELOW_M = 0.25          # the band starts this far under the ground line (the kit sinks into uneven ground)
COPING_ROWS = (340, 372)      # rowlock course, 8.0 m x 0.25 m
CONC_RECT = (0, 380, 512, 520)        # grey concrete (caps, platform), 4.0 m x 1.1 m
WHITE_RECT = (512, 380, 1024, 520)    # painted concrete (canopy)
FACE_PX_M = 256.0
SILICATE = (168, 163, 150)    # sand-lime brick, weathered (sRGB, read off the CC0 photo P11-129; WORKING_VALUE)
MORTAR = (118, 115, 108)
PLAQUE_RED = (122, 28, 40)
BOARD_BLUE = (24, 62, 132)
INFO_BLUE = (20, 110, 190)
PROTOS = {}                   # prototype name -> (lod0, lod1, collision); read by props.build_all


def prototypes():
    return dict(PROTOS)


def _rng(key):
    return np.random.default_rng(int(hashlib.sha1(key.encode()).hexdigest()[:8], 16))


# ------------------------------------------------------------------------------------------------- atlas drawings
def _smooth_noise(rng, h, w, cells):
    low = Image.fromarray((rng.random((max(2, cells * h // max(w, 1)), cells)) * 255).astype(np.uint8))
    return np.asarray(low.resize((w, h), Image.BICUBIC)).astype(np.float32) / 255.0


def brick_band(key="silicate"):
    """Sand-lime (silicate) brick 250 x 65 mm, 10 mm joints, stretcher bond; per-brick tone, a few dark / chipped
    bricks, damp base, run-off under the coping. RGB array (rows, 1024, 3)."""
    rng = _rng("mg-brick:" + key)
    W = int(BRICK_BAND_M[0] * BRICK_PX_M)
    H = int(round(BRICK_BAND_M[1] * BRICK_PX_M))
    course = 0.075 * BRICK_PX_M
    blen = 0.260 * BRICK_PX_M
    joint = max(1.0, 0.011 * BRICK_PX_M)
    img = np.zeros((H, W, 3), np.float32)
    yy = np.arange(H)[:, None].astype(np.float32)
    xx = np.arange(W)[None, :].astype(np.float32)
    row = np.floor(yy / course).astype(int)
    off = np.where(row % 2 == 0, 0.0, blen / 2)
    col = np.floor((xx + off) / blen).astype(int)
    n_rows, n_cols = int(row.max()) + 1, int(col.max()) + 2
    tone = 1.0 + rng.normal(0, 0.055, (n_rows, n_cols))
    tone[rng.random((n_rows, n_cols)) < 0.09] *= 0.80           # darker (wet / sooted) bricks
    tone[rng.random((n_rows, n_cols)) < 0.05] *= 1.10           # a few bleached ones
    warm = rng.normal(0, 0.02, (n_rows, n_cols))
    t = tone[row, col]
    wm = warm[row, col]
    base = np.array(SILICATE, np.float32) / 255.0
    img[..., 0] = base[0] * t * (1 + wm)
    img[..., 1] = base[1] * t
    img[..., 2] = base[2] * t * (1 - wm)
    fy = yy - row * course
    fx = (xx + off) - col * blen
    mortar = (fy < joint) | (fx < joint)
    img[np.broadcast_to(mortar, (H, W))] = np.array(MORTAR, np.float32) / 255.0
    # brick arris shading: a darker line under each joint (the joint is recessed), a lighter top edge
    img *= np.where((fy >= joint) & (fy < joint + 1.5), 0.90, 1.0)[..., None]
    grain = rng.normal(0, 0.018, (H, W)).astype(np.float32)
    img += grain[..., None]
    mott = _smooth_noise(rng, H, W, 22)
    img *= (0.93 + 0.14 * mott)[..., None]
    z_m = BRICK_BAND_M[1] - yy / BRICK_PX_M - BRICK_BELOW_M      # metres above the ground line
    damp = np.clip((0.45 - z_m) / 0.45, 0, 1) ** 1.3 * (0.5 + 0.8 * _smooth_noise(rng, H, W, 40))
    img *= (1 - 0.30 * damp)[..., None]
    img[..., 1] += 0.025 * damp[..., 0] if damp.ndim == 3 else 0.025 * damp          # algae tint at the foot
    streak = np.clip(_smooth_noise(rng, 1, W, 90) - 0.55, 0, 1) * 2.2
    run = np.clip((z_m - 1.0) / 0.9, 0, 1) * streak
    img *= (1 - 0.22 * run)[..., None]
    return np.clip(img, 0, 1)


def coping_band(key="silicate"):
    """Rowlock course (bricks on edge, 65 mm faces) seen from the side and from above."""
    rng = _rng("mg-coping:" + key)
    W, H = ATLAS, COPING_ROWS[1] - COPING_ROWS[0]
    unit = 0.075 * BRICK_PX_M
    xx = np.arange(W)[None, :].astype(np.float32)
    col = np.floor(xx / unit).astype(int)
    tone = 0.90 + rng.normal(0, 0.06, int(col.max()) + 1)
    img = np.ones((H, W, 3), np.float32) * (np.array(SILICATE, np.float32) / 255.0) * tone[col][..., None] * 0.92
    img[:, (xx[0] - col[0] * unit) < 1.4] = np.array(MORTAR, np.float32) / 255.0
    img *= (0.9 + 0.18 * _smooth_noise(rng, H, W, 60))[..., None]          # lichen / soot on the top
    return np.clip(img, 0, 1)


def concrete(rect, key, white=False):
    rng = _rng("mg-conc:" + key)
    w, h = rect[2] - rect[0], rect[3] - rect[1]
    base = np.array((214, 212, 204) if white else (150, 148, 142), np.float32) / 255.0
    img = np.ones((h, w, 3), np.float32) * base
    img *= (0.90 + 0.16 * _smooth_noise(rng, h, w, 14))[..., None]
    img += rng.normal(0, 0.015, (h, w, 1)).astype(np.float32)
    yy = (np.arange(h)[:, None] / h).astype(np.float32)
    streak = np.clip(_smooth_noise(rng, 1, w, 48) - 0.5, 0, 1) * 2.0
    img *= (1 - (0.30 if white else 0.18) * streak * np.clip(yy * 1.6, 0, 1))[..., None]      # run-off down the face
    return np.clip(img, 0, 1)


def _font(px):
    return SG._font(max(6, int(px)))


def plaque(w, h, lines, key):
    """Enamel name plate: dark red field, thin white frame, a header line and one or two lines of neutral text."""
    im = Image.new("RGB", (w, h), PLAQUE_RED)
    d = ImageDraw.Draw(im)
    d.rectangle([2, 2, w - 3, h - 3], outline=(214, 206, 200), width=1)
    f0, f1 = _font(h * 0.15), _font(h * 0.21)
    y = h * 0.10
    for k, t in enumerate(lines[:3]):
        f = f0 if k == 0 else f1
        bb = d.textbbox((0, 0), t, font=f)
        d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], y), t, font=f, fill=(226, 218, 212))
        y += (bb[3] - bb[1]) * 1.45 + (h * 0.05 if k == 0 else 0)
    return im.filter(ImageFilter.GaussianBlur(0.4))


def text_board(w, h, header, lines, bg, header_fill, fill, italic_gap=0.0):
    im = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(im)
    d.rectangle([1, 1, w - 2, h - 2], outline=(224, 224, 224), width=2)
    n = len(lines)
    hh = h * (0.30 if n <= 3 else 0.16)
    f = _font(hh * 0.62)
    while f.size > 6 and d.textbbox((0, 0), header, font=f)[2] > w * 0.90:
        f = _font(f.size - 1)
    bb = d.textbbox((0, 0), header, font=f)
    d.text(((w - bb[2] + bb[0]) / 2 - bb[0], h * 0.06), header, font=f, fill=header_fill)
    y = h * 0.06 + hh
    step = (h * 0.92 - y) / max(n, 1)
    fl = _font(min(step * 0.70, h * 0.14))
    for t in lines:
        ff = fl
        while ff.size > 6 and d.textbbox((0, 0), t, font=ff)[2] > w * 0.86:
            ff = _font(ff.size - 1)
        d.text((w * 0.07, y), t, font=ff, fill=fill)
        y += step
    return im


def info_board(w, h):
    """Blue information board of an admissions desk: white pictogram tile (letter H, no protected emblem), a yellow
    header and lines of small neutral text (not legible from the drive)."""
    im = Image.new("RGB", (w, h), INFO_BLUE)
    d = ImageDraw.Draw(im)
    d.rectangle([1, 1, w - 2, h - 2], outline=(230, 230, 230), width=2)
    s = int(w * 0.26)
    x0, y0 = int(w * 0.08), int(h * 0.06)
    d.rounded_rectangle([x0, y0, x0 + s, y0 + s], radius=4, fill=(240, 240, 238))
    t = max(3, s // 6)
    d.rectangle([x0 + s * 0.22, y0 + s * 0.18, x0 + s * 0.22 + t, y0 + s * 0.82], fill=INFO_BLUE)
    d.rectangle([x0 + s * 0.78 - t, y0 + s * 0.18, x0 + s * 0.78, y0 + s * 0.82], fill=INFO_BLUE)
    d.rectangle([x0 + s * 0.22, y0 + s * 0.5 - t / 2, x0 + s * 0.78, y0 + s * 0.5 + t / 2], fill=INFO_BLUE)
    yel = (246, 214, 40)
    f = _font(h * 0.085)
    for k, t_ in enumerate(("IZBA", "PRZYJĘĆ")):
        d.text((x0 + s + w * 0.06, y0 + k * h * 0.10), t_, font=f, fill=yel)
    fs = _font(h * 0.045)
    y = y0 + s + h * 0.05
    for k, t_ in enumerate(("wejście od strony", "budynku głównego", "", "rejestracja", "całodobowo", "",
                            "informacja", "w portierni")):
        if t_:
            bb = d.textbbox((0, 0), t_, font=fs)
            d.text(((w - bb[2]) / 2, y), t_, font=fs, fill=(236, 240, 244) if k % 3 else yel)
        y += h * 0.075
    return im


def c2_face():
    """C-2 `nakaz jazdy w prawo za znakiem`: blue disc, white arrow that runs up and bends to the right (the straight
    horizontal arrow is C-1, `przed znakiem`). Drawn from primitives like streetscape.signs.c9."""
    im, d = SG.disc(SG.BLUE)
    S_ = SG.S
    st = S_ * 0.10
    x0 = S_ * 0.36
    yb, yt = S_ * 0.78, S_ * 0.44
    d.rectangle([x0 - st / 2, yt, x0 + st / 2, yb], fill=SG.WHITE)
    d.pieslice([x0 - st / 2, yt - st * 1.5, x0 + st * 2.5, yt + st * 1.5], 180, 270, fill=SG.WHITE)
    d.pieslice([x0 + st / 2, yt - st * 0.5, x0 + st * 1.5, yt + st * 0.5], 180, 270, fill=SG.BLUE)
    d.rectangle([x0 + st, yt - st * 1.5, S_ * 0.58, yt - st * 0.5], fill=SG.WHITE)
    ya = yt - st
    d.polygon([(S_ * 0.80, ya), (S_ * 0.56, ya - S_ * 0.15), (S_ * 0.56, ya + S_ * 0.15)], fill=SG.WHITE)
    return im


def sign_face(code, px, fade=0.0):
    """(shape, RGB image px x px) of a vertical sign face on a neutral ground (the mesh is cut to the outline)."""
    if code == "C-2":
        shape, im = "disc", c2_face()
    else:
        shape, im = SG.face(code)
    bg = Image.new("RGBA", im.size, (*SG.GREY_BACK, 255))
    im = Image.alpha_composite(bg, im.convert("RGBA")).convert("RGB").resize((px, px), Image.LANCZOS)
    if fade:                                   # sun-faded foil: red loses chroma first (old plates on gate posts)
        a = np.asarray(im).astype(np.float32) / 255.0
        lum = (a @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
        a = (a * (1 - 0.55 * fade) + lum * (0.55 * fade)) * (1 - 0.12 * fade) + 0.04 * fade
        im = Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))
    return shape, im


BOARDS = {
    # name: (drawer(w_px, h_px) -> RGB image)
    "entry_rules": lambda w, h: text_board(w, h, "WJAZD NA PODSTAWIE", ["- przepustki", "- skierowania", "- biletu"],
                                           BOARD_BLUE, (236, 238, 242), (236, 238, 242)),
    "admissions": lambda w, h: info_board(w, h),
    "fee": lambda w, h: text_board(w, h, "OPŁATA", ["ZA WJAZD"], BOARD_BLUE, (236, 238, 242), (236, 238, 242)),
}
PLAQUE_TEXTS = [("SZPITAL", "Oddział I"), ("SZPITAL", "Oddział II"), ("SZPITAL", "Poradnie"), ("SZPITAL", "Pracownie"),
                ("SZPITAL", "Administracja"), ("SZPITAL", "Apteka")]
SWATCH = {"galv": (146, 149, 150), "roof": (58, 60, 62), "back": SG.GREY_BACK, "white": (226, 226, 220),
          "glass": (214, 208, 180), "green": (52, 92, 66)}


class Atlas:
    """Packs the fixed bands (brick, coping, concrete) and the faces / boards / plaques of one kit; returns uv rects."""

    def __init__(self, key):
        self.key = key
        self.im = Image.new("RGB", (ATLAS, ATLAS), (128, 128, 128))
        b = (brick_band(key) * 255 + 0.5).astype(np.uint8)
        self.im.paste(Image.fromarray(b), (0, 0))
        c = (coping_band(key) * 255 + 0.5).astype(np.uint8)
        self.im.paste(Image.fromarray(c), (0, COPING_ROWS[0]))
        for rect, white in ((CONC_RECT, False), (WHITE_RECT, True)):
            a = (concrete(rect, key + str(white), white) * 255 + 0.5).astype(np.uint8)
            self.im.paste(Image.fromarray(a), rect[:2])
        self.x, self.y, self.rowh = 0, 530, 0
        self.sw = {}
        d = ImageDraw.Draw(self.im)
        for k, (name, col) in enumerate(sorted(SWATCH.items())):
            x0 = 8 + k * 40
            d.rectangle([x0, ATLAS - 40, x0 + 31, ATLAS - 9], fill=col)
            self.sw[name] = ((x0 + 16) / ATLAS, 1 - (ATLAS - 24) / ATLAS)

    def put(self, im):
        w, h = im.size
        if self.x + w + 4 > ATLAS:
            self.x, self.y, self.rowh = 0, self.y + self.rowh + 4, 0
        if self.y + h > ATLAS - 48:
            raise ValueError("masonry_gate: atlas full")
        self.im.paste(im, (self.x, self.y))
        r = (self.x, self.y, self.x + w, self.y + h)
        self.x += w + 4
        self.rowh = max(self.rowh, h)
        return r


def _uv(px, py):
    return (px / ATLAS, 1 - py / ATLAS)


# ------------------------------------------------------------------------------------------------------- geometry
class Kit:
    """Mesh builder in region-local metres relative to the kit origin (x = east, y = north, z up above the ground)."""

    def __init__(self, key):
        self.key = key
        self.mat = f"sign_{key}"
        self.atlas = Atlas(key)
        self.m = PP.Mesh()
        self.col = PP.Mesh()
        self.rng = _rng("mg-kit:" + key)
        self.tris = 0

    # every quad: corners a, b, c, d counter-clockwise seen from outside (normal = (b-a) x (c-a))
    def quad(self, a, b, c, d, uvs):
        self.m.add(self.mat, [a, b, c, d], [(0, 1, 2), (0, 2, 3)], uvs)
        self.tris += 2

    def flat(self, a, b, c, d, name):
        self.quad(a, b, c, d, [self.atlas.sw[name]] * 4)

    def wall_face(self, p0, p1, z0, z1, u0=None):
        """Vertical brick face from p0 to p1 (2D), seen with p0 on the viewer's LEFT; u runs left to right."""
        L = float(np.hypot(*(np.asarray(p1) - p0)))
        if u0 is None:
            u0 = float(self.rng.uniform(0.0, max(BRICK_BAND_M[0] - L, 0.0)))
        # snap the window to whole courses / half bricks so neighbouring faces do not shear the bond visibly
        u0 = round(u0 / 0.13) * 0.13
        u0 = min(u0, max(BRICK_BAND_M[0] - L, 0.0))
        xa, xb = u0 * BRICK_PX_M, (u0 + L) * BRICK_PX_M
        ya = (BRICK_BAND_M[1] - BRICK_BELOW_M - z0) * BRICK_PX_M
        yb = (BRICK_BAND_M[1] - BRICK_BELOW_M - z1) * BRICK_PX_M
        # seen from outside with p0 on the left, the outward normal is to the RIGHT of p0 -> p1 rotated... the quad
        # (p0 low, p1 low, p1 high, p0 high) has normal (p1-p0) x up = (dy, -dx, 0): the right-hand side of p0 -> p1
        self.quad([p0[0], p0[1], z0], [p1[0], p1[1], z0], [p1[0], p1[1], z1], [p0[0], p0[1], z1],
                  [_uv(xa, ya), _uv(xb, ya), _uv(xb, yb), _uv(xa, yb)])

    def rect_top(self, ring, z, rect):
        """Horizontal quad (ring counter-clockwise seen from above) textured from the atlas rect (px)."""
        x0, y0, x1, y1 = rect
        self.quad(*[[p[0], p[1], z] for p in ring], [_uv(x0, y1), _uv(x1, y1), _uv(x1, y0), _uv(x0, y0)])

    def rect_side(self, p0, p1, z0, z1, rect):
        x0, y0, x1, y1 = rect
        self.quad([p0[0], p0[1], z0], [p1[0], p1[1], z0], [p1[0], p1[1], z1], [p0[0], p0[1], z1],
                  [_uv(x0, y1), _uv(x1, y1), _uv(x1, y0), _uv(x0, y0)])

    def prism(self, ring, z0, z1, side, top=None, bottom=False):
        """ring counter-clockwise seen from above; side(p0, p1) draws one wall (outward normal on the right of
        p0 -> p1 for a CCW ring), top(ring, z) the lid."""
        n = len(ring)
        for k in range(n):
            side(ring[k], ring[(k + 1) % n], z0, z1)
        if top is not None:
            top(ring, z1)
        if bottom:
            self.flat(*[[p[0], p[1], z0] for p in ring[::-1]], "back")

    def box_ring(self, c, u, hw, hd):
        """4 corners (CCW from above) of a rectangle centred at c, half width hw along unit u, half depth hd."""
        u = np.asarray(u, float)
        v = np.array([-u[1], u[0]])
        c = np.asarray(c, float)
        return [c - u * hw - v * hd, c + u * hw - v * hd, c + u * hw + v * hd, c - u * hw + v * hd]

    def conc_rect(self, w_m, h_m, white=False):
        R = WHITE_RECT if white else CONC_RECT
        w = min(int(w_m * BRICK_PX_M), R[2] - R[0] - 2)
        h = min(max(int(h_m * BRICK_PX_M), 4), R[3] - R[1] - 2)
        x0 = R[0] + int(self.rng.integers(0, R[2] - R[0] - w))
        y0 = R[1] + int(self.rng.integers(0, R[3] - R[1] - h))
        return (x0, y0, x0 + w, y0 + h)

    def brick_pier(self, c, u, w, d, z1, cap=True, z0=-BRICK_BELOW_M + 0.05):
        ring = self.box_ring(c, u, w / 2, d / 2)
        self.prism(ring, z0, z1, self.wall_face)
        if cap:                                  # precast concrete cap, 4 cm overhang
            cr = self.box_ring(c, u, w / 2 + 0.04, d / 2 + 0.04)
            self.prism(cr, z1, z1 + 0.07,
                       lambda a, b, za, zb: self.rect_side(a, b, za, zb, self.conc_rect(float(np.hypot(*(b - a))), 0.07)),
                       lambda r, z: self.rect_top(r, z, self.conc_rect(w + 0.08, d + 0.08)), bottom=True)
        else:
            self.rect_top(ring, z1, self.conc_rect(w, d))
        self.col.box("collision_building", [c[0], c[1], z1 / 2], max(w, d) / 2, max(w, d) / 2, z1 / 2)
        return ring

    def wall(self, P, h, thick, coping):
        P = [np.asarray(p, float) for p in P]
        for a, b in zip(P[:-1], P[1:]):
            L = float(np.hypot(*(b - a)))
            if L < 0.05:
                continue
            u = (b - a) / L
            n = np.array([u[1], -u[0]]) * (thick / 2)            # right of a -> b
            k = max(1, int(math.ceil(L / 4.0)))
            for i in range(k):
                s0, s1 = a + u * (L * i / k), a + u * (L * (i + 1) / k)
                self.wall_face(s0 + n, s1 + n, -BRICK_BELOW_M + 0.05, h)        # right face
                self.wall_face(s1 - n, s0 - n, -BRICK_BELOW_M + 0.05, h)        # left face
                # coping: rowlock course 2 cm proud on both sides
                nn = n * (1 + 0.04 / thick)
                x0 = int(self.rng.integers(0, ATLAS - int(L / k * BRICK_PX_M) - 1))
                rc = (x0, COPING_ROWS[0], x0 + int(L / k * BRICK_PX_M), COPING_ROWS[1])
                rs = (x0, COPING_ROWS[0], x0 + int(L / k * BRICK_PX_M), COPING_ROWS[0] + 15)
                self.rect_side(s0 + nn, s1 + nn, h, h + coping, rs)
                self.rect_side(s1 - nn, s0 - nn, h, h + coping, rs)
                self.rect_top([s0 + nn, s1 + nn, s1 - nn, s0 - nn], h + coping, rc)
            self.col.add("collision_building", *_col_slab(a, b, thick, h + coping))
        # end faces
        for p, q in ((P[0], P[1]), (P[-1], P[-2])):
            u = (p - q) / np.hypot(*(p - q))
            n = np.array([u[1], -u[0]]) * (thick / 2)
            self.wall_face(p + n, p - n, -BRICK_BELOW_M + 0.05, h + coping)

    def panel(self, c, facing, w, h, z, rect, proud=0.02, back=True):
        """Flat panel centred at c (2D) at height z (centre), looking along the unit vector `facing`."""
        f = np.asarray(facing, float)
        right = np.array([-f[1], f[0]])                  # viewer's right when looking at the face (viewer looks -f)
        c = np.asarray(c, float) + f * proud
        a, b = c - right * (w / 2), c + right * (w / 2)
        x0, y0, x1, y1 = rect
        self.quad([a[0], a[1], z - h / 2], [b[0], b[1], z - h / 2], [b[0], b[1], z + h / 2], [a[0], a[1], z + h / 2],
                  [_uv(x0, y1), _uv(x1, y1), _uv(x1, y0), _uv(x0, y0)])
        if back:
            self.flat([b[0], b[1], z - h / 2], [a[0], a[1], z - h / 2], [a[0], a[1], z + h / 2], [b[0], b[1], z + h / 2],
                      "back")

    def face(self, c, facing, code, size, z, fade=0.0, proud=0.03):
        """Sign plate cut to its outline (disc 20-gon / octagon), front from the atlas, grey back."""
        px = int(round(size * FACE_PX_M))
        shape, im = sign_face(code, px, fade)
        x0, y0, x1, y1 = self.atlas.put(im)
        f = np.asarray(facing, float)
        right = np.array([-f[1], f[0]])
        c = np.asarray(c, float) + f * proud
        n = {"disc": 20, "octagon": 8}.get(shape, 4)
        rot = {"disc": 0.0, "octagon": math.pi / 8}.get(shape, math.pi / 4)
        rr = size / 2 * (1 / math.cos(math.pi / 4) if n == 4 else 1.0)
        pts = [(rr * math.cos(rot + 2 * math.pi * k / n), rr * math.sin(rot + 2 * math.pi * k / n)) for k in range(n)]
        if n == 4:
            pts = [(max(-size / 2, min(size / 2, x)), max(-size / 2, min(size / 2, zz))) for x, zz in pts]
        V = [[c[0] + right[0] * x, c[1] + right[1] * x, z + zz] for x, zz in pts]
        UV = [_uv(x0 + (0.5 + x / size) * (x1 - x0), y0 + (0.5 - zz / size) * (y1 - y0)) for x, zz in pts]
        # pts run counter-clockwise for a viewer in front (x = viewer's right, z up): normal toward the viewer
        self.m.add(self.mat, V, [(0, k, k + 1) for k in range(1, n - 1)], UV)
        Vb = [[v[0] - f[0] * 0.02, v[1] - f[1] * 0.02, v[2]] for v in V]
        self.m.add(self.mat, Vb, [(0, k + 1, k) for k in range(1, n - 1)], [self.atlas.sw["back"]] * n)
        self.tris += 2 * (n - 2)

    def tube(self, p, z0, z1, r, name, seg=8):
        pm = PP.Mesh()
        pm.tube("p", [p[0], p[1], z0], [p[0], p[1], z1], r, None, seg)
        Vs, Ts, _ = pm.prims["p"]
        off = 0
        for V, T in zip(Vs, Ts):
            self.m.add(self.mat, V, np.asarray(T) - off, [self.atlas.sw[name]] * len(V))
            off += len(V)
            self.tris += len(T)

    def meshes(self):
        return self.m, self.m, self.col


def _col_slab(a, b, thick, h):
    u = (b - a) / np.hypot(*(b - a))
    n = np.array([u[1], -u[0]]) * (thick / 2)
    ring = [a + n, b + n, b - n, a - n]
    V = [[p[0], p[1], 0.0] for p in ring] + [[p[0], p[1], h] for p in ring]
    T = []
    for k in range(4):
        k2 = (k + 1) % 4
        T += [(k, k2, 4 + k2), (k, 4 + k2, 4 + k)]
    T += [(4, 5, 6), (4, 6, 7)]
    return V, T


# -------------------------------------------------------------------------------------------------------- planning
def _bearing_vec(deg):
    a = math.radians(float(deg))
    return np.array([math.sin(a), math.cos(a)])


class Frame:
    def __init__(self, anchor):
        self.o = np.asarray(anchor["at_en"], float)
        f = _bearing_vec(anchor["enter_bearing_deg"])
        self.out = -f                                    # +a: toward the street
        self.right = np.array([f[1], -f[0]])             # +l: right of a vehicle driving in

    def en(self, la):
        return self.o + self.right * float(la[0]) + self.out * float(la[1])

    def facing(self, spec):
        return _bearing_vec(spec["facing_deg"]) if "facing_deg" in spec else self.out


def kit_key(o):
    return "MG" + hashlib.sha1(repr(sorted((k, repr(v)) for k, v in o.items()
                                           if k not in ("reason", "verify", "confidence"))).encode()).hexdigest()[:8]


def plan(overrides):
    """[{id, key, frame, spec, wall_lines (region-local 2D arrays), solids [(E, N)]}] for every masonry_gate override."""
    out = []
    for o in overrides:
        if o.get("kind") != KIND:
            continue
        fr = Frame(o["anchor"])
        lines = [np.array([fr.en(p) for p in w["line_la"]]) for w in o.get("walls", [])]
        solids = [fr.en(p["at_la"]) for p in o.get("piers", [])]
        solids += [fr.en(p) for w in o.get("walls", []) for p in w.get("pillars_la", [])]
        out.append({"id": o["id"], "key": kit_key(o), "frame": fr, "spec": o, "wall_lines": lines, "solids": solids})
    return out


def fence_cut(kits):
    """Polygons where the rule fence must not be drawn (the wall stands there)."""
    from shapely.geometry import LineString
    out = []
    for k in kits:
        d = float(k["spec"].get("fence_cut_m", 1.2))
        out += [LineString(ln).buffer(d) for ln in k["wall_lines"] if len(ln) >= 2]
    return out


def build_kit(k):
    """(lod0, lod1, collision, atlas image, tris) of one planned kit; vertices relative to the anchor, x east, y north."""
    o, fr = k["spec"], k["frame"]
    kit = Kit(k["key"])
    rel = lambda la: fr.en(la) - fr.o                                   # noqa: E731
    along = fr.right                                                     # the gate line
    for w in o.get("walls", []):
        h, th, cop = float(w.get("height_m", 1.75)), float(w.get("thick_m", 0.25)), float(w.get("coping_m", 0.12))
        kit.wall([rel(p) for p in w["line_la"]], h, th, cop)
        ps, ph = float(w.get("pillar_m", 0.38)), float(w.get("pillar_h_m", h + cop + 0.12))
        P = [rel(p) for p in w["line_la"]]
        for p in w.get("pillars_la", []):
            c = rel(p)
            j = int(np.argmin([np.hypot(*(q - c)) for q in P]))
            a, b = (P[j - 1], P[j]) if j > 0 else (P[0], P[1])
            u = (b - a) / np.hypot(*(b - a))
            kit.brick_pier(c, u, ps, ps, ph, cap=True)
        pq = w.get("plaques")
        if pq:
            f = fr.facing(pq)
            right = np.array([-f[1], f[0]])
            c0 = rel(pq["at_la"]) + f * (th / 2)
            pw, phh = pq.get("size_m", [0.70, 0.28])
            cols, count = int(pq.get("cols", 2)), int(pq.get("count", 5))
            texts = pq.get("texts") or PLAQUE_TEXTS
            for i in range(count):
                r_, c_ = divmod(i, cols)
                im = plaque(int(pw * FACE_PX_M), int(phh * FACE_PX_M), texts[i % len(texts)], f"{k['key']}:{i}")
                rect = kit.atlas.put(im)
                cc = c0 + right * ((c_ - (cols - 1) / 2) * (pw + 0.03))
                kit.panel(cc, f, pw, phh, float(pq.get("z_m", 1.45)) - r_ * (phh + 0.03), rect, proud=0.015, back=False)
    for p in o.get("piers", []):
        w_, d_ = p.get("size_m", [0.38, 0.38])
        kit.brick_pier(rel(p["at_la"]), along, float(w_), float(d_), float(p["height_m"]), cap=bool(p.get("cap", False)),
                       z0=float(p.get("z0_m", -BRICK_BELOW_M + 0.05)))
    pf = o.get("platform")
    if pf:
        l0, a0, l1, a1 = pf["rect_la"]
        ring = [rel((l0, a0)), rel((l0, a1)), rel((l1, a1)), rel((l1, a0))]
        if _signed_area(ring) < 0:
            ring = ring[::-1]
        hp = float(pf.get("height_m", 0.25))
        kit.prism(ring, -0.2, hp,
                  lambda a, b, za, zb: kit.rect_side(a, b, za, zb, kit.conc_rect(float(np.hypot(*(b - a))), zb - za)),
                  lambda r, z: kit.rect_top(r, z, kit.conc_rect(abs(l1 - l0), abs(a1 - a0))))
        cx, cy = np.mean(ring, axis=0)
        kit.col.add("collision_building", *_col_ring(ring, hp))
    cn = o.get("canopy")
    if cn:
        l0, a0, l1, a1 = cn["rect_la"]
        ring = [rel((l0, a0)), rel((l0, a1)), rel((l1, a1)), rel((l1, a0))]
        if _signed_area(ring) < 0:
            ring = ring[::-1]
        z0, th = float(cn["z_m"]), float(cn.get("thick_m", 0.20))
        white = lambda a, b, za, zb: kit.rect_side(a, b, za, zb, kit.conc_rect(float(np.hypot(*(b - a))), zb - za, True))  # noqa: E731
        kit.prism(ring, z0, z0 + th, white)
        kit.quad(*[[p[0], p[1], z0] for p in ring[::-1]],                 # soffit
                 [_uv(*q) for q in _rect_corners(kit.conc_rect(abs(l1 - l0), abs(a1 - a0), True))])
        c = np.mean(ring, axis=0)                                           # sheet roof, 6 cm overhang, fall to the back
        roof = [c + (p - c) * 1.0 + (p - c) / np.hypot(*(p - c)) * 0.08 for p in ring]
        kit.prism(roof, z0 + th, z0 + th + 0.05, lambda a, b, za, zb: kit.flat([a[0], a[1], za], [b[0], b[1], za],
                                                                               [b[0], b[1], zb], [a[0], a[1], zb], "roof"),
                  lambda r, z: kit.flat(*[[p[0], p[1], z] for p in r], "roof"))
    for s in o.get("faces", []):
        kit.face(rel(s["at_la"]), fr.facing(s), s["face"], float(s.get("size_m", 0.6)), float(s["z_m"]),
                 fade=float(s.get("fade", 0.0)))
    for b in o.get("boards", []):
        w_, h_ = b["size_m"]
        rect = kit.atlas.put(BOARDS[b["board"]](int(w_ * FACE_PX_M), int(h_ * FACE_PX_M)))
        kit.panel(rel(b["at_la"]), fr.facing(b), float(w_), float(h_), float(b["z_m"]), rect)
    for p in o.get("posts", []):
        c = rel(p["at_la"])
        hp = float(p.get("height_m", 3.0))
        r = float(p.get("d_m", 0.076)) / 2
        kit.tube(c, -0.05, hp, r, "galv")
        kit.col.tube("collision_steel", [c[0], c[1], 0], [c[0], c[1], min(hp, 2.6)], 0.05, None, 4)
        if p.get("lantern"):                             # park lantern: opal bowl under a flat hood
            kit.tube(c, hp, hp + 0.30, 0.13, "glass", seg=8)
            kit.tube(c, hp + 0.30, hp + 0.36, 0.24, "roof", seg=8)
        f = fr.facing(p)
        for s in p.get("faces", []):
            kit.face(c + f * r, f, s["face"], float(s.get("size_m", 0.6)), float(s["z_m"]), fade=float(s.get("fade", 0.0)))
        pt = p.get("plate")
        if pt:
            w_, h_ = pt.get("size_m", [0.40, 0.14])
            right = np.array([-f[1], f[0]])
            cc = c + f * (r + 0.02)
            a, b = cc - right * (w_ / 2), cc + right * (w_ / 2)
            z = float(pt["z_m"])
            kit.flat([a[0], a[1], z - h_ / 2], [b[0], b[1], z - h_ / 2], [b[0], b[1], z + h_ / 2], [a[0], a[1], z + h_ / 2],
                     "white")
    return (*kit.meshes(), kit.atlas.im, kit.tris)


def _signed_area(ring):
    return 0.5 * sum(ring[k][0] * ring[(k + 1) % len(ring)][1] - ring[(k + 1) % len(ring)][0] * ring[k][1]
                     for k in range(len(ring)))


def _rect_corners(rect):
    x0, y0, x1, y1 = rect
    return [(x0, y1), (x1, y1), (x1, y0), (x0, y0)]


def _col_ring(ring, h):
    V = [[p[0], p[1], 0.0] for p in ring] + [[p[0], p[1], h] for p in ring]
    n = len(ring)
    T = []
    for k in range(n):
        k2 = (k + 1) % n
        T += [(k, k2, n + k2), (k, n + k2, n + k)]
    T += [(n, n + k, n + k + 1) for k in range(1, n - 1)]
    return V, T


def build(pl, kits, boards, report, carriage=None):
    """Place every planned kit: registers prototype masonry_gate_<key>, its atlas in `boards` (exported at native
    resolution, see streetscape.export) and one instance at the anchor (yaw 0: the mesh is already in E/N)."""
    from shapely.geometry import Point
    rep = {"kits": [], "stale": []}
    for k in kits:
        fr = k["frame"]
        try:
            lod0, lod1, col, im, tris = build_kit(k)
        except (KeyError, ValueError) as e:
            rep["stale"].append(f"{k['id']}: {e}")
            continue
        on_road = []
        if carriage is not None:
            on_road = [[round(float(p[0]), 1), round(float(p[1]), 1)] for p in k["solids"]
                       if carriage.contains(Point(float(p[0]), float(p[1])))]
        proto = f"masonry_gate_{k['key']}"
        PROTOS[proto] = (lod0, lod1, col)
        boards[k["key"]] = (ATLAS / FACE_PX_M, ATLAS / FACE_PX_M, im)
        # seat on the lowest ground under the solids, so no pier floats (the brick band continues 0.2 m below z = 0)
        pts = np.array(k["solids"] + [fr.o])
        zs = np.asarray(pl.zsurf(pts[:, 0], pts[:, 1]), float)
        z = float(np.median(zs[:-1])) if len(zs) > 1 else float(zs[-1])
        pl.add(proto, fr.o, 0.0, z=z, src=f"override:{k['id']}")
        rep["kits"].append({"id": k["id"], "proto": proto, "anchor": [round(float(v), 1) for v in fr.o],
                            "z": round(z, 2), "ground_range_m": round(float(zs.max() - zs.min()), 2), "tris": int(tris),
                            "wall_m": round(float(sum(np.hypot(*np.diff(ln, axis=0).T).sum() for ln in k["wall_lines"])), 1),
                            "on_carriageway": on_road,
                            "faces": [s["face"] for s in k["spec"].get("faces", [])] +
                                     [s["face"] for p in k["spec"].get("posts", []) for s in p.get("faces", [])]})
    report["masonry_gates"] = rep
    return rep
