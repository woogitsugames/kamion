"""ADR 0303: every material named in the built world chunks (Data/raw/derived/<tile>/world/*.glb) must be defined in the
tile's generated/world_manifest.json of THIS checkout, or RegionImporter leaves the slot empty (warning
"material 'x' not in manifest") and the mesh renders magenta.

How it happens: Data/raw/derived is a junction shared by every worktree (D43), Data/Regions/<tile>/generated is per
branch. A tile rebuilt by another agent (newer generator: e.g. `noise_post_light`, ADR 0293) lands in the shared GLBs at
once, its manifest only after that branch is merged. Seen s24: magenta posts of the noise barriers in
bialystok-knyszynska (walls-gps-s24) = GLB from regen-wave-s24 + manifest of main.

    uv run --project tools/worldgen python tools/worldgen/qa/manifest_materials.py --tiles a,b [--derived <dir>]
    exit 1 = a GLB material missing in the manifest (rebuild the tile here or take the manifest of the branch that built it)
"""
from __future__ import annotations

import argparse
import glob
import json
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def glb_materials(path: str) -> set[str]:
    b = Path(path).read_bytes()
    jl = struct.unpack("<I", b[12:16])[0]
    return {m.get("name") for m in json.loads(b[20:20 + jl]).get("materials", []) if m.get("name")}


def check(tile: str, derived: Path, regions: Path) -> dict:
    mf = regions / tile / "generated" / "world_manifest.json"
    files = sorted(glob.glob(str(derived / tile / "world" / "*.glb")))
    if not mf.exists() or not files:
        return {"tile": tile, "built": False, "missing": []}
    defined = set(json.loads(mf.read_text(encoding="utf-8"))["materials"])
    used: set[str] = set()
    for f in files:
        used |= glb_materials(f)
    return {"tile": tile, "built": True, "glb_materials": len(used), "missing": sorted(used - defined)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tiles", required=True)
    ap.add_argument("--derived", type=Path, default=REPO / "Data/raw/derived")
    ap.add_argument("--regions", type=Path, default=REPO / "Data/Regions")
    a = ap.parse_args(argv)
    bad = 0
    for t in [x for x in a.tiles.split(",") if x]:
        r = check(t, a.derived, a.regions)
        if not r["built"]:
            print(f"{t:28s} not built / no manifest")
            continue
        bad += bool(r["missing"])
        print(f"{t:28s} glb materials {r['glb_materials']:3d}  missing in manifest {r['missing']}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
