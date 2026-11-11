"""Does the kerb really drop at the driveways? Pass-1 geometry without and with apply_drops: kerb-top height above the
gutter at every access point (road-layer `curb_concrete` vertices within 1.2 m of the carriageway edge point q).
    uv run --project tools/worldgen python artifacts/buildings-r15/drop_check.py"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import numpy as np  # noqa: E402
from roads import pipeline  # noqa: E402
from streetscape import plots as PLT, stage as SS  # noqa: E402

rid = "bialystok-industrial-c"
w0 = pipeline.build(rid)
rp = SS.plan_plots(w0, rid)
w1 = pipeline.build(rid, side_edit=lambda net: PLT.apply_drops(net, rp["drops"]))
print("drops", len(rp["drops"]), "applied", w1.stats.get("side_edit"))


def kerb(w, q):
    zs, za = [], []
    for p in w.buf.parts:
        if p.layer != "road":
            continue
        d = np.hypot(p.V[:, 0] - q[0], p.V[:, 1] - q[1])
        m = d < 1.2
        if not m.any():
            continue
        if p.mat == "curb_concrete":
            zs += list(p.V[m, 2])
        elif p.mat.startswith("road_"):
            za += list(p.V[m, 2])
    if not zs or not za:
        return None
    return max(zs) - float(np.median(za))


rows = []
for p in rp["plots"]:
    a = p.get("access")
    if not a:
        continue
    h0, h1 = kerb(w0, a["q"]), kerb(w1, a["q"])
    rows.append((p["id"][-6:], a["chain"] is not None, a["walk"], a["kind"], None if h0 is None else round(h0, 3), None if h1 is None else round(h1, 3)))
for r in rows:
    print(r)
ok = [r for r in rows if r[5] is not None and r[5] < 0.06]
print(f"{len(ok)} of {len(rows)} accesses have a kerb below 6 cm after the drop")
