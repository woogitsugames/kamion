"""Tile adjacency graph for additive streaming of region scenes (ADR 0235).

    uv run --project tools/worldgen python tools/worldgen/streaming/tile_graph.py           # rewrite the graph
    uv run --project tools/worldgen python tools/worldgen/streaming/tile_graph.py --check   # exit 1 when stale

Input (all in git, no Data/raw):
  - Data/Regions/<id>/region.yaml       bbox (EPSG:2180) and the floating-origin anchor (origin x / y / z)
  - Data/Regions/<id>/route_endpoints.json  route entry / exit points snapped to the tile edge (ADR 0203-0214)
Output:
  game/Assets/_Project/World/Runtime/Streaming/Resources/WorldStreaming/tile_graph.json
  (Resources, read at run time by Game.World.Streaming.TileGraph through JsonUtility: arrays of objects only).

Adjacency = two tile rectangles that touch (shared edge longer than 1 m: side N/E/S/W; a shared corner only:
NE/NW/SE/SW). A portal is a route exit of tile A that is the route entry of tile B on their shared edge (<= PORTAL_TOL_M = 2 m).
Corridors are the chains of portals (the D67 corridor Bialystok C -> DK65 -> Knyszyn).

worldMemoryMB: WORLD_MEMORY Low of the import of each region, as cited in ADR 0229 (table "Szacunek rozmiaru APK i
pamieci", sources ADR 0188 / 0203 / 0205-0214). ESTIMATED: values from different days; a regeneration can change them.
The run-time streamer uses them only to keep the sum of loaded tiles under the tier budget (WORKING_VALUE).
worldMemoryHighMB (ADR 0273): WORLD_MEMORY High of the same imports, as tabulated in ADR 0234 §7 (sources: the region
ADRs 0188 / 0204-0214; the pack estimator script stays on branch regionpacks-0234); used when the High content tier streams (PC High/Ultra).
Standard library + PyYAML (worldgen project).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
REGIONS = REPO / "Data" / "Regions"
OUT = REPO / "game" / "Assets" / "_Project" / "World" / "Runtime" / "Streaming" / "Resources" / "WorldStreaming" / "tile_graph.json"
SCHEMA = "truck-sim-pl/tile-graph/1"
PORTAL_TOL_M = 2.0   # route_endpoints of neighbours are snapped separately (dk65-02/03: 1.0 m apart); WORKING_VALUE
MIN_SEAM_M = 1.0

# WORLD_MEMORY Low [MB] per region, quoted by ADR 0229 (ESTIMATED; see module docstring).
WORLD_MEMORY_LOW_MB = {
    "bialystok-industrial-c": (124.2, "ADR 0188 via ADR 0229"),
    "bialystok-dojlidy": (99.6, "ADR 0188 via ADR 0229"),
    "bialystok-maczka": (153.2, "ADR 0203/0208 via ADR 0229"),
    "bialystok-kleeberga": (156.7, "ADR 0206 via ADR 0229"),
    "bialystok-knyszynska": (116.0, "ADR 0208 via ADR 0229"),
    "dk65-01": (68.2, "ADR 0205 via ADR 0229"),
    "dk65-02": (60.2, "ADR 0210 via ADR 0229"),
    "dk65-03": (50.5, "ADR 0207 via ADR 0229"),
    "dk65-04": (76.1, "ADR 0207 via ADR 0229"),
    "dk65-05": (75.5, "ADR 0207 via ADR 0229"),
    "dk65-06": (59.0, "ADR 0214 via ADR 0229"),
    "dk65-07": (59.1, "ADR 0214 via ADR 0229"),
    "dk65-08": (55.5, "ADR 0214 via ADR 0229"),
    "dk65-09": (51.4, "ADR 0214 via ADR 0229"),
    "dk65-10": (49.0, "ADR 0214 via ADR 0229"),
    "dk65-11": (48.2, "ADR 0214 via ADR 0229"),
    "knyszyn-s": (40.8, "ADR 0212 via ADR 0229"),
    "knyszyn": (95.5, "ADR 0212 via ADR 0229"),
    "knyszyn-w": (54.0, "ADR 0212 via ADR 0229"),
    "dk65-monki-01": (46.6, "ADR 0212 via ADR 0229"),
    "dw671-tykocin-01": (45.7, "ADR 0212 via ADR 0229"),
    "s8-01": (88.1, "ADR 0288: import Win64 2026-11-17 (WORLD_MEMORY)"),
    "s8-02": (62.4, "ADR 0288: import Win64 2026-11-17 (WORLD_MEMORY)"),
    "s8-03": (60.3, "ADR 0288: import Win64 2026-11-17 (WORLD_MEMORY)"),
    "s8-04": (55.8, "ADR 0288: import Win64 2026-11-17 (WORLD_MEMORY)"),
    "s8-05": (50.8, "ADR 0288: import Win64 2026-11-17 (WORLD_MEMORY)"),
    "dk65-monki-02": (55.1, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dk65-monki-03": (40.3, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dk65-monki-04": (47.6, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dk65-monki-05": (46.4, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dk65-monki-06": (47.8, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dk65-monki-07": (71.8, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "monki-e": (109.9, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "monki": (104.7, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dw671-tykocin-02": (55.1, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dw671-tykocin-03": (69.0, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dw671-tykocin-04": (50.0, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dw671-tykocin-05": (40.1, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dw671-tykocin-06": (47.5, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dw671-tykocin-07": (52.5, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dw671-tykocin-08": (43.1, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dw671-tykocin-09": (53.4, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "tykocin": (79.4, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dw671-jasionowka-01": (48.7, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
}
# WORLD_MEMORY High [MB] per region, ADR 0234 §7 table (ESTIMATED; same imports as the Low values above).
WORLD_MEMORY_HIGH_MB = {
    "bialystok-industrial-c": (267.0, "ADR 0188 via ADR 0234"),
    "bialystok-dojlidy": (214.9, "ADR 0188 via ADR 0234"),
    "bialystok-maczka": (420.4, "ADR 0208 via ADR 0234"),
    "bialystok-kleeberga": (356.8, "ADR 0206 via ADR 0234"),
    "bialystok-knyszynska": (260.2, "ADR 0208 via ADR 0234"),
    "dk65-01": (165.9, "ADR 0205 via ADR 0234"),
    "dk65-02": (139.3, "ADR 0210 via ADR 0234"),
    "dk65-03": (131.7, "ADR 0207 via ADR 0234"),
    "dk65-04": (181.5, "ADR 0207 via ADR 0234"),
    "dk65-05": (176.5, "ADR 0207 via ADR 0234"),
    "dk65-06": (136.1, "ADR 0214 via ADR 0234"),
    "dk65-07": (136.5, "ADR 0214 via ADR 0234"),
    "dk65-08": (122.7, "ADR 0214 via ADR 0234"),
    "dk65-09": (122.4, "ADR 0214 via ADR 0234"),
    "dk65-10": (117.3, "ADR 0214 via ADR 0234"),
    "dk65-11": (113.0, "ADR 0214 via ADR 0234"),
    "knyszyn-s": (106.8, "ADR 0204 via ADR 0234"),
    "knyszyn": (216.7, "ADR 0204/0212 via ADR 0234"),
    "knyszyn-w": (129.2, "ADR 0209 via ADR 0234"),
    "dk65-monki-01": (113.6, "ADR 0212 via ADR 0234"),
    "dw671-tykocin-01": (119.4, "ADR 0212 via ADR 0234"),
    "s8-01": (185.2, "ADR 0288: import Win64 2026-11-17 (WORLD_MEMORY)"),
    "s8-02": (154.0, "ADR 0288: import Win64 2026-11-17 (WORLD_MEMORY)"),
    "s8-03": (144.3, "ADR 0288: import Win64 2026-11-17 (WORLD_MEMORY)"),
    "s8-04": (132.5, "ADR 0288: import Win64 2026-11-17 (WORLD_MEMORY)"),
    "s8-05": (130.8, "ADR 0288: import Win64 2026-11-17 (WORLD_MEMORY)"),
    "dk65-monki-02": (123.3, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dk65-monki-03": (107.7, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dk65-monki-04": (117.2, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dk65-monki-05": (123.5, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dk65-monki-06": (123.7, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dk65-monki-07": (168.1, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "monki-e": (278.8, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "monki": (225.0, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dw671-tykocin-02": (151.2, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dw671-tykocin-03": (153.9, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dw671-tykocin-04": (126.4, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dw671-tykocin-05": (108.6, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dw671-tykocin-06": (118.7, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dw671-tykocin-07": (121.5, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dw671-tykocin-08": (108.9, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dw671-tykocin-09": (123.9, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "tykocin": (171.7, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
    "dw671-jasionowka-01": (121.3, "ADR 0231 ring, import world2-finish r3 2026-11-17 (Win64)"),
}
UNKNOWN_MEMORY_MB = 160.0   # a region without a measurement counts as the heaviest measured one (conservative)
UNKNOWN_MEMORY_HIGH_MB = 420.4   # same rule for High: the heaviest measured High import (Maczka)


def load_tiles(regions_dir: Path = REGIONS) -> list[dict]:
    tiles = []
    for ry in sorted(regions_dir.glob("*/region.yaml")):
        d = yaml.safe_load(ry.read_text(encoding="utf-8"))
        b, o = d["bbox"], d["origin"]
        rid = d["id"]
        mem, src = WORLD_MEMORY_LOW_MB.get(rid, (UNKNOWN_MEMORY_MB, "UNKNOWN: conservative default"))
        mem_high, _ = WORLD_MEMORY_HIGH_MB.get(rid, (UNKNOWN_MEMORY_HIGH_MB, "UNKNOWN"))
        t = {
            "id": rid,
            "xmin": float(b["xmin"]), "ymin": float(b["ymin"]), "xmax": float(b["xmax"]), "ymax": float(b["ymax"]),
            "anchorX": float(o["x"]), "anchorY": float(o["y"]), "anchorZ": float(o["z"]),
            "worldMemoryMB": mem, "worldMemoryHighMB": mem_high, "memorySource": src,
            "routeEntry": None, "routeExit": None,
        }
        ep = ry.parent / "route_endpoints.json"
        if ep.exists():
            e = json.loads(ep.read_text(encoding="utf-8"))
            if e.get("start_epsg2180") and e.get("end_epsg2180"):
                t["routeEntry"] = [float(v) for v in e["start_epsg2180"]]
                t["routeExit"] = [float(v) for v in e["end_epsg2180"]]
        tiles.append(t)
    return tiles


def side_of(a: dict, b: dict, eps: float = 0.01) -> tuple[str | None, float]:
    """Side of tile a on which b touches it and the length of the shared edge (0 for a corner); (None, 0) = apart."""
    ox = min(a["xmax"], b["xmax"]) - max(a["xmin"], b["xmin"])
    oy = min(a["ymax"], b["ymax"]) - max(a["ymin"], b["ymin"])
    if ox < -eps or oy < -eps:
        return None, 0.0
    if ox > eps and oy > eps:
        raise ValueError(f"tiles {a['id']} and {b['id']} overlap ({ox:.1f} x {oy:.1f} m)")
    north = abs(b["ymin"] - a["ymax"]) <= eps
    south = abs(b["ymax"] - a["ymin"]) <= eps
    east = abs(b["xmin"] - a["xmax"]) <= eps
    west = abs(b["xmax"] - a["xmin"]) <= eps
    if (north or south) and ox >= MIN_SEAM_M:
        return ("N" if north else "S"), ox
    if (east or west) and oy >= MIN_SEAM_M:
        return ("E" if east else "W"), oy
    ns = "N" if north else "S" if south else ""
    ew = "E" if east else "W" if west else ""
    if ns and ew:
        return ns + ew, 0.0
    return None, 0.0


def on_seam(p: list[float], a: dict, side: str, eps: float = PORTAL_TOL_M) -> bool:
    x, y = p
    if side == "N":
        return abs(y - a["ymax"]) <= eps and a["xmin"] - eps <= x <= a["xmax"] + eps
    if side == "S":
        return abs(y - a["ymin"]) <= eps and a["xmin"] - eps <= x <= a["xmax"] + eps
    if side == "E":
        return abs(x - a["xmax"]) <= eps and a["ymin"] - eps <= y <= a["ymax"] + eps
    if side == "W":
        return abs(x - a["xmin"]) <= eps and a["ymin"] - eps <= y <= a["ymax"] + eps
    return False


def build(regions_dir: Path = REGIONS) -> dict:
    tiles = load_tiles(regions_dir)
    by_id = {t["id"]: t for t in tiles}
    for t in tiles:
        t["neighbors"] = []
    for i, a in enumerate(tiles):
        for b in tiles[i + 1:]:
            s, length = side_of(a, b)
            if s is None:
                continue
            a["neighbors"].append({"id": b["id"], "side": s, "seamM": round(length, 3)})
            s2, _ = side_of(b, a)
            b["neighbors"].append({"id": a["id"], "side": s2, "seamM": round(length, 3)})
    portals = []
    for a in tiles:
        if a["routeExit"] is None:
            continue
        for n in a["neighbors"]:
            if len(n["side"]) != 1:
                continue
            b = by_id[n["id"]]
            if not on_seam(a["routeExit"], a, n["side"]):
                continue
            if b["routeEntry"] is None:
                continue
            dx = a["routeExit"][0] - b["routeEntry"][0]
            dy = a["routeExit"][1] - b["routeEntry"][1]
            gap = (dx * dx + dy * dy) ** 0.5
            if gap <= PORTAL_TOL_M:
                portals.append({"from": a["id"], "to": b["id"], "side": n["side"],
                                "x": round(a["routeExit"][0], 3), "y": round(a["routeExit"][1], 3), "gapM": round(gap, 3)})
    # A tile without its own route_endpoints (region C, the first imported region) is the start of a chain when a
    # neighbour's route entry lies on their shared edge.
    for b in tiles:
        if b["routeEntry"] is None or any(p["to"] == b["id"] for p in portals):
            continue
        for n in b["neighbors"]:
            a = by_id[n["id"]]
            if a["routeExit"] is not None or len(n["side"]) != 1:
                continue
            if on_seam(b["routeEntry"], b, n["side"]):
                opposite = {"N": "S", "S": "N", "E": "W", "W": "E"}[n["side"]]
                portals.append({"from": a["id"], "to": b["id"], "side": opposite,
                                "x": round(b["routeEntry"][0], 3), "y": round(b["routeEntry"][1], 3), "gapM": 0.0})
    # Corridors: maximal chains of portals.
    nxt = {}
    has_prev = set()
    for p in portals:
        if p["from"] in nxt:
            raise ValueError(f"tile {p['from']} has two route exits ({nxt[p['from']]}, {p['to']})")
        nxt[p["from"]] = p["to"]
        has_prev.add(p["to"])
    corridors = []
    for start in sorted(set(nxt) - has_prev):
        chain = [start]
        while chain[-1] in nxt and nxt[chain[-1]] not in chain:
            chain.append(nxt[chain[-1]])
        corridors.append({"id": f"{chain[0]}..{chain[-1]}", "tiles": chain})
    out_tiles = []
    for t in tiles:
        out_tiles.append({k: t[k] for k in ("id", "xmin", "ymin", "xmax", "ymax", "anchorX", "anchorY", "anchorZ",
                                             "worldMemoryMB", "worldMemoryHighMB", "memorySource")} |
                         {"neighbors": sorted(t["neighbors"], key=lambda n: (len(n["side"]), n["side"], n["id"]))})
    return {
        "schema": SCHEMA,
        "generator": "tools/worldgen/streaming/tile_graph.py (ADR 0235)",
        "crs": "EPSG:2180 (x east, y north) + PL-EVRF2007-NH heights; Unity X = east, Z = north (ADR 0003)",
        "memoryNote": "worldMemoryMB / worldMemoryHighMB = WORLD_MEMORY Low / High of the region import as quoted in "
                      "ADR 0229 / ADR 0234 §7; ESTIMATED",
        "tiles": out_tiles,
        "portals": portals,
        "corridors": corridors,
    }


def dumps(graph: dict) -> str:
    return json.dumps(graph, ensure_ascii=False, indent=1) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 when the committed graph differs from the data")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    text = dumps(build())
    if a.check:
        cur = a.out.read_text(encoding="utf-8") if a.out.exists() else ""
        if cur != text:
            print(f"STALE: {a.out} differs from Data/Regions (run without --check)")
            return 1
        print(f"OK: {a.out}")
        return 0
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(text, encoding="utf-8", newline="\n")
    g = json.loads(text)
    print(f"tiles {len(g['tiles'])}, portals {len(g['portals'])}, corridors {[c['id'] for c in g['corridors']]} -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
