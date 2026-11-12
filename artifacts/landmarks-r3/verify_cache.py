"""Stream-check all generated runtime files against the manifest under the heavy slot."""
import hashlib
import json
import sys
from pathlib import Path

out = Path(__file__).resolve().parent
root = out.parents[1]
stage = sys.argv[1]
manifest_path = root / "Data/Regions/bialystok-industrial-c/generated/world_manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


records = []
for chunk in manifest["chunks"]:
    for tier, entry in (("High", chunk), ("Low", chunk["low"]), ("instances", chunk["instances"])):
        relative = entry["file"]
        assert relative.startswith("Data/raw/derived/bialystok-industrial-c/world/"), relative
        path = root / relative
        actual = sha(path)
        assert actual == entry["sha256"], f"Stale cache: {relative}"
        if "bytes" in entry:
            assert path.stat().st_size == entry["bytes"], relative
        records.append(dict(tier=tier, file=relative, sha256=actual, bytes=path.stat().st_size))
assert len(manifest["chunks"]) == 64 and len(records) == 192
result = dict(stage=stage, files=records, all_manifest_hashes_match=True,
              manifest_sha256=sha(manifest_path),
              source_sha256={name: sha(root / name) for name in (
                  "tools/worldgen/streetscape/ec_chimneys.py", "tools/worldgen/streetscape/hero_building.py",
                  "tools/worldgen/streetscape/landmarks.py", "Data/Regions/bialystok-industrial-c/ec_chimneys.json",
                  "tests/gis/test_ec_chimneys.py", "tools/worldgen/streetscape/materials.py",
                  "Data/Regions/bialystok-industrial-c/viaduct_underdeck.json",
                  "tests/gis/test_viaduct_underdeck.py", "tools/worldgen/streetscape/hero_bridge.py",
                  "art-source/world/landmarks/ec_chimney_single/ec_chimney_single.glb",
                  "art-source/world/landmarks/ec_chimney_single/ec_chimney_single_meta.json",
                  "art-source/world/landmarks/ec_chimney_multi/ec_chimney_multi.glb",
                  "art-source/world/landmarks/ec_chimney_multi/ec_chimney_multi_meta.json")})
if stage == "after-tests":
    before = json.loads((out / "cache-before-tests.json").read_text(encoding="utf-8"))
    for key in ("files", "manifest_sha256", "source_sha256"):
        assert result[key] == before[key], f"Changed during tests: {key}"
    result["unchanged_since_rendered_checkpoint"] = True
(out / f"cache-{stage}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(f"{stage}: 64 High + 64 Low GLB and 64 instance files verified")
