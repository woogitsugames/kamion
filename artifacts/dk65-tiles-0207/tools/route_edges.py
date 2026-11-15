"""ADR 0207: route_start.json -> list of route edges with station ranges (s from the tile entry)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
reg = sys.argv[1]
r = json.loads((ROOT / "Data/Regions" / reg / "route_start.json").read_text(encoding="utf-8"))
g = json.loads((ROOT / "Data/Regions" / reg / "roads.graph.json").read_text(encoding="utf-8"))
E = {e["id"]: e for e in g["edges"]}
st = r["step_m"]; rows = []
for i, e in enumerate(r["edge"]):
    if rows and rows[-1][0] == e:
        rows[-1][2] = i * st
    else:
        rows.append([e, i * st, i * st])
for e, a, b in rows:
    ed = E.get(e, {}); at = ed.get("attrs", {})
    print(f"{a:7.0f} {b:7.0f}  {e:45s} w={at.get('width', {}).get('v')} {at.get('name', {}).get('v')} bridge={at.get('bridge', {}).get('v')} maxspeed={at.get('maxspeed', {}).get('v')}")
