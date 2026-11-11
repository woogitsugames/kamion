"""Record actual source/raw/fixture provenance; never changes generated products."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/worldgen"))
from streetscape import fab_details as FD

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    manifest = ROOT / "Data/Regions/bialystok-industrial-c/generated/world_manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    raw = []
    for c in data["chunks"]:
        for r in (c, c["low"], c["instances"]):
            p = ROOT / r["file"]
            got = sha(p)
            raw.append(dict(file=r["file"], sha256=got, expected=r["sha256"], valid=got == r["sha256"]))
    assert len(raw) == 192 and all(x["valid"] for x in raw), "Raw products do not match manifest"
    ready = FD.load_ready()
    fixtures = {}
    for folder in ("game/Assets/_Generated/Truck", "game/Assets/_Generated/Trailer"):
        for p in sorted((ROOT / folder).rglob("*")):
            if p.is_file() and p.suffix in (".prefab", ".mat", ".fbx", ".FBX"):
                fixtures[p.relative_to(ROOT).as_posix()] = sha(p)
    sources = {}
    old = json.loads((ROOT / "artifacts/car-paint-r1/bootstrap-proof.json").read_text())
    for name in old["source_sha256"]:
        sources[name] = sha(ROOT / name)
    result = dict(manifest_sha256=sha(manifest), raw_count=len(raw), mismatches=0,
                  fab_ready=len(ready), fab_fallback=not bool(ready), raw=raw,
                  fixture_sha256=fixtures, source_sha256=sources)
    assert result["fab_ready"] == 15 and not result["fab_fallback"]
    out = ROOT / f"artifacts/car-paint-r1/{tag}-source-proof.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"raw": 192, "mismatches": 0, "fab": len(ready), "fallback": False, "fixtures": len(fixtures)}))

if __name__ == "__main__":
    main()
