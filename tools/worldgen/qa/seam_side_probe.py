"""ADR 0304 probe: side profile (kind / kerb height / width / mat) of the chains crossing a seam, per station near the
seam, in both tiles (generator networks as qa.seams builds them).

  uv run --project tools/worldgen python -m tools.worldgen.qa.seam_side_probe <tile_a> <tile_b> <osm_way> [--m 40]
"""
from __future__ import annotations

import argparse
import sys

import numpy as np

from tools.worldgen.qa import seams as Q


def probe(a_id, b_id, way, m=40.0, nets=None, trims=False):
    ta, tb = Q.load_tile(a_id), Q.load_tile(b_id)
    se = Q.shared_edge(ta.bbox, tb.bbox)
    nets = nets or Q.build_nets([ta, tb], [(ta, tb, se)], trims=trims)
    out = []
    for t in (ta, tb):
        net = nets[t.id]
        o = np.array(t.origin)
        for c in net.chains:
            ways = {net.sec_list[int(i)].edge_id.split(":")[0].lstrip("w") for i in np.unique(c.sec_idx)}
            if str(way) not in ways:
                continue
            for end in (0, -1):
                if not Q._on_seam(c.line.p[end] + o, se):
                    continue
                s_end = float(c.line.s[end])
                sel = np.where(np.abs(c.line.s - s_end) <= m)[0]
                for side in ("L", "R"):
                    sd = (c.side or {}).get(side)
                    if not sd:
                        continue
                    for i in sel[:: max(1, len(sel) // 12)]:
                        out.append((t.id, c.id, end, side, round(abs(float(c.line.s[i]) - s_end), 1),
                                    int(sd["kind"][i]), round(float(sd["raw"]["h"][i]), 3),
                                    round(float(sd["raw"]["w"][i]), 2), int(sd["mat"][i]), bool(sd["walk"][i])))
                print(t.id, c.id, "end", end, "len", round(c.length, 1), "t_a/t_b", getattr(c, "t_a", None),
                      getattr(c, "t_b", None), "meta", {k: c.meta.get(k) for k in ("tight_m", "flush_m")})
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("a"); ap.add_argument("b"); ap.add_argument("way")
    ap.add_argument("--m", type=float, default=40.0)
    ap.add_argument("--trims", action="store_true", help="second assign_sides pass (what the generator meshes)")
    a = ap.parse_args(argv)
    for r in probe(a.a, a.b, a.way.lstrip("w"), a.m, trims=a.trims):
        print(*r)


if __name__ == "__main__":
    sys.exit(main())
