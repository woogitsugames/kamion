"""Compare fixed flat and steep boundaries without touching generator modules."""
import json
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import LineString

sys.path.insert(0, 'tools/worldgen')
from streetscape import furniture as F

scope = dict(F.__dict__)
exec(Path(__file__).with_name('panel_candidate.py').read_text(), scope)


class Buffer:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, V, UV, T, **kwargs):
        self.parts.append((layer, mat, np.asarray(V), np.asarray(T)))


result = {}
for slope in (0.0, 0.1, 0.4):
    row = {}
    for name, fn in [('before', F.panel_fence), ('candidate', scope['panel_fence'])]:
        buf = Buffer()
        lin = F.Lin(buf, lambda e, n: slope * e)
        fn(lin, LineString([(0, 0), (10, 0), (10, 5)]), 'fence_green', 'fixed')
        exposed = [float(np.max(V[:, 2] - slope*V[:, 0])) for layer, mat, V, T in buf.parts
                   if mat == 'concrete_plinth']
        row[name] = dict(triangles=sum(len(t) for l,m,v,t in buf.parts if l != 'collision'),
                         materials=sorted({m for l,m,v,t in buf.parts if l != 'collision'}),
                         maximum_plinth_above_ground=max(exposed))
    result[str(slope)] = row
print(json.dumps(result, indent=2))
Path(__file__).with_name('candidate-measurements.json').write_text(json.dumps(result, indent=2)+'\n')
