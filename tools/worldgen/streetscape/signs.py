"""Our own vector reproductions of Polish vertical sign faces (PNG textures for the plate prototypes).

Design per Załącznik nr 1 of the 2003 sign regulation (t.j. Dz.U. 2019 poz. 2311, amended by Dz.U. 2021 poz. 438 and
2066, 2022 poz. 2377, 2026 poz. 132; the numbers used for the E boards are in sign_norms.py):
  A (warning)      yellow field, red border; A-7 is an inverted triangle without a symbol.
  B (prohibition)  white disc, red ring; B-33 black numerals; B-20 red octagon, white border, "STOP".
  C (mandatory)    blue disc, white symbol; C-12 three arrows in a circle (counter-clockwise).
  D (information)  D-1 yellow square diamond with a white border; D-6 / D-15 blue square, white inner field
                   with a black symbol (pedestrian / bus).
  E (direction)    E-1 / E-2 boards laid out by the norm's letter heights, inscription lengths and row heights
                   (ADR 0236): green field for national-road destinations, white field for local ones, route
                   numbers as E-15a (red, white numerals), E-15b (yellow, black) and E-16 (green) miniatures.
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

from . import sign_norms as SN

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
        # ADR 0162: the D-15 pictogram is a bus in side view without lettering (wzór znaku D-15; BKM rack drawing
        # G5-004); the old face had a front view and the word "BUS".
        d.rectangle([S * 0.16, S * 0.12, S * 0.84, S * 0.88], fill=WHITE)
        d.rounded_rectangle([S * 0.22, S * 0.38, S * 0.78, S * 0.62], radius=10, fill=BLACK)
        for k in range(5):
            x = S * (0.255 + 0.10 * k)
            d.rectangle([x, S * 0.41, x + S * 0.075, S * 0.50], fill=WHITE)
        d.rectangle([S * 0.745, S * 0.41, S * 0.765, S * 0.56], fill=WHITE)            # front door glass
        for x in (0.33, 0.67):
            d.ellipse([S * x - 26, S * 0.585, S * x + 26, S * 0.685], fill=BLACK)
            d.ellipse([S * x - 10, S * 0.62, S * x + 10, S * 0.65], fill=WHITE)
    return im


def shield_colours(ref):
    """Route number shield (E-15a/b/c of [ZNAKI-Z1]): national road (1-2 digits) red with white numerals, voivodeship
    road (3 digits) yellow with black numerals, E-roads green. Returns (field, text)."""
    r = ref.strip().upper()
    if r.startswith("E"):
        return GREEN, WHITE
    if r.isdigit() and len(r) == 3:
        return YELLOW, BLACK
    return RED, WHITE



# ------------------------------------------------------------------------------------------------ ADR 0162 boards
# Direction boards read off research G3 (S8 / DK8 signs, 2024 frames; content only - Mapillary crops are CC BY-SA and
# never used as pixels, the faces are our own drawings): stacked panels with their own arrows (↑ ← → ↗) instead of a
# downward lane arrow, "Centrum" as blue letters in a white box (G3 P002 / P005 / P007 / P009), country codes as
# black letters in white ovals after a border-crossing destination ("Kuźnica PL BY", P004 / P009), voivodeship road
# shields yellow with black digits (675).
CITY_BLUE = (0, 70, 150)
ARROW_VEC = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0), "up_right": (0.707, -0.707),
             "up_left": (-0.707, -0.707)}
ARROW_RIGHT_SIDE = ("right", "up_right")


def _split_dest(dest):
    """'Kuźnica PL/BY' / 'Kuźnica PL BY' -> ('Kuźnica', ['PL', 'BY'])."""
    toks = dest.replace("/", " ").split()
    codes = []
    while toks and len(toks[-1]) == 2 and toks[-1].isalpha() and toks[-1].isupper():
        codes.insert(0, toks.pop())
    return " ".join(toks), codes



# ---------------------------------------------------------------------------------- ADR 0236: boards by the norm
# Direction boards (E-1, E-2, overhead E-2b) are laid out from the numbers of [ZNAKI-Z1] collected in sign_norms.py:
# letter height d of a letter group (Tabela 1.8 / 1.9), inscription length from the letter widths of Tabela 1.10,
# route-number signs by Tabela 9.5.3, row heights of drogowskazy tablicowe by Tabela 9.5.4 (first direction b1, every
# further one (b - b1) / 2), country ovals by Tabela 9.5.5, arrows by Tabela 9.5.6, frame by Tabela 9.5.2. The glyphs
# stay DejaVu Sans Bold (schematic stand-in, no traced artwork) but are scaled to the norm's cap height and squeezed
# to the norm's inscription length, so a board has the footprint the regulation gives it. Until ADR 0236 the rule
# boards had 66-74 mm letters and the overhead default a 0.62 m row (the 'wielkie' motorway row is 0.61 m).
_CAP = []


def _cap_ratio():
    if not _CAP:
        bb = _font(1000).getbbox("H")
        _CAP.append((bb[3] - bb[1]) / 1000.0)
    return _CAP[0]


class _Norm:
    """Pixel sizes of the board elements at letter height d_m (m) and px_m pixels per metre."""

    def __init__(self, d_m, px_m, green=True, arrow="srednie"):
        self.d_m, self.px = float(d_m), float(px_m)
        self.dp = self.d_m * self.px                       # cap height, px
        self.gr = self.dp / SN.GR_PER_D
        self.no = {k: v * self.px for k, v in SN.route_no(self.d_m).items()}
        key = min(SN.COUNTRY_OVAL_MM, key=lambda k: abs(k / 1000.0 - self.d_m))
        k = self.d_m / (key / 1000.0) * self.px / 1000.0
        self.oval = (SN.COUNTRY_OVAL_MM[key][1] * k, SN.COUNTRY_OVAL_MM[key][0] * k)       # (w, h)
        ka = self.d_m / 0.210 * self.px / 1000.0          # Tabela 9.5.6: 'średnie' at d = 210 mm; 'duze' = the larger
        self.arrow = {n: v * ka for n, v in SN.E2_ARROW_MM[arrow].items()}     # arrows of a dual carriageway > 60 km/h
        self.line = {n: SN.E_CONSTRUCTION_MM["srednie"][n] * ka for n in ("a", "a1")}     # E-1 direction lines
        self.no_gap = SN.NO_GAP_MM * self.d_m / 0.210 * self.px / 1000.0
        self.name_gap = (SN.NO_NAME_GAP_GR + 0.5) * self.gr
        self.margin = SN.EDGE_GAP_GR * self.gr
        self.bg, self.fg = (GREEN, WHITE) if green else (WHITE, BLACK)
        self.green = green

    # ---- inscriptions
    def text_w(self, text, dp=None):
        return SN.text_len_gr(text) * (dp or self.dp) / SN.GR_PER_D

    def text(self, im, x, yc, text, fill, dp=None):
        """Inscription with its capitals centred on yc: cap height dp, length by Tabela 1.10. Returns the end x."""
        dp = dp or self.dp
        wt = max(1, int(round(self.text_w(text, dp))))
        f = _font(max(6, int(round(dp / _cap_ratio()))))
        asc, desc = f.getmetrics()
        bb = f.getbbox(text, anchor="ls")
        m = Image.new("L", (max(1, bb[2] - bb[0]), asc + desc), 0)
        ImageDraw.Draw(m).text((-bb[0], asc), text, font=f, fill=255, anchor="ls")
        m = m.resize((wt, asc + desc), Image.LANCZOS)
        im.paste(Image.new("RGBA", m.size, (*fill, 255)), (int(round(x)), int(round(yc + dp / 2 - asc))), m)
        return x + wt

    # ---- route numbers (E-15 / E-16 miniatures, Tabela 9.5.3)
    def ref_w(self, ref):
        return SN.route_no_width_m(ref, {k: v / self.px for k, v in self.no.items()}) * self.px

    def refs_w(self, refs):
        return sum(self.ref_w(r) for r in refs) + self.no_gap * max(len(refs) - 1, 0)

    def ref(self, im, x, yc, ref):
        d = ImageDraw.Draw(im)
        w, h = self.ref_w(ref), self.no["h"]
        bgc, txc = shield_colours(ref)
        d.rounded_rectangle([x, yc - h / 2, x + w, yc + h / 2], radius=self.no["r"], fill=bgc,
                            outline=BLACK if bgc == YELLOW else WHITE, width=max(2, int(round(self.no["o"]))))
        r = ref.strip().upper().replace(" ", "")
        xx = x + self.no["m"]
        if r[:1].isalpha():
            xx = self.text(im, xx, yc, r[0], txc, self.no["d1"]) + self.no["P"]
            r = r[1:]
        self.text(im, xx, yc, r, txc, self.no["d1"])
        return w

    def refs(self, im, x, yc, refs):
        for r in refs:
            x += self.ref(im, x, yc, r) + self.no_gap
        return x

    # ---- destinations: name (+ "Centrum" in a white field, country ovals of a border crossing)
    def dest_w(self, dest):
        name, codes = _split_dest(dest)
        w = self.text_w(name)
        if self.green and name.lower() == "centrum":
            w += 2 * self.gr
        return w + len(codes) * (self.oval[0] + 1.5 * self.gr)

    def dest(self, im, x, yc, dest):
        d = ImageDraw.Draw(im)
        name, codes = _split_dest(dest)
        if self.green and name.lower() == "centrum":           # informacja lokalna: white field, blue letters
            w = self.text_w(name) + 2 * self.gr
            d.rounded_rectangle([x, yc - 4 * self.gr, x + w, yc + 4 * self.gr], radius=self.gr, fill=WHITE)
            self.text(im, x + self.gr, yc, name, CITY_BLUE)
            x += w
        else:
            x = self.text(im, x, yc, name, self.fg)
        ow, oh = self.oval
        for c in codes:
            x += 1.5 * self.gr
            d.ellipse([x, yc - oh / 2, x + ow, yc + oh / 2], fill=WHITE, outline=BLACK, width=max(2, int(oh * 0.07)))
            dp = oh * 0.52
            self.text(im, x + (ow - self.text_w(c, dp)) / 2, yc, c, BLACK, dp)
            x += ow
        return x

    def row_w(self, refs, dest):
        return self.refs_w(refs) + (self.name_gap if refs else 0.0) + self.dest_w(dest)

    def block_w(self, rows):
        """Width of rows drawn with a common number column (row(..., refs_col=...))."""
        col = max([self.refs_w(r[0]) for r in rows] + [0.0])
        return col + (self.name_gap if col else 0.0) + max([self.dest_w(r[1]) for r in rows] + [0.0])

    def row(self, im, x, yc, refs, dest, refs_col=None):
        """One row; with refs_col the numbers end flush at x + refs_col (a common column for several rows)."""
        if refs_col is not None:
            self.refs(im, x + refs_col - self.refs_w(refs), yc, refs)
            return self.dest(im, x + refs_col + (self.name_gap if refs_col else 0.0), yc, dest)
        if refs:
            x = self.refs(im, x, yc, refs) - self.no_gap + self.name_gap
        return self.dest(im, x, yc, dest)

    # ---- arrows (rys. 9.5.18) and the frame (Tabela 9.5.2)
    def arrow_box(self, kind):
        """(width, height) px an arrow of this kind occupies."""
        a, c = self.arrow["a"], self.arrow["c"]
        base = kind[:-1] if kind.endswith("2") else kind
        if base in ("up", "down"):
            return a, c
        if base in ("left", "right"):
            return c, a
        if base == "fork_right":
            return self.line["a"] * 3.2, c * 2.0
        return (c + a) * 0.707, (c + a) * 0.707

    def draw_arrow(self, d, kind, cx, cy, col=None, scale=1.0):
        col = col or self.fg
        a, a1, c, c1 = (self.arrow[k] * scale for k in ("a", "a1", "c", "c1"))
        if kind == "fork_right":            # E-1 "przeddrogowskaz": straight on + a branch to the right (R2-079);
            h = self.arrow["c"] * 2.0 * scale      # the lines keep the E-1 widths a / a1 (Tabela 9.5.1) at any height
            wa, wb = self.line["a"], self.line["a1"]
            x0 = cx - wa * 1.1
            d.polygon([(x0 - wa / 2, cy + h / 2), (x0 - wa / 2, cy - h / 2 + wa), (x0, cy - h / 2),
                       (x0 + wa / 2, cy - h / 2 + wa), (x0 + wa / 2, cy + h / 2)], fill=col)
            yb = cy + h * 0.10
            d.line([(x0, yb + wa * 1.5), (x0 + wa * 0.9, yb + wa * 0.25), (x0 + wa * 1.7, yb), (x0 + wa * 2.3, yb)],
                   fill=col, width=max(2, int(round(wb))), joint="curve")
            d.polygon([(x0 + wa * 2.3, yb - wb * 0.5), (x0 + wa * 2.7, yb), (x0 + wa * 2.3, yb + wb * 0.5)], fill=col)
            return
        dx, dy = ARROW_VEC[kind]
        nx, ny = -dy, dx
        tail = (cx - dx * c / 2, cy - dy * c / 2)
        tip = (cx + dx * c / 2, cy + dy * c / 2)
        hb = (tip[0] - dx * c1, tip[1] - dy * c1)
        d.polygon([(tail[0] + nx * a1 / 2, tail[1] + ny * a1 / 2), (hb[0] + nx * a1 / 2, hb[1] + ny * a1 / 2),
                   (hb[0] + nx * a / 2, hb[1] + ny * a / 2), tip, (hb[0] - nx * a / 2, hb[1] - ny * a / 2),
                   (hb[0] - nx * a1 / 2, hb[1] - ny * a1 / 2), (tail[0] - nx * a1 / 2, tail[1] - ny * a1 / 2)], fill=col)

    def frame(self, d, x0, y0, x1, y1):
        """White frame e wide, inset by the edging c (>= 2 px so the texture edge keeps the field colour)."""
        k = self.d_m / 0.210 * self.px / 1000.0
        ins = max(2, int(round(SN.E_FRAME_MM["srednie"]["c"] * k)))
        d.rounded_rectangle([x0 + ins, y0 + ins, x1 - 1 - ins, y1 - 1 - ins], radius=SN.E_FRAME_MM["srednie"]["r"] * k,
                            outline=self.fg, width=max(3, int(round(SN.E_FRAME_MM["srednie"]["e"] * k))))


ROW_U = SN.E2_ROW_PITCH_PER_D          # row pitch in units of d (10 gr / 6 gr)
PAD_U = SN.E2_FIRST_EXTRA_PER_D        # extra height of a panel: (b1 - row) in units of d
ARROW_LEFT_SIDE = ("up", "down", "left", "up_left", "fork_right")


def _panel_units(n_rows):
    return ROW_U * n_rows + PAD_U


def panel_board(panels, size_m=None, row_m=None, px_m=160, green=True, d_m=None, single_frame=False, arrow="duze"):
    """Board of stacked panels, panels = [{"rows": [(refs, dest)], "arrow": up | up2 | down | down2 | left | right |
    up_right | up_left | fork_right | none}]. Arrows pointing straight on / left stand left of the names, right /
    up-right ones right of them (pkt 6.3.2.2, s. 271); up2 / down2 on both ends (a board over two lanes).
    Geometry by the norm (see the block comment): a panel of n rows is d * (ROW_U * n + PAD_U) high, i.e. 0.50 m +
    0.35 m per further row at d = 210 mm (Tabela 9.5.4). `size_m` = (w, h) measured on a photo: d follows from the
    height, the field is widened to the width with the rows centred. `row_m` = row pitch (d = 0.6 row). Default
    d = sign_norms.E_OVERHEAD_D_M. `single_frame`: one frame around all panels (E-1 with a forked arrow).
    Returns (image, w_m, h_m)."""
    units = sum(_panel_units(len(p["rows"])) for p in panels)
    if size_m:
        d_m = float(size_m[1]) / units
    elif d_m is None:
        d_m = (float(row_m) / ROW_U) if row_m else SN.E_OVERHEAD_D_M
    N = _Norm(d_m, px_m, green, arrow)
    probe = [(p, p.get("arrow", "down")) for p in panels]
    left = max([N.arrow_box(k)[0] for _, k in probe if (k[:-1] if k.endswith("2") else k) in ARROW_LEFT_SIDE] + [0.0])
    right = max([N.arrow_box(k)[0] for _, k in probe if k in ARROW_RIGHT_SIDE or k.endswith("2")] + [0.0])
    zl = left + 2 * N.margin if left else 1.5 * N.margin
    zr = right + 2 * N.margin if right else 1.5 * N.margin
    sw = max(N.refs_w(r[0]) for p in panels for r in p["rows"])
    tw = max(N.dest_w(r[1]) for p in panels for r in p["rows"])
    W0 = int(math.ceil(zl + sw + (N.name_gap if sw else 0.0) + tw + zr))
    heights = [int(round(_panel_units(len(p["rows"])) * N.dp)) for p in panels]
    H = sum(heights)
    W = max(W0, int(round(float(size_m[0]) * px_m))) if size_m else W0
    shift = (W - W0) / 2.0
    im = Image.new("RGBA", (W, H), (*N.bg, 255))
    d = ImageDraw.Draw(im)
    y0 = 0
    for (p, kind), hp in zip(probe, heights):
        if not single_frame:
            N.frame(d, 0, y0, W, y0 + hp)
        base = kind[:-1] if kind.endswith("2") else kind
        if kind != "none":
            aw = N.arrow_box(kind)[0]
            fit = (hp - 2 * N.margin) / N.arrow_box(kind)[1]
            fit = (hp - 5 * N.margin) / N.arrow_box(kind)[1] if base == "fork_right" else min(1.0, fit)
            xs = []
            if base in ARROW_LEFT_SIDE or kind.endswith("2"):
                xs.append(N.margin + aw / 2)
            if kind in ARROW_RIGHT_SIDE or kind.endswith("2"):
                xs.append(W - N.margin - aw / 2)
            for ax in xs:
                N.draw_arrow(d, base, ax, y0 + hp / 2, scale=fit)
        for i, (refs, dest) in enumerate(p["rows"]):
            yc = y0 + (PAD_U / 2 + ROW_U * (i + 0.5)) * N.dp
            N.row(im, zl + shift, yc, refs, dest, refs_col=sw)
        y0 += hp
    if single_frame:
        N.frame(d, 0, 0, W, H)
    if size_m and W > int(round(float(size_m[0]) * px_m)):
        # the measured board is narrower than the norm's inscriptions at this letter height (the stand-in typeface
        # and our spacing): keep the measured footprint, squeeze the face
        W = int(round(float(size_m[0]) * px_m))
        im = im.resize((W, H), Image.LANCZOS)
    return im, W / px_m, H / px_m


def overhead_board(rows, row_m=None, size_m=None, arrows=1):
    """Overhead direction board over its lane(s) (E-2b; our own schematic drawing after the CC0 photo of the gantry
    at the Andersa / Rondo Putry approach): green field, white frame, one row per destination with the route numbers
    left of the name and a downward lane arrow (two with `arrows` >= 2: a board over two lanes, Mapillary
    275528677534382). rows = [(refs, destination)]. Returns (image, width_m, height_m).
    ADR 0236: the row pitch is no longer the WORKING_VALUE 0.62 m but the norm's 10 gr = 0.35 m at d = 210 mm, the
    first row 0.50 m (Tabela 9.5.4 [ZNAKI-Z1]); `size_m` = (w, h) measured on a photo still wins (ADR 0139)."""
    return panel_board([{"rows": rows, "arrow": "down2" if arrows >= 2 else "down"}], size_m=size_m, row_m=row_m)


def direction_board(dests, refs, green, d_m=None):
    """E-2a board beside the carriageway by rule (roundabout exits, link starts): destinations one per row, the
    route numbers left of the first name, an up-right arrow right of the names (pkt 6.3.2.2). Green field when a
    route number is signed, else white with black letters (local destination). Letter height
    sign_norms.E_RULE_BOARD_D_M (WORKING_VALUE group, see there). Returns (image, w_m, h_m)."""
    lines = [x.strip() for x in dests if x.strip()][:3] or ["?"]
    shields = [r for r in refs if r][:2]
    rows = [(shields if i == 0 else [], t) for i, t in enumerate(lines)]
    return panel_board([{"rows": rows, "arrow": "up_right"}], green=green, d_m=d_m or SN.E_RULE_BOARD_D_M, px_m=320,
                       arrow="srednie")


def _rows(v):
    """(refs, dest) or [(refs, dest), ...] -> list of rows."""
    if v and isinstance(v[0], (list, tuple)) and len(v) == 2 and isinstance(v[1], str):
        return [(list(v[0]), v[1])]
    return [(list(r[0]), r[1]) for r in v]


def e1_cross_board(top, left, right, size_m=None, px_m=160, d_m=None):
    """E-1 advance board with a crossroads diagram (G3-P009, al. Tysiąclecia southbound before Rondo Putry, 2024;
    R2-081, the Andersa link, 2021): `top` = (refs, dest) or rows above the vertical road, `left` / `right` = rows
    beside the cross arms. Our own schematic: the real diagram's curved ramps are a plain cross of double lines with
    arrow heads (line width a1 = 75 mm at d = 210 mm, Tabela 9.5.1). Laid out in units of the letter height d; with
    `size_m` d is the largest that fits the measured board, else `d_m` (default 210 mm). Returns (image, w, h)."""
    top, left, right = _rows(top), _rows(left), _rows(right)
    d_ref = d_m or SN.E_OVERHEAD_D_M
    U = _Norm(d_ref, 1000.0)                                # widths in units of d (proportions of Tabela 9.5.3)
    lw = U.block_w(left) / U.dp
    rw = U.block_w(right) / U.dp
    tw = max([U.row_w(*r) for r in top] + [0.0]) / U.dp
    mx, my, arm, vup, vdn = 0.6, 0.45, 1.5, 2.2, 2.1
    dw = 2 * arm + 1.2
    wu = max(mx + lw + 0.5 + dw + 0.5 + rw + mx, tw + 2 * mx)
    hu = max(my + ROW_U * len(top) + 0.3 + vup + vdn + my, ROW_U * max(len(left), len(right)) + 2 * my)
    if size_m:
        d_m = min(float(size_m[0]) / wu, float(size_m[1]) / hu)
        W, H = int(round(size_m[0] * px_m)), int(round(size_m[1] * px_m))
    else:
        d_m = d_m or SN.E_OVERHEAD_D_M
        W, H = int(math.ceil(wu * d_m * px_m)), int(math.ceil(hu * d_m * px_m))
    N = _Norm(d_m, px_m)
    u = N.dp
    im = Image.new("RGBA", (W, H), (*GREEN, 255))
    d = ImageDraw.Draw(im)
    N.frame(d, 0, 0, W, H)
    xl0, xr1 = mx * u, W - mx * u
    cx = (xl0 + lw * u + xr1 - rw * u) / 2
    vpad = (H - hu * u) / 2
    cy = vpad + (my + ROW_U * len(top) + 0.3 + vup) * u
    cy = min(max(cy, H * 0.45), H - (vdn * 0.6 + my) * u)
    lwid = max(3, int(round(N.line["a1"])))
    gap = lwid * 1.3
    ytop, xa, xb = cy - vup * u + 0.55 * u, cx - arm * u, cx + arm * u
    for s in (-1, 1):                                            # double-line roads: vertical and horizontal
        d.line([(cx + s * gap, H - my * u * 0.6), (cx + s * gap, ytop)], fill=WHITE, width=lwid)
        d.line([(xa, cy + s * gap), (xb, cy + s * gap)], fill=WHITE, width=lwid)
    hd = 0.55 * u
    for (px_, py_), (dx, dy) in (((cx, ytop), (0, -1)), ((xa, cy), (-1, 0)), ((xb, cy), (1, 0))):
        d.polygon([(px_ + dx * hd, py_ + dy * hd), (px_ - dy * hd * 0.6, py_ + dx * hd * 0.6),
                   (px_ + dy * hd * 0.6, py_ - dx * hd * 0.6)], fill=WHITE)
    y = max(my * u, cy - (vup + 0.3 + ROW_U * len(top)) * u) + ROW_U * u / 2
    for refs, dest in top:
        x = min(max(cx - N.row_w(refs, dest) / 2, mx * u), W - mx * u - N.row_w(refs, dest))
        N.row(im, x, y, refs, dest)
        y += ROW_U * u
    for rows, right_side in ((left, False), (right, True)):
        if not rows:
            continue
        col = max(N.refs_w(r[0]) for r in rows)
        y = min(max(cy - ROW_U * u * (len(rows) - 1) / 2, my * u + ROW_U * u / 2),
                H - my * u - ROW_U * u * (len(rows) - 0.5))
        for refs, dest in rows:
            N.row(im, (xr1 - rw * u) if right_side else xl0, y, refs, dest, refs_col=col)
            y += ROW_U * u
    return im, W / px_m, H / px_m


def vms_board(lines, size_m, cols=150):
    """Variable-message sign of the ITS gantry (G3-P010, 2024-08-15): black field, white LED dot matrix. The text is
    the momentary message of that frame (travel times are not a game parameter), shown as a static texture.
    Returns (image, w, h)."""
    import numpy as np
    W, H = int(size_m[0] * 160), int(size_m[1] * 160)
    rows = max(8, int(round(cols * size_m[1] / size_m[0])))
    lo = Image.new("L", (cols, rows), 0)
    d = ImageDraw.Draw(lo)
    lh = rows / (len(lines) + 0.6)
    # review s17-0162: "5 MIN" touched the right frame - the widest line must keep >= 5 % of the matrix free on
    # both sides; shrink the font until it fits.
    fs = max(6, int(lh * 0.82))
    f = _font(fs)
    while fs > 6 and max(d.textlength(t, font=f) for t in lines) > cols * 0.90:
        fs -= 1
        f = _font(fs)
    for i, t in enumerate(lines):
        d.text((cols * 0.05, lh * (0.35 + i)), t, font=f, fill=255)
    on = np.asarray(lo) > 110
    im = Image.new("RGBA", (W, H), (14, 14, 15, 255))
    dd = ImageDraw.Draw(im)
    pw, ph = W / cols, H / rows
    r = 0.36 * min(pw, ph)
    for yy in range(rows):
        for xx in range(cols):
            cxp, cyp = (xx + 0.5) * pw, (yy + 0.5) * ph
            dd.ellipse([cxp - r, cyp - r, cxp + r, cyp + r], fill=(236, 236, 228) if on[yy, xx] else (34, 34, 36))
    dd.rectangle([0, 0, W - 1, H - 1], outline=(60, 62, 64), width=max(4, int(H * 0.03)))
    return im, size_m[0], size_m[1]


def plate_back(shape=None):
    """Back of an aluminium sign plate (256 px = 1 m): mill-finish grey with faint horizontal rolling marks, road
    grime toward the bottom and a small producer label (blank: no third-party mark). Deterministic."""
    import numpy as np
    n = 256
    rng = np.random.default_rng(2311)
    rows = rng.normal(0, 1, (n, 1)) * 2.0 + rng.normal(0, 1, (n, n)) * 1.2
    yy = np.linspace(0, 1, n)[:, None]
    shade = 1.0 - 0.10 * np.clip((yy - 0.5) / 0.5, 0, 1)                  # (n, 1)
    img = np.array(GREY_BACK, np.float32)[None, None, :] * shade[..., None] * np.ones((1, n, 1), np.float32)
    img = img + rows[..., None]
    img[96:128, 150:200] = (225, 226, 222)                     # label
    img[100:104, 156:194] = (150, 150, 150)
    img[110:113, 156:186] = (165, 165, 165)
    # ADR0120: aluminium oxidises; brown runoff comes only from steel fasteners.
    # props.plate insets the vertical UV by 0.6 and uses a 1 m physical width on every shape.
    xx = np.linspace(0, 1, n)[None, :]
    runoff = np.zeros((n, n))
    for mount in (0.368, 0.668):
        below = yy - mount
        for bolt in (0.46, 0.54):
            width = 0.009 + 0.014 * np.clip(below / 0.2, 0, 1)
            mark = np.exp(-((xx-bolt) / width) ** 2)
            mark *= np.clip(below / 0.012, 0, 1) * np.clip(1-below / 0.22, 0, 1)
            runoff = np.maximum(runoff, mark * 0.68)
    img = img * (1-runoff[..., None]) + np.array([116, 78, 47]) * runoff[..., None]
    a = np.full((n, n, 1), 255.0)
    return Image.fromarray(np.clip(np.concatenate([img, a], -1), 0, 255).astype(np.uint8), "RGBA")


def digits_atlas():
    """Dock number atlas: 10 cells (0-9), black on white, 1280 x 160."""
    im = Image.new("RGBA", (1280, 160), (*WHITE, 255))
    d = ImageDraw.Draw(im)
    f = _font(130)
    for k in range(10):
        bb = d.textbbox((0, 0), str(k), font=f)
        d.text((128 * k + 64 - (bb[2] - bb[0]) / 2 - bb[0], 80 - (bb[3] - bb[1]) / 2 - bb[1]), str(k), font=f, fill=BLACK)
    return im


def b1():
    im, d = disc(WHITE, RED)
    return im


def b2():
    im, d = disc(RED)
    d.rectangle([S * 0.17, S * 0.42, S * 0.83, S * 0.58], fill=WHITE)
    return im


def b36():
    im, d = disc(BLUE, RED)
    w = int(S * 0.085)
    c, r = S / 2, S * 0.40
    for a in (math.pi / 4, -math.pi / 4):
        d.line([(c - r * math.cos(a), c - r * math.sin(a)), (c + r * math.cos(a), c + r * math.sin(a))], fill=RED, width=w)
    return im


def c9():
    """C-9 nakaz jazdy z prawej strony znaku: white arrow pointing down to the right (splitter islands)."""
    im, d = disc(BLUE)
    w = S * 0.085
    a0 = (S * 0.31, S * 0.31)
    tip = (S * 0.70, S * 0.70)
    d.line([a0, (S * 0.60, S * 0.60)], fill=WHITE, width=int(w))
    k = S * 0.15
    d.polygon([tip, (tip[0] - k * 1.35, tip[1] - k * 0.05), (tip[0] - k * 0.05, tip[1] - k * 1.35)], fill=WHITE)
    return im


# ------------------------------------------------------------------------------------------------ ADR 0268
# Signs of the approach to a level crossing (Dz.U. 2025 poz. 1105 § 79). Faces redrawn from the colour patterns of
# Dz.U. 2019 poz. 2310 (PDF p. 41: A-9, A-10; p. 51: G-1a-f, G-2), viewed 2026-11-15; simplified pictograms from
# primitives, no traced artwork. Plate sizes: RECT below.
TRI_UP_TOP = (S - (S - 16) * math.sqrt(3) / 2) / 2      # px: apex row of the upright warning triangle (side S - 16)
# code -> (width m, height m) of rectangular plates. ADR 0279: G-1 and G-2 SOURCED from the construction drawings of
# Dz.U. 2019 poz. 2311 zał. 1, rys. 9.8.1-9.8.6 (PDF s. 507-509: G-1 300 x 1000 mm) and rys. 9.8.7 (s. 510: G-2
# 440 x 600 mm; was WORKING_VALUE 0.35 x 0.50 from the colour pattern) = sign_norms.G1_MM / G2_MM. "T-SA" = tablica
# "Sygnalizacja automatyczna" (Dz.U. 2025 poz. 1105 § 79 pkt 6): neither act gives a pattern - white board, black
# frame and lettering, UNVERIFIED design and size.
RECT = {**{f"G-1{k}": (SN.G1_MM[0] / 1000.0, SN.G1_MM[1] / 1000.0) for k in "abcdef"},
        "G-2": (SN.G2_MM[0] / 1000.0, SN.G2_MM[1] / 1000.0), "T-SA": (0.90, 0.36)}


def _tri_up():
    """Upright warning triangle: red border, yellow field. Returns (image, draw)."""
    im = _img()
    d = ImageDraw.Draw(im)
    s = S - 16
    h = s * math.sqrt(3) / 2
    top = TRI_UP_TOP
    outer = [(S / 2, top), (S - 8, top + h), (8, top + h)]
    d.polygon(outer, fill=RED)
    k = 0.80
    cx, cy = S / 2, top + 2 * h / 3
    d.polygon([(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in outer], fill=YELLOW)
    return im, d


def a9():
    """A-9 "przejazd kolejowy z zaporami": black fence (4 pickets on 2 rails)."""
    im, d = _tri_up()
    x0, x1, yb = S * 0.30, S * 0.70, S * 0.80
    for k in range(4):
        x = x0 + (x1 - x0) * (k + 0.5) / 4
        w = S * 0.030
        d.polygon([(x - w, yb), (x - w, S * 0.57), (x, S * 0.52), (x + w, S * 0.57), (x + w, yb)], fill=BLACK)
    for y in (0.62, 0.72):
        d.rectangle([x0 - S * 0.02, S * y - S * 0.016, x1 + S * 0.02, S * y + S * 0.016], fill=BLACK)
    return im


def a10():
    """A-10 "przejazd kolejowy bez zapór": black steam locomotive in side view (simplified)."""
    im, d = _tri_up()
    yb = S * 0.80                                                    # rail
    d.rectangle([S * 0.27, yb - 5, S * 0.73, yb + 3], fill=BLACK)
    d.rectangle([S * 0.33, S * 0.62, S * 0.60, S * 0.735], fill=BLACK)   # boiler
    d.rectangle([S * 0.56, S * 0.555, S * 0.69, S * 0.735], fill=BLACK)  # cab
    d.rectangle([S * 0.545, S * 0.535, S * 0.705, S * 0.565], fill=BLACK)  # cab roof
    d.rectangle([S * 0.595, S * 0.60, S * 0.655, S * 0.655], fill=YELLOW)  # cab window
    d.polygon([(S * 0.36, S * 0.62), (S * 0.345, S * 0.545), (S * 0.415, S * 0.545), (S * 0.40, S * 0.62)], fill=BLACK)
    d.ellipse([S * 0.455, S * 0.585, S * 0.505, S * 0.635], fill=BLACK)   # dome
    d.polygon([(S * 0.33, S * 0.735), (S * 0.285, S * 0.775), (S * 0.33, S * 0.775)], fill=BLACK)   # pilot
    for x in (0.375, 0.47, 0.565, 0.65):
        d.ellipse([S * x - 21, yb - 44, S * x + 21, yb - 2], fill=BLACK)
    for cx_, cy_, r in ((0.40, 0.49, 15), (0.45, 0.455, 19), (0.515, 0.43, 22)):   # smoke
        d.ellipse([S * cx_ - r, S * cy_ - r, S * cx_ + r, S * cy_ + r], fill=BLACK)
    return im


def g1(code):
    """G-1a-f "słupek wskaźnikowy": white field, red frame, 3 / 2 / 1 red bars; on the right-hand posts (a-c) the bars
    fall towards the carriageway (down to the left), on the left-hand posts (d-f) they are mirrored."""
    w, h = 154, S
    im = _img(w, h)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=RED)
    b = 9
    d.rectangle([b, b, w - 1 - b, h - 1 - b], fill=WHITE)
    n = {"a": 3, "b": 2, "c": 1, "d": 3, "e": 2, "f": 1}[code[-1]]
    left = code[-1] in "def"
    bar, rise = h * 0.118, (w - 2 * b) * 0.50          # bar thickness (vertical), rise across the plate
    pitch = h * 0.30
    for k in range(n):
        yc = h / 2 + (k - (n - 1) / 2) * pitch
        ya, yb_ = (yc - rise / 2, yc + rise / 2) if left else (yc + rise / 2, yc - rise / 2)   # y at left / right edge
        d.polygon([(b, ya - bar / 2), (w - 1 - b, yb_ - bar / 2), (w - 1 - b, yb_ + bar / 2), (b, ya + bar / 2)],
                  fill=RED)
    return im


def g2():
    """G-2 "sieć pod napięciem": white plate with a black frame, yellow warning triangle with a black lightning bolt,
    yellow panel with the black legend of the pattern."""
    w, h = 376, S                                   # 440 x 600 mm (rys. 9.8.7) at 512 px height
    im = _img(w, h)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=18, fill=BLACK)
    d.rounded_rectangle([7, 7, w - 8, h - 8], radius=12, fill=WHITE)
    tri = [(w / 2, 40), (w - 44, 300), (44, 300)]
    d.polygon(tri, fill=BLACK)
    cx, cy = w / 2, (40 + 300 + 300) / 3
    d.polygon([(cx + (x - cx) * 0.86, cy + (y - cy) * 0.86) for x, y in tri], fill=(250, 226, 40))
    d.polygon([(w * 0.53, 105), (w * 0.44, 190), (w * 0.505, 190), (w * 0.455, 262), (w * 0.47, 262), (w * 0.44, 285),
               (w * 0.405, 255), (w * 0.425, 258), (w * 0.47, 205), (w * 0.40, 205), (w * 0.47, 105)], fill=BLACK)
    d.rectangle([20, 330, w - 21, h - 22], fill=(250, 226, 40))
    for k, (txt, px) in enumerate((("Nie dotykać", 34), ("Przewodów trakcyjnych!", 21), ("Zagrożenie dla życia!", 21))):
        f = _font(px)
        tw = d.textlength(txt, font=f)
        d.text(((w - tw) / 2, 345 + k * 44), txt, font=f, fill=BLACK)
    return im


def t_sa():
    """Tablica informacyjna "Sygnalizacja automatyczna" (Dz.U. 2025 poz. 1105 § 79 pkt 6) - UNVERIFIED design."""
    w, h = S, 205
    im = _img(w, h)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=14, fill=BLACK)
    d.rounded_rectangle([6, 6, w - 7, h - 7], radius=10, fill=WHITE)
    for k, txt in enumerate(("Sygnalizacja", "automatyczna")):
        f = _font(58)
        tw = d.textlength(txt, font=f)
        d.text(((w - tw) / 2, 26 + k * 78), txt, font=f, fill=BLACK)
    return im



FACES = {"A-7": ("triangle", a7), "B-20": ("octagon", b20), "C-12": ("disc", c12), "D-1": ("diamond", d1),
         "D-6": ("square", lambda: square("D-6")), "D-15": ("square", lambda: square("D-15")),
         "B-1": ("disc", b1), "B-2": ("disc", b2), "B-36": ("disc", b36), "C-9": ("disc", c9),
         # ADR 0268: approach to a level crossing (plates of rail_approach.py only; furniture.sign_assembly never
         # stacks them - "triangle_up" / "rect" are handled by props.plate)
         "A-9": ("triangle_up", a9), "A-10": ("triangle_up", a10), "G-2": ("rect", g2), "T-SA": ("rect", t_sa),
         **{f"G-1{k}": ("rect", (lambda k=k: g1(f"G-1{k}"))) for k in "abcdef"}}
KNOWN = set(FACES)


def roundabout_diagram(items, px_m=200, d_m=None):
    """E-1 board (tablica przeddrogowskazowa) before a roundabout by rule: the ring, the approach from the bottom,
    every other arm at its real bearing (ang degrees, 0 = straight on, + = left) with its destinations and route
    numbers (rys. 6.3.1.4 [ZNAKI-Z1]: "tablica E-1 przed skrzyżowaniem o ruchu okrężnym"). items = [(ang, [lines],
    [refs])]. Green field when a road number is signed, else white with black letters.
    ADR 0236: letters by the norm - names in group IV = 132 mm (sign_norms.E1_RULE_D_M; Tabela 1.9 allows VI / V / IV
    for E-1 in 'średnie' and 'duże'), numbers one group smaller (Tabela 9.5.3), inscription lengths by Tabela 1.10,
    direction lines a1 = 75 mm (Tabela 9.5.1; a roundabout has no priority arm). The board is as large as its
    content (the old fixed 2.44 x 2.0 m canvas had 74 mm letters). Returns (image, w_m, h_m)."""
    green = any(r for _, _, r in items)
    N = _Norm(d_m or SN.E1_RULE_D_M, px_m, green)
    u = N.dp
    R, L, hd = 0.22 * px_m, 0.30 * px_m, 0.11 * px_m
    lw = max(4, int(round(SN.E_CONSTRUCTION_MM["srednie"]["a1"] / 1000.0 * px_m)))
    D = R + L + hd
    m, g = 0.12 * px_m, 0.07 * px_m
    blocks = {"top": [], "left": [], "right": []}
    for ang, lines, refs in sorted(items):
        rows = [(list(refs[:2]) if i == 0 else [], t) for i, t in enumerate(lines[:2])]
        bw = N.block_w(rows)
        side = "top" if abs(ang) < 35 else "left" if ang > 0 else "right"
        blocks[side].append((ang, rows, bw, ROW_U * u * len(rows)))
    left_w = max([b[2] for b in blocks["left"]] + [0.0])
    right_w = max([b[2] for b in blocks["right"]] + [0.0])
    top_w = sum(b[2] for b in blocks["top"]) + g * max(len(blocks["top"]) - 1, 0)
    top_h = max([b[3] for b in blocks["top"]] + [0.0])
    W = int(math.ceil(max(m + left_w + g + 2 * D + g + right_w + m, top_w + 2 * m)))
    cx = m + left_w + g + D + max(0.0, (W - (m + left_w + g + 2 * D + g + right_w + m)) / 2)
    cy = m + top_h + g + D
    side_h = max([sum(b[3] for b in blocks[s]) + g * (len(blocks[s]) - 1) for s in ("left", "right") if blocks[s]] + [0.0])
    H = int(math.ceil(max(cy + R + 0.40 * px_m + m, 2 * m + side_h, cy + side_h / 2 + m)))
    im = Image.new("RGBA", (W, H), (*N.bg, 255))
    d = ImageDraw.Draw(im)
    N.frame(d, 0, 0, W, H)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=N.fg, width=lw)
    d.line([(cx, H - m * 0.7), (cx, cy + R - lw / 2)], fill=N.fg, width=lw)             # approach (no arrow)
    for ang, _, _ in items:
        a = math.radians(90.0 + ang)
        ux, uy = math.cos(a), -math.sin(a)
        p0, p1 = (cx + ux * (R - lw / 2), cy + uy * (R - lw / 2)), (cx + ux * (R + L), cy + uy * (R + L))
        d.line([p0, p1], fill=N.fg, width=lw)
        nx, ny = -uy * hd * 0.75, ux * hd * 0.75
        d.polygon([(p1[0] + ux * hd, p1[1] + uy * hd), (p1[0] + nx, p1[1] + ny), (p1[0] - nx, p1[1] - ny)], fill=N.fg)

    def put(rows, x, y):
        col = max(N.refs_w(r[0]) for r in rows)
        for i, (refs, dest) in enumerate(rows):
            N.row(im, x, y + ROW_U * u * (i + 0.5), refs, dest, refs_col=col)

    x = cx - top_w / 2
    x = min(max(x, m), W - m - top_w)
    for ang, rows, bw, bh in sorted(blocks["top"], key=lambda b: -b[0]):                 # left-most arm first
        put(rows, x, m + top_h - bh)
        x += bw + g
    for side in ("left", "right"):
        y_prev = m
        for ang, rows, bw, bh in sorted(blocks[side], key=lambda b: -math.sin(math.radians(90.0 + b[0]))):
            tip_y = cy - math.sin(math.radians(90.0 + ang)) * (R + L)
            y = min(max(tip_y - bh / 2, y_prev), H - m - bh)
            put(rows, m if side == "left" else cx + D + g, y)
            y_prev = y + bh + g
    return im, W / px_m, H / px_m


def weather(im, key, strength=1.0):
    """Subtle road film and edge damage; deterministic, coverage/legend preserved.

    WORKING_VALUE appearance, not the measured condition of a particular plate.
    No rust blanket on aluminium. strength=0 is the unmodified RGBA source.
    """
    import hashlib
    import numpy as np
    strength = float(np.clip(strength, 0.0, 1.5))
    source = im.convert("RGBA")
    if strength == 0:
        return source.copy()
    a = np.asarray(source).astype(np.float32) / 255.0
    h, w = a.shape[:2]
    rng = np.random.default_rng(int(hashlib.sha1(key.encode()).hexdigest()[:8], 16))
    age = 0.55 + 0.45 * float(rng.random())
    low = Image.fromarray((rng.random((12, 12)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    mott = np.asarray(low).astype(np.float32) / 255.0
    yy = np.linspace(0, 1, h)[:, None]
    film = strength * age * (0.025 + 0.11 * np.clip((yy - 0.42) / 0.58, 0, 1) ** 1.5)
    k = 1.0 - film * (0.65 + 0.70 * mott)
    rgb = a[..., :3]
    # Small, strength-controlled pigment fading; no colour change in the zero-wear control.
    red = (rgb[..., 0] > 0.55) & (rgb[..., 1] < 0.35)
    fade = min(1.0, strength * age)
    faded = rgb * np.array([1.0 - 0.045 * fade, 1.0 + 0.05 * fade, 1.0 + 0.05 * fade]) + 0.008 * fade
    rgb = np.where(red[..., None], faded, rgb)
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722])
    rgb = rgb * (1.0 - 0.035 * fade) + lum[..., None] * (0.035 * fade)
    cov = a[..., 3] > 0.5
    # Pad with uncovered space. Unlike np.roll this also finds the edges of a full rectangular board.
    radius = max(1, int(round(min(w, h) * 0.008)))
    padded = np.pad(cov, radius, constant_values=False)
    inner = cov.copy()
    for dy, dx in ((-radius, 0), (radius, 0), (0, -radius), (0, radius)):
        inner &= padded[radius + dy:radius + dy + h, radius + dx:radius + dx + w]
    rim = cov & ~inner
    k = np.where(rim, k * (1.0 - 0.08 * fade), k)
    speck = (rng.random((h, w)) < 0.0015 * strength * age) & cov
    k = np.where(speck, k * 0.84, k)
    worn = np.clip(rgb * k[..., None], 0, 1)
    # Rare tiny edge chips expose neutral aluminium, never paint over the legend.
    chips = rim & red & (rng.random((h, w)) < 0.008 * strength * age)
    worn = np.where(chips[..., None], np.array([0.39, 0.40, 0.40]), worn)
    # Preserve transparent texels as well as alpha. This avoids coloured mip fringes outside coverage.
    worn = np.where(cov[..., None], worn, a[..., :3])
    out = np.concatenate([worn, a[..., 3:]], -1)
    return Image.fromarray((out * 255 + 0.5).astype(np.uint8), "RGBA")


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
