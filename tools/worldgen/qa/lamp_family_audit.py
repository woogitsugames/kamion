"""ADR 0216b: street-lamp families per street of a region, from the committed region data only (roads.graph.json,
overrides.yaml, osm_context.json - no Data/raw, no heightfield). Uses the generator's own rule
(streetscape.furniture.chain_lamp_proto) on the network with junction trims; pole counts are an ESTIMATE (spacing
along the trimmed chain, one side; no dedup against nearby poles, medians, bridges) - the regenerated
generated/streetscape_qa.json is the measurement.

    uv run --project tools/worldgen python tools/worldgen/qa/lamp_family_audit.py --region bialystok-dojlidy [--json out]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from roads import junctions as J, pipeline, standards as S  # noqa: E402
from streetscape import furniture as F  # noqa: E402

OLD = ("lamp_old_concrete_", "lamp_old_steel_")


def audit(rid: str, overrides=None):
    """{"by_street": [...], "totals_est": {proto: poles}} with the region's lamp policy (or `overrides` if given)."""
    net, graph, ov, _ = pipeline.build_network(rid)
    ov = ov if overrides is None else overrides
    region = pipeline.load_region(rid)
    origin = (region["origin"]["x"], region["origin"]["y"])
    ctx = json.loads((pipeline.REGIONS / rid / "generated" / "osm_context.json").read_text(encoding="utf-8"))
    pts, _ = pipeline.ctx_local(ctx, origin)
    J.build_junctions(net, pts)                   # trims + absorbed chains, as in the build
    led_all, led_ways = F.lamp_led_scope(ov)
    names = {e["id"]: e["attrs"].get("name", {}).get("v") or "" for e in graph["edges"]}
    rows = defaultdict(lambda: {"chains": 0, "est_poles": 0, "osm_ways": set(), "highway": set()})
    for c in net.chains:
        proto, sec = F.chain_lamp_proto(c, net, led_all, led_ways)
        if proto is None:
            continue
        spec = S.LAMP[sec.cls]
        s0, s1 = c.t_a + 4, c.length - c.t_b - 4
        if s1 - s0 < spec["spacing"] * 0.6:
            continue
        r = rows[(proto, names.get(sec.edge_id, ""))]
        r["chains"] += 1
        r["est_poles"] += len(np.arange(s0 + (F._h(c.id) % 7), s1, spec["spacing"]))
        r["osm_ways"].add(int(F._edge_way(sec.edge_id)))
        r["highway"].add(sec.highway)
    out, tot = [], defaultdict(int)
    for (proto, name), r in sorted(rows.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        tot[proto] += r["est_poles"]
        out.append({"proto": proto, "street": name, "chains": r["chains"], "est_poles": r["est_poles"],
                    "highway": sorted(r["highway"]), "osm_ways": sorted(r["osm_ways"])})
    return {"region": rid, "led_all": led_all, "led_target_ways": len(led_ways), "by_street": out,
            "totals_est": dict(sorted(tot.items()))}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--region", required=True)
    ap.add_argument("--json")
    a = ap.parse_args()
    res = audit(a.region)
    print(json.dumps({k: v for k, v in res.items() if k != "by_street"}, indent=1))
    for r in res["by_street"]:
        if r["proto"].startswith(OLD):
            print(f"{r['proto']:28s} {r['est_poles']:4d}  {','.join(r['highway']):24s} {r['street'] or '(unnamed)'}")
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
