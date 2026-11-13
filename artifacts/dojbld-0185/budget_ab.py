"""A/B of the generator's static frame estimate (streetscape_qa.json mesh_budget): git HEAD~ref vs working tree."""
import json, subprocess, sys
ref = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
p = "Data/Regions/bialystok-dojlidy/generated/streetscape_qa.json"
new = json.load(open(p, encoding="utf8"))["mesh_budget"]
old = json.loads(subprocess.run(["git", "show", f"{ref}:{p}"], capture_output=True, text=True, encoding="utf8").stdout)["mesh_budget"]
o = {c["camera"]: c for c in old["frame_estimate"]}
print(f"{'camera':28} mats_low  tris_low            bld_low          mats_high tris_high")
tot = [0, 0, 0, 0]
for c in new["frame_estimate"]:
    b = o.get(c["camera"])
    if not b:
        continue
    d = lambda k: (b[k], c[k])
    bl = (b["by_category_low"].get("buildings", 0), c["by_category_low"].get("buildings", 0))
    if any(x != y for x, y in (d("materials_low"), d("tris_low"), d("materials_high"), d("tris_high"))):
        print(f"{c['camera']:28} {b['materials_low']}->{c['materials_low']}  {b['tris_low']}->{c['tris_low']} ({(c['tris_low']/b['tris_low']-1)*100:+.2f}%)  "
              f"{bl[0]}->{bl[1]}  {b['materials_high']}->{c['materials_high']} {b['tris_high']}->{c['tris_high']} ({(c['tris_high']/b['tris_high']-1)*100:+.2f}%)")
    for i, k in enumerate(("materials_low", "tris_low", "materials_high", "tris_high")):
        tot[i] = max(tot[i], c[k] - b[k])
print("cameras", len(new["frame_estimate"]), "max delta mats_low/tris_low/mats_high/tris_high", tot)
print("max tris_low", max(c["tris_low"] for c in new["frame_estimate"]), "max tris_high", max(c["tris_high"] for c in new["frame_estimate"]))
