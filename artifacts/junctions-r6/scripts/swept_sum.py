"""swept_sum.py <swept dir> : per segment min tyre clearance and min prop clearance (ADR 0110 before/after)."""
import json, sys
d = json.load(open(sys.argv[1] + "/summary.json", encoding="utf-8"))
for name, seg in sorted(d["segments"].items()):
    ty = min(v["min_clear_m"] for v in seg["tyres"].values())
    props = [v.get("min_prop_clear_m") for v in seg.get("bodies", seg.get("body", {})).values() if isinstance(v, dict)]
    props = [p for p in props if p is not None]
    print(f"{name:22s} tyre min {ty:+.2f}  prop min {min(props) if props else float('nan'):.2f}")
