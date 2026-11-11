"""Read-only audit of evidence/source drift before restoring generator side effects."""
import hashlib
import json
import subprocess
from pathlib import Path

here = Path(__file__).resolve().parent
root = here.parents[1]
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
old = read(here / "snapshot-candidate-b-pretests/sha256.json")["files"]
changed, missing = [], []
for name, digest in old.items():
    path = root / name
    if not path.exists():
        missing.append(name)
    elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        changed.append(name)
proof = read(here / "evidence-summary.json")
source_drift = [name for name, digest in proof["files"].items()
                if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest]
result = dict(changed_canonical_outputs=changed, missing=missing,
              source_drift_since_render=source_drift,
              note="Raw and generated outputs must be interpreted separately from the source diff.")
(here / "posttests-audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
(here / "posttests-worktree.txt").write_text(subprocess.check_output(
    ["git", "status", "--porcelain=v1"], cwd=root, text=True), encoding="utf-8")
print(json.dumps(result, indent=2))
if source_drift:
    raise SystemExit("Rendered source has drifted; stop before publishing REPORT")
