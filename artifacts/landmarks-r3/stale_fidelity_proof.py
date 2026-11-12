"""Read-only provenance check of the two failures outside the landmarks stream."""
import hashlib
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
region = root / "Data/Regions/bialystok-industrial-c"
report = json.loads((region / "generated/fidelity_qa.json").read_text(encoding="utf-8"))
base = "14ccbaf1"
rows = []
for name, expected in report["inputs_sha256"].items():
    path = region / name if "/" not in name else root / name
    raw = path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual == expected:
        continue
    relative = path.relative_to(root).as_posix()
    original = subprocess.check_output(["git", "show", f"{base}:{relative}"], cwd=root)
    canonical_equal = raw.replace(b"\r\n", b"\n") == original.replace(b"\r\n", b"\n")
    diff = subprocess.check_output(["git", "diff", base, "--", relative], cwd=root)
    assert canonical_equal and not diff, relative
    rows.append(dict(path=relative, report_sha256=expected, current_sha256=actual,
                     unchanged_since_round_base=True, canonical_bytes_equal=True))
assert {r["path"] for r in rows} == {
    "Data/Regions/bialystok-industrial-c/overrides.yaml", "tools/worldgen/roads/meshing.py"}
result = dict(base=base, stale_inputs=rows, action="No road source or fidelity report modified")
(Path(__file__).parent / "stale-fidelity-proof.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
