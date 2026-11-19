"""D94 / ADR 0306: plan view of the built surfaces of a tile with the tyre tracks of qa/combo_lane_check.py (--dump-tile).

    uv run --project tools/worldgen python tools/worldgen/qa/combo_topview.py <combo.json> <tile> <E> <N> <half_m> <out.png>
        [--title TEXT] [--piece link:knyszyn-dk65-to-dw671-w ...]

Grey = carriageway (road_*), light = truck apron, tan = kerb / sidewalk / shoulder, green = no hard surface. Tracks:
tractor front axle path (black), tyre edges ok (blue = tractor, cyan = trailer), apron (violet), kerb (orange),
opposite lane (red), off hard surface (magenta)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import seam_section as SS  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
import os  # noqa: E402
if os.environ.get("KAMION_DATA_ROOT"):
    ROOT = Path(os.environ["KAMION_DATA_ROOT"])   # built chunks of another checkout (main = BEFORE)
COL = {"ok_t": "#1f5fbf", "ok_tr": "#2bb5c9", "apron": "#8a3fd1", "kerb": "#ff8c00", "opposite": "#e01010",
       "off_hard": "#ff00ff"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("combo"); ap.add_argument("tile"); ap.add_argument("e", type=float); ap.add_argument("n", type=float)
    ap.add_argument("half", type=float); ap.add_argument("out")
    ap.add_argument("--title", default=""); ap.add_argument("--piece", action="append")
    ap.add_argument("--swing", action="store_true", help="draw the driver-swing line instead of the lane centre")
    a = ap.parse_args(argv)
    c = np.array([a.e, a.n])
    fig, ax = plt.subplots(figsize=(9.6, 9.6), dpi=100)
    ax.set_facecolor("#9fc08a")
    tris, cols = [], []
    for node in ("road", "paved", "bridge"):
        for k, T in SS.tris(ROOT, a.tile, node, c, rad=a.half * 1.5).items():
            if k.startswith("road_"):
                col = "#6e6e6e"
            elif k.startswith("apron_"):
                col = "#cfcac0"
            elif any(w in k for w in ("grass", "verge", "island")):
                col = "#9fc08a"
            else:
                col = "#d9c39a"
            tris.append(T); cols += [col] * len(T)
    if tris:
        T = np.concatenate(tris); o = np.argsort(T[:, :, 2].mean(1))      # painter's order: islands over the patch
        ax.add_collection(PolyCollection(T[o, :, :2], facecolors=np.array(cols)[o], edgecolors="none", zorder=1))
    d = json.loads(Path(a.combo).read_text(encoding="utf-8"))
    rows = [r for rows in d["corridors"].values() for r in rows if r.get("tile") == a.tile and "dump" in r]
    rows += [r for r in d["links"].values() if r.get("tile") == a.tile and "dump" in r]
    seen = set()
    for r in rows:
        if a.piece and r["piece"] not in a.piece or r["piece"] in seen:
            continue
        seen.add(r["piece"])
        D = r["swing"]["dump"] if a.swing and "swing" in r and "dump" in r["swing"] else r["dump"]
        P = np.array(D["path"]); ax.plot(P[:, 0], P[:, 1], color="black", lw=0.8, zorder=4)
        pts, cls, axle = np.array(D["pts"]), np.array(D["cls"]), np.array(D["axle"])
        tr = np.char.startswith(axle.astype(str), "trailer")
        for k in ("ok", "apron", "kerb", "opposite", "off_hard"):
            m = cls == k
            if k == "ok":
                ax.scatter(pts[m & ~tr, 0], pts[m & ~tr, 1], s=1.2, c=COL["ok_t"], zorder=5, linewidths=0)
                ax.scatter(pts[m & tr, 0], pts[m & tr, 1], s=1.2, c=COL["ok_tr"], zorder=5, linewidths=0)
            elif m.any():
                ax.scatter(pts[m, 0], pts[m, 1], s=9, c=COL[k], zorder=6, linewidths=0, label=f"{k} ({int(m.sum())})")
    ax.set_xlim(a.e - a.half, a.e + a.half); ax.set_ylim(a.n - a.half, a.n + a.half); ax.set_aspect("equal")
    ax.set_title(a.title or f"{a.tile}: tor zestawu 16,5 m (os przednia na srodku pasa)", fontsize=10)
    h, l = ax.get_legend_handles_labels()
    if h:
        ax.legend(loc="lower left", fontsize=8)
    ax.tick_params(labelsize=7)
    fig.tight_layout(); Path(a.out).parent.mkdir(parents=True, exist_ok=True); fig.savefig(a.out); plt.close(fig)
    print(a.out)


if __name__ == "__main__":
    main()
