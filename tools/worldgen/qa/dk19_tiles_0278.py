"""Definitions of tiles 5-7 of the map plan of ADR 0278 (owner D81): bialystok-mickiewicza, -bojary, -wygoda.

The truck route C <-> Dojlidy of the plan (corridor "c-to-dojlidy-g10": numbered roads preferred, hgv=no and
maxweight < 40 t left out; OSM API 0.6 extract of 2026-11-16 in git) is cut at the tile edges; every tile gets the
piece inside it as its control route (authored route_endpoints.json), an empty overrides.yaml and the NMT pin.

  uv run --project tools/worldgen python tools/worldgen/qa/dk19_tiles_0278.py            # json of the three pieces
  uv run --project tools/worldgen python tools/worldgen/qa/dk19_tiles_0278.py --init     # + missing authored files
  uv run --project tools/worldgen python tools/worldgen/qa/dk19_tiles_0278.py --print-regions
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from shapely.geometry import LineString, box

sys.path.insert(0, str(Path(__file__).resolve().parent))
import map_plan_0278 as MP  # noqa: E402

START, END = (779019.0, 595250.0), (779019.0, 590258.0)      # corridor c-to-dojlidy-g10 of the plan
TILES = ("bialystok-wygoda", "bialystok-bojary", "bialystok-mickiewicza")      # driving order C -> Dojlidy
TITLES = {
    "bialystok-wygoda": "Białystok — DK19/DK65 Andersa na wschód od C, narożnik trasy C ↔ Dojlidy (Wygoda)",
    "bialystok-bojary": "Białystok — DK19 Andersa, Sosabowskiego i Piastowska (Bojary)",
    "bialystok-mickiewicza": "Białystok — DK19 Piastowska, pl. Antonowicza, Branickiego, rondo Meyera, Ciołkowskiego DW678 (Mickiewicza)",
}
NEIGHBOUR = {"bialystok-wygoda": ("bialystok-industrial-c", "bialystok-bojary"),
             "bialystok-bojary": ("bialystok-wygoda", "bialystok-mickiewicza"),
             "bialystok-mickiewicza": ("bialystok-bojary", "bialystok-dojlidy")}
# NMT: both built neighbours on the route seams (C, Dojlidy) come from the 2025 series (gugik-nmt-2025-<id>).
PIN = "2025"


def truck_path(extract, L):
    import networkx as nx
    g = MP._digraph(extract, L, truck_costs=True)

    def near(p, r=40.0):
        return sorted(n for n in g.nodes if (n[0] - p[0]) ** 2 + (n[1] - p[1]) ** 2 <= r * r)

    best = None
    for a in near(START):
        for b in near(END):
            try:
                c, p = nx.single_source_dijkstra(g, a, b, weight="w")
            except nx.NetworkXNoPath:
                continue
            if best is None or (c, a, b) < best[0]:
                best = ((c, a, b), p)
    if best is None:
        raise SystemExit("no truck route in the extract")
    return g, best[1]


def pieces() -> dict:
    extract = json.loads(MP.EXTRACT.read_text(encoding="utf-8"))
    L = MP.lines(extract)
    g, path = truck_path(extract, L)
    line = LineString(path)
    out = {}
    for tid in TILES:
        bb = MP.tile_bbox(*MP.CANDIDATES[tid]["ij"])
        part = line.intersection(box(*bb))
        parts = [q for q in getattr(part, "geoms", [part]) if q.geom_type == "LineString"]
        part = max(parts, key=lambda q: q.length)
        ways = []
        for u, v in zip(path, path[1:]):
            mx, my = (u[0] + v[0]) / 2, (u[1] + v[1]) / 2
            if bb[0] <= mx <= bb[2] and bb[1] <= my <= bb[3] and (not ways or ways[-1] != g[u][v]["way"]):
                ways.append(g[u][v]["way"])
        a, b = part.coords[0], part.coords[-1]
        out[tid] = {"bbox": list(bb), "start": [round(a[0], 1), round(a[1], 1)], "end": [round(b[0], 1), round(b[1], 1)],
                    "length_m": round(part.length, 1), "pieces_in_tile": len(parts), "ways": ways,
                    "from": NEIGHBOUR[tid][0], "to": NEIGHBOUR[tid][1]}
    return out


def authored(tid: str, r: dict) -> dict[str, str]:
    bb = r["bbox"]
    ox, oy = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
    ov = (f"# Authored overrides of region {tid} (ADR 0278, owner D81). Every entry survives a re-import; coordinates are\n"
          f"# region-local E/N (origin EPSG:2180 {ox:.0f}, {oy:.0f}) or EPSG:2180 where the key says so.\n"
          f"overrides: []\n")
    src = json.dumps({
        "provenance": f"authored_override (ADR 0278, mechanism of ADR 0209/0212): source pins of region {tid}, read by ingest.py and build_region.py",
        "pins": {"nmt_year": PIN},
        "reason": ("The seams of the truck route C <-> Dojlidy are shared with bialystok-industrial-c and bialystok-dojlidy, both "
                   "built from NMT 2025 (gugik-nmt-2025-bialystok-industrial-c, gugik-nmt-2025-bialystok-dojlidy); the three "
                   "tiles of the route keep that series. GUGiK sheet index: docs/reports/map/map_plan_0278_gugik.json "
                   "(2025 fully covers the tile)."),
        "verify": "none (move together with the pin of the neighbours named in the reason)",
    }, indent=1, ensure_ascii=False) + "\n"
    rt = json.dumps({
        "provenance": "authored_override (ADR 0278, owner D81): control route for cameras/QA = the truck route C <-> Dojlidy inside this tile",
        "description": (f"Piece of the plan corridor c-to-dojlidy-g10 inside the tile: from the seam with {r['from']} to the seam with "
                        f"{r['to']}, {r['length_m']:.0f} m over the OSM ways {', '.join(str(w) for w in r['ways'])}. Points from the "
                        f"OSM API 0.6 extract of 2026-11-16 (Data/Plans/map-plan-0278/); build_world snaps them to the nearest "
                        f"graph node. Generated by tools/worldgen/qa/dk19_tiles_0278.py."),
        "start_epsg2180": r["start"],
        "end_epsg2180": r["end"],
        "confidence": "medium (OSM 2026-11-16 vs the pinned pbf: re-check after build_region that both are graph boundary nodes)",
    }, indent=1, ensure_ascii=False) + "\n"
    return {"overrides.yaml": ov, "sources.authored.json": src, "route_endpoints.json": rt}


def print_regions(p: dict) -> str:
    plan = json.loads(MP.PLAN.read_text(encoding="utf-8"))
    by = {t["id"]: t for t in plan["candidates"]}
    out = []
    for tid in TILES:
        t = by[tid]
        i, j = t["ij"]
        extra = ("\n        teryt_powiat_extra=(" + "".join(f'"{q}", ' for q in t["teryt_powiat_extra"]).rstrip() + "),"
                 if t["teryt_powiat_extra"] else "")
        out.append(f'''    "{tid}": Region(
        id="{tid}",
        title="{TITLES[tid]}",
        candidate="P_{t['group'].replace('-', '_')}",
        bbox=({t['bbox'][0]}, {t['bbox'][1]}, {t['bbox'][2]}, {t['bbox'][3]}),
        origin=({t['origin'][0]}, {t['origin'][1]}),
        teryt_powiat="{t['teryt_powiat']}",{extra}
        status="WORKING_ASSUMPTION (ADR 0278, owner D81; tile = lattice ({i},{j}) of the ADR 0203 plan)",
    ),''')
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--print-regions", action="store_true")
    a = ap.parse_args()
    p = pieces()
    if a.print_regions:
        print(print_regions(p))
        return
    print(json.dumps(p, indent=1, ensure_ascii=False))
    if a.init:
        for tid, r in p.items():
            d = MP.REG / tid
            d.mkdir(parents=True, exist_ok=True)
            for name, text in authored(tid, r).items():
                if not (d / name).exists():                    # authored files: never overwritten
                    (d / name).write_text(text, encoding="utf-8", newline="\n")
                    print("written", f"{tid}/{name}", file=sys.stderr)


if __name__ == "__main__":
    main()
