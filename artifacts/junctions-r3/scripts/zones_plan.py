"""P-21 zones: orthophoto 0.08 m | orthophoto + analytic hatch quads (ADR 0100 tracing aid).

    uv run --project tools/worldgen python artifacts/junctions-r3/scripts/zones_plan.py --out artifacts/junctions-r3/zones0 [--id <zone id> ...]
    [--extra "id;E,N E,N ...;key=val,..."]  (try an un-committed zone: polygon + chevron_axis/axis given as E,N lists)
"""
import argparse, sys
from pathlib import Path
import numpy as np, yaml
from PIL import Image, ImageDraw
sys.path.insert(0, "tools/worldgen")
from roads import pipeline, p21_hatch as H
from fidelity import ortho as O


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="bialystok-industrial-c")
    ap.add_argument("--out", required=True)
    ap.add_argument("--id", action="append", default=[])
    ap.add_argument("--px", type=int, default=800)
    ap.add_argument("--margin", type=float, default=4.0)
    a = ap.parse_args()
    reg = pipeline.load_region(a.region)
    ox, oy = reg["origin"]["x"], reg["origin"]["y"]
    ov = yaml.safe_load(open(f"Data/Regions/{a.region}/overrides.yaml", encoding="utf-8"))
    ov = ov.get("overrides", ov)
    ortho = O.Ortho(reg)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for o in ov:
        if o.get("kind") != "painted_zone" or (a.id and o["id"] not in a.id):
            continue
        g = H.hatch(o)
        x0, y0, x1, y1 = g["polygon"].bounds
        c = ((x0 + x1) / 2, (y0 + y1) / 2)
        half = max(x1 - x0, y1 - y0) / 2 + a.margin
        res = 2 * half / a.px
        rgb, _ = ortho.window((ox + c[0] - half, oy + c[1] - half, ox + c[0] + half, oy + c[1] + half), res)
        im = Image.fromarray(rgb).resize((a.px, a.px), Image.LANCZOS)
        im2 = im.copy()
        dr = ImageDraw.Draw(im2)

        def px(P):
            P = np.asarray(P, float)
            return [((p[0] - (c[0] - half)) / res, ((c[1] + half) - p[1]) / res) for p in P]
        for q in g["border"]:
            dr.polygon(px(q), outline=(0, 255, 255))
        for q in g["stripes"]:
            dr.polygon(px(q), outline=(255, 255, 0))
        for k in ("chevron_axis", "axis"):
            if o.get(k):
                dr.line(px(o[k]), fill=(255, 0, 0), width=2)
        # 1 m grid ticks
        for e in np.arange(np.floor(c[0] - half), c[0] + half, 1.0):
            x = (e - (c[0] - half)) / res
            dr.line([(x, 0), (x, 6 if e % 5 else 16)], fill=(255, 255, 255))
        for n in np.arange(np.floor(c[1] - half), c[1] + half, 1.0):
            y = ((c[1] + half) - n) / res
            dr.line([(0, y), (6 if n % 5 else 16, y)], fill=(255, 255, 255))
        sheet = Image.new("RGB", (2 * a.px + 6, a.px), (0, 0, 0))
        sheet.paste(im, (0, 0)); sheet.paste(im2, (a.px + 6, 0))
        ImageDraw.Draw(sheet).text((8, 8), f"{o['id']}  E {c[0]-half:.1f}..{c[0]+half:.1f} N {c[1]-half:.1f}..{c[1]+half:.1f}  {g['mode']} {g['fields']}", fill=(255, 255, 0))
        sheet.save(out / f"{o['id']}.jpg", quality=88)
        print(o["id"], g["fields"])


if __name__ == "__main__" and not any(x.startswith("--at") for x in sys.argv):
    main()


def grid_view(argv=None):
    """--at E,N,half,name [--poly "E,N E,N ..."]: ortho crop with a 1 m grid (5 m labelled) for tracing."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="bialystok-industrial-c")
    ap.add_argument("--out", required=True)
    ap.add_argument("--at", required=True)
    ap.add_argument("--poly", action="append", default=[])
    ap.add_argument("--px", type=int, default=1000)
    ap.add_argument("--step", type=float, default=1.0)
    a = ap.parse_args(argv)
    from PIL import ImageFont
    reg = pipeline.load_region(a.region)
    ox, oy = reg["origin"]["x"], reg["origin"]["y"]
    e, n, half, name = a.at.split(","); e, n, half = float(e), float(n), float(half)
    res = 2 * half / a.px
    rgb, _ = O.Ortho(reg).window((ox + e - half, oy + n - half, ox + e + half, oy + n + half), res)
    im = Image.fromarray(rgb).resize((a.px, a.px), Image.LANCZOS)
    dr = ImageDraw.Draw(im, "RGBA")
    X = lambda v: (v - (e - half)) / res
    Y = lambda v: ((n + half) - v) / res
    for v in np.arange(np.ceil(e - half), e + half, a.step):
        major = abs(v / 5 - round(v / 5)) < 1e-6
        dr.line([(X(v), 0), (X(v), a.px)], fill=(255, 255, 0, 140 if major else 45))
        if major:
            dr.text((X(v) + 2, 2), f"{v:.0f}", fill=(255, 255, 0, 255))
    for v in np.arange(np.ceil(n - half), n + half, a.step):
        major = abs(v / 5 - round(v / 5)) < 1e-6
        dr.line([(0, Y(v)), (a.px, Y(v))], fill=(255, 255, 0, 140 if major else 45))
        if major:
            dr.text((2, Y(v) + 2), f"{v:.0f}", fill=(255, 255, 0, 255))
    for s in a.poly:
        P = [tuple(float(t) for t in pt.split(",")) for pt in s.split()]
        dr.line([(X(p[0]), Y(p[1])) for p in P] + [(X(P[0][0]), Y(P[0][1]))], fill=(255, 0, 255, 255), width=2)
    Path(a.out).mkdir(parents=True, exist_ok=True)
    im.save(Path(a.out) / f"{name}.jpg", quality=90)


if __name__ == "__main__" and any(x.startswith("--at") for x in sys.argv):
    grid_view()
