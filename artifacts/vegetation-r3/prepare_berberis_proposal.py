"""Small offline geometry study, NOT production code or a Unity result."""
import difflib
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import box

here = Path(__file__).resolve().parent
root = here.parents[1]
sys.path.insert(0, str(root/'tools/worldgen'))
from streetscape import plantings as baseline

source_path = root/'tools/worldgen/streetscape/plantings.py'
original = source_path.read_text(encoding='utf-8')
source = original
edits = [
    ('local_top=True),', 'local_top=True, leaf_core=True),'),
    ('    core_m, shell_m, sprig_m = hedge_mats(plant)\n',
     '    core_m, shell_m, sprig_m = hedge_mats(plant)\n'
     '    leaf_core = S.get("leaf_core", False)\n'
     '    core_draw_m = shell_m if leaf_core else core_m\n'),
    ('    nt += strip(core, core_m, np.column_stack([np.tile(per[cs], len(core)),\n'
     '                                               np.concatenate([np.full(nc, f * h) for _, f, _ in prof])]))',
     '    core_uv = np.column_stack([np.tile(per[cs], len(core)),\n'
     '                               np.concatenate([np.full(nc, f * h) for _, f, _ in prof])])\n'
     '    # Proposal only: leaf-size UV and separate phase on the inner layer.\n'
     '    if leaf_core:\n'
     '        core_uv = core_uv / HEDGE_TILE_M + np.array([0.37, 0.61])\n'
     '    nt += strip(core, core_draw_m, core_uv)'),
    ('        buf.add("furniture", core_m, np.column_stack([P2, z2]), P2.copy(), Tt, src=src)',
     '        core_top_uv = P2 / HEDGE_TILE_M + np.array([0.37, 0.61]) if leaf_core else P2.copy()\n'
     '        buf.add("furniture", core_draw_m, np.column_stack([P2, z2]), core_top_uv, Tt, src=src)'),
]
for old, new in edits:
    if source.count(old) != 1:
        raise SystemExit('Source drift: proposal must be reviewed again')
    source = source.replace(old, new)
out = here/'next-round-proposal'
out.mkdir(exist_ok=True)
(out/'plantings_leaf_core.py').write_text(source, encoding='utf-8')
(out/'leaf-core-proposal.patch').write_text(''.join(difflib.unified_diff(
    original.splitlines(True), source.splitlines(True),
    fromfile='a/tools/worldgen/streetscape/plantings.py',
    tofile='b/tools/worldgen/streetscape/plantings.py')), encoding='utf-8')
spec = importlib.util.spec_from_file_location('streetscape.leaf_core_proposal', out/'plantings_leaf_core.py')
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)

class Capture:
    def __init__(self): self.parts = []
    def add(self, layer, material, vertices, uv, triangles, **kwargs):
        self.parts.append((layer, material, np.asarray(vertices), np.asarray(uv), np.asarray(triangles)))

results = {}
for plant in baseline.SPECIES:
    captures = []
    for module in (baseline, candidate):
        buf = Capture()
        module.hedge_mass(buf, box(0,0,8,1.3), lambda x,y: np.zeros_like(x),
                          ('proposal','same-geometry'), h=.65, plant=plant)
        captures.append(buf.parts)
    a,b = captures
    same_geometry = len(a)==len(b) and all(x[0]==y[0] and np.array_equal(x[2],y[2]) and np.array_equal(x[4],y[4]) for x,y in zip(a,b))
    same_all = same_geometry and all(x[1]==y[1] and np.array_equal(x[3],y[3]) for x,y in zip(a,b))
    results[plant] = dict(triangles_before=sum(len(p[4]) for p in a),
                         triangles_proposal=sum(len(p[4]) for p in b),
                         exact_vertices_indices_and_layers=same_geometry,
                         all_fields_unchanged=same_all,
                         materials_before=sorted({p[1] for p in a}),
                         materials_proposal=sorted({p[1] for p in b}))
    if not same_geometry or (plant!='berberis_red' and not same_all):
        raise SystemExit('Unexpected geometry or other-species change')
result = dict(status='PROPOSAL ONLY, NOT APPLIED OR RENDERED',
              baseline_source_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
              cases=results,
              note='One small 8x1.3m synthetic bed per species. No GIS pytest, world build, Unity launch or production writes. This is geometry analysis, not visual or GPU acceptance.')
(out/'geometry-study.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
