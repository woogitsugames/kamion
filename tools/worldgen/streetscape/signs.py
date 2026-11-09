"""Our own vector reproductions of Polish vertical sign faces (PNG textures for the plate prototypes).

Design per Załącznik nr 1 of the 2003 sign regulation (t.j. Dz.U. 2019 poz. 2311 + Dz.U. 2021 poz. 2066):
  A (warning)      yellow field, red border; A-7 is an inverted triangle without a symbol.
  B (prohibition)  white disc, red ring; B-33 black numerals; B-20 red octagon, white border, "STOP".
  C (mandatory)    blue disc, white symbol; C-12 three arrows in a circle (counter-clockwise).
  D (information)  D-1 yellow square diamond with a white border; D-6 / D-15 blue square, white inner field
                   with a black symbol (pedestrian / bus).
  E (direction)    schematic E-2 boards: green field for national-road destinations, white field for local ones,
                   red route shields with white numbers (E-15a).
Colours are the nominal sRGB values of the sign foils (approximate, WORKING_VALUE until checked against
the regulation's colour table). Pictograms are simplified, drawn here from primitives - no traced artwork.
Text font: DejaVu Sans Bold (Bitstream Vera licence, shipped with matplotlib) - schematic, not the
official "Drogowskaz" typeface.
"""

from __future__ import annotations

import io
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RED = (196, 30, 36)
YELLOW = (250, 196, 0)
BLUE = (0, 84, 160)
WHITE = (245, 245, 242)
BLACK = (24, 24, 24)
GREEN = (0, 112, 72)
GREY_BACK = (150, 152, 152)
S = 512   # texture size (square plates)


def _font(px):
    import matplotlib
    p = Path(matplotlib.__file__).parent / "mpl-data" / "fonts" / "ttf" / "DejaVuSans-Bold.ttf"
    return ImageFont.truetype(str(p), px)


def _img(w=S, h=S):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def _poly(n, r, cx, cy, rot):
    return [(cx + r * math.cos(rot + 2 * math.pi * k / n), cy + r * math.sin(rot + 2 * math.pi * k / n)) for k in range(n)]


def a7():
    im = _img()
    d = ImageDraw.Draw(im)
    # inverted triangle, side = S-8
    s = S - 16
    h = s * math.sqrt(3) / 2
    top = (S - h) / 2
    outer = [(8, top), (S - 8, top), (S / 2, top + h)]
    d.polygon(outer, fill=RED)
    k = 0.72
    cx, cy = S / 2, top + h / 3
    inner = [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in outer]
    d.polygon(inner, fill=YELLOW)
    return im


def disc(field, ring=None):
    im = _img()
    d = ImageDraw.Draw(im)
    if ring:
        d.ellipse([4, 4, S - 4, S - 4], fill=ring)
        d.ellipse([S * 0.1, S * 0.1, S * 0.9, S * 0.9], fill=field)
    else:
        d.ellipse([4, 4, S - 4, S - 4], fill=field)
    return im, d


def b33(v):
    im, d = disc(WHITE, RED)
    f = _font(int(S * 0.42))
    t = str(int(v))
    bb = d.textbbox((0, 0), t, font=f)
    d.text(((S - (bb[2] - bb[0])) / 2 - bb[0], (S - (bb[3] - bb[1])) / 2 - bb[1]), t, font=f, fill=BLACK)
    return im


def b20():
    im = _img()
    d = ImageDraw.Draw(im)
    d.polygon(_poly(8, S / 2 - 4, S / 2, S / 2, math.pi / 8), fill=WHITE)
    d.polygon(_poly(8, S / 2 - 18, S / 2, S / 2, math.pi / 8), fill=RED)
    f = _font(int(S * 0.24))
    bb = d.textbbox((0, 0), "STOP", font=f)
    d.text(((S - (bb[2] - bb[0])) / 2 - bb[0], (S - (bb[3] - bb[1])) / 2 - bb[1]), "STOP", font=f, fill=WHITE)
    return im


def _arrow_arc(d, cx, cy, r, a0, a1, w, col):
    pts = [(cx + r * math.cos(a), cy - r * math.sin(a)) for a in [a0 + (a1 - a0) * t / 24 for t in range(25)]]
    d.line(pts, fill=col, width=int(w), joint="curve")
    # arrow head at a1 (counter-clockwise travel)
    ax, ay = pts[-1]
    tang = (-math.sin(a1), -math.cos(a1))           # CCW tangent in image coords
    nrm = (math.cos(a1), -math.sin(a1))
    L, W = w * 2.0, w * 1.6
    tip = (ax + tang[0] * L, ay + tang[1] * L)
    d.polygon([tip, (ax + nrm[0] * W, ay + nrm[1] * W), (ax - nrm[0] * W, ay - nrm[1] * W)], fill=col)


