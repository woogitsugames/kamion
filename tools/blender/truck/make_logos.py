"""Generate the three candidate brand marks (Track A2) as plain SVG.

    python tools/blender/truck/make_logos.py                 # SVGs only (stdlib)
    uv run --no-project --with pillow python tools/blender/truck/make_logos.py --preview out.png

Letters are geometric strokes and marks are polygons, all defined here (no fonts
-> no font licence issue, identical result everywhere). One colour, so a mark can
become a chrome or painted badge later. Output: art-source/truck/brand/<name>.svg
The optional --preview rasterises the same geometry with Pillow for visual QA.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "..", "art-source", "truck", "brand")
INK = "#1d1f22"
W, H = 640, 160
SCALE, STROKE, TRACK = 4.0, 6.0, 14.0  # wordmark: cap height 56 px

# Glyphs on a cap-height-14 grid: (advance width, [polyline, ...]); y up.
GLYPHS = {
    "T": (10, [[(0, 14), (10, 14)], [(5, 14), (5, 0)]]),
    "R": (10, [[(0, 0), (0, 14), (7.5, 14), (10, 11.5), (10, 9), (7.5, 6.5), (0, 6.5)], [(5, 6.5), (10, 0)]]),
    "A": (10, [[(0, 0), (0, 10), (4, 14), (6, 14), (10, 10), (10, 0)], [(0, 6), (10, 6)]]),
    "K": (10, [[(0, 0), (0, 14)], [(10, 14), (0, 5)], [(3.6, 8.2), (10, 0)]]),
    "B": (10, [[(0, 7), (0, 14), (7, 14), (9, 12), (9, 9), (7, 7), (0, 7), (0, 0), (8, 0), (10, 2), (10, 5),
                (8, 7), (7, 7)]]),
    "I": (0, [[(0, 0), (0, 14)]]),
    "E": (9, [[(9, 14), (0, 14), (0, 0), (9, 0)], [(0, 7), (7, 7)]]),
    "L": (9, [[(0, 14), (0, 0), (9, 0)]]),
    "N": (10, [[(0, 0), (0, 14), (10, 0), (10, 14)]]),
    "W": (14, [[(0, 14), (3, 0), (7, 10), (11, 0), (14, 14)]]),
}


def circle(cx, cy, r, n=72, ccw=False):
    s = -1 if ccw else 1
    return [(cx + r * math.cos(s * 2 * math.pi * i / n), cy + r * math.sin(s * 2 * math.pi * i / n)) for i in range(n)]


def bezier(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def band(center, half):
    """Closed polygon of constant width around an open centre polyline."""
    left, right = [], []
    for i, (x, y) in enumerate(center):
        x0, y0 = center[max(i - 1, 0)]
        x1, y1 = center[min(i + 1, len(center) - 1)]
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        left.append((x + nx * half, y + ny * half))
        right.append((x - nx * half, y - ny * half))
    return left + right[::-1]


def mark_trakt():
    """A road in perspective forms the stem of a T; two lane dashes are cut out."""
    t = [(30, 30), (150, 30), (150, 48), (104, 48), (122, 130), (58, 130), (76, 48), (30, 48)]
    return [t], [[(87, 62), (93, 62), (93, 80), (87, 80)], [(86, 92), (94, 92), (94, 114), (86, 114)]]


def mark_bielik():
    """One swept wing of three feathers (asymmetric on purpose, not a chevron pair)."""
    return [[(28, 58), (150, 34), (142, 52), (36, 70)],
            [(40, 80), (138, 62), (130, 80), (48, 92)],
            [(52, 102), (124, 90), (116, 106), (60, 114)]], []


def mark_narew():
    """Ring crossed by a river meander."""
    # ends sit at r~54 so the band merges into the ring instead of poking out of it
    river = bezier((40, 100), (58, 56), (78, 60), (90, 82)) + bezier((90, 82), (102, 104), (122, 104), (140, 60))[1:]
    return [circle(90, 80, 60), band(river, 8.5)], [circle(90, 80, 48)]


MARKS = {
    "trakt": ("TRAKT", mark_trakt, "TRAKT (old Polish word for a highway). Mark: road in perspective as the stem of a T."),
    "bielik": ("BIELIK", mark_bielik,
               "BIELIK (white-tailed eagle of the Podlasie wetlands). Mark: a single swept wing of three feathers."),
    "narew": ("NAREW", mark_narew, "NAREW (river running past Bialystok). Mark: ring crossed by a river meander."),
}


def wordmark_lines(text):
    x, y_base, lines = W * 0.30, H * 0.5 + 28, []
    for ch in text:
        adv, glyph = GLYPHS[ch]
        for pl in glyph:
            lines.append([(x + px * SCALE, y_base - py * SCALE) for px, py in pl])
        x += adv * SCALE + TRACK
    return lines


def to_svg(text, fills, holes, desc):
    def d(polys):
        return " ".join("M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in p) + " Z" for p in polys)

    # the meander must stay solid where it crosses the ring hole: holes only apply to the first polygon
    first = f'<path fill-rule="evenodd" d="{d([fills[0]] + holes)}"/>'
    rest = "".join(f'<path d="{d([p])}"/>' for p in fills[1:])
    lines = "\n    ".join('<polyline points="' + " ".join(f"{x:.2f},{y:.2f}" for x, y in pl) + '"/>'
                          for pl in wordmark_lines(text))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <title>{text} - candidate truck brand mark (TRUCK SIM PL, original, fictional)</title>
  <desc>{desc}</desc>
  <g fill="{INK}" stroke="none">{first}{rest}</g>
  <g fill="none" stroke="{INK}" stroke-width="{STROKE}" stroke-linecap="square" stroke-linejoin="miter">
    {lines}
  </g>
</svg>
"""


def preview(path):
    from PIL import Image, ImageDraw
    ss = 3
    variants = [("#ffffff", INK), ("#3a4f63", "#d9d9d6")]  # on paper; light badge on painted cab
    sheet = Image.new("RGB", (W * 2, H * 3 + 60), "white")
    for row, key in enumerate(MARKS):
        text, fn, _ = MARKS[key]
        fills, holes = fn()
        for col, (bg, ink) in enumerate(variants):
            im = Image.new("RGB", (W * ss, H * ss), bg)
            dr = ImageDraw.Draw(im)
            dr.polygon([(x * ss, y * ss) for x, y in fills[0]], fill=ink)
            for h in holes:
                dr.polygon([(x * ss, y * ss) for x, y in h], fill=bg)
            for p in fills[1:]:
                dr.polygon([(x * ss, y * ss) for x, y in p], fill=ink)
            for pl in wordmark_lines(text):
                pts = [(x * ss, y * ss) for x, y in pl]
                dr.line(pts, fill=ink, width=int(STROKE * ss), joint="curve")
            full = im.resize((W, H), Image.LANCZOS)
            sheet.paste(full, (col * W, row * H))
            if col == 0:  # small-size legibility test: badge ~40 px tall
                small = full.resize((W // 4, H // 4), Image.LANCZOS)
                sheet.paste(small, (row * (W // 4 + 20) + 10, H * 3 + 10))
    sheet.save(path)
    print("preview", path)


def main():
    os.makedirs(OUT, exist_ok=True)
    for key, (text, fn, desc) in MARKS.items():
        fills, holes = fn()
        p = os.path.normpath(os.path.join(OUT, f"{key}.svg"))
        with open(p, "w", encoding="utf-8") as f:
            f.write(to_svg(text, fills, holes, desc))
        print("wrote", p)
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])


if __name__ == "__main__":
    main()
