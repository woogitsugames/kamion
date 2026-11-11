"""Plan view of the generated road surface + markings beside the GUGiK orthophoto (ADR 0093 iteration tool).

    uv run --project tools/worldgen python tools/worldgen/fidelity/planview.py --out artifacts/junctions-r1/plan0 \
        [--rebuild] --at E,N,half,name ...   (cache: scratch pickle of road / markings parts, single-pass build)
Extra: --poly "E,N E,N ..." draws a yellow outline on both panels (tracing aid); --grid 10 draws a metre grid.
"""
import argparse, pickle, sys, os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from roads import pipeline, markings as MK
from fidelity import ortho as O

COL = {"road_asphalt": (70, 70, 74), "road_asphalt_new": (60, 60, 64), "road_concrete": (150, 150, 145),
       "road_paving": (170, 160, 150), "road_sett": (150, 130, 115), "curb_concrete": (205, 205, 200),
       "sidewalk_paving": (176, 170, 160), "verge_grass": (88, 120, 70), "shoulder_gravel": (140, 130, 110),
       "apron_sett": (160, 120, 100), "bridge_concrete": (120, 120, 118)}


def load(region, cache, rebuild):
    if cache.exists() and not rebuild:
        return pickle.load(open(cache, "rb"))
    w = pipeline.build(region)
    rep = {}
    MK.build_markings(w.buf, w.net, w.junctions, w.ctx["points"], rep)
    parts = [(p.layer, p.mat, p.src, p.V, p.T) for p in w.buf.parts if p.layer in ("road", "bridge", "markings") and len(p.T)]
    d = {"parts": parts, "origin": w.origin, "gores": w.stats.get("gores"), "mk": rep.get("markings"), "tl": rep.get("through_lines"), "pz": rep.get("painted_zones")}
    print("through", d["tl"], "zones", d["pz"])
    pickle.dump(d, open(cache, "wb"))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="bialystok-industrial-c")
    ap.add_argument("--out", required=True)
    ap.add_argument("--at", action="append", default=[])
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--poly", action="append", default=[])
    ap.add_argument("--grid", type=float, default=10.0)
    ap.add_argument("--px", type=int, default=900)
    ap.add_argument("--ortho-only", action="store_true")
    ap.add_argument("--outline", action="store_true", help="generated carriageway outline (cyan) + kerbs (magenta) on the ortho")
    ap.add_argument("--route", action="store_true", help="draw Data/Regions/<id>/route_start.json (red) on both panels")
    ap.add_argument("--cache", default=os.environ.get("PLAN_CACHE", "artifacts/junctions-r1/plan_cache.pkl"))
    a = ap.parse_args()
    d = load(a.region, Path(a.cache), a.rebuild)
    reg = pipeline.load_region(a.region)
    ox, oy = d["origin"]
    ortho = O.Ortho(reg)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    polys = [np.array([[float(v) for v in pt.split(",")] for pt in s.split()]) for s in a.poly]
    route = None
    if a.route:
        import json
        route = np.asarray(json.loads((pipeline.REGIONS / a.region / "route_start.json").read_text(encoding="utf-8"))["points_en"], float)
    for spec in a.at:
        e, n, half, name = spec.split(","); e, n, half = float(e), float(n), float(half)
        res = 2 * half / a.px
        rgb, src = ortho.window((ox + e - half, oy + n - half, ox + e + half, oy + n + half), res)
        im_o = Image.fromarray(rgb).resize((a.px, a.px), Image.LANCZOS)
        im_g = Image.new("RGB", (a.px, a.px), (96, 110, 84))
        dr = ImageDraw.Draw(im_g)

        def px(P):
            return np.column_stack([(P[:, 0] - (e - half)) / res, ((n + half) - P[:, 1]) / res])
        items = []
        for layer, mat, srcn, V, T in d["parts"]:
            lo, hi = V[:, :2].min(0), V[:, :2].max(0)
            if hi[0] < e - half or lo[0] > e + half or hi[1] < n - half or lo[1] > n + half:
                continue
            if layer == "markings":
                col = (245, 245, 240) if mat == "marking_white" else (230, 200, 60)
                pri = 2
            else:
                col = COL.get(mat)
                if col is None:
                    continue
                pri = 1 if mat == "curb_concrete" else 0
            tri = V[T]
            m = (tri[:, :, 0].max(1) > e - half) & (tri[:, :, 0].min(1) < e + half) & (tri[:, :, 1].max(1) > n - half) & (tri[:, :, 1].min(1) < n + half)
            for t in tri[m]:
                items.append((pri, float(t[:, 2].mean()), col, px(t)))
        items.sort(key=lambda x: (x[0], x[1]))
        for _, _, col, P in items:
            dr.polygon([tuple(q) for q in P], fill=col)
        for im in (im_o, im_g):
            dd = ImageDraw.Draw(im)
            if a.grid > 0:
                g0 = np.ceil((e - half) / a.grid) * a.grid
                while g0 < e + half:
                    x = (g0 - (e - half)) / res
                    dd.line([(x, 0), (x, 6)], fill=(255, 255, 0)); dd.text((x + 2, 6), f"{g0:.0f}", fill=(255, 255, 0))
                    g0 += a.grid
                g0 = np.ceil((n - half) / a.grid) * a.grid
                while g0 < n + half:
                    y = ((n + half) - g0) / res
                    dd.line([(0, y), (6, y)], fill=(255, 255, 0)); dd.text((8, y - 5), f"{g0:.0f}", fill=(255, 255, 0))
                    g0 += a.grid
            for P in polys:
                q = [tuple(v) for v in px(P)]
                dd.line(q + q[:1], fill=(255, 220, 0), width=1)
            if route is not None:
                m = (np.abs(route[:, 0] - e) < half + 5) & (np.abs(route[:, 1] - n) < half + 5)
                if m.sum() > 1:
                    dd.line([tuple(v) for v in px(route[m])], fill=(255, 40, 40), width=2)
        if a.outline:
            import shapely
            cw, kb = [], []
            for layer, mat, srcn, V, T in d["parts"]:
                if layer == "markings":
                    continue
                lo, hi = V[:, :2].min(0), V[:, :2].max(0)
                if hi[0] < e - half or lo[0] > e + half or hi[1] < n - half or lo[1] > n + half:
                    continue
                tri = V[T][:, :, :2]
                m = (tri[:, :, 0].max(1) > e - half) & (tri[:, :, 0].min(1) < e + half) & (tri[:, :, 1].max(1) > n - half) & (tri[:, :, 1].min(1) < n + half)
                tri = tri[m]
                if not len(tri):
                    continue
                a2 = np.abs((tri[:, 1, 0] - tri[:, 0, 0]) * (tri[:, 2, 1] - tri[:, 0, 1]) - (tri[:, 2, 0] - tri[:, 0, 0]) * (tri[:, 1, 1] - tri[:, 0, 1]))
                tri = tri[a2 > 1e-4]
                (cw if mat.startswith("road_") else kb if mat == "curb_concrete" else []).extend(shapely.polygons(tri))
            dd = ImageDraw.Draw(im_o)
            for geoms, colr in ((cw, (0, 255, 255)), (kb, (255, 0, 255))):
                if not geoms:
                    continue
                u = shapely.union_all([g.buffer(0.02) for g in geoms])
                for g in getattr(u, "geoms", [u]):
                    for ring in [g.exterior, *g.interiors]:
                        dd.line([tuple(q) for q in px(np.asarray(ring.coords))], fill=colr, width=1)
        if a.ortho_only:
            im_o.save(out / f"{name}_o.jpg", quality=90)
            print(name, src)
            continue
        both = Image.new("RGB", (2 * a.px + 6, a.px), (0, 0, 0))
        both.paste(im_o, (0, 0)); both.paste(im_g, (a.px + 6, 0))
        both.save(out / f"{name}.jpg", quality=88)
        print(name, src, both.size)


if __name__ == "__main__":
    main()
