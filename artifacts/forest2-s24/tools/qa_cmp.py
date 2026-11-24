"""forest2-s24: one-line comparison of streetscape_qa.json (r5 of the predecessor vs this round).  qa_cmp.py <round> <region>.."""
import json
import sys
from pathlib import Path

A = Path(__file__).resolve().parents[1]
R5 = Path(r"C:\Users\matma\Documents\Claude\kamion\artifacts\forest-height-s24\r5-after-qa")
for rid in sys.argv[2:]:
    for n, p in (("r5", R5 / f"{rid}.streetscape_qa.json"), (sys.argv[1], A / sys.argv[1] / rid / "streetscape_qa.json")):
        q = json.loads(p.read_text(encoding="utf-8"))
        v = q["vegetation"]
        f = q["mesh_budget"]["frame_estimate"]
        print(rid, n, "plants", sum(v["trees"].values()), v["forest_hlod"], "capped", v["forest_chm"].get("scale_capped"),
              v["forest_chm"]["canopy_h_m"], "worst High", max(x["tris_high"] for x in f), "Low", max(x["tris_low"] for x in f))
        print("   ", json.dumps(v["trees"], sort_keys=True))
