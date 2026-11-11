"""Cross-sections of the built RENDER surfaces (terrain_lod0 + road / paved parts of the full chunk glb): heights of
every surface along a lateral line (right of the direction).
    uv run --project tools/worldgen python artifacts/roads-p0-r10/scripts/xsec.py E:N:dirE:dirN:fwd:lat0:lat1:step ..."""
import sys
from pathlib import Path
import numpy as np
repo = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(repo / "tests" / "gis"))
import route_corridor as rc
rid = "bialystok-industrial-c"
wd = repo / "Data/raw/derived" / rid / "world"
man = None
for a in sys.argv[1:]:
    e, n, de, dn, fwd, l0, l1, st = map(float, a.split(":"))
    d = np.array([de, dn]); d /= np.linalg.norm(d); r = np.array([d[1], -d[0]])
    p0 = np.array([e, n]) + d * fwd
    grids = {}
    for f in sorted(wd.glob("chunk_*_*.glb")):
        if ".low" in f.name:
            continue
        doc, data, off = rc.read_glb(f)
        for node in ("terrain_lod0", "road", "paved"):
            for m, t in rc.node_triangles(doc, data, off, node).items():
                sel = (t[:, :, 0].max(1) >= p0[0] - 40) & (t[:, :, 0].min(1) <= p0[0] + 40) & \
                      (t[:, :, 1].max(1) >= p0[1] - 40) & (t[:, :, 1].min(1) <= p0[1] + 40)
                if sel.any():
                    grids.setdefault(f"{node[:4]}:{m}", []).append(t[sel])
    grids = {k: rc.TriGrid(np.concatenate(v)) for k, v in grids.items()}
    print("##", a)
    for lat in np.arange(l0, l1 + 1e-6, st):
        x, y = p0 + r * lat
        row = []
        for k, g in grids.items():
            c = g.query(x, y, x, y)
            z = rc.ray_heights(g.tris[c], x, y) if len(c) else np.zeros(0)
            z = z[~np.isnan(z)]
            for v in sorted(set(np.round(z, 2))):
                row.append(f"{k}={v:.2f}")
        print(f"lat={lat:+5.1f} e={x:.1f} n={y:.1f}  " + "  ".join(row))
