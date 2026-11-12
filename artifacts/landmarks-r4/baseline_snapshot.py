"""Run after baseline capture, before any model edit. Preserve exact rendered inputs."""
import hashlib
import json
import shutil
from pathlib import Path

out = Path(__file__).resolve().parent
root = out.parents[1]
base = out / "baseline-generated"
base.mkdir(exist_ok=True)
def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
result = json.loads((out / "baseline-result.json").read_text(encoding="utf-8-sig"))
assert result["complete"]
inventories = {c: sorted(p.name for p in (out / "before" / c).glob("*.png")) for c in
               ("Low-overcast", "Low-clear", "High-overcast", "High-clear")}
assert len({tuple(v) for v in inventories.values()}) == 1
assert len(inventories["Low-overcast"]) >= 48
result["camera_inventories"] = inventories
result["count_per_condition"] = len(inventories["Low-overcast"])
manifest = json.loads((base / "world_manifest.json").read_text(encoding="utf-8-sig"))
verified = []
for chunk in manifest["chunks"]:
    for entry in (chunk, chunk["low"], chunk["instances"]):
        assert sha(root / entry["file"]) == entry["sha256"], entry["file"]
        verified.append(entry["file"])
assert len(verified) == 192
sources = {
    "fire_station_jrg2.glb": "art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2.glb",
    "fire_station_jrg2_meta.json": "art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2_meta.json",
    "fire_station_jrg2.spec.json": "Data/Regions/bialystok-industrial-c/generated/landmarks/fire_station_jrg2.spec.json",
    "dims.json": "art-source/world/landmarks/fire_station_jrg2/dims.json",
    "make_fire_station.py": "tools/blender/world/landmarks/make_fire_station.py",
}
for name, relative in sources.items():
    shutil.copyfile(root / relative, base / name)
meta = json.loads((base / "fire_station_jrg2_meta.json").read_text(encoding="utf-8-sig"))
assert meta["glb_sha256"] == sha(base / "fire_station_jrg2.glb")
result["asset_tris"] = meta["tris"]
result["verified_runtime_files"] = len(verified)
result["snapshot_sha256"] = {name: sha(base / name) for name in sources}
(out / "baseline-result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(f"Baseline snapshot: {len(verified)} runtime hashes, {result['count_per_condition']} cameras per condition, tris {meta['tris']}")
