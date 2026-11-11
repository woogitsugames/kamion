"""Fetch GUGiK WMS HighResolution 0.08 m cells around local E,N boxes into artifacts/junctions-r2/ortho_hr
(Data/raw/refs is a read-only junction in this worktree).  fetch_hr.py E0,N0,E1,N1 ..."""
import sys
sys.path.insert(0, "tools/worldgen")
import shapely
from roads import pipeline
from fidelity import ortho as O
O.UA = "worldgen-fidelity/0.1"
reg = pipeline.load_region("bialystok-industrial-c")
ox, oy = reg["origin"]["x"], reg["origin"]["y"]
boxes = [shapely.box(ox + a, oy + b, ox + c, oy + d) for a, b, c, d in
         (tuple(float(v) for v in s.split(",")) for s in sys.argv[1:])]
cells = O.cells_for(reg, boxes)
have = O._load_manifest(O.cell_dir(reg["id"]))
cells = [c for c in cells if f"c_{c[0]:02d}_{c[1]:02d}.jpg" not in have]
print("cells to fetch", cells)
O.fetch_cells(reg, cells, out_dir="artifacts/junctions-r2/ortho_hr")
