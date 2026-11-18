"""ADR 0211 dev: cross-sections of the DK8 cutting from dev_dump.pkl (road z, zc0, deck) per tunnel chain."""
import json
import pickle
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import numpy as np  # noqa: E402
from roads import pipeline  # noqa: E402
from roads.network import side_params, side_profile  # noqa: E402

d = pickle.load(open(REPO / "artifacts/tunnel-0211/dev_dump.pkl", "rb"))
w, zc, deck, dmask = d["w"], d["zc"], d["deck"], d["deck_mask"]
hf = w.hf
g = json.loads((pipeline.REGIONS / "bialystok-kleeberga" / "roads.graph.json").read_text(encoding="utf-8"))
eids = {e["id"] for e in g["edges"] if str(e["attrs"].get("tunnel", {}).get("v", "no")) not in ("no", "building_passage")}


def samp(a, x, y):
    i = int(round(x - hf.x0)); j = int(round(hf.y1 - y))
    return float(a[j, i])


for c in w.net.chains:
    tun = np.array([w.net.sec_list[int(k)].edge_id in eids for k in c.sec_idx])
    if not tun.any():
        continue
    s = c.line.s
    sa, sb = s[tun].min(), s[tun].max()
    print(c.id, "len", round(c.length), "tunnel s", round(sa, 1), round(sb, 1), "t_a/t_b", round(c.t_a, 1), round(c.t_b, 1))
    for side, sg in (("L", 1), ("R", -1)):
        kind, kh, wd, depth, mat = side_params(c, side, 0.5 * (sa + sb))
        print("  side", side, kind, kh, wd, depth, mat, "prof", side_profile(kind, kh, wd, depth, mat))
    for st in np.arange(sa - 160, sb + 161, 20.0):
        if st < 0 or st > c.length:
            continue
        p = c.line.point(st); _, n = c.line.frame(st)
        hw = float(c.hw_at(st)); zr = float(c.zc(st))
        row = []
        for lat in (-24, -18, -14, -11, -9, -7, -5, 5, 7, 9, 11, 14, 18, 24):
            q = p + n * lat
            try:
                z = samp(zc, *q) - zr
                dk = samp(deck, *q) - zr if samp(dmask, *q) else None
            except IndexError:
                z, dk = float("nan"), None
            row.append(f"{lat:+d}:{z:5.1f}" + (f"/D{dk:4.1f}" if dk is not None else ""))
        print(f"  s {st:6.1f} in={sa <= st <= sb} hw {hw:4.2f} zr {zr:6.2f} | " + " ".join(row))
