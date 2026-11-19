"""Lane / carriageway width audit along the start route (ADR 0301): orthophoto vs the generator, station by station.

  uv run --project tools/worldgen python tools/worldgen/qa/lane_width_audit.py --region <id> [--step 50] [--fetch]
         [--out artifacts/lanes-audit-s24/<tag>] [--edges w1,w2 (OSM ways instead of the route)]

What is measured (every --step m along Data/Regions/<id>/route_start.json; the route runs in the middle of the lane the
truck drives, so u = 0 of every profile is "the generated route lane centre"):
  * a profile perpendicular to the route, u = -20 ... +20 m (left of travel = +), 0.05 m step, median of 13 rows
    -3 ... +3 m along the route;
  * orthophoto: GUGiK WMS HighResolution 0.08 m cells (fidelity/ortho.py, --fetch gets the missing ones along the
    route, polite, cached with a manifest) or the 0.25 m 2024-05-27 sheet; asphalt = run of grey, unsaturated,
    non-green samples through the core +-1.2 m (paint counts as asphalt, 0.3 m of noise tolerated); paint lines =
    brightness peaks >= core + LINE_DV that are <= 0.45 m wide;
  * generated: the in-memory generator (fidelity/gen.py = roads.pipeline.build + markings.build_markings), carriageway
    triangles (run through u = 0) and longitudinal marking triangles (kinds in LONG_KINDS) on the same profile.
Derived per station and side: carriageway width, number of lanes (= interior lines + 1, a line < EDGE_TOL m from the
asphalt edge is an edge line P-7, not a lane line), width of the route lane (between the lines / edges around u = 0)
and the lateral offset of the real lane centre from the generated route point (positive = real lane is left).

Accuracy: about +-0.1 m for a line on the 0.08 m cells, +-0.25 m on the sheet; asphalt edges +-0.3 m (shadows, parked
cars, kerb stones in asphalt colour). Junction mouths, lay-bys and tree shadow give wrong asphalt widths: each station
is drawn on a strip sheet (<out>/strips_*.jpg, <= 960 px) and every number used in a decision is looked at there.
Outputs: <out>/<region>.json (rows), <out>/<region>.md (table). Reference only (docs/05 §3): no pixel goes to the game.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
REPO = HERE.parents[3]

U = np.arange(-20.0, 20.0 + 1e-9, 0.05)
V = np.arange(-6.0, 6.0 + 1e-9, 0.5)   # +-6 m covers one period of P-1a (4 + 8 m)
K0 = len(U) // 2
LINE_DV = 22.0          # WORKING_VALUE: paint brighter than the asphalt core by this much (0-255 mean RGB)
LINE_MAX_W = 0.45       # m, wider bright runs are kerbs / concrete / crossings, not a line
LINE_ROWS = 0.2         # WORKING_VALUE: share of the 25 rows with a narrow peak at that column
EDGE_TOL = 0.6          # m, a line this close to the asphalt edge is an edge line (P-7), not a lane boundary
LONG_KINDS = {"lane", "centre", "P-1a", "P-1b", "P-1c", "P-1d", "P-1e", "P-2a", "P-2b", "P-3a", "P-3b", "P-4", "P-6", "P-7a", "P-7b",
              "P-7c", "P-7d"}


def runs(mask):
    """[(i0, i1)] inclusive index runs of True."""
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def run_through(mask, k0=K0, gap=6):
    """(u_right, u_left) of the run of `mask` through index k0, gaps <= `gap` samples bridged; None if k0 is off."""
    lo = max(0, k0 - 24)
    if not mask[lo:k0 + 25].any():
        return None

    def ext(step):
        k, miss, last = k0, 0, k0
        while 0 < k < len(mask) - 1 and miss <= gap:
            k += step
            if mask[k]:
                last, miss = k, 0
            else:
                miss += 1
        return last
    return float(U[ext(-1)]), float(U[ext(+1)])


def ortho_profile(rgb):
    """rgb (len(V), len(U), 3) -> dict(asphalt (uR, uL) | None, lines [u], core brightness)."""
    a = rgb.astype(float)
    med = np.median(a, axis=0)
    v = med.mean(axis=1)
    mx, mn = med.max(axis=1), med.min(axis=1)
    sat = (mx - mn) / np.maximum(mx, 1)
    green = med[:, 1] - 0.5 * (med[:, 0] + med[:, 2])
    # paint: per row, narrow (<= LINE_MAX_W) peaks brighter than the asphalt 0.4-0.6 m to both sides by LINE_DV and
    # unsaturated; a line = a column where such peaks occur in >= LINE_ROWS of the rows (dashes cover 1/3 of +-6 m,
    # car roofs and kerbs are wider than a line and drop out)
    L = a.mean(axis=2)
    S_ = (a.max(axis=2) - a.min(axis=2)) / np.maximum(a.max(axis=2), 1)
    side = np.maximum(np.roll(L, 10, axis=1), np.roll(L, -10, axis=1))
    side2 = np.maximum(np.roll(L, 12, axis=1), np.roll(L, -12, axis=1))
    peak = (L > np.maximum(side, side2) + LINE_DV) & (S_ < 0.18)
    frac = peak.mean(axis=0)
    frac = np.convolve(frac, np.ones(3) / 3, mode="same")
    core = slice(K0 - 24, K0 + 25)
    a_v, a_sat = float(np.median(v[core])), float(np.median(sat[core]))
    ok = (sat < a_sat + 0.07) & (np.abs(v - a_v) < 38) & (green < 6)
    paint = frac >= LINE_ROWS
    asph = run_through(ok | paint | (np.percentile(L, 80, axis=0) > a_v + LINE_DV))
    lines = []
    for i0, i1 in runs(paint):
        lines.append(round(float(U[i0 + int(np.argmax(frac[i0:i1 + 1]))]), 2))
    if asph:
        lines = [u for u in lines if asph[0] - 0.15 <= u <= asph[1] + 0.15]
    return {"asphalt": asph, "lines": lines, "core_v": round(a_v, 1)}


def layout(asph, lines):
    """Lanes from an asphalt run and its paint lines: (n_lanes, boundaries incl. edges, edge lines, route lane width,
    route lane centre). Lane boundaries: interior lines; at each side the edge line if there is one, else the edge."""
    if not asph:
        return None
    uR, uL = asph
    inner = sorted(u for u in lines if uR + EDGE_TOL < u < uL - EDGE_TOL)
    eR = [u for u in lines if u <= uR + EDGE_TOL]
    eL = [u for u in lines if u >= uL - EDGE_TOL]
    bR = max(eR) if eR else uR
    bL = min(eL) if eL else uL
    b = [bR] + inner + [bL]
    lane = None
    for a, c in zip(b, b[1:]):
        if a <= 0.0 <= c:
            lane = (a, c)
    if lane is None:                                  # route point outside every lane: nearest one
        lane = min(zip(b, b[1:]), key=lambda p: min(abs(p[0]), abs(p[1])))
    return {"width": round(uL - uR, 2), "lanes": len(inner) + 1, "bounds": [round(x, 2) for x in b],
            "edge_lines": [bool(eR), bool(eL)], "lane_w": round(lane[1] - lane[0], 2),
            "lane_c": round(0.5 * (lane[0] + lane[1]), 2)}


def route_stations(region, step, ways=None):
    d = REPO / "Data/Regions" / region
    rs = json.loads((d / "route_start.json").read_text(encoding="utf-8"))
    P = np.array(rs["points_en"], float)[:, :2]
    E = rs["edge"]
    s = np.r_[0.0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    out = []
    for st in np.arange(step / 2, s[-1] - 5.0, step):
        i = int(np.searchsorted(s, st))
        i = min(max(i, 1), len(P) - 2)
        a, b = P[max(i - 4, 0)], P[min(i + 4, len(P) - 1)]
        t = (b - a) / max(np.hypot(*(b - a)), 1e-9)
        out.append({"s": round(float(st), 1), "xy": P[i], "t": t, "edge": E[i]})
    return out


def sample_grid(c, t):
    n = np.array([-t[1], t[0]])
    X = c[0] + U[None, :] * n[0] + V[:, None] * t[0]
    Y = c[1] + U[None, :] * n[1] + V[:, None] * t[1]
    return X, Y


def gen_profile(G, c, t, res=0.05):
    from fidelity.gen import rasterize
    half = 22.0
    x0, y1 = c[0] - half, c[1] + half
    shape = (int(2 * half / res), int(2 * half / res))
    X, Y = sample_grid(c, t)
    col = np.clip(((X - x0) / res).astype(int), 0, shape[1] - 1)
    row = np.clip(((y1 - Y) / res).astype(int), 0, shape[0] - 1)
    cw = rasterize(G.tris, x0, y1, res, shape)[row, col].mean(0) >= 0.5
    lm = np.zeros(shape, bool)
    for k, tr in G.mark_tris.items():
        if k.split("-P-2a")[0] in LONG_KINDS:
            lm |= rasterize(tr, x0, y1, res, shape)
    lp = lm[row, col].mean(0) >= 0.12
    asph = run_through(cw, gap=4)
    lines = [round(float(0.5 * (U[i0] + U[i1])), 2) for i0, i1 in runs(lp)]
    if asph:
        lines = [u for u in lines if asph[0] - 0.15 <= u <= asph[1] + 0.15]
    return {"asphalt": asph, "lines": lines}


def strip_image(rgb_full, g, o, label):
    """Straightened orthophoto strip (u across, rows along) with generated edges (red), generated lines (cyan),
    orthophoto lines (yellow), route point (magenta)."""
    from PIL import Image, ImageDraw
    im = Image.fromarray(np.uint8(np.clip(rgb_full, 0, 255)))
    d = ImageDraw.Draw(im)
    h = im.height
    px = lambda u: int(round((u - U[0]) / 0.05))
    if g["asphalt"]:
        for u in g["asphalt"]:
            d.line([(px(u), 0), (px(u), h)], fill=(255, 40, 40), width=2)
    for u in g["lines"]:
        d.line([(px(u), 0), (px(u), h // 2)], fill=(0, 230, 255), width=2)
    for u in o["lines"]:
        d.line([(px(u), h // 2), (px(u), h)], fill=(255, 230, 0), width=2)
    if o["asphalt"]:
        for u in o["asphalt"]:
            d.line([(px(u), h - 14), (px(u), h)], fill=(255, 140, 0), width=3)
    d.ellipse([px(0) - 4, h // 2 - 4, px(0) + 4, h // 2 + 4], outline=(255, 0, 255), width=2)
    for m in range(-20, 21, 2):
        d.line([(px(m), h - 6), (px(m), h)], fill=(255, 255, 255), width=1)
    d.rectangle([0, 0, 8 * len(label) + 6, 14], fill=(0, 0, 0))
    d.text((3, 1), label, fill=(255, 255, 0))
    return im


def osm_attrs(graph, eid):
    for e in graph["edges"]:
        if e["id"] == eid:
            a = e["attrs"]
            v = lambda k: (a.get(k) or {}).get("v")
            return {"way": e.get("osm_way"), "name": v("name"), "highway": v("highway"), "oneway": v("oneway"),
                    "lanes": v("lanes"), "width": v("width"), "width_src": (a.get("width") or {}).get("src"),
                    "turn": v("turn:lanes") or v("turn:lanes:forward")}
    return {}


def audit(region, step=50.0, fetch=False, out=None, gen=None, reuse_gen=None):
    from fidelity import ortho as O
    from fidelity import gen as FG
    from roads import pipeline
    reg = pipeline.load_region(region)
    ox, oy = reg["origin"]["x"], reg["origin"]["y"]
    st = route_stations(region, step)
    if fetch:
        import shapely
        rs = json.loads((REPO / "Data/Regions" / region / "route_start.json").read_text(encoding="utf-8"))
        line = shapely.LineString(np.array(rs["points_en"], float)[:, :2] + [ox, oy])
        O.fetch_cells(reg, O.cells_for(reg, [line], pad=24.0))
    orth = O.Ortho(reg)
    prev = None
    if reuse_gen:
        prev = {r["station"]: r for r in json.loads(Path(reuse_gen).read_text(encoding="utf-8"))}
    G = gen or (None if prev else FG.build(region))
    graph = json.loads((REPO / "Data/Regions" / region / "roads.graph.json").read_text(encoding="utf-8"))
    secs = G.world.net.sections if G else {}
    rows, strips = [], []
    for k, s in enumerate(st):
        c, t = s["xy"], s["t"]
        X, Y = sample_grid(c, t)
        bb = (float(X.min() + ox - 1), float(Y.min() + oy - 1), float(X.max() + ox + 1), float(Y.max() + oy + 1))
        rgb, src = orth.window(bb, 0.05)
        col = np.clip(((X + ox - bb[0]) / 0.05).astype(int), 0, rgb.shape[1] - 1)
        row = np.clip(((bb[3] - (Y + oy)) / 0.05).astype(int), 0, rgb.shape[0] - 1)
        o = ortho_profile(rgb[row, col])
        g = ({kk: prev[k]["gen"][kk] for kk in ("asphalt", "lines")} if prev else gen_profile(G, c, t))
        lo, lg = layout(o["asphalt"], o["lines"]), layout(g["asphalt"], g["lines"])
        sec = secs.get(s["edge"])
        r = {"region": region, "station": k, "s": s["s"], "e": round(float(c[0]), 1), "n": round(float(c[1]), 1),
             "edge": s["edge"], "osm": osm_attrs(graph, s["edge"]), "ortho_src": src,
             "gen_sec": prev[k]["gen_sec"] if prev else None if sec is None else {"lanes": sec.lanes, "lane_w": sec.lane_w, "width": sec.width,
                                                  "edge_strip": sec.edge_strip, "width_src": sec.width_src,
                                                  "cls": sec.cls},
             "ortho": dict(o, layout=lo), "gen": dict(g, layout=lg)}
        if lo and lg:
            r["d_width"] = round(lg["width"] - lo["width"], 2)
            r["d_lanes"] = lg["lanes"] - lo["lanes"]
            r["d_lane_w"] = round(lg["lane_w"] - lo["lane_w"], 2)
            r["lane_offset"] = lo["lane_c"]
        rows.append(r)
        # strip: 40 m across x 12 m along at 0.05 m
        Va = np.arange(6.0, -6.0 - 1e-9, -0.05)
        n_ = np.array([-t[1], t[0]])
        Xs = c[0] + U[None, :] * n_[0] + Va[:, None] * t[0]
        Ys = c[1] + U[None, :] * n_[1] + Va[:, None] * t[1]
        bb2 = (float(Xs.min() + ox - 1), float(Ys.min() + oy - 1), float(Xs.max() + ox + 1), float(Ys.max() + oy + 1))
        rgb2, _ = orth.window(bb2, 0.05)
        c2 = np.clip(((Xs + ox - bb2[0]) / 0.05).astype(int), 0, rgb2.shape[1] - 1)
        r2 = np.clip(((bb2[3] - (Ys + oy)) / 0.05).astype(int), 0, rgb2.shape[0] - 1)
        nm = (r["osm"].get("name") or r["osm"].get("highway") or "")[:18]
        lab = (f"{region.replace('bialystok-', '')} #{k} s{s['s']:.0f} {nm} "
               f"W o{lo['width'] if lo else '-'}/g{lg['width'] if lg else '-'} "
               f"L o{lo['lanes'] if lo else '-'}/g{lg['lanes'] if lg else '-'} "
               f"lw o{lo['lane_w'] if lo else '-'}/g{lg['lane_w'] if lg else '-'}")
        strips.append(strip_image(rgb2[r2, c2], g, o, lab))
        print(json.dumps({kk: r.get(kk) for kk in ("station", "s", "edge", "d_width", "d_lanes", "d_lane_w",
                                                     "lane_offset")}), flush=True)
    if out:
        out = Path(out)
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{region}.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False, default=float),
                                            encoding="utf-8")
        (out / f"{region}.md").write_text(table(rows), encoding="utf-8")
        save_sheets(strips, out / f"strips_{region}")
    return rows


def save_sheets(strips, prefix, per=8):
    from PIL import Image
    for p in range(0, len(strips), per):
        part = [s.resize((960, int(s.height * 960 / s.width))) for s in strips[p:p + per]]
        sheet = Image.new("RGB", (960, sum(s.height for s in part)))
        y = 0
        for s in part:
            sheet.paste(s, (0, y))
            y += s.height
        sheet.save(f"{prefix}_{p // per:02d}.jpg", quality=86)


def table(rows):
    h = ("| # | s m | edge | name | OSM lanes / width(src) | gen lanes x lane_w (src) | ortho W / lanes / lane_w | "
         "gen W / lanes / lane_w | dW | dLanes | dLaneW | lane offset |\n" + "|---" * 12 + "|\n")
    out = [h]
    for r in rows:
        o, g, sec, osm = r["ortho"]["layout"], r["gen"]["layout"], r["gen_sec"] or {}, r["osm"]
        f = lambda L: f"{L['width']} / {L['lanes']} / {L['lane_w']}" if L else "-"
        out.append(f"| {r['station']} | {r['s']:.0f} | {r['edge']} | {osm.get('name') or osm.get('highway')} | "
                   f"{osm.get('lanes')} / {osm.get('width')} ({osm.get('width_src')}) | "
                   f"{sec.get('lanes')} x {sec.get('lane_w')} ({sec.get('width_src')}) | {f(o)} | {f(g)} | "
                   f"{r.get('d_width', '-')} | {r.get('d_lanes', '-')} | {r.get('d_lane_w', '-')} | "
                   f"{r.get('lane_offset', '-')} |\n")
    good = [r for r in rows if "d_width" in r]
    if good:
        dw = [abs(r["d_width"]) for r in good]
        dl = [abs(r["d_lane_w"]) for r in good]
        out.append(f"\nStations {len(rows)}, measured {len(good)}; |dW| median {statistics.median(dw):.2f} m, "
                   f"|dLaneW| median {statistics.median(dl):.2f} m, lane count differs at "
                   f"{sum(1 for r in good if r['d_lanes'])}.\n")
    return "".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--region", required=True, action="append")
    ap.add_argument("--step", type=float, default=50.0)
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--reuse-gen", default=None, help="<dir>: take the generated profiles from <dir>/<region>.json")
    a = ap.parse_args(argv)
    for r in a.region:
        audit(r, a.step, a.fetch, a.out, reuse_gen=(Path(a.reuse_gen) / f"{r}.json") if a.reuse_gen else None)


if __name__ == "__main__":
    main()
