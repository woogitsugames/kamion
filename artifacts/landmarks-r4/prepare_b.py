"""Prepare conifer-only variant B from the preserved baseline, not rejected A."""
import ast
import json
from pathlib import Path

out = Path(__file__).resolve().parent
root = out.parents[1]
base = out / "baseline-generated"
path = root / "tools/blender/world/landmarks/make_fire_station.py"
original = (base / "make_fire_station.py").read_text(encoding="utf-8")
tree = ast.parse(original)
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_conifer")
function = ast.get_source_segment(original, node)
old = '''            rr = max(radius*.025,radius*fill*shape*(.86+.28*h01(key,j,i,"inner")))
            level = f+.014*(h01(key,j,i,"z")-.5)*(j<len(profile)-1)'''
new = '''            if D["spruce"].get("irregular_core_WORKING_VALUE", False):
                r0, r1 = D["spruce"]["core_radius_factor_WORKING_VALUE"]
                factor = r0+(r1-r0)*h01(key,j,i,"inner")
                span = min(f-profile[j-1][0],profile[j+1][0]-f) if 0 < j < len(profile)-1 else 0.0
                level = f+span*D["spruce"]["core_level_stagger_WORKING_VALUE"]*(2*h01(key,j,i,"z")-1)
            else:
                factor = .86+.28*h01(key,j,i,"inner")
                level = f+.014*(h01(key,j,i,"z")-.5)*(j<len(profile)-1)
            rr = max(radius*.025,radius*fill*shape*factor)'''
assert function.count(old) == 1
function = function.replace(old, new)
old = '''        rings.append(ring); normals.append(nr)
    for j in range(len(rings)-1):'''
new = '''        rings.append(ring); normals.append(nr)
    if D["spruce"].get("irregular_core_WORKING_VALUE", False):
        # Smooth normals follow the staggered surface, not an ideal cone.
        for j in range(len(rings)):
            for i in range(sides):
                around = rings[j][(i+1)%sides]-rings[j][(i-1)%sides]
                upward = rings[min(j+1,len(rings)-1)][i]-rings[max(j-1,0)][i]
                normal = np.cross(around,upward)
                radial = rings[j][i]-c; radial[2] = 0
                if np.dot(normal,radial) < 0: normal = -normal
                normals[j][i] = normal/np.linalg.norm(normal)
    for j in range(len(rings)-1):'''
assert function.count(old) == 1
function = function.replace(old, new).replace("a tiered opaque inner crown", "an irregular opaque inner crown")
lines = original.splitlines(keepends=True)
updated = "".join(lines[:node.lineno-1]) + function + "\n" + "".join(lines[node.end_lineno:])
path.write_text(updated, encoding="utf-8", newline="\n")
d = json.loads((base / "dims.json").read_text(encoding="utf-8"))
s = d["spruce"]
s.update(inner_core_fill_r_WORKING_VALUE=.90,
         core_profile_WORKING_VALUE=[[.045,.5],[.13,.95],[.27,.85],[.40,.72],[.53,.56],[.67,.43],[.82,.2],[.975,.025]],
         irregular_core_WORKING_VALUE=True, core_radius_factor_WORKING_VALUE=[.72,1.20],
         core_level_stagger_WORKING_VALUE=.40)
s["core_shape_note"] = "ADR 0116 r4 B: eight tapered rings with azimuth-dependent radius and staggered levels instead of full annular skirts; geometry-derived smooth normals. Original 12 Low / 54 High bough cards and UV are unchanged. WORKING_VALUE, pending rendered comparison."
s["inner_core_note"] = "ADR 0116 r4 B: opaque canopy without synchronised radial shelves; original CC0 needle cards, species remains an unverified fir proxy. Positions, heights, authored radii, atlas and material slots unchanged."
s["low_core_budget_note"] = "ADR 0116 r4 B: original five smooth-normal sides x seven segments=70 core tris,12 cards=24,trunk4;98 per tree. Whole Low hero limit2828 remains unchanged. No added alpha cards or area."
(root / "art-source/world/landmarks/fire_station_jrg2/dims.json").write_text(json.dumps(d,ensure_ascii=False,indent=1)+"\n", encoding="utf-8")
print("Prepared B: original bough geometry, irregular eight-ring core; no Blender/world execution")
