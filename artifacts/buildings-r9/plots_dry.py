"""Dry run of plots.build on synthetic data is not possible (needs the road net); this checks the kit functions and
the canopy assignment logic on a fake plot. uv run --project tools/worldgen python artifacts/buildings-r9/plots_dry.py"""
import sys
from pathlib import Path
import numpy as np
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
from shapely.geometry import Polygon, box
from streetscape import plots as PLT, plot_canopy as PCN

class Buf:
    def __init__(s): s.parts = []
    def add(s, layer, mat, V, UV, T, **k): s.parts.append((layer, mat, len(T)))

poly = box(0, 0, 24, 30)
foot = box(7, 12, 17, 22)
front = np.array([0.0, -1.0])
edges = PLT._edges(poly)
runs = [{"style": "picket" if float(e[4] @ front) > 0.7 else "chainlink", "h": 1.3, "a": e[0], "b": e[1], "n": e[4], "front": float(e[4] @ front) > 0.7} for e in edges]
plot = {"key": "k", "id": "x", "age": "old", "front_style": "picket", "side_style": "chainlink", "front_h": 1.3, "side_h": 1.3,
        "poly": poly, "foot": foot, "front": front, "house_polys": [foot], "door_zones": [], "hard": box(1, 0, 4, 20),
        "lay": {"runs": runs, "gate": None, "wicket": None, "wickets": []}, "drive": None}
can = np.array([[20.0, 5.0, 3.5, 0, 60], [12.0, 26.0, 1.8, 0, 60], [3.0, 26.0, 0.9, 0, 60], [21.0, 25.0, 2.0, 1, 50], [10.0, -3.5, 3.0, 0, 60],
                [12.0, 17.0, 3.0, 0, 60]])
rp = {"plots": [plot], "drops": [], "canopy": can, "roads_poly": box(-50, -20, 80, -9), "carriage": box(-50, -20, 80, -11), "bpoly": foot}
rep = {}
b = Buf()
out = PLT.build(b, rp, lambda q: 0.0, None, rep)
print({k: v for k, v in rep["plots"].items() if k not in ("list",)})
print("trees", out["trees"])
print(b.parts)
