"""Region registry for TRUCK SIM PL worldgen.

A region is a rectangular tile in EPSG:2180 (PL-1992; x = easting, y = northing, metres). Everything
downstream (ingest, build, QA, tests) reads the bbox from here, so switching the start area from
candidate C to A or B means adding one entry and re-running two commands.

How the C tile was chosen (reproducible: `uv run tools/worldgen/regions.py --derive C_andersa_putry`):
  1. Route = shortest truck path through the candidate waypoints of `analyze_candidates.py`
     (Kwadrat Park gate -> Rondo Bieżeństwa -> Andersa -> Rondo Putry -> Al. Tysiąclecia / DK8+DK19).
     Route bounds: x 777258.6..778732.0, y 595528.7..596917.3 (1473 x 1389 m).
  2. Tile = 2048 x 2048 m square centred on the route bounds (centre rounded to 1 m).
     2048 m at 1 m spacing = 2049 height samples per side = a valid Unity terrain heightmap resolution
     (2^n + 1). Resulting margin around the route: >= 287 m east/west, >= 330 m north/south
     (task asked for ~300 m; 287 m is the price of the power-of-two tile, accepted).
  3. Floating-origin anchor (ADR 0003) = tile centre, integer metres.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    id: str
    title: str
    candidate: str                          # id in analyze_candidates.CANDIDATES
    bbox: tuple[float, float, float, float]  # EPSG:2180 xmin, ymin, xmax, ymax
    origin: tuple[float, float]             # floating-origin anchor, EPSG:2180
    teryt_powiat: str                       # GUGiK per-powiat datasets (BDOT10k, LoD1/2, trees)
    status: str
    min_route_margin_m: float = 280.0

    @property
    def width(self) -> float:
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> float:
        return self.bbox[3] - self.bbox[1]


REGIONS: dict[str, Region] = {
    "bialystok-industrial-c": Region(
        id="bialystok-industrial-c",
        title="Białystok — Kwadrat Park / Andersa / Rondo Putry → DK8/DK19 (kandydat C)",
        candidate="C_andersa_putry",
        bbox=(776971.0, 595199.0, 779019.0, 597247.0),
        origin=(777995.0, 596223.0),
        teryt_powiat="2061",
        status="WORKING_ASSUMPTION (lead), owner decision on D4 pending — see docs/map-decisions.md",
    ),
}

TILE_SIZE_M = 2048.0
WORK_CRS = "EPSG:2180"
# Compound horizontal + vertical CRS of GUGiK NMT/NMPT/LiDAR (PL-1992 + PL-EVRF2007-NH).
HEIGHT_CRS = "EPSG:9651"   # EVRF2007-PL height (= GUGiK "PL-EVRF2007-NH")
COMPOUND_CRS = "EPSG:2180+9651"  # no single EPSG code exists for CS92 + EVRF2007-PL (checked in PROJ db)


def get(region_id: str) -> Region:
    try:
        return REGIONS[region_id]
    except KeyError:
        raise SystemExit(f"unknown region {region_id!r}; known: {', '.join(REGIONS)}") from None


def derive_tile(route_bounds: tuple[float, float, float, float], size: float = TILE_SIZE_M):
    """Square tile of `size` metres centred on route bounds; returns (bbox, origin)."""
    x0, y0, x1, y1 = route_bounds
    cx, cy = round((x0 + x1) / 2), round((y0 + y1) / 2)
    h = size / 2
    return (cx - h, cy - h, cx + h, cy + h), (float(cx), float(cy))


def route_for(region: Region):
    """Recompute the candidate route (OSM graph). Returns (node_path, coords, graph)."""
    import analyze_candidates as ac
    import osm_extract as oe
    layers = oe.load_layers()
    g, coords, snap = ac.build_graph(layers["roads"])
    cand = next(c for c in ac.CANDIDATES if c["id"] == region.candidate)
    path = ac.route_through(g, coords, snap, cand["waypoints"])
    return path, coords, g


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--derive", metavar="REGION_ID", help="recompute tile bbox from the route")
    a = ap.parse_args()
    if a.derive:
        r = get(a.derive)
        path, coords, _ = route_for(r)
        xs = [coords[n][0] for n in path]
        ys = [coords[n][1] for n in path]
        rb = (min(xs), min(ys), max(xs), max(ys))
        bbox, origin = derive_tile(rb)
        print("route bounds", [round(v, 1) for v in rb])
        print("tile bbox", bbox, "origin", origin, "registered", r.bbox, r.origin)
        print("margins W/S/E/N", [round(v, 1) for v in (rb[0] - bbox[0], rb[1] - bbox[1], bbox[2] - rb[2], bbox[3] - rb[3])])
    else:
        for r in REGIONS.values():
            print(r.id, r.bbox, r.origin, r.status)


if __name__ == "__main__":
    main()
