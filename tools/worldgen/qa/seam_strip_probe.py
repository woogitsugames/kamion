"""seam-knw-s24: built surface along lines parallel to a vertical (x = const) tile seam, both tiles, read from chunk GLBs.

For every material of the `road` node (and `markings`) prints the N intervals covered at x = seam -/+ d (d inside each
tile), so a step in asphalt / kerb / sidewalk across the seam is visible as numbers (EPSG:2180 N).
uv run --project tools/worldgen python tools/worldgen/qa/seam_strip_probe.py <tileW> <tileE> <x_seam> <n_lo> <n_hi> [out.json]
"""
import json, sys
from pathlib import Path
import numpy as np, yaml
sys.path.insert(0, str(Path(__file__).resolve().parent))
from seam_section import tris, locate, runs  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]


def origin(t):
    return yaml.safe_load((ROOT / "Data/Regions" / t / "region.yaml").read_text(encoding="utf-8"))["origin"]


def probe(tile, x, n_lo, n_hi, step=0.05, nodes=("road", "markings", "terrain")):
    o = origin(tile); ns = np.arange(n_lo, n_hi + 1e-9, step)
    pts = np.column_stack([np.full_like(ns, x - o["x"]), ns - o["y"]])
    centre = pts[len(pts) // 2]; rad = (n_hi - n_lo) / 2 + 5
    out = {}
    for node in nodes:
        for mat, T in tris(ROOT, tile, node, centre, rad=rad).items():
            z = locate(T, pts)
            r = [(round(a + o["y"], 2), round(b + o["y"], 2)) for a, b in runs(~np.isnan(z), ns - o["y"]) if b - a > 0.08]
            if r:
                out[f"{node}:{mat}"] = r
    return out


if __name__ == "__main__":
    tw, te, xs, lo, hi = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
    res = {}
    for d in (0.3, 1.0, 3.0, 6.0):
        for t, x in ((tw, xs - d), (te, xs + d)):
            r = probe(t, x, lo, hi); res[f"{t}@{x:.2f}"] = r
            print(f"== {t} x={x:.2f} (d={d})")
            for k, v in sorted(r.items()):
                if not k.startswith("terrain"):
                    print(f"   {k:40s} {v}")
    if len(sys.argv) > 6:
        Path(sys.argv[6]).write_text(json.dumps(res, indent=1), encoding="utf-8")
