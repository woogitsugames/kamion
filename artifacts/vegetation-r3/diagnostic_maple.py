"""Consumer-input A/B only: grow the existing maple, no new records or movement."""
import json
import shutil
import sys
from pathlib import Path

import numpy as np

here = Path(__file__).resolve().parent
root = here.parents[1].resolve()
world = (root / "Data/raw/derived/bialystok-industrial-c/world").resolve()
if not world.is_relative_to(root):
    raise SystemExit("Wrong worktree world inputs")
sys.path.insert(0, str(root / "tools/worldgen"))
from streetscape.vegetation import _seed

dest = here / "diagnostic-maple-height"
backup = dest / "input-backup"
backup.mkdir(parents=True, exist_ok=True)
path = world / "instances_3_4.json"
data = json.loads(path.read_text())
matches = [t for t in data["instances"] if t["p"] == "tree_maple" and t.get("v") == 2
           and abs(t["e"]+209.82) < .01 and abs(t["n"]+209.29) < .01 and t["src"].endswith(":self")]
if len(matches) != 1 or matches[0]["h"] != 8.0:
    raise SystemExit("Expected the unmodified unique 8m synthetic maple")
if (backup / path.name).exists():
    raise SystemExit("Diagnostic already has an input backup; do not overwrite it")
shutil.copyfile(path, backup / path.name)
tree = matches[0]
old = dict(tree)
tree["h"] = round(float(np.random.default_rng(_seed("ortho:gugik-2024:g3-b-120:4")).uniform(12.5, 15.)), 1)
path.write_text(json.dumps(data, sort_keys=True, separators=(",", ":"))+"\n", encoding="utf-8")
proof = dict(status="DIAGNOSTIC INPUT ONLY, not producer-generated B2", before=old, after=tree,
             changed_fields=["h"], note="No root, prototype, variant, source id or instance count change. Full source implementation/generation required before acceptance.")
(dest / "input-change.json").write_text(json.dumps(proof, indent=2)+"\n", encoding="utf-8")
print(json.dumps(proof, indent=2))
