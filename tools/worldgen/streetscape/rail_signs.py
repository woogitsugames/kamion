"""Faces of the approach signs of a level crossing (ADR 0255, Dz.U. 2025 poz. 1105 § 79 pkt 1 lit. a, pkt 3, pkt 6):
A-9 "przejazd kolejowy z zaporami", A-10 "przejazd kolejowy bez zapór", the G-1a...G-1f distance posts and the
"Sygnalizacja automatyczna" board. Our own schematic drawings (PIL primitives, no traced artwork); they are drawn by
streetscape.gate3_landmarks.draw_face (one assembly = one prototype = one material) - this module only adds the codes.

Sources (Dz.U. 2019 poz. 2311 zał. 1, t.j., api.sejm.gov.pl/eli/acts/DU/2019/2311/text.pdf, read 2026-11-15, SHA256
f94925ec05a75ca8cc1cea478727592a3b1b4c9822cdc76b309420556b550543):
  - A triangle side 900 mm = group "średnie" (Tabela 1.1; group S on single-carriageway national / voivodeship roads,
    pkt 1.2.1 lit. c) - SOURCED, the same value as roads.standards.SIGN_SIZE["triangle"];
  - G-1a...G-1f: 300 x 1000 mm, 20 mm edge, slanted stripes (rys. 9.8.1-9.8.6) - outline SOURCED; stripe positions
    read off the drawings to about +-30 mm (WORKING_VALUE); colours (white field, red stripes and edge) are not in the
    monochrome drawings: UNVERIFIED;
  - "Sygnalizacja automatyczna": the text of the board is § 79 pkt 6 of Dz.U. 2025 poz. 1105; its size and colours are
    in neither text read here: 0.90 x 0.30 m, black text on white = WORKING_VALUE / UNVERIFIED.
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw

TRI_SIDE_M = 0.90                       # Tabela 1.1, group S (średnie) - SOURCED
G1_W_M, G1_H_M = 0.30, 1.00             # rys. 9.8.1-9.8.6 - SOURCED
G1_EDGE_M = 0.02                        # rys. 9.8.1: 20 mm edge - SOURCED
G1_STRIPE_M = 0.15                      # vertical thickness of a stripe (rys. 9.8.1: 150 mm) - read off the drawing
G1_PITCH_M = 0.30                       # stripe + gap (150 + 150 mm) - read off the drawing
G1_RISE_M = 0.15                        # rise of a stripe across the 260 mm inner width - read off the drawing
# stripe group centred on the plate: lowest stripe's low end 0.5 - n * 0.15 m above the bottom (G-1a 0.05 m, G-1b
# 0.20 m: rys. 9.8.1 shows 30 + 20 mm, rys. 9.8.2 180 + 20 mm - read off the drawings, +-30 mm)
SA_W_M, SA_H_M = 0.90, 0.30             # WORKING_VALUE (size of the "Sygnalizacja automatyczna" board not read)

# code -> (shape, width m, height m); merged into gate3_landmarks.FACE_DIM
G1 = {"G-1a": (3, "R"), "G-1b": (2, "R"), "G-1c": (1, "R"), "G-1d": (3, "L"), "G-1e": (2, "L"), "G-1f": (1, "L")}
FACE_DIM = {"A-9": ("tri_up", TRI_SIDE_M, TRI_SIDE_M * math.sqrt(3) / 2),
            "A-10": ("tri_up", TRI_SIDE_M, TRI_SIDE_M * math.sqrt(3) / 2),
            "SA": ("rect", SA_W_M, SA_H_M),
            **{k: ("rect", G1_W_M, G1_H_M) for k in G1}}

RED = (196, 30, 36)
FLUO = (238, 208, 0)
BLACK = (24, 24, 24)
WHITE = (245, 245, 242)


def _warning(w, h):
    """Yellow upright triangle with the red border (same construction as gate3_landmarks A-30)."""
    im = Image.new("RGB", (w, h), RED)
    d = ImageDraw.Draw(im)
    b = 0.105 * w
    inner = [(w / 2, 2 * b), (w - b * math.sqrt(3), h - b), (b * math.sqrt(3), h - b)]
    d.polygon(inner, fill=FLUO)
    return im, d


def _a9(w, h):
    """A-9: a gate (fence) - two posts and three rails with vertical pales, black."""
    im, d = _warning(w, h)
    x0, x1 = 0.37 * w, 0.63 * w                              # inside the yellow field (border 0.105 w)
    y0, y1 = 0.56 * h, 0.80 * h
    st = max(2, int(0.018 * w))
    for x in (x0, x1):                                       # posts
        d.rectangle([x - st, y0 - 0.04 * h, x + st, y1], fill=BLACK)
    for y in (y0, (y0 + y1) / 2, y1 - st):                   # rails
        d.rectangle([x0, y - st / 2, x1, y + st / 2], fill=BLACK)
    for k in range(1, 4):                                    # pales between the posts
        x = x0 + (x1 - x0) * k / 4
        d.rectangle([x - st / 2, y0, x + st / 2, y1], fill=BLACK)
    return im


def _a10(w, h):
    """A-10: a steam locomotive facing left - boiler, cab, chimney, three wheels, black."""
    im, d = _warning(w, h)
    base = 0.80 * h                                          # rail level
    d.rectangle([0.27 * w, base - 0.012 * h, 0.73 * w, base], fill=BLACK)                      # rail
    d.rectangle([0.30 * w, 0.56 * h, 0.56 * w, 0.70 * h], fill=BLACK)                          # boiler
    d.rectangle([0.56 * w, 0.47 * h, 0.70 * w, 0.70 * h], fill=BLACK)                          # cab
    d.rectangle([0.58 * w, 0.50 * h, 0.66 * w, 0.56 * h], fill=FLUO)                           # cab window
    d.rectangle([0.34 * w, 0.48 * h, 0.39 * w, 0.56 * h], fill=BLACK)                          # chimney
    d.rectangle([0.32 * w, 0.46 * h, 0.41 * w, 0.48 * h], fill=BLACK)
    r = 0.045 * w
    for cx in (0.36 * w, 0.48 * w, 0.62 * w):                                                  # wheels
        d.ellipse([cx - r, base - 0.014 * h - 2 * r, cx + r, base - 0.014 * h], fill=BLACK)
    d.rectangle([0.30 * w, 0.70 * h, 0.70 * w, 0.73 * h], fill=BLACK)                          # frame
    return im


def _g1(code, w, h):
    """G-1: white field, red edge, `n` red stripes rising away from the carriageway (right posts: lower on the left)."""
    n, side = G1[code]
    im = Image.new("RGB", (w, h), RED)
    d = ImageDraw.Draw(im)
    sx, sy = w / G1_W_M, h / G1_H_M
    e = G1_EDGE_M
    d.rectangle([e * sx, e * sy, w - e * sx - 1, h - e * sy - 1], fill=WHITE)
    xl, xr = e, G1_W_M - e
    for k in range(n):
        lo = 0.5 - n * G1_STRIPE_M + k * G1_PITCH_M                       # height of the stripe's lower edge at its low end
        if side == "R":                                      # low end on the left (towards the carriageway)
            zl0, zr0 = lo, lo + G1_RISE_M
        else:
            zl0, zr0 = lo + G1_RISE_M, lo
        pts = [(xl, zl0), (xr, zr0), (xr, zr0 + G1_STRIPE_M), (xl, zl0 + G1_STRIPE_M)]
        d.polygon([(x * sx, h - z * sy) for x, z in pts], fill=RED)
    return im


def _sa(w, h, fit_text):
    im = Image.new("RGB", (w, h), BLACK)
    d = ImageDraw.Draw(im)
    m = max(2, int(0.02 * w))
    d.rectangle([m, m, w - m - 1, h - m - 1], fill=WHITE)
    fit_text(d, (m, m, w - m, h - m), "SYGNALIZACJA\nAUTOMATYCZNA", BLACK, int(h * 0.30))
    return im


def draw(code, w_px, h_px, fit_text):
    """RGB image of one face (the whole cell filled; the mesh is cut to the outline)."""
    if code == "A-9":
        return _a9(w_px, h_px)
    if code == "A-10":
        return _a10(w_px, h_px)
    if code in G1:
        return _g1(code, w_px, h_px)
    if code == "SA":
        return _sa(w_px, h_px, fit_text)
    raise KeyError(code)
