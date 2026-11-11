"""Regenerate either saved Argon code or r2; archive exact GIS/mesh provenance."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/worldgen"))
OUT = ROOT / "artifacts/edge-far-r2"
WORLD = ROOT / "Data/raw/derived/bialystok-industrial-c/world"
phase = sys.argv[1]
if phase == "before":
    cached = OUT / "baseline/argon-gis-cache.json"
    if cached.exists():
        shutil.copy2(cached, WORLD / "far_field_gis_cache.json")
    source = OUT / "baseline/far_field_before.py"
    if not source.exists():
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(subprocess.check_output([
            "git", "show", "293c5f69:tools/worldgen/streetscape/far_field.py"], cwd=ROOT))
    spec = importlib.util.spec_from_file_location("far_field_before", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
else:
    from streetscape import far_field as module
qa = module.build_far_field("bialystok-industrial-c")
dest = OUT / phase / "generated"
dest.mkdir(parents=True, exist_ok=True)
for name in ("far_field.glb", "far_field.low.glb", "far_field_apron.json", "far_field_gis_cache.json"):
    shutil.copy2(WORLD / name, dest / name)
(dest / "qa.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")
print(json.dumps(qa, indent=2))
