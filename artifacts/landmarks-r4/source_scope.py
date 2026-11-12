"""Prove the trial changes one geometry function and conifer-only data."""
import ast
import json
import subprocess
from pathlib import Path

out = Path(__file__).resolve().parent
root = out.parents[1]
base = out / "baseline-generated"
builder = root / "tools/blender/world/landmarks/make_fire_station.py"
def unrelated(source):
    tree = ast.parse(source)
    tree.body = [n for n in tree.body if not (isinstance(n, ast.FunctionDef) and n.name == "build_conifer")]
    return ast.dump(tree, include_attributes=False)
assert unrelated((base / "make_fire_station.py").read_text(encoding="utf-8")) == unrelated(builder.read_text(encoding="utf-8"))
old = json.loads((base / "dims.json").read_text(encoding="utf-8"))
new = json.loads((root / "art-source/world/landmarks/fire_station_jrg2/dims.json").read_text(encoding="utf-8"))
a, b = old.pop("spruce"), new.pop("spruce")
assert old == new
allowed = {"inner_core_fill_r_WORKING_VALUE", "core_profile_WORKING_VALUE", "low_bough_counts",
           "high_bough_counts_WORKING_VALUE", "lateral_bough_cards_WORKING_VALUE", "bough_width_r_WORKING_VALUE",
           "core_shape_note", "low_core_budget_note", "inner_core_note"}
changed = {k for k in a.keys() | b.keys() if a.get(k) != b.get(k)}
assert changed <= allowed
assert a["items"] == b["items"]
protected = ["art-source/world/materials/_src/sets_fire_station.py",
             "art-source/world/textures/fire_station_alpha.png",
             "art-source/world/landmarks/fire_station_jrg2/atlas_layout.json",
             "tools/worldgen/streetscape/materials.py", "tools/worldgen/streetscape/hero_bridge.py",
             "tools/worldgen/streetscape/ec_chimneys.py", "tools/worldgen/streetscape/hero_building.py",
             "tools/worldgen/streetscape/landmarks.py", "Data/Regions/bialystok-industrial-c/viaduct_underdeck.json",
             "Data/Regions/bialystok-industrial-c/ec_chimneys.json", "Data/Regions/bialystok-industrial-c/overrides.yaml"]
assert not subprocess.check_output(["git", "diff", "e0fa8a6d", "--", *protected], cwd=root)
result = dict(complete=True, only_geometry_function_changed="build_conifer", non_conifer_dims_identical=True,
              conifer_positions_heights_radii_identical=True, changed_conifer_keys=sorted(changed),
              protected_paths_unchanged_since_round_base=protected)
(out / "source-scope.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
