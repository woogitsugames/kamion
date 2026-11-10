"""Dump parked-vehicle prototypes for the Blender control render (ADR 0073).

  uv run --project tools/worldgen python tools/worldgen/qa/car_preview.py --out DIR [--lod 0] [--protos a,b,...]
  blender -b -P tools/blender/world/render_cars.py -- DIR/cars.json DIR

Writes DIR/cars.json: materials (streetscape.materials.M subset) and per prototype the primitives with the same
per-corner normals the GLB export writes (export.crease_normals), plus a triangle table on stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streetscape import export as E  # noqa: E402
from streetscape import life_cars as LC  # noqa: E402
from streetscape.materials import M  # noqa: E402

DEFAULT = ["car_hatch_silver", "car_sedan_grey", "car_estate_red", "car_suv_white", "van_white", "car_hatch_blue",
           "car_suv_black", "car_estate_silver"]


def build(name):
    if name.startswith("van_"):
        return LC.van(name[4:])
    _, body, colour = name.split("_")
    return LC.car(body, colour)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--lod", type=int, default=0)
    ap.add_argument("--protos", default=",".join(DEFAULT))
    a = ap.parse_args()
    out = Path(a.out).resolve()
    (out / "tex").mkdir(parents=True, exist_ok=True)
    E.car_dirt_png().save(out / "tex" / "car_dirt.png")       # generated here: the art-source copies are LFS files
    LC.plate_atlas().save(out / "tex" / "car_plates.png")
    doc = {"materials": {}, "protos": {}, "textures": str(out / "tex")}
    for name in a.protos.split(","):
        P = build(name)
        mesh = P[{0: 0, 1: 1, 2: 3}[a.lod]]
        prims = E.crease_normals(mesh.out())
        tris = {k: sum(len(p["T"]) for p in P[i].out()) for k, i in (("lod0", 0), ("lod1", 1), ("lod2", 3))}
        by = {p["mat"]: len(p["T"]) for p in prims}
        print(name, tris, json.dumps(dict(sorted(by.items(), key=lambda kv: -kv[1]))), flush=True)
        doc["protos"][name] = [{"mat": p["mat"], "V": np.round(p["V"], 5).tolist(), "N": np.round(p["N"], 4).tolist(),
                                "UV": np.round(p["UV"], 5).tolist(), "T": np.asarray(p["T"]).tolist()} for p in prims]
        for p in prims:
            doc["materials"][p["mat"]] = {k: v for k, v in M[p["mat"]].items() if isinstance(v, (int, float, list, str, bool))}
    (out / "cars.json").write_text(json.dumps(doc), encoding="utf-8")


if __name__ == "__main__":
    main()
