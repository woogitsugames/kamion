"""Verify the trial only replaces the separate hero GLB, not the city cache."""
import hashlib
import json
from pathlib import Path

out = Path(__file__).resolve().parent
root = out.parents[1]
generated = root / "Data/Regions/bialystok-industrial-c/generated"
base = out / "baseline-generated"
def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
before = json.loads((base / "world_manifest.json").read_text(encoding="utf-8-sig"))
after = json.loads((generated / "world_manifest.json").read_text(encoding="utf-8-sig"))
assert before == after, "World manifest changed outside the separate hero asset"
assert sha(base / "roads_qa.json") == sha(generated / "roads_qa.json")
records = []
for chunk in after["chunks"]:
    for tier, entry in (("High", chunk), ("Low", chunk["low"]), ("instances", chunk["instances"])):
        actual = sha(root / entry["file"])
        assert actual == entry["sha256"], entry["file"]
        records.append(dict(tier=tier, file=entry["file"], sha256=actual))
assert len(records) == 192
result = dict(complete=True, all_manifest_fields_identical=True, all_material_definitions_identical=True,
              roads_qa_byte_identical=True, high_chunks_identical=64, low_chunks_identical=64,
              instance_files_identical=64, current_manifest_sha256=sha(generated / "world_manifest.json"),
              runtime_files=records)
(out / "world-scope.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print("World scope PASS: 128 chunk meshes,64 instance files, all manifest fields and roads_qa unchanged")
