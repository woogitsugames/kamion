"""Print the island / lane-into-island / edge numbers of fidelity_qa.json (ADR 0077 working aid).

    uv run --project tools/worldgen tools/worldgen/fidelity/summary.py [region]
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def main():
    region = sys.argv[1] if len(sys.argv) > 1 else "bialystok-industrial-c"
    d = json.loads((REPO / "Data/Regions" / region / "generated/fidelity_qa.json").read_text(encoding="utf-8"))
    r = d["summary"]["route"]
    e = r["edge_vs_ortho_m"]
    print({k: r[k] for k in ("gen_islands_absent_on_ortho", "lane_into_island", "lane_into_island_generator_bug",
                             "ortho_islands_missing_in_gen")}, "edge p50", e["p50"], "p95", e["p95"], "n", e["n"],
          "signed p50", e["signed_p50"])
    lii = d["lane_into_island"]
    print("tile lane->island", len(lii), "generator bug", sum(x["verdict"] == "generator_island_on_real_road" for x in lii))
    for x in lii:
        if x["on_route"]:
            print("  LII", x["junction"], x["chain"], x["turn"], x["dist_m"], x["xy"], x["verdict"], x["ortho_road_frac"])
    for tag, key, cond in (("ABS", "gen_islands", lambda g: g["verdict"] == "absent_on_ortho"),
                           ("MISS", "ortho_islands_missing_in_gen", lambda g: True)):
        seen = set()
        for s in d["sites"]:
            for g in s[key]:
                k = tuple(round(v) for v in g["xy"])
                if cond(g) and g["route_dist_m"] <= 20 and k not in seen:
                    seen.add(k)
                    print(" ", tag, s["id"], {a: ([round(v, 1) for v in b] if isinstance(b, list) else b)
                                              for a, b in g.items()})


if __name__ == "__main__":
    main()
