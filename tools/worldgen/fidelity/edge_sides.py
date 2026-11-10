"""Per-side carriageway edge offsets (orthophoto edge minus generated edge, + = real road wider) for route edges
or given OSM ways: the evidence behind authored width overrides (ADR 0077).

    uv run --project tools/worldgen tools/worldgen/fidelity/edge_sides.py bialystok-industrial-c [way_id ...]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fidelity import gen as G  # noqa: E402
from fidelity import metrics as Mx  # noqa: E402
from fidelity import ortho as O  # noqa: E402
from fidelity import osm_truth  # noqa: E402
from fidelity.run import chain_span_of_edge, route_edges  # noqa: E402
from roads import pipeline  # noqa: E402


def main():
    region = sys.argv[1]
    ways = set(sys.argv[2:])
    reg = pipeline.load_region(region)
    rdir = pipeline.REGIONS / region
    route, r_edges = route_edges(rdir)
    g = G.build(region)
    ctx = Mx.Ctx(reg, g, osm_truth.extract(reg), O.Ortho(reg), np.array(route["points_en"]))
    eids = [e for e in ctx.net.sections if e.split(":")[0].lstrip("w") in ways] if ways else r_edges
    for eid in eids:
        c = ctx.chain_of_edge.get(eid)
        if c is None:
            continue
        sp = chain_span_of_edge(c, eid)
        s0, s1 = max(sp[0], c.t_a), min(sp[1], c.length - c.t_b)
        if s1 - s0 <= 2:
            continue
        rows = [r for r in Mx.chain_edge_profiles(ctx, c, s0, s1) if not r.get("skip")]
        rev = any(r for e, r in c.edges if e == eid)
        out = {}
        for k in ("L", "R"):
            v = [r[k] for r in rows if r.get(k) is not None]
            vg = [r[k] for r in rows if r.get(k) is not None and r.get(k + "_green") and not r.get(k + "_walk")]
            out[k] = (len(v), round(float(np.median(v)), 2) if v else None,
                      len(vg), round(float(np.median(vg)), 2) if vg else None)
        hw = float(np.median([r["hw"] for r in rows])) if rows else 0.0
        print(f"{eid:42s} width {2 * hw:5.2f} chain-rev {int(rev)} L(n,med,n_green,med_green) {out['L']} R {out['R']}",
              flush=True)


if __name__ == "__main__":
    main()
