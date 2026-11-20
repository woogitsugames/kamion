"""Definition of tile 4 of the map plan of ADR 0278 (owner D81/D93, D63 "rough first"): bialystok-krywlany.

Lattice (0,-3) of the ADR 0203 plan: west neighbour of bialystok-dojlidy, south-west corner neighbour of
bialystok-mickiewicza. The truck route C <-> Dojlidy of the plan (corridor c-to-dojlidy-g10, the same truck path as
tools/worldgen/qa/dk19_tiles_0278.py) leaves mickiewicza on the north seam of Dojlidy, runs a short stub inside the NW
corner of Dojlidy (Ciolkowskiego DW678) and turns into this tile; it re-enters Dojlidy at the Dojlidy route entry on
its west edge (Dywizjonu 303, start of the Dojlidy control route). The piece inside this tile becomes its control route
(authored route_endpoints.json, start = Dojlidy | krywlany seam on Ciolkowskiego, end = Dojlidy route entry), the
Dojlidy stub is printed for the route link of the corridor (Data/Streaming/route_links.yaml).

  uv run --project tools/worldgen python tools/worldgen/qa/krywlany_tile_0278.py            # json of the pieces
  uv run --project tools/worldgen python tools/worldgen/qa/krywlany_tile_0278.py --init     # + missing authored files
  uv run --project tools/worldgen python tools/worldgen/qa/krywlany_tile_0278.py --print-regions
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from shapely.geometry import LineString, box

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dk19_tiles_0278 as DK  # noqa: E402
import map_plan_0278 as MP  # noqa: E402

TID = "bialystok-krywlany"
TITLE = ("Białystok — Ciołkowskiego DW678, rondo Wünschego i Dywizjonu 303 przy lotnisku Krywlany, "
         "zachodni sąsiad Dojlid (Krywlany)")
# Dojlidy route entry (Data/Regions/bialystok-dojlidy/route_endpoints.json start_epsg2180): the corridor ends there.
DOJLIDY_ENTRY = (779019.0, 590253.0)
# NMT: the seams with bialystok-dojlidy (route) and bialystok-mickiewicza (corner) are NMT 2025 (gugik-nmt-2025-*).
PIN = "2025"


def pieces() -> dict:
    extract = json.loads(MP.EXTRACT.read_text(encoding="utf-8"))
    L = MP.lines(extract)
    g, path = DK.truck_path(extract, L)
    line = LineString(path)
    out = {}
    for tid in (TID, "bialystok-dojlidy"):
        bb = MP.tile_bbox(*MP.CANDIDATES[tid]["ij"]) if tid in MP.CANDIDATES else (779019.0, 589055.0, 781067.0, 591103.0)
        part = line.intersection(box(*bb))
        parts = [q for q in getattr(part, "geoms", [part]) if q.geom_type == "LineString" and q.length > 1.0]
        rows = []
        for q in parts:
            ways = []
            qb = q.buffer(0.5)
            for u, v in zip(path, path[1:]):
                mx, my = (u[0] + v[0]) / 2, (u[1] + v[1]) / 2
                from shapely.geometry import Point
                if qb.contains(Point(mx, my)) and (not ways or ways[-1] != g[u][v]["way"]):
                    ways.append(g[u][v]["way"])
            a, b = q.coords[0], q.coords[-1]
            rows.append({"start": [round(a[0], 1), round(a[1], 1)], "end": [round(b[0], 1), round(b[1], 1)],
                         "length_m": round(q.length, 1), "ways": ways})
        out[tid] = {"bbox": list(bb), "pieces": rows}
    return out


def authored(r: dict) -> dict[str, str]:
    bb = r["bbox"]
    ox, oy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    p = max(r["pieces"], key=lambda q: q["length_m"])
    ov = (f"# Authored overrides of region {TID} (ADR 0278 tile 4, owner D81/D93). Every entry survives a re-import;\n"
          f"# coordinates are region-local E/N (origin EPSG:2180 {ox:.0f}, {oy:.0f}) or EPSG:2180 where the key says so.\n"
          f"overrides: []\n")
    src = json.dumps({
        "provenance": f"authored_override (ADR 0278, mechanism of ADR 0209/0212): source pins of region {TID}, read by ingest.py and build_region.py",
        "pins": {"nmt_year": PIN},
        "reason": ("The route seam with bialystok-dojlidy (Ciolkowskiego, Dywizjonu 303) and the corner with "
                   "bialystok-mickiewicza are built from NMT 2025 (gugik-nmt-2025-bialystok-dojlidy, "
                   "gugik-nmt-2025-bialystok-mickiewicza); this tile keeps that series. GUGiK sheet index: "
                   "docs/reports/map/map_plan_0278_gugik.json (2025 fully covers the tile, sheets N-34-107-C-b-3-1..4)."),
        "verify": "none (move together with the pin of the neighbours named in the reason)",
    }, indent=1, ensure_ascii=False) + "\n"
    rt = json.dumps({
        "provenance": "authored_override (ADR 0278 tile 4, owner D81): control route for cameras/QA = the truck route C <-> Dojlidy inside this tile",
        "description": (f"Piece of the plan corridor c-to-dojlidy-g10 inside the tile: from the seam with bialystok-dojlidy "
                        f"(Ciolkowskiego DW678, after the NW-corner stub of Dojlidy) to the Dojlidy route entry on the same seam "
                        f"(Dywizjonu 303), {p['length_m']:.0f} m over the OSM ways {', '.join(str(w) for w in p['ways'])}. "
                        f"Points from the OSM API 0.6 extract of 2026-11-16 (Data/Plans/map-plan-0278/); build_world snaps "
                        f"them to the nearest graph node. Generated by tools/worldgen/qa/krywlany_tile_0278.py."),
        "start_epsg2180": p["start"],
        "end_epsg2180": list(DOJLIDY_ENTRY),
        "confidence": "medium (OSM 2026-11-16 vs the pinned pbf: re-check after build_region that both are graph boundary nodes)",
    }, indent=1, ensure_ascii=False) + "\n"
    return {"overrides.yaml": ov, "sources.authored.json": src, "route_endpoints.json": rt}


def print_regions() -> str:
    plan = json.loads(MP.PLAN.read_text(encoding="utf-8"))
    t = {c["id"]: c for c in plan["candidates"]}[TID]
    i, j = t["ij"]
    extra = ("\n        teryt_powiat_extra=(" + "".join(f'"{q}", ' for q in t["teryt_powiat_extra"]).rstrip() + "),"
             if t["teryt_powiat_extra"] else "")
    return f'''    "{TID}": Region(
        id="{TID}",
        title="{TITLE}",
        candidate="P_{t['group'].replace('-', '_')}",
        bbox=({t['bbox'][0]}, {t['bbox'][1]}, {t['bbox'][2]}, {t['bbox'][3]}),
        origin=({t['origin'][0]}, {t['origin'][1]}),
        teryt_powiat="{t['teryt_powiat']}",{extra}
        status="WORKING_ASSUMPTION (ADR 0278 tile 4, owner D81/D93; tile = lattice ({i},{j}) of the ADR 0203 plan)",
    ),'''


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--print-regions", action="store_true")
    a = ap.parse_args()
    if a.print_regions:
        print(print_regions())
        return
    p = pieces()
    print(json.dumps(p, indent=1, ensure_ascii=False))
    if a.init:
        d = MP.REG / TID
        d.mkdir(parents=True, exist_ok=True)
        for name, text in authored(p[TID]).items():
            if not (d / name).exists():                    # authored files: never overwritten
                (d / name).write_text(text, encoding="utf-8", newline="\n")
                print("written", f"{TID}/{name}", file=sys.stderr)


if __name__ == "__main__":
    main()
