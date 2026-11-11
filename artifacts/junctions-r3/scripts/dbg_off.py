import sys
sys.path.insert(0, "tools/worldgen")
import numpy as np
from roads import pipeline
from roads.geom import Polyline
net, *_ = pipeline.build_network("bialystok-industrial-c")
for cid in [a for a in sys.argv[1:] if not a.startswith("@")]:
    c = next(c for c in net.chains if cid in c.id)
    raw = Polyline(np.asarray(c.raw, float))
    off = c.meta.get("center_offset")
    print("==", c.id, "L", round(c.length, 1), [(e, net.sections[e].center_offset, net.sections[e].center_offset_profile, net.sections[e].width_profile, net.sections[e].lane_edges) for e, _ in c.edges])
    for s in (np.arange(0, c.length + 0.1, max(5.0, c.length / 12)) if len(sys.argv) < 3 or not sys.argv[-1].startswith("@") else np.arange(float(sys.argv[-1][1:].split(",")[0]), float(sys.argv[-1][1:].split(",")[1]), 2.5)):
        i = c.idx(s)
        _, lat = raw.project(c.line.p[i])
        print(f"  s {s:6.1f} meta_off {None if off is None else round(float(off[i]),2)} actual lat vs raw {lat:+.2f} hw {float(c.hw[i]):.2f}")
