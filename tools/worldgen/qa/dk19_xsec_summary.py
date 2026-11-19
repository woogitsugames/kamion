"""Per-street summary of ortho_xsec.py station files for the DK19 route tiles (ADR 0278 tiles 5-7, method of ADR 0272).

ortho_xsec.summarise keeps only 6.0-7.6 m carriageways (rural single carriageway); the city route has one-way
carriageways of 7-14 m, so this summary groups the stations by street name + lane count of the graph edge and reports
the median / quartiles of the asphalt width for stations inside PLAUSIBLE (m) whose asphalt run does not touch the
+-14 m window (a run to the window edge = junction mouth, bus bay or shadow: rejected, counted).

  uv run --project tools/worldgen python tools/worldgen/qa/dk19_xsec_summary.py <region> <stations.json> [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PLAUSIBLE = (5.0, 16.0)
WINDOW = 13.9


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("region")
    ap.add_argument("stations", type=Path)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()
    g = json.loads((REPO / "Data" / "Regions" / a.region / "roads.graph.json").read_text(encoding="utf-8"))
    at = {e["id"]: {k: d.get("v") for k, d in e["attrs"].items()} for e in g["edges"]}
    rows = json.loads(a.stations.read_text(encoding="utf-8"))
    grp = defaultdict(list)
    for r in rows:
        x = at[r["edge"]]
        grp[(x.get("name") or f"way {r['way']}", x.get("lanes"), x.get("width"))].append(r)
    out = []
    for (name, lanes, bdot), rs in sorted(grp.items(), key=lambda kv: (str(kv[0][0]), kv[0][1] or 0)):
        ok = [r for r in rs if PLAUSIBLE[0] <= r["asphalt_w"] <= PLAUSIBLE[1] and r["asphalt_L"] < WINDOW and r["asphalt_R"] > -WINDOW]
        w = sorted(r["asphalt_w"] for r in ok)
        d = {"street": name, "lanes_osm": lanes, "width_graph_m": bdot, "stations": len(rs), "used": len(ok),
             "ways": sorted({r["way"] for r in rs})}
        if w:
            d["asphalt_median_m"] = round(statistics.median(w), 2)
            d["asphalt_min_max_m"] = [w[0], w[-1]]
            if lanes:
                d["per_lane_m"] = round(d["asphalt_median_m"] / lanes, 2)
        out.append(d)
        print(json.dumps(d, ensure_ascii=False))
    if a.json:
        a.json.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
