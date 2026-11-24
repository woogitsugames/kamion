"""forest-height-s24 (ADR 0339): control cameras looking at the forests of a tile, in the gate3 camera format
(scripts/visual-qa.ps1 -Gate3 <file>), chosen from the route, the BDOT forest polygons and the canopy height model.

    uv run --project tools/worldgen python artifacts/forest-height-s24/tools/forest_cams.py dk65-04 dk65-05 dw671-tykocin-03

Per region -> artifacts/forest-height-s24/cams/<id>.json + <id>_map.png (CHM, route, cameras):
  fh_cab_corridor   driver eye on the route where the stand is closest on both sides
  fh_cab_approach   driver eye where the nearest stand ahead is 150-450 m away (stand silhouette against the sky)
  fh_side_a / _b    eye height on the route, looking square at a stand edge 90-350 m across open ground
  fh_air            60 m above the route, 20 deg down, over the most varied stand (structure of the canopy)
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import shapely
import yaml

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
from roads.profile import load_heightfield  # noqa: E402
from streetscape import forest_chm as FCH  # noqa: E402

OUT = REPO / "artifacts" / "forest-height-s24" / "cams"


EXTRAS = {
    "dw671-tykocin-03": [
        ("fh_side_a", (600, 80), (860, -40), "shelter belt 250-300 m east of the road, side on"),
        ("fh_side_b", (760, 440), (380, 800), "the wood north-west of the road, 500 m away (far stand line)"),
        ("fh_side_c", (330, -330), (500, -410), "small clump 170 m east of the road (the dark box of frame t3271)"),
    ],
}


def main(rid):
    rdir = REPO / "Data" / "Regions" / rid
    reg = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
    org = (float(reg["origin"]["x"]), float(reg["origin"]["y"]))
    oz = float(reg["origin"]["z"])
    hf = load_heightfield(json.loads((rdir / "terrain.json").read_text(encoding="utf-8")), REPO, org)
    chm = FCH.load(rid, org)
    route = np.array(json.loads((rdir / "route_start.json").read_text(encoding="utf-8"))["points_en"], float)
    src = json.loads((rdir / "generated" / "streetscape_sources.json").read_text(encoding="utf-8"))
    polys = [shapely.Polygon(f["geometry"]["coordinates"][0]) for f in src["bdot10k"]["OT_PTLZ_A"]]
    forest = shapely.affinity.translate(shapely.union_all([p if p.is_valid else p.buffer(0) for p in polys]), -org[0], -org[1])
    shapely.prepare(forest)
    half = float(reg["bbox"]["width_m"]) / 2
    n = len(route)
    d = np.gradient(route, axis=0)
    d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
    left = np.column_stack([-d[:, 1], d[:, 0]])

    def tall(P):                                # a grown stand of the model inside a BDOT forest
        dom, _, _, ins = chm.sample(P)
        return ins & (dom >= 10.0) & shapely.contains_xy(forest, P[:, 0], P[:, 1])

    def first_hit(p, v, lo, hi, step=6.0):
        rs = np.arange(lo, hi, step)
        Q = p[None, :] + rs[:, None] * v[None, :]
        ok = (np.abs(Q) < half - 5).all(axis=1)
        h = tall(Q) & ok
        return float(rs[np.argmax(h)]) if h.any() else None

    idx = np.arange(15, n - 15, 10)             # every 20 m
    lat = {i: (first_hit(route[i], left[i], 8, 420), first_hit(route[i], -left[i], 8, 420)) for i in idx}
    ahead = {i: first_hit(route[i], d[i], 20, 700, 10.0) for i in idx}
    cams = []

    def zg(p):
        return float(hf.sample(p[0], p[1])) - oz

    def add(cid, kind, p, look, fov, note, eye=2.5, seat=None):
        p = np.asarray(p, float)
        look = np.asarray(look, float)
        e = {"id": cid, "kind": kind, "pos": [round(p[0], 2), round(p[1], 2), round(zg(p) + eye, 2)],
             "look_at": [round(look[0], 2), round(look[1], 2), round(zg(p) + eye + (look[2] if len(look) > 2 else 0.0), 2)],
             "fov_deg": fov, "note": note}
        if seat:
            e["seat"] = seat
        cams.append(e)

    # corridor: both sides close
    cor = [(max(a, b), i) for i, (a, b) in lat.items() if a is not None and b is not None and max(a, b) < 60]
    if cor:
        _, i = min(cor)
        add("fh_cab_corridor", "driver_eye", route[i], route[i] + d[i] * 60, 60,
            f"driver eye, route point {i}: stand {lat[i][0]:.0f} m left / {lat[i][1]:.0f} m right")
    else:
        one = [(min(x for x in ab if x is not None), i) for i, ab in lat.items() if any(x is not None for x in ab)]
        if one:
            _, i = min(one)
            add("fh_cab_corridor", "driver_eye", route[i], route[i] + d[i] * 60, 60,
                f"driver eye, route point {i}: nearest stand beside the road {min(x for x in lat[i] if x is not None):.0f} m")
    # approach: open here, stand 150-450 m ahead or ahead-right / ahead-left
    best = None
    for i in idx:
        for ang in (0.0, 12.0, -12.0, 25.0, -25.0):
            c, s_ = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            v = np.array([d[i][0] * c - d[i][1] * s_, d[i][0] * s_ + d[i][1] * c])
            r = first_hit(route[i], v, 20, 600, 10.0)
            near = min([x for x in lat[i] if x is not None] or [999])
            if r is not None and 150 <= r <= 450 and near > 80:
                # width of the stand across the view: how many of 9 rays +-16 deg hit a stand within 700 m
                w = sum(first_hit(route[i], np.array([v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a)]),
                                  20, 700, 10.0) is not None for a in np.radians(np.linspace(-16, 16, 9)))
                score = (w, -abs(r - 280))
                if best is None or score > best[0]:
                    best = (score, i, r)
    if best:
        _, i, r = best
        add("fh_cab_approach", "driver_eye", route[i], route[i] + d[i] * 60, 60,
            f"driver eye, route point {i}: stand {r:.0f} m ahead, silhouette against the sky")
    # side views: square at a stand edge across open ground, most varied top line first
    side = []
    for i in idx:
        for sgn, r in ((1, lat[i][0]), (-1, lat[i][1])):
            if r is None or not 90 <= r <= 350:
                continue
            v = left[i] * sgn
            # tops of the stand along 240 m of its edge as seen from here
            tops = []
            for a in np.radians(np.linspace(-28, 28, 15)):
                w = np.array([v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a)])
                rr = first_hit(route[i], w, 8, 600)
                if rr is not None:
                    q = route[i] + (rr + 12) * w
                    tops.append(float(chm.sample(q)[0][0]))
            if len(tops) >= 11:
                side.append((float(np.std(tops)), i, sgn, r, min(tops), max(tops)))
    side.sort(reverse=True)
    used = []
    for sd, i, sgn, r, lo, hi in side:
        if any(abs(i - j) < 150 for j in used):
            continue
        v = left[i] * sgn
        add(f"fh_side_{'ab'[len(used)]}", "photo_match", route[i] + v * 3.0, route[i] + v * 60 + np.array([0, 0]), 50,
            f"eye 2.5 m beside the road at route point {i}, square at a stand edge {r:.0f} m away; crown tops of the model "
            f"{lo:.0f}-{hi:.0f} m along the view", seat="file")
        used.append(i)
        if len(used) == 2:
            break
    # air view over the most varied stand near the route
    best = None
    for i in idx:
        Q = route[i] + d[i] * 150 + np.random.default_rng(i).uniform(-120, 120, (400, 2))
        m = tall(Q)
        if m.mean() > 0.45:
            dom = chm.sample(Q)[0]
            sc = float(np.std(dom[shapely.contains_xy(forest, Q[:, 0], Q[:, 1])]))
            if best is None or sc > best[0]:
                best = (sc, i)
    if best:
        _, i = best
        p = route[i]
        e = {"id": "fh_air", "kind": "photo_match", "seat": "file",
             "pos": [round(p[0], 2), round(p[1], 2), round(zg(p) + 60.0, 2)],
             "look_at": [round(p[0] + d[i][0] * 150, 2), round(p[1] + d[i][1] * 150, 2), round(zg(p) + 60.0 - 55.0, 2)],
             "fov_deg": 60, "note": f"60 m above route point {i}, 20 deg down along the road: canopy structure"}
        cams.append(e)
    # hand-picked views where the picker finds none (stands far from the road): (id, route point near E/N, look at E/N)
    for cid, near, look, note in EXTRAS.get(rid, []):
        i = int(np.argmin(np.hypot(*(route - np.asarray(near, float)).T)))
        add(cid, "photo_match", route[i], np.asarray(look, float), 40, f"eye 2.5 m on the route at point {i}: {note}", seat="file")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{rid}.json").write_text(json.dumps({"schema": "truck-sim-pl/gate3-cameras/1", "region": rid,
                                                 "provenance": "artifacts/forest-height-s24/tools/forest_cams.py",
                                                 "cameras": cams}, indent=1) + "\n", encoding="utf-8", newline="\n")
    # map
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 9), dpi=100)
    im = ax.imshow(chm.top, extent=(-half, half, -half, half), cmap="viridis", vmin=0, vmax=32)
    plt.colorbar(im, ax=ax, fraction=0.035, label="crown top above ground [m] (GUGiK NMPT - NMT)")
    for g in getattr(forest, "geoms", [forest]):
        ax.plot(*g.exterior.xy, color="white", lw=0.4)
    ax.plot(route[:, 0], route[:, 1], color="red", lw=1.2)
    for c in cams:
        p, q = np.array(c["pos"][:2]), np.array(c["look_at"][:2])
        v = (q - p) / max(np.hypot(*(q - p)), 1e-9)
        ax.annotate("", xy=p + v * 140, xytext=p, arrowprops={"arrowstyle": "->", "color": "orange", "lw": 1.5})
        ax.text(p[0] + 12, p[1] + 12, c["id"][3:], color="orange", fontsize=8)
    ax.set_title(f"{rid}: canopy height model, route, forest cameras")
    fig.tight_layout()
    fig.savefig(OUT / f"{rid}_map.png")
    plt.close(fig)
    print(rid, [(c["id"], c["note"]) for c in cams])


if __name__ == "__main__":
    for r in sys.argv[1:]:
        main(r)