def c12():
    im, d = disc(BLUE)
    for k in range(3):
        a0 = math.radians(100 + 120 * k)
        _arrow_arc(d, S / 2, S / 2, S * 0.26, a0, a0 + math.radians(62), S * 0.06, WHITE)
    return im


def d1():
    im = _img()
    d = ImageDraw.Draw(im)
    d.polygon([(S / 2, 4), (S - 4, S / 2), (S / 2, S - 4), (4, S / 2)], fill=WHITE)
    d.polygon([(S / 2, 40), (S - 40, S / 2), (S / 2, S - 40), (40, S / 2)], fill=YELLOW)
    return im


def square(sym):
    im = _img()
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, S - 4, S - 4], radius=24, fill=BLUE)
    if sym == "D-6":
        d.polygon([(S / 2, S * 0.14), (S * 0.86, S * 0.84), (S * 0.14, S * 0.84)], fill=WHITE)
        # zebra + walking figure (simplified)
        for k in range(4):
            x = S * (0.30 + 0.11 * k)
            d.rectangle([x, S * 0.76, x + S * 0.06, S * 0.80], fill=BLACK)
        cx = S * 0.52
        d.ellipse([cx - 16, S * 0.36, cx + 16, S * 0.42], fill=BLACK)
        d.line([(cx, S * 0.43), (cx - 6, S * 0.58)], fill=BLACK, width=18)
        d.line([(cx - 6, S * 0.58), (cx - 40, S * 0.72)], fill=BLACK, width=16)
        d.line([(cx - 6, S * 0.58), (cx + 28, S * 0.72)], fill=BLACK, width=16)
        d.line([(cx - 2, S * 0.46), (cx - 36, S * 0.55)], fill=BLACK, width=12)
        d.line([(cx - 2, S * 0.46), (cx + 30, S * 0.53)], fill=BLACK, width=12)
    elif sym == "D-15":
        d.rectangle([S * 0.16, S * 0.12, S * 0.84, S * 0.88], fill=WHITE)
        d.rounded_rectangle([S * 0.24, S * 0.30, S * 0.76, S * 0.70], radius=14, fill=BLACK)
        for k in range(3):
            x = S * (0.28 + 0.16 * k)
            d.rectangle([x, S * 0.35, x + S * 0.12, S * 0.48], fill=WHITE)
        for x in (0.33, 0.67):
            d.ellipse([S * x - 22, S * 0.66, S * x + 22, S * 0.74], fill=BLACK)
        f = _font(int(S * 0.10))
        d.text((S * 0.36, S * 0.74), "BUS", font=f, fill=BLACK)
    return im


def direction_board(dests, refs, green):
    """E-2 style board (schematic): arrow + destinations (+ red route shields). Returns (image, w_m, h_m)."""
    lines = [x.strip() for x in dests if x.strip()][:3]
    f = _font(64)
    px = 2.0 / 512 * 64
    tw = max((ImageDraw.Draw(_img()).textbbox((0, 0), t, font=f)[2] for t in lines), default=200)
    shields = [r for r in refs if r][:2]
    W = int(tw + 180 + 140 * len(shields) + 60)
    H = int(40 + 90 * max(len(lines), 1))
    im = Image.new("RGBA", (W, H), (*(GREEN if green else WHITE), 255))
    d = ImageDraw.Draw(im)
    fg = WHITE if green else BLACK
    d.rectangle([6, 6, W - 7, H - 7], outline=fg, width=8)
    # arrow (up-right)
    ax, ay = 70, H / 2
    d.line([(ax - 20, ay + 34), (ax + 26, ay - 20)], fill=fg, width=16)
    d.polygon([(ax + 44, ay - 40), (ax + 4, ay - 30), (ax + 34, ay)], fill=fg)
    x = 140
    for i, t in enumerate(lines):
        d.text((x, 26 + 90 * i), t, font=f, fill=fg)
    sx = x + tw + 40
    for r in shields:
        d.rounded_rectangle([sx, H / 2 - 40, sx + 110, H / 2 + 40], radius=10, fill=RED, outline=WHITE, width=5)
        fr = _font(52 if len(r) < 3 else 40)
        bb = d.textbbox((0, 0), r, font=fr)
        d.text((sx + 55 - (bb[2] - bb[0]) / 2 - bb[0], H / 2 - (bb[3] - bb[1]) / 2 - bb[1]), r, font=fr, fill=WHITE)
        sx += 130
    return im, W * px / 64 * 0.36, H * px / 64 * 0.36


