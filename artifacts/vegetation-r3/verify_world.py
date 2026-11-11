"""Audit actual placed trees and isolate unrelated output drift after world generation."""
import hashlib
import json
from collections import Counter
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parents[1]
world = root / "Data/raw/derived/bialystok-industrial-c/world"
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
qa = read(root / "Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json")
trees_qa = qa["vegetation"]["orthophoto_trees"]
mega = qa["furniture"]["megascans"]
before, after, mapped = Counter(), Counter(), []
for old in (here / "snapshot-baseline/instances").glob("instances_*.json"):
    before.update(json.dumps(x, sort_keys=True) for x in read(old)["instances"])
    for x in read(world / old.name)["instances"]:
        if x.get("src", "").startswith("ortho:gugik-2024:"):
            mapped.append(x)
        else:
            after[json.dumps(x, sort_keys=True)] += 1
snapshot = read(here / "snapshot-baseline/sha256.json")["files"]
changed_glbs = [name for name, digest in snapshot.items() if name.endswith(".glb")
                and hashlib.sha256((root / name).read_bytes()).hexdigest() != digest]
other_added, other_removed = after-before, before-after
result = dict(orthophoto_qa=trees_qa, mapped_instances=mapped,
    available_megascans=len(mega.get("available", [])), fallback=mega.get("fallback", False),
    existing_instances_added=sum(other_added.values()), existing_instances_removed=sum(other_removed.values()),
    existing_delta_examples={"added": list(other_added)[:8], "removed": list(other_removed)[:8]},
    raw_glbs_changed=changed_glbs,
    note="Full GLB hashes are generator inputs, not Unity asset hashes. Inspect any drift before claiming unchanged physics.")
(here / "world-proof.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
print(json.dumps(result, indent=2))
if result["fallback"] or result["available_megascans"] < 15:
    raise SystemExit("Megascans inputs incomplete; stop before importing a fallback world")
if len(mapped) != trees_qa["placed"]:
    raise SystemExit("Placed count differs between QA and instance files")
if not mapped:
    raise SystemExit("All source points rejected; inspect blocked/orthophoto before visual QA")
