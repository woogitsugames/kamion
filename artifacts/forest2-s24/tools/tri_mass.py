"""forest2-s24: clean ablation of the tree triangle mass (dry run, no roads): sum of the LOD0 / LOD1 triangles of the
prototypes of all forest plants of a tile, round 1 (KAMION_FOREST_CHM_R2=0) vs round 2, same code.
    uv run --project tools/worldgen python artifacts/forest2-s24/tools/tri_mass.py dk65-05 ..."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze as A  # noqa: E402

out = {}
for rid in sys.argv[1:]:
    row = {}
    for name, flag in (("round1", "0"), ("round2", "1")):
        os.environ["KAMION_FOREST_CHM_R2"] = flag
        res, trees, _ = A.run(rid)
        l0 = sum(A.META[f"{t['p']}_{t['v']}"]["tris_lod0"] for t in trees)
        l1 = sum(A.META[f"{t['p']}_{t['v']}"]["tris_lod1"] for t in trees)
        row[name] = {"plants": len(trees), "tris_lod0_all": l0, "tris_lod1_all": l1, "hlod_tris": res["hlod"]["triangles"]}
    a, b = row["round1"], row["round2"]
    row["delta_pct"] = {k: round((b[k] / a[k] - 1) * 100, 2) for k in a}
    out[rid] = row
    print(rid, json.dumps(row))
(A.REPO / "artifacts" / "forest2-s24" / "tri_mass.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
