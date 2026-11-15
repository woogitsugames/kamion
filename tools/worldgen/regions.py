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
    # ADR 0166 (owner D60): Dojlidy/Krywlany. Tile on the 2048 m lattice anchored at tile C
    # (x = 776971 + 2048*i, y = 595199 + 2048*j); here i = +1, j = -3. Covers the SSSE Dojlidy/Krywlany
    # cluster (KAN, Rosti, Bravilor, Masterpress, Odlewnia, Bison, PSS Społem DC, BPN-T) on Kuronia /
    # Dywizjonu 303 and the east half of Krywlany aerodrome (both runways' 27 ends). Browar Dojlidy and
    # Biawar fall in lattice tile (+2,-3); aeroklub hangars + rondo Wünschego in (0,-3). See ADR 0166.
    "bialystok-dojlidy": Region(
        id="bialystok-dojlidy",
        title="Białystok — Dojlidy/Krywlany: Kuronia / Dywizjonu 303 / SSSE + lotnisko Krywlany (wsch.)",
        candidate="D_dojlidy_krywlany",
        bbox=(779019.0, 589055.0, 781067.0, 591103.0),
        origin=(780043.0, 590079.0),
        teryt_powiat="2061",
        status="WORKING_ASSUMPTION (ADR 0166, owner D60 chose the area; exact tile = agent proposal)",
    ),
    # ADR 0205 (owner D64): first DK65 corridor tile past the Białystok city limit, lattice (-4,0) of the
    # ADR 0203 plan (route variant A km 8.76-9.39: Szosa Knyszyńska clips the NE corner, 631 m). Powiat 2002.
    "dk65-01": Region(
        id="dk65-01",
        title="DK65 korytarz 01 — Szosa Knyszyńska za granicą Białegostoku (gm. Dobrzyniewo Duże)",
        candidate="F_dk65_corridor",
        bbox=(768779.0, 595199.0, 770827.0, 597247.0),
        origin=(769803.0, 596223.0),
        teryt_powiat="2002",
        status="WORKING_ASSUMPTION (ADR 0205, owner D64; tile = lattice (-4,0) of the ADR 0203 plan)",
    ),
    # ADR 0203 (owner D64): first Białystok tile on the truck route to Knyszyn, lattice i = -1, j = 0 (shares its
    # east edge x = 776971 with tile C). DK8/DK65 Gen. Maczka ("Trasa Generalska"), 2.05 km of dual carriageway
    # with grade-separated junctions. Route + tile plan: tools/worldgen/qa/dk65_route_plan.py,
    # docs/reports/map/dk65_route_plan.json. Next tiles (-2,0) bialystok-kleeberga, (-3,0) bialystok-knyszynska.
    "bialystok-maczka": Region(
        id="bialystok-maczka",
        title="Białystok — DK8/DK65 Gen. Maczka (Trasa Generalska), kafel na zachód od C w stronę Knyszyna",
        candidate="E_dk65_maczka",
        bbox=(774923.0, 595199.0, 776971.0, 597247.0),
        origin=(775947.0, 596223.0),
        teryt_powiat="2061",
        status="WORKING_ASSUMPTION (ADR 0203, owner D64 chose the direction; tile = lattice neighbour of C)",
    ),
    # ADR 0204 (owner D64): Knyszyn. Two tiles of the 2048 m lattice reserved by ADR 0203 (x = 776971 + 2048*i,
    # y = 595199 + 2048*j). `knyszyn` (i = -8, j = 8): the town - Rynek, DW671 Tykocka/Bialostocka, the DK65/DW671
    # roundabout (37 m inside the west edge). `knyszyn-s` (i = -8, j = 7): DK65 inlet from the corridor seam
    # (x = 762635) and the expressway construction zone (roundabout under construction at 762502, 609913).
    # Powiat moniecki 2008; the SE corner of knyszyn-s lies in powiat 2002 (see ADR 0204).
    "knyszyn": Region(
        id="knyszyn",
        title="Knyszyn — miasto: Rynek, DW671, rondo DK65/DW671",
        candidate="K_knyszyn",
        bbox=(760587.0, 611583.0, 762635.0, 613631.0),
        origin=(761611.0, 612607.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0204, owner D64; tile = lattice (-8,8) of the ADR 0203 plan)",
    ),
    "knyszyn-s": Region(
        id="knyszyn-s",
        title="Knyszyn — wlot DK65 od Białegostoku i strefa budowy ekspresówki",
        candidate="K_knyszyn_s",
        bbox=(760587.0, 609535.0, 762635.0, 611583.0),
        origin=(761611.0, 610559.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0204, owner D64; tile = lattice (-8,7) of the ADR 0203 plan)",
    ),
    # ADR 0207 (owner D64): DK65 corridor tile, lattice (-4,1) of the ADR 0203 plan, route variant A km 9.39-11.80. Powiat 2002.
    "dk65-02": Region(
        id="dk65-02",
        title="DK65 korytarz 02 — Szosa Knyszyńska / Ełcka przez Fasty (południe), most km 10,85 (gm. Dobrzyniewo Duże)",
        candidate="F_dk65_corridor",
        bbox=(768779.0, 597247.0, 770827.0, 599295.0),
        origin=(769803.0, 598271.0),
        teryt_powiat="2002",
        status="WORKING_ASSUMPTION (ADR 0207, owner D64; tile = lattice (-4,1) of the ADR 0203 plan)",
    ),
    # ADR 0207 (owner D64): DK65 corridor tile, lattice (-5,1) of the ADR 0203 plan, route variant A km 11.80-12.28. Powiat 2002.
    "dk65-03": Region(
        id="dk65-03",
        title="DK65 korytarz 03 — Ełcka na północ od Fast (gm. Dobrzyniewo Duże)",
        candidate="F_dk65_corridor",
        bbox=(766731.0, 597247.0, 768779.0, 599295.0),
        origin=(767755.0, 598271.0),
        teryt_powiat="2002",
        status="WORKING_ASSUMPTION (ADR 0207, owner D64; tile = lattice (-5,1) of the ADR 0203 plan)",
    ),
    # ADR 0207 (owner D64): DK65 corridor tile, lattice (-5,2) of the ADR 0203 plan, route variant A km 12.28-14.36. Powiat 2002.
    "dk65-04": Region(
        id="dk65-04",
        title="DK65 korytarz 04 — Ełcka przez Fasty (północ): Białostocka/Kościelna, Szkolna (gm. Dobrzyniewo Duże)",
        candidate="F_dk65_corridor",
        bbox=(766731.0, 599295.0, 768779.0, 601343.0),
        origin=(767755.0, 600319.0),
        teryt_powiat="2002",
        status="WORKING_ASSUMPTION (ADR 0207, owner D64; tile = lattice (-5,2) of the ADR 0203 plan)",
    ),
    # ADR 0207 (owner D64): DK65 corridor tile, lattice (-5,3) of the ADR 0203 plan, route variant A km 14.36-16.56. Powiat 2002.
    "dk65-05": Region(
        id="dk65-05",
        title="DK65 korytarz 05 — Ełcka/Studzienna przez Dobrzyniewo Duże (gm. Dobrzyniewo Duże)",
        candidate="F_dk65_corridor",
        bbox=(766731.0, 601343.0, 768779.0, 603391.0),
        origin=(767755.0, 602367.0),
        teryt_powiat="2002",
        status="WORKING_ASSUMPTION (ADR 0207, owner D64; tile = lattice (-5,3) of the ADR 0203 plan)",
    ),
    # ADR 0206 (owner D64): second Białystok tile on the truck route to Knyszyn, lattice i = -2, j = 0 (shares its
    # east edge x = 774923 with bialystok-maczka). DK8/DK65: west end of Gen. Maczka, Gen. Kleeberga with the
    # interchange towards rondo Pamięci Męczeństwa Kresowian (km 3.58-5.80 of route variant A, ADR 0203 plan).
    "bialystok-kleeberga": Region(
        id="bialystok-kleeberga",
        title="Białystok — DK8/DK65 Gen. Maczka (zachód) i Gen. Kleeberga, kafel -2,0 w stronę Knyszyna",
        candidate="E_dk65_kleeberga",
        bbox=(772875.0, 595199.0, 774923.0, 597247.0),
        origin=(773899.0, 596223.0),
        teryt_powiat="2061",
        status="WORKING_ASSUMPTION (ADR 0206, tile id/bbox reserved by the ADR 0203 plan, lattice -2,0)",
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
