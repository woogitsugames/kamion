"""Reversible tree-only ablation in this worktree's ignored generator inputs."""
import argparse
import json
import shutil
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("mode", choices=("zero", "restore"))
args = parser.parse_args()
here = Path(__file__).resolve().parent
root = here.parents[1].resolve()
world = (root / "Data/raw/derived/bialystok-industrial-c/world").resolve()
if not world.is_relative_to(root):
    raise SystemExit("World inputs must belong to this worktree")
slot = Path("C:/Users/matma/Documents/Claude/kamion/artifacts/locks/unity-slots/gpt-vegetation.slot")
if slot.exists():
    raise SystemExit("Wait for this session's Unity slot to be released")
backup = here / "snapshot-candidate-a/instances"
state_file = here / "ablation-state.json"
state = json.loads(state_file.read_text()) if state_file.exists() else {"state": "candidate-a"}
manifest = root / "Data/Regions/bialystok-industrial-c/generated/world_manifest.json"
if args.mode == "zero":
    if state["state"] == "zero":
        print("Zero-tree ablation already prepared; original backup preserved")
        raise SystemExit(0)
    if not backup.exists():
        backup.mkdir()
        for path in world.glob("instances_*.json"):
            shutil.copyfile(path, backup / path.name)
    source = here / "snapshot-baseline/instances"
    source_manifest = here / "snapshot-baseline/imported-world/world_manifest.json"
    next_state = "zero"
else:
    if not backup.exists():
        raise SystemExit("Missing original candidate instance backup")
    source = backup
    source_manifest = here / "snapshot-candidate-a/world_manifest.json"
    next_state = "candidate-a-restored"
for path in source.glob("instances_*.json"):
    shutil.copyfile(path, world / path.name)
shutil.copyfile(source_manifest, manifest)
state = dict(state=next_state, mode=args.mode,
             note="Temporary consumer-input ablation. Production source, road meshes and landmark assets untouched. Restore candidate inputs before further source generation.")
state_file.write_text(json.dumps(state, indent=2)+"\n", encoding="utf-8")
print(next_state)