def overhead_board(rows, row_m=0.62):
    """Overhead direction board on a gantry (our own schematic drawing after the CC0 photo of the gantry at the
    Andersa / Rondo Putry approach): green field, white border, one row per destination with route shields
    (E-roads: green shield with a white border, national roads: red shield) and a downward lane arrow on the
    left. rows = [(refs, destination)]. Returns (image, width_m, height_m); row height `row_m` (WORKING_VALUE)."""
    px_m = 160                                     # pixels per metre
    rh = int(row_m * px_m)
    f = _font(int(rh * 0.52))
    fs = _font(int(rh * 0.36))
    probe = ImageDraw.Draw(_img())
    shield_w = int(rh * 0.95)
    nsh = max(len(r[0]) for r in rows)
    tw = max(probe.textbbox((0, 0), d, font=f)[2] for _, d in rows)
    W = int(rh * 0.9 + nsh * (shield_w + 12) + tw + rh * 0.6)
    H = int(rh * len(rows) + rh * 0.3)
    im = Image.new("RGBA", (W, H), (*GREEN, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([5, 5, W - 6, H - 6], outline=WHITE, width=8)
    ax = int(rh * 0.45)                             # downward arrow (lane assignment)
    d.line([(ax, H * 0.22), (ax, H * 0.72)], fill=WHITE, width=max(10, rh // 9))
    d.polygon([(ax - rh * 0.22, H * 0.66), (ax + rh * 0.22, H * 0.66), (ax, H * 0.84)], fill=WHITE)
    for i, (refs, dest) in enumerate(rows):
        y0 = int(rh * 0.15 + i * rh)
        x = int(rh * 0.9)
        for r in refs:
            e = r.upper().startswith("E")
            d.rounded_rectangle([x, y0 + rh * 0.18, x + shield_w, y0 + rh * 0.82], radius=8,
                                fill=GREEN if e else RED, outline=WHITE, width=5)
            bb = d.textbbox((0, 0), r, font=fs)
            d.text((x + shield_w / 2 - (bb[2] - bb[0]) / 2 - bb[0], y0 + rh / 2 - (bb[3] - bb[1]) / 2 - bb[1]), r,
                   font=fs, fill=WHITE)
            x += shield_w + 12
        x = int(rh * 0.9 + nsh * (shield_w + 12) + rh * 0.15)
        bb = d.textbbox((0, 0), dest, font=f)
        d.text((x - bb[0], y0 + rh / 2 - (bb[3] - bb[1]) / 2 - bb[1]), dest, font=f, fill=WHITE)
    return im, W / px_m, H / px_m


def plate_back(shape):
    im = _img(64, 64)
    ImageDraw.Draw(im).rectangle([0, 0, 63, 63], fill=GREY_BACK)
    return im


def digits_atlas():
    """Dock number atlas: 10 cells (0-9), black on white, 1280 x 160."""
    im = Image.new("RGBA", (1280, 160), (*WHITE, 255))
    d = ImageDraw.Draw(im)
    f = _font(130)
    for k in range(10):
        bb = d.textbbox((0, 0), str(k), font=f)
        d.text((128 * k + 64 - (bb[2] - bb[0]) / 2 - bb[0], 80 - (bb[3] - bb[1]) / 2 - bb[1]), str(k), font=f, fill=BLACK)
    return im


FACES = {"A-7": ("triangle", a7), "B-20": ("octagon", b20), "C-12": ("disc", c12), "D-1": ("diamond", d1),
         "D-6": ("square", lambda: square("D-6")), "D-15": ("square", lambda: square("D-15"))}


def face(code):
    if code.startswith("B-33_"):
        return "disc", b33(code.split("_")[1])
    shape, fn = FACES[code]
    return shape, fn()


def png_bytes(im, size=None):
    if size:
        im = im.resize(size, Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, format="PNG", optimize=True)
    return b.getvalue()
