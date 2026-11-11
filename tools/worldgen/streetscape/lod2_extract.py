"""Dump the GUGiK LoD2 (2017, CC BY 4.0) roof and wall surfaces of the buildings around a point as JSON.

Dimension source for hero buildings (ADR 0070): eave / ridge heights per roof plane, relative to the building's
lowest LoD2 vertex, in region-local E/N metres.

    uv run --project tools/worldgen python tools/worldgen/streetscape/lod2_extract.py \
        --region bialystok-industrial-c --e -235 --n -147 --radius 60 --out <json>
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from xml.etree.ElementTree import iterparse

import shapely
import yaml

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import buildings as B  # noqa: E402

ZIP = REPO / "Data" / "raw" / "gugik" / "lod2-2017-2061" / "2061_lod2_gml.zip"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--e", type=float, required=True)
    ap.add_argument("--n", type=float, required=True)
    ap.add_argument("--radius", type=float, default=60.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    reg = yaml.safe_load((REPO / "Data" / "Regions" / a.region / "region.yaml").read_text(encoding="utf-8"))
    ox, oy = reg["origin"]["x"], reg["origin"]["y"]
    cx, cy = ox + a.e, oy + a.n
    bbox = (cx - a.radius, cy - a.radius, cx + a.radius, cy + a.radius)
    tile = shapely.box(*bbox)
    out = []
    with zipfile.ZipFile(ZIP) as zf:
        for name in sorted(n for n in zf.namelist() if n.lower().endswith(".gml")):
            with zf.open(name) as f:
                head = f.read(6000)
            if not B._envelope_hits(head, bbox):
                continue
            with zf.open(name) as f:
                for _, el in iterparse(f, events=("end",)):
                    if el.tag != f"{B.BLDG}Building":
                        continue
                    rec = B._building_record(el, 2)
                    if rec and rec["footprint"] is not None and rec["footprint"].intersects(tile):
                        zmin = rec["zmin"]

                        def rel(r):
                            return [[round(x - ox, 2), round(y - oy, 2), round(z - zmin, 2)] for x, y, z in r]

                        out.append({
                            "id": rec["id"], "file": name, "zmin": round(zmin, 2), "height": round(rec["zmax"] - zmin, 2),
                            "roof_type": rec["roof_type"],
                            "roofs": [rel(r) for rs in el.iter(f"{B.BLDG}RoofSurface") for r in B._rings(rs)],
                            "walls": [rel(r) for ws in el.iter(f"{B.BLDG}WallSurface") for r in B._rings(ws)],
                        })
                    el.clear()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({
        "source": "GUGiK LoD2 2017, powiat 2061 (CC BY 4.0), Data/SourceManifests/gugik-lod2-2017-2061.json",
        "frame": "region-local E/N metres; z relative to the lowest LoD2 vertex of the building",
        "buildings": out}, indent=1), encoding="utf-8")
    for b in out:
        print(b["id"], b["file"], "h", b["height"], "roofs", len(b["roofs"]), "walls", len(b["walls"]))
        for r in b["roofs"]:
            zs = [p[2] for p in r]
            print("   roof n", len(r) - 1, "z", min(zs), max(zs), "area", round(shapely.Polygon([p[:2] for p in r]).area, 1),
                  "c", [round(v, 1) for v in shapely.Polygon([p[:2] for p in r]).centroid.coords[0]])


if __name__ == "__main__":
    main()
