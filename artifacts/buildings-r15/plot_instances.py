"""ADR 0107: plot instances near the control cameras (distinct prototypes = instanced draws x submeshes, triangles).
    uv run --project tools/worldgen python artifacts/buildings-r15/plot_instances.py [radius m]"""
import glob, json, sys
from collections import Counter
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
R = float(sys.argv[1]) if len(sys.argv) > 1 else 120.0
SNAP = REPO / "artifacts/buildings-r15/_snap" / (sys.argv[2] if len(sys.argv) > 2 else "r1")
inst = []
for f in sorted(glob.glob(str(SNAP / "world/instances_*.json"))):
    inst += [i for i in json.load(open(f, encoding="utf-8"))["instances"] if str(i.get("src", "")).startswith("plot:")]
meta = json.load(open(SNAP / "props/props_meta.json", encoding="utf-8"))["prototypes"]
print("plot instances", len(inst), Counter(i["p"].split("_")[1] if i["p"].startswith("plot_") else i["p"] for i in inst).most_common())
cams = json.load(open(REPO / "Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json", encoding="utf-8"))["cameras"]
cams += json.load(open(Path(__file__).parent / "cams_r13.json", encoding="utf-8"))["cameras"]
for c in cams:
    x, y = c["pos"][:2]
    near = [i for i in inst if (i["e"] - x) ** 2 + (i["n"] - y) ** 2 < R * R]
    if not near:
        continue
    protos = Counter(i["p"] for i in near if i["p"].startswith("plot_"))
    sub = sum(len(meta[p]["materials"]) for p in protos)
    tris = sum(meta[p]["tris_lod0" if (i["e"] - x) ** 2 + (i["n"] - y) ** 2 < 30 * 30 else "tris_lod1"]
               for i in near for p in [i["p"]] if p.startswith("plot_"))
    print(f"{c['id']}: {len(near)} instances within {R:.0f} m, {len(protos)} plot prototypes, {sub} submesh draws (one LOD), ~{tris} tris (LOD0 < 30 m)")
