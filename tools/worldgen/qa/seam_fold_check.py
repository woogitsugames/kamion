"""seam-knw-s24: winding of the road-node triangles near a seam point (EPSG:2180), per material: a folded ribbon (a
station row overtaking the next one) shows up as triangles of the opposite orientation to the rest of that material.
uv run --project tools/worldgen python tools/worldgen/qa/seam_fold_check.py <tile> <E> <N> [radius] [root]"""
import sys
from pathlib import Path
import numpy as np, yaml
sys.path.insert(0, str(Path(__file__).resolve().parent))
from seam_section import tris  # noqa: E402

if __name__ == "__main__":
    tile, e, n = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    rad = float(sys.argv[4]) if len(sys.argv) > 4 else 15.0
    root = Path(sys.argv[5]) if len(sys.argv) > 5 else Path(__file__).resolve().parents[3]
    o = yaml.safe_load((root / "Data/Regions" / tile / "region.yaml").read_text(encoding="utf-8"))["origin"]
    tot = 0
    for node in ("road", "collision"):
        for mat, T in sorted(tris(root, tile, node, (e - o["x"], n - o["y"]), rad=rad).items()):
            a = T[:, 1, :2] - T[:, 0, :2]; b = T[:, 2, :2] - T[:, 0, :2]
            ar = 0.5 * (a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0])
            flat = np.abs(ar) > 1e-4                     # vertical faces (kerb risers, flanges) excluded
            pos, neg = int((ar[flat] > 0).sum()), int((ar[flat] < 0).sum())
            minority = min(pos, neg)
            tot += minority if mat.startswith(("road_asphalt", "sidewalk", "curb", "collision")) else 0
            print(f"{tile} {node}:{mat:28s} +{pos:5d} -{neg:5d} minority {minority}")
    print(f"TOTAL minority (asphalt/sidewalk/curb/collision) {tot}")
