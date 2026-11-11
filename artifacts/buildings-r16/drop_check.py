"""Does the kerb really drop at every driveway (ADR 0124 item 1: 'pomiar wysokości z siatki dla wszystkich zjazdów')?
Pass-1 geometry without and with the side edit (house-street kerbs + drops): kerb-top height above the gutter at every
access point (road-layer `curb_concrete` vertices within 1.2 m of the carriageway edge point q), and the kerb height
of the house streets away from the driveways.
    uv run --project tools/worldgen python artifacts/buildings-r16/drop_check.py"""
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
hk = {}


def edit(net):
    hk.update(PLT.apply_house_kerbs(net, rp["plots"]))
    return PLT.apply_drops(net, rp["drops"])


w1 = pipeline.build(rid, side_edit=edit)
print("plots", len(rp["plots"]), "gates", sum(p["lay"]["gate"] is not None for p in rp["plots"]), "drops", len(rp["drops"]),
      "applied", w1.stats.get("side_edit"), "access stats", rp["access_stats"], "house-kerb chains", len(hk), round(sum(hk.values())), "m")


def kerb(w, q, r=1.2):
    zs, za = [], []
    for p in w.buf.parts:
        if p.layer != "road":
            continue
        d = np.hypot(p.V[:, 0] - q[0], p.V[:, 1] - q[1])
        m = d < r
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
    g = p["lay"]["gate"]
    t = g["t"]
    h0, h1 = kerb(w0, a["q"]), kerb(w1, a["q"])
    side = [kerb(w1, a["q"] + t * s, 0.8) for s in (-8.0, 8.0)]          # the street kerb 8 m either side of the driveway
    rows.append((p["id"][-6:], p["front_style"], a["walk"], a["kind"], bool(a.get("kerbed")), round(a["d_cw"], 1),
                 None if h0 is None else round(h0, 3), None if h1 is None else round(h1, 3),
                 [None if s is None else round(s, 3) for s in side]))
for r in rows:
    print(r)
kerbed = [r for r in rows if r[4]]
ok = [r for r in kerbed if r[7] is not None and r[7] < 0.06]
h = [r[7] for r in kerbed if r[7] is not None]
print(f"{len(rows)} driveways; {len(kerbed)} at a kerbed edge, {len(ok)} of them with the kerb below 6 cm after the drop "
      f"(min {min(h):.3f}, median {np.median(h):.3f}, max {max(h):.3f} m); {len(rows) - len(kerbed)} at an edge without a kerb")
st = [s for r in rows for s in r[8] if s is not None]
print(f"street kerb 8 m beside the driveways: n {len(st)}, median {np.median(st):.3f}, p10 {np.percentile(st, 10):.3f}, p90 {np.percentile(st, 90):.3f} m")
