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
import powiaty as PW  # noqa: E402  (ADR 0219)


def lod2_zips(bbox) -> tuple[list[tuple[str, Path]], list[str]]:
    """ADR 0219: LoD2 ZIP of every powiat the window overlaps (was powiat 2061 only) + powiaty not on disk."""
    zips, missing = [], []
    for t in PW.powiaty_for_bbox(bbox):
        files = PW.package_files("lod2-2017", t)
        if files and files[0].exists():
            zips.append((t, files[0]))
        else:
            missing.append(t)
    return zips, missing


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
    zips, missing = lod2_zips(bbox)
    if missing:
        print(f"WARNING: no LoD2 package on disk for powiat(y) {', '.join(missing)} "
              f"(ingest: tools/worldgen/ingest.py); buildings there are missing from the dump")
    seen = set()
    for _, zpath in zips:
        _dump_zip(zpath, bbox, tile, ox, oy, out, seen)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    pw = [t for t, _ in zips]
    Path(a.out).write_text(json.dumps({
        "source": "GUGiK LoD2 2017, powiat %s (CC BY 4.0), %s" % (
            ", ".join(pw), ", ".join(f"Data/SourceManifests/gugik-lod2-2017-{t}.json" for t in pw)),
        **({"powiaty_missing": missing} if missing else {}),
        "frame": "region-local E/N metres; z relative to the lowest LoD2 vertex of the building",
        "buildings": out}, indent=1), encoding="utf-8")
    for b in out:
        print(b["id"], b["file"], "h", b["height"], "roofs", len(b["roofs"]), "walls", len(b["walls"]))
        for r in b["roofs"]:
            zs = [p[2] for p in r]
            print("   roof n", len(r) - 1, "z", min(zs), max(zs), "area", round(shapely.Polygon([p[:2] for p in r]).area, 1),
                  "c", [round(v, 1) for v in shapely.Polygon([p[:2] for p in r]).centroid.coords[0]])


def _dump_zip(zpath, bbox, tile, ox, oy, out, seen) -> None:
    """Append the LoD2 buildings of one powiat ZIP; a building already dumped from an earlier powiat (on the
    boundary, in both packages) is skipped, records inside one ZIP are kept as before."""
    mine = set()
    with zipfile.ZipFile(zpath) as zf:
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
                    if (rec and rec["footprint"] is not None and rec["footprint"].intersects(tile)
                            and rec["id"] not in seen):          # seen = ids of the EARLIER powiaty only
                        mine.add(rec["id"])
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
    seen |= mine


if __name__ == "__main__":
    main()
