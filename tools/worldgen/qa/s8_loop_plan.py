"""ADR 0288 (owner D82, D63 "drivable first"): the loop S8 <-> DW671 <-> Tykocin - rough definition of its 15 tiles on
the 2048 m lattice of ADR 0203, in driving order from dk65-01 (Bialystok) along the S8 to the Jezewo junction and
back north on the DW671 to the `tykocin` tile of the ring (ADR 0231, PR #115).

    uv run --project tools/worldgen python tools/worldgen/qa/s8_loop_plan.py                  # plan json (no network)
    uv run --project tools/worldgen python tools/worldgen/qa/s8_loop_plan.py --png            # + control render
    uv run --project tools/worldgen python tools/worldgen/qa/s8_loop_plan.py --print-regions  # regions.py entries
    uv run --project tools/worldgen python tools/worldgen/qa/s8_loop_plan.py --init-regions   # authored files (missing only)

Input: the pinned Geofabrik pbf of the pipeline (Data/SourceManifests/osm-geofabrik-podlaskie.json; ODbL), read
through osm_extract with the wider window LOOP_BBOX_WGS84 (the pipeline window of osm_extract.BBOX_WGS84 ends at
22.80 E: the tiles s8-09..12 and dw671-jezewo-* lie west of it - see "leader tasks" in the ADR). The seams, the
control routes and the junction list therefore come from the SAME OSM snapshot build_region.py uses.
Tile ids follow the owner's research pack research/mistral-s8-loop-s23 (tiles.json; its bboxes were checked against
the lattice here: test_s8_loop.py).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from shapely.geometry import LineString, Point, box

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import regions  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
ADR = "0288"
PLAN = REPO / "docs" / "reports" / "map" / "s8_loop_plan.json"
PNG = REPO / "docs" / "reports" / "map" / "s8_loop_plan.png"
REG = REPO / "Data" / "Regions"
C = regions.REGIONS["bialystok-industrial-c"]
X0, Y0, T = C.bbox[0], C.bbox[1], regions.TILE_SIZE_M
# = osm_extract.BBOX_WGS84 of branch world2-s23 (same cache key there); covers every tile of the loop + one tile margin
LOOP_BBOX_WGS84 = (22.60, 53.05, 23.32, 53.50)
MAJOR = ("motorway", "trunk", "primary", "secondary", "tertiary", "motorway_link", "trunk_link", "primary_link",
         "secondary_link", "tertiary_link")

# driving order: (id, lattice i, j)
TILES: list[tuple[str, int, int]] = [
    ("s8-01", -5, 0), ("s8-02", -6, 0), ("s8-03", -7, 0), ("s8-04", -8, 0), ("s8-05", -9, 0),
    ("s8-06", -9, -1), ("s8-07", -10, -1), ("s8-08", -11, -1), ("s8-09", -12, -1),
    ("s8-10", -12, -2), ("s8-11", -13, -2), ("s8-12", -14, -2),
    ("dw671-jezewo-01", -13, -1), ("dw671-jezewo-02", -13, 0), ("dw671-jezewo-03", -13, 1),
]
BUILD_FIRST = 5
# neighbours outside the loop: built tiles (regions.py) + the ring of ADR 0231 (PR #115, not in main: lattice only)
RING_0231 = {"tykocin": (-13, 2), "dw671-tykocin-09": (-13, 3)}
# control route of each tile: entry edge / exit edge + route ref of the exit; chained = entry is the exit point of the
# previous tile. s8-12 turns round at the Jezewo junction (S8 in, DW671 out); the DW671 tiles restart from the S8 tiles.
THROUGH: dict[str, dict] = {
    "s8-01": {"entry": ("E", "dk65-01"), "exit": ("W", "s8-02"), "refs": ["S8"], "chained": False},
    "s8-02": {"entry": ("E", "s8-01"), "exit": ("W", "s8-03"), "refs": ["S8"], "chained": True},
    "s8-03": {"entry": ("E", "s8-02"), "exit": ("W", "s8-04"), "refs": ["S8"], "chained": True},
    "s8-04": {"entry": ("E", "s8-03"), "exit": ("W", "s8-05"), "refs": ["S8"], "chained": True},
    "s8-05": {"entry": ("E", "s8-04"), "exit": ("S", "s8-06"), "refs": ["S8"], "chained": True},
    "s8-06": {"entry": ("N", "s8-05"), "exit": ("W", "s8-07"), "refs": ["S8"], "chained": True},
    "s8-07": {"entry": ("E", "s8-06"), "exit": ("W", "s8-08"), "refs": ["S8"], "chained": True},
    "s8-08": {"entry": ("E", "s8-07"), "exit": ("W", "s8-09"), "refs": ["S8"], "chained": True},
    "s8-09": {"entry": ("E", "s8-08"), "exit": ("S", "s8-10"), "refs": ["S8"], "chained": True},
    "s8-10": {"entry": ("N", "s8-09"), "exit": ("W", "s8-11"), "refs": ["S8"], "chained": True},
    "s8-11": {"entry": ("E", "s8-10"), "exit": ("W", "s8-12"), "refs": ["S8"], "chained": True},
    "s8-12": {"entry": ("E", "s8-11"), "exit": ("E", "s8-11"), "refs": ["671"], "chained": False,
              "entry_highway": "motorway_link"},   # the westbound off-ramp leaves the S8 already in s8-11
    "dw671-jezewo-01": {"entry": ("S", "s8-11"), "exit": ("N", "dw671-jezewo-02"), "refs": ["671"], "chained": False},
    "dw671-jezewo-02": {"entry": ("S", "dw671-jezewo-01"), "exit": ("N", "dw671-jezewo-03"), "refs": ["671"], "chained": True},
    "dw671-jezewo-03": {"entry": ("S", "dw671-jezewo-02"), "exit": ("N", "tykocin"), "refs": ["671"], "chained": True},
}
TITLES = {
    "s8-01": "S8 pętla 01 — węzeł Choroszcz, od szwu z dk65-01 na zachód (strefa przemysłowa przy Białymstoku)",
    "s8-02": "S8 pętla 02 — od węzła Choroszcz w stronę Złotorii",
    "s8-03": "S8 pętla 03 — węzeł Tykocin (Złotoria) i MOP Złotoria",
    "s8-04": "S8 pętla 04 — od węzła Tykocin w stronę Rzędzian (Babino)",
    "s8-05": "S8 pętla 05 — narożnik kafla, S8 skręca na południowy zachód",
    "s8-06": "S8 pętla 06 — S8 ku węzłowi Rzędziany",
    "s8-07": "S8 pętla 07 — węzeł Rzędziany",
    "s8-08": "S8 pętla 08 — od Rzędzian ku Jeżewu",
    "s8-09": "S8 pętla 09 — MOP Radule",
    "s8-10": "S8 pętla 10 — S8 ku węzłowi Jeżewo",
    "s8-11": "S8 pętla 11 — węzeł Jeżewo, strona wschodnia (S8 + DW671)",
    "s8-12": "S8 pętla 12 — węzeł Jeżewo (S8 / DK64 / DW671), Jeżewo Stare — zawrotka pętli na DW671",
    "dw671-jezewo-01": "DW671 Jeżewo–Tykocin 01 — od węzła Jeżewo na północ",
    "dw671-jezewo-02": "DW671 Jeżewo–Tykocin 02 — odcinek środkowy",
    "dw671-jezewo-03": "DW671 Jeżewo–Tykocin 03 — do szwu z kaflem tykocin (pierścień ADR 0231)",
}


def tile_bbox(i: int, j: int) -> tuple[float, float, float, float]:
    return (X0 + T * i, Y0 + T * j, X0 + T * (i + 1), Y0 + T * (j + 1))


def dump(obj) -> str:
    return json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def lattice_of_regions() -> dict[str, tuple[int, int]]:
    """Every regions.py tile that sits on the lattice (the loop tiles excluded) + the ring tiles next to the loop."""
    own = {t[0] for t in TILES}
    out = {}
    for rid, r in regions.REGIONS.items():
        if rid in own:
            continue
        i, j = (r.bbox[0] - X0) / T, (r.bbox[1] - Y0) / T
        if i == int(i) and j == int(j) and r.width == T and r.height == T:
            out[rid] = (int(i), int(j))
    for rid, ij in RING_0231.items():
        out.setdefault(rid, ij)
    return out


def load_osm() -> tuple[dict, dict, list[dict]]:
    """(extract in the map_plan_0278 form, {way id: LineString EPSG:2180}, motorway_junction nodes) from the pinned pbf."""
    import osm_extract as oe
    oe.BBOX_WGS84 = LOOP_BBOX_WGS84
    layers = oe.load_layers()
    area = box(X0 + T * -15, Y0 + T * -3, X0 + T * -3, Y0 + T * 3)
    roads = layers["roads"]
    roads = roads[roads["highway"].isin(MAJOR) & roads.intersects(area)]
    ways, L = [], {}
    keep = ("highway", "ref", "name", "oneway", "junction", "lanes", "maxspeed", "bridge", "tunnel", "layer")
    for r in roads.itertuples():
        tags = {k: getattr(r, k) for k in keep if isinstance(getattr(r, k, None), str)}
        ways.append({"id": int(r.osm_id), "tags": tags})
        L[int(r.osm_id)] = r.geometry
    ways.sort(key=lambda w: w["id"])
    pts = layers["points"]
    pts = pts[(pts["kind"] == "highway=motorway_junction") & pts.intersects(area)]
    junctions = [{"osm_node": int(p.osm_id), "name": p.name if isinstance(p.name, str) else None,
                  "ref": p.ref if isinstance(p.ref, str) else None,
                  "x": round(p.geometry.x, 1), "y": round(p.geometry.y, 1)} for p in pts.itertuples()]
    junctions.sort(key=lambda d: d["osm_node"])
    return {"ways": ways}, L, junctions


def build_plan() -> dict:
    import map_plan_0278 as mp
    import powiaty
    extract, L, junctions = load_osm()
    tags = {w["id"]: w["tags"] for w in extract["ways"]}
    others = lattice_of_regions()
    by_ij = {(i, j): tid for tid, i, j in TILES}
    by_ij_other = {ij: rid for rid, ij in others.items()}
    step = {"W": (-1, 0), "E": (1, 0), "S": (0, -1), "N": (0, 1)}
    tiles, prev = [], None
    for n, (tid, i, j) in enumerate(TILES, start=1):
        bb = tile_bbox(i, j)
        b = box(*bb)
        shares = powiaty.powiat_shares(bb)
        km = {}
        for w in extract["ways"]:
            ln = L[w["id"]]
            if ln.intersects(b):
                k = w["tags"]["highway"]
                km[k] = km.get(k, 0.0) + ln.intersection(b).length / 1000.0
        seams = {}
        for e, (di, dj) in step.items():
            nb = by_ij.get((i + di, j + dj)) or by_ij_other.get((i + di, j + dj))
            cr = mp.edge_crossings(extract, L, bb, e)
            if nb is None and not cr:
                continue
            row = {"neighbour": nb, "neighbour_status": ("loop" if (i + di, j + dj) in by_ij else
                                                           "ring-0231 (PR #115)" if nb in RING_0231 else
                                                           "built" if nb else "none (open edge)"),
                   "crossings": cr}
            if nb and nb in regions.REGIONS and nb not in {t[0] for t in TILES}:
                gc = mp.graph_crossings(nb, mp.OPPOSITE[e])
                if gc is not None:
                    major = [g for g in gc if g["highway"] in MAJOR]
                    row["built_graph_crossings"] = major
                    row["max_offset_m"] = max(
                        (min((abs(c["x"] - g["x"]) + abs(c["y"] - g["y"]) for g in major if g["osm_way"] == c["osm_way"]),
                             default=None) or 0.0 for c in cr), default=0.0)
                    row["ways_missing_in_built_graph"] = sorted({c["osm_way"] for c in cr} - {g["osm_way"] for g in major})
            seams[e] = row
        spec = dict(THROUGH[tid])
        if "entry_highway" in spec:
            spec["entry_ways"] = [c["osm_way"] for c in mp.edge_crossings(extract, L, bb, spec["entry"][0])
                                  if c["highway"] == spec["entry_highway"]]
        r = mp.through_route(extract, L, bb, spec, prev["exit"] if (prev and spec["chained"]) else None)
        if not r["found"]:
            raise SystemExit(f"{tid}: no through route {spec}: {dump(r)}")
        prev = r
        tiles.append({
            "n": n, "id": tid, "ij": [i, j], "bbox": list(bb), "origin": [(bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2],
            "build_now": n <= BUILD_FIRST, "title": TITLES[tid],
            "teryt_powiat": next(iter(shares)), "teryt_powiat_extra": list(shares)[1:],
            "powiat_shares": {k: round(v, 4) for k, v in shares.items()},
            "km_major": {k: round(v, 2) for k, v in sorted(km.items())},
            "motorway_junctions": [q for q in junctions if b.contains(Point(q["x"], q["y"]))],
            "bridges": sorted(w["id"] for w in extract["ways"]
                              if w["tags"].get("bridge") not in (None, "no") and L[w["id"]].intersects(b)),
            "seams": seams,
            "through": {k: r[k] for k in ("entry", "exit", "length_m", "ways", "from", "to", "edge_in", "edge_out")},
            "through_tags": {str(w): tags[w] for w in r["ways"]},
            "in_pipeline_osm_window": _in_pipeline_window(bb),
        })
    return {"adr": ADR, "crs": "EPSG:2180", "tile_size_m": T,
            "lattice": {"x0": X0, "y0": Y0, "rule": "x = x0 + 2048*i, y = y0 + 2048*j (ADR 0203)"},
            "osm": {"source": "Data/SourceManifests/osm-geofabrik-podlaskie.json (pinned pbf of the pipeline)",
                    "window_wgs84": list(LOOP_BBOX_WGS84)},
            "tiles": tiles, "loop_km_through": round(sum(t["through"]["length_m"] for t in tiles) / 1000.0, 2)}


def _in_pipeline_window(bb) -> bool:
    """Is the tile + 300 m context inside osm_extract.BBOX_WGS84 of THIS checkout (build_region can read its roads)?"""
    from pyproj import Transformer
    tr = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    w = (22.80, 53.05, 23.32, 53.38)
    pts = [tr.transform(x, y) for x in (bb[0] - 300, bb[2] + 300) for y in (bb[1] - 300, bb[3] + 300)]
    return all(w[0] <= lo <= w[2] and w[1] <= la <= w[3] for lo, la in pts)


# ---------------------------------------------------------------------------------------------- authored files
def overrides_yaml(t: dict) -> str:
    ox, oy = t["origin"]
    return (f"# Authored overrides of region {t['id']} (ADR {ADR}, owner D82/D63: drivable first).\n"
            f"# Every entry survives a re-import; coordinates are region-local E/N (origin EPSG:2180 {ox:.0f}, {oy:.0f})\n"
            f"# or EPSG:2180 where the key says so.\n"
            f"overrides: []\n")


def route_endpoints(t: dict) -> str:
    r = t["through"]
    a, b = r["entry"], r["exit"]
    return json.dumps({
        "provenance": f"authored_override (ADR {ADR}): control route for cameras/QA = the through road of this tile in the driving direction of the loop",
        "description": (f"From the {r['edge_in']} tile edge (seam with {r['from']}, OSM way {a['osm_way']}) to the {r['edge_out']} "
                        f"tile edge (OSM way {b['osm_way']}, ref {b['ref']}; seam with {r['to']}); {r['length_m']:.0f} m over the OSM ways "
                        f"{', '.join(str(w) for w in r['ways'])}. Points from the pinned pbf of the pipeline "
                        f"(tools/worldgen/qa/s8_loop_plan.py); build_world snaps them to the nearest graph node."),
        "start_epsg2180": [a["x"], a["y"]],
        "end_epsg2180": [b["x"], b["y"]],
        "confidence": "high (same OSM snapshot as build_region.py)",
    }, indent=1, ensure_ascii=False) + "\n"


def init_regions(plan: dict) -> list[str]:
    written = []
    for t in plan["tiles"]:
        d = REG / t["id"]
        d.mkdir(parents=True, exist_ok=True)
        for name, text in {"overrides.yaml": overrides_yaml(t), "route_endpoints.json": route_endpoints(t)}.items():
            if not (d / name).exists():                      # authored files: never overwritten
                (d / name).write_text(text, encoding="utf-8", newline="\n")
                written.append(f"{t['id']}/{name}")
    return written


def print_regions(plan: dict) -> str:
    out = []
    for t in plan["tiles"]:
        i, j = t["ij"]
        extra = ("\n        teryt_powiat_extra=(" + "".join(f'"{p}", ' for p in t["teryt_powiat_extra"]).rstrip() + "),"
                 if t["teryt_powiat_extra"] else "")
        out.append(f'''    "{t['id']}": Region(
        id="{t['id']}",
        title="{t['title']}",
        candidate="L_s8_loop",
        bbox=({t['bbox'][0]}, {t['bbox'][1]}, {t['bbox'][2]}, {t['bbox'][3]}),
        origin=({t['origin'][0]}, {t['origin'][1]}),
        teryt_powiat="{t['teryt_powiat']}",{extra}
        status="WORKING_ASSUMPTION (ADR {ADR}, owner D82/D63; tile = lattice ({i},{j}) of the ADR 0203 plan, loop tile {t['n']}/15)",
    ),''')
    return "\n".join(out)


# ---------------------------------------------------------------------------------------------- control render
def render(plan: dict, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    extract, L, junctions = load_osm()
    fig, ax = plt.subplots(figsize=(15, 8), dpi=110)
    col = {"motorway": "#c0392b", "motorway_link": "#e67e22", "trunk": "#8e44ad", "primary": "#8e44ad",
           "secondary": "#2471a3", "tertiary": "#7f8c8d"}
    for w in extract["ways"]:
        k = w["tags"]["highway"]
        x, y = L[w["id"]].xy
        ax.plot(x, y, color=col.get(k, col.get(k.split("_")[0], "#bbbbbb")), lw=1.6 if k.startswith("motorway") else 0.8, zorder=2)
    for rid, (i, j) in lattice_of_regions().items():
        bb = tile_bbox(i, j)
        if bb[2] < X0 + T * -15 or bb[0] > X0 + T * -3 or bb[1] > Y0 + T * 4 or bb[3] < Y0 + T * -3:
            continue
        ax.add_patch(plt.Rectangle((bb[0], bb[1]), T, T, fc="#e8e8e8", ec="#888888", lw=0.8, zorder=1))
        ax.text(bb[0] + 40, bb[1] + 60, rid, fontsize=6, color="#555555", zorder=4)
    for t in plan["tiles"]:
        bb = t["bbox"]
        ax.add_patch(plt.Rectangle((bb[0], bb[1]), T, T, fc="#f4a261" if t["build_now"] else "#ffe8c2", ec="#333333",
                                   lw=1.0, alpha=0.55, zorder=1))
        ax.text(bb[0] + 40, bb[3] - 190, f"{t['n']} {t['id']}", fontsize=7, weight="bold", zorder=5)
        a, b = t["through"]["entry"], t["through"]["exit"]
        ax.plot([a["x"]], [a["y"]], "o", ms=4, color="#1e8449", zorder=6)
        ax.plot([b["x"]], [b["y"]], "s", ms=4, color="#111111", zorder=6)
        for q in t["motorway_junctions"]:
            ax.plot([q["x"]], [q["y"]], "^", ms=6, color="#c0392b", mec="white", zorder=7)
    ax.set_xlim(X0 + T * -15, X0 + T * -3)
    ax.set_ylim(Y0 + T * -3, Y0 + T * 4)
    ax.set_aspect("equal")
    ax.set_title(f"ADR {ADR} / D82: pętla S8 - DW671 - Tykocin, 15 kafli (ciemniejsze = budowane teraz); trójkąt = motorway_junction (OSM), "
                 f"zielone kółko = wjazd trasy kontrolnej, kwadrat = wyjazd", fontsize=8)
    ax.tick_params(labelsize=6)
    fig.tight_layout()
    fig.savefig(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--png", action="store_true")
    ap.add_argument("--print-regions", action="store_true")
    ap.add_argument("--init-regions", action="store_true")
    a = ap.parse_args()
    plan = build_plan()
    PLAN.write_text(dump(plan), encoding="utf-8", newline="\n")
    if a.print_regions:
        print(print_regions(plan))
        return
    if a.init_regions:
        print("\n".join(init_regions(plan)))
    if a.png:
        render(plan, PNG)
    for t in plan["tiles"]:
        print(f"{t['n']:2d} {t['id']:16s} {tuple(t['ij'])} {t['teryt_powiat']}+{t['teryt_powiat_extra']} "
              f"{t['through']['edge_in']}->{t['through']['edge_out']} {t['through']['length_m']:.0f} m "
              f"junctions {[q['name'] or q['ref'] for q in t['motorway_junctions']]} window {t['in_pipeline_osm_window']}")
    print("loop through km", plan["loop_km_through"])


if __name__ == "__main__":
    main()
