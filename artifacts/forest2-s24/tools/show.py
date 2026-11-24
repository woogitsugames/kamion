"""forest2-s24: short table of analyze.py results.  python show.py base r1 [region]"""
import json
import sys
from pathlib import Path

A = Path(__file__).resolve().parents[1]
names = [a for a in sys.argv[1:] if not a.startswith("dk") and not a.startswith("dw")]
regs = [a for a in sys.argv[1:] if a.startswith(("dk", "dw"))] or ["dk65-05"]
for rid in regs:
    for n in names:
        d = json.loads((A / f"{n}_{rid}.json").read_text(encoding="utf-8"))
        print(rid, n, d["seconds"], "trees", d["trees"], d["hlod"])
        print("  chm", {k: v for k, v in d["forest_chm"].items() if k != "source"})
        for fk, c in d["by_category"].items():
            print("  ", fk, c["canopy_trees"], c["canopy_share"], c["canopy_h_m"])
            print("      edge", c["edge_share"])
            print("      under", c["under_share"])
            print("      scale max", {k: v["max"] for k, v in c["canopy_scale"].items()})
