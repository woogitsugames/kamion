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
    # ADR 0208: a tile across a powiat boundary (bialystok-knyszynska: city 2061 + powiat 2002) reads the BDOT10k /
    # LoD1 / LoD2 of every listed powiat; () = single-powiat region, outputs byte-identical to before the field.
    teryt_powiat_extra: tuple[str, ...] = ()
    water: bool = False                     # ADR 0210: surface-water stage (rivers, ponds) opt-in per region
    rail: bool = False                      # ADR 0217: railway track bed + level crossings, opt-in per region

    @property
    def powiaty(self) -> tuple[str, ...]:
        return (self.teryt_powiat,) + tuple(self.teryt_powiat_extra)

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
    # ADR 0208 (owner D64): third Białystok tile on the truck route to Knyszyn, lattice (-3,0) of the ADR 0203 plan
    # (route variant A km 5.80-8.76: end of Kleeberga, slip road, rondo Pamięci Męczeństwa Kresowian, Szosa Ełcka,
    # city limit at 772066, Szosa Knyszyńska). Shares x = 772875 with bialystok-kleeberga (ADR 0206) and
    # x = 770827 with dk65-01 (ADR 0205). Two powiaty: Białystok 2061 + powiat białostocki 2002.
    "bialystok-knyszynska": Region(
        id="bialystok-knyszynska",
        title="Białystok — Kleeberga / rondo Pamięci Męczeństwa Kresowian / Szosa Ełcka → Szosa Knyszyńska (granica miasta)",
        candidate="F_dk65_corridor",
        bbox=(770827.0, 595199.0, 772875.0, 597247.0),
        origin=(771851.0, 596223.0),
        teryt_powiat="2061",
        teryt_powiat_extra=("2002",),
        status="WORKING_ASSUMPTION (ADR 0208, owner D64; tile = lattice (-3,0) of the ADR 0203 plan)",
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
    # ADR 0209 (owner D64): west part of Knyszyn, lattice (-9,8) (shares its east edge x = 760587 with `knyszyn`, 37 m
    # west of the DK65/DW671 roundabout). DK65 outlet towards Monki, DW671 towards Tykocin, west streets of the town.
    # 100 % powiat moniecki 2008 (OSM admin relations: gmina Knyszyn 97.6 %, gmina Krypno 2.4 %).
    "knyszyn-w": Region(
        id="knyszyn-w",
        title="Knyszyn — zachód: wylot DK65 na Mońki, DW671 na Tykocin",
        candidate="K_knyszyn_w",
        bbox=(758539.0, 611583.0, 760587.0, 613631.0),
        origin=(759563.0, 612607.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0209, owner D64; tile = lattice (-9,8) of the ADR 0203 plan)",
    ),
    # ADR 0212 (owner D64): lattice (-9,9), north of `knyszyn-w` (shared edge y = 613631): DK65 further towards Monki
    # through the fields NW of Knyszyn. Powiat moniecki 2008. NMT survey year pinned to 2022 (sources.authored.json)
    # like knyszyn-w, so the terrain of the shared edge comes from the same sheets.
    "dk65-monki-01": Region(
        id="dk65-monki-01",
        title="DK65 w stronę Moniek 01 — pola na północny zachód od Knyszyna",
        candidate="K_knyszyn_w",
        bbox=(758539.0, 613631.0, 760587.0, 615679.0),
        origin=(759563.0, 614655.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0212, owner D64; tile = lattice (-9,9) of the ADR 0203 plan)",
    ),
    # ADR 0212: lattice (-9,7), south of `knyszyn-w` (y = 611583) and west of `knyszyn-s` (x = 760587): DW671 Tykocka
    # from Knyszyn towards Tykocin. Powiat moniecki 2008. NMT pinned to 2022 like both neighbours.
    "dw671-tykocin-01": Region(
        id="dw671-tykocin-01",
        title="DW671 w stronę Tykocina 01 — na południowy zachód od Knyszyna",
        candidate="K_knyszyn_w",
        bbox=(758539.0, 609535.0, 760587.0, 611583.0),
        origin=(759563.0, 610559.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0212, owner D64; tile = lattice (-9,7) of the ADR 0203 plan)",
        rail=True,          # ADR 0217: line 38 + the DW671 level crossing (first and only region with the stage)
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
        water=True,      # ADR 0210: Supraśl + Biała under the DK65 bridge (km 10.85)
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
        water=True,      # ADR 0213: the Supraśl continues west of the dk65-02 confluence (level continuous at the seam)
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
    # ADR 0214 (owner D64/D65): DK65 corridor tile, lattice (-5,4) of the ADR 0203 plan, route variant A km 16.56-18.26
    # (old DK65, D65 p.4: no diversion, expressway sites beside the road). Powiat 2002.
    "dk65-06": Region(
        id="dk65-06",
        title="DK65 korytarz 06 — stara DK65, km 16,6–18,3",
        candidate="F_dk65_corridor",
        bbox=(766731.0, 603391.0, 768779.0, 605439.0),
        origin=(767755.0, 604415.0),
        teryt_powiat="2002",
        status="WORKING_ASSUMPTION (ADR 0214, owner D64/D65; tile = lattice (-5,4) of the ADR 0203 plan)",
    ),
    # ADR 0214 (owner D64/D65): DK65 corridor tile, lattice (-6,4) of the ADR 0203 plan, route variant A km 18.26-19.13
    # (old DK65, D65 p.4: no diversion, expressway sites beside the road). Powiat 2002.
    "dk65-07": Region(
        id="dk65-07",
        title="DK65 korytarz 07 — stara DK65, km 18,3–19,1",
        candidate="F_dk65_corridor",
        bbox=(764683.0, 603391.0, 766731.0, 605439.0),
        origin=(765707.0, 604415.0),
        teryt_powiat="2002",
        status="WORKING_ASSUMPTION (ADR 0214, owner D64/D65; tile = lattice (-6,4) of the ADR 0203 plan)",
    ),
    # ADR 0214 (owner D64/D65): DK65 corridor tile, lattice (-6,5) of the ADR 0203 plan, route variant A km 19.13-21.49
    # (old DK65, D65 p.4: no diversion, expressway sites beside the road). Powiat 2002.
    "dk65-08": Region(
        id="dk65-08",
        title="DK65 korytarz 08 — stara DK65, km 19,1–21,5",
        candidate="F_dk65_corridor",
        bbox=(764683.0, 605439.0, 766731.0, 607487.0),
        origin=(765707.0, 606463.0),
        teryt_powiat="2002",
        status="WORKING_ASSUMPTION (ADR 0214, owner D64/D65; tile = lattice (-6,5) of the ADR 0203 plan)",
    ),
    # ADR 0214 (owner D64/D65): DK65 corridor tile, lattice (-7,5) of the ADR 0203 plan, route variant A km 21.49-21.84
    # (old DK65, D65 p.4: no diversion, expressway sites beside the road). Powiat 2002.
    "dk65-09": Region(
        id="dk65-09",
        title="DK65 korytarz 09 — stara DK65, km 21,5–21,8",
        candidate="F_dk65_corridor",
        bbox=(762635.0, 605439.0, 764683.0, 607487.0),
        origin=(763659.0, 606463.0),
        teryt_powiat="2002",
        status="WORKING_ASSUMPTION (ADR 0214, owner D64/D65; tile = lattice (-7,5) of the ADR 0203 plan)",
    ),
    # ADR 0214 (owner D64/D65): DK65 corridor tile, lattice (-7,6) of the ADR 0203 plan, route variant A km 21.84-24.45
    # (old DK65, D65 p.4: no diversion, expressway sites beside the road). Powiat 2002: land cover 62 % 2002 / 32 % 2008;
    # the route crosses into powiat 2008 at km 23.67 (one teryt per region - see ADR 0214).
    "dk65-10": Region(
        id="dk65-10",
        title="DK65 korytarz 10 — stara DK65, km 21,8–24,4",
        candidate="F_dk65_corridor",
        bbox=(762635.0, 607487.0, 764683.0, 609535.0),
        origin=(763659.0, 608511.0),
        teryt_powiat="2002",
        teryt_powiat_extra=("2008",),      # ADR 0208 mechanism: the route crosses into powiat moniecki at km 23.67
        status="WORKING_ASSUMPTION (ADR 0214, owner D64/D65; tile = lattice (-7,6) of the ADR 0203 plan)",
    ),
    # ADR 0214 (owner D64/D65): DK65 corridor tile, lattice (-7,7) of the ADR 0203 plan, route variant A km 24.45-24.83
    # (old DK65, D65 p.4: no diversion, expressway sites beside the road). Powiat 2008: BDOT10k land cover 75 % 2008 / 25 % 2002,
    # the route of the tile lies in powiat moniecki (admin crossings km 23.67 / 25.22 of the plan).
    "dk65-11": Region(
        id="dk65-11",
        title="DK65 korytarz 11 — stara DK65, km 24,4–24,8",
        candidate="F_dk65_corridor",
        bbox=(762635.0, 609535.0, 764683.0, 611583.0),
        origin=(763659.0, 610559.0),
        teryt_powiat="2008",
        teryt_powiat_extra=("2002",),      # ADR 0208 mechanism: 25 % of the tile is powiat białostocki
        status="WORKING_ASSUMPTION (ADR 0214, owner D64/D65; tile = lattice (-7,7) of the ADR 0203 plan)",
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
    # ADR 0231 (owner D63/D64): next ring past Knyszyn, ROUGH DEFINITION ONLY (not ingested, not built). Tiles of the
    # 2048 m lattice of ADR 0203 that DK65 (towards Monki, from the west edge of dk65-monki-01), DW671 (towards Tykocin,
    # from the south edge of dw671-tykocin-01) and DW671 north of Knyszyn (towards Jasionowka, from the north edge of
    # knyszyn) pass through, in driving order. Generated by tools/worldgen/qa/ring_0231_plan.py --print-regions from the
    # OSM extract in git (Data/Plans/ring-0231/); powiat = largest area share of the tile in OSM admin_level=6
    # relations, a second powiat from 5 % (WORKING_VALUE). Corner tiles with < 0.5 km of road (dk65-monki-03/-05,
    # monki-e, dw671-tykocin-02) exist only to keep the road continuous across lattice seams.
    "dk65-monki-02": Region(
        id="dk65-monki-02",
        title="DK65 w stronę Moniek 02 — km 0,0–2,1 za dk65-monki-01, most na Nareśli",
        candidate="M_dk65_monki",
        bbox=(756491.0, 613631.0, 758539.0, 615679.0),
        origin=(757515.0, 614655.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0231, owner D63/D64; tile = lattice (-10,9) of the ADR 0203 plan; definition only, not built)",
    ),
    "dk65-monki-03": Region(
        id="dk65-monki-03",
        title="DK65 w stronę Moniek 03 — narożnik kafla, km 2,1–2,5 (w kaflu Czechowizna)",
        candidate="M_dk65_monki",
        bbox=(756491.0, 615679.0, 758539.0, 617727.0),
        origin=(757515.0, 616703.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0231, owner D63/D64; tile = lattice (-10,10) of the ADR 0203 plan; definition only, not built)",
    ),
    "dk65-monki-04": Region(
        id="dk65-monki-04",
        title="DK65 w stronę Moniek 04 — km 2,5–5,4 (w kaflu linia kolejowa)",
        candidate="M_dk65_monki",
        bbox=(754443.0, 615679.0, 756491.0, 617727.0),
        origin=(755467.0, 616703.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0231, owner D63/D64; tile = lattice (-11,10) of the ADR 0203 plan; definition only, not built)",
    ),
    "dk65-monki-05": Region(
        id="dk65-monki-05",
        title="DK65 w stronę Moniek 05 — narożnik kafla, km 5,4–5,5 (w kaflu Konopczyn, Przytulanka)",
        candidate="M_dk65_monki",
        bbox=(754443.0, 617727.0, 756491.0, 619775.0),
        origin=(755467.0, 618751.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0231, owner D63/D64; tile = lattice (-11,11) of the ADR 0203 plan; definition only, not built)",
    ),
    "dk65-monki-06": Region(
        id="dk65-monki-06",
        title="DK65 w stronę Moniek 06 — km 5,5–7,6 (w kaflu Magnusze)",
        candidate="M_dk65_monki",
        bbox=(752395.0, 617727.0, 754443.0, 619775.0),
        origin=(753419.0, 618751.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0231, owner D63/D64; tile = lattice (-12,11) of the ADR 0203 plan; definition only, not built)",
    ),
    "dk65-monki-07": Region(
        id="dk65-monki-07",
        title="DK65 w stronę Moniek 07 — km 7,6–9,9, wjazd do Moniek (Białostocka; w kaflu Ciesze)",
        candidate="M_dk65_monki",
        bbox=(752395.0, 619775.0, 754443.0, 621823.0),
        origin=(753419.0, 620799.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0231, owner D63/D64; tile = lattice (-12,12) of the ADR 0203 plan; definition only, not built)",
    ),
    "monki-e": Region(
        id="monki-e",
        title="Mońki wschód — DK65 Białostocka, narożnik kafla km 9,9–10,2 (w kaflu Świerzbienie)",
        candidate="M_dk65_monki",
        bbox=(752395.0, 621823.0, 754443.0, 623871.0),
        origin=(753419.0, 622847.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0231, owner D63/D64; tile = lattice (-12,13) of the ADR 0203 plan; definition only, not built)",
    ),
    "monki": Region(
        id="monki",
        title="Mońki — DK65 Białostocka/Ełcka przez miasto, przejazd kolejowy, km 10,2–12,9",
        candidate="M_dk65_monki",
        bbox=(750347.0, 621823.0, 752395.0, 623871.0),
        origin=(751371.0, 622847.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0231, owner D63/D64; tile = lattice (-13,13) of the ADR 0203 plan; definition only, not built)",
    ),
    "dw671-tykocin-02": Region(
        id="dw671-tykocin-02",
        title="DW671 w stronę Tykocina 02 — narożnik kafla (0,1 km), linia kolejowa",
        candidate="T_dw671_tykocin",
        bbox=(758539.0, 607487.0, 760587.0, 609535.0),
        origin=(759563.0, 608511.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0231, owner D63/D64; tile = lattice (-9,6) of the ADR 0203 plan; definition only, not built)",
    ),
    "dw671-tykocin-03": Region(
        id="dw671-tykocin-03",
        title="DW671 w stronę Tykocina 03 — km 0,1–2,3 (w kaflu Krypno Kościelne, Krypno Wielkie)",
        candidate="T_dw671_tykocin",
        bbox=(756491.0, 607487.0, 758539.0, 609535.0),
        origin=(757515.0, 608511.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0231, owner D63/D64; tile = lattice (-10,6) of the ADR 0203 plan; definition only, not built)",
    ),
    "dw671-tykocin-04": Region(
        id="dw671-tykocin-04",
        title="DW671 w stronę Tykocina 04 — km 2,3–4,2",
        candidate="T_dw671_tykocin",
        bbox=(756491.0, 605439.0, 758539.0, 607487.0),
        origin=(757515.0, 606463.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0231, owner D63/D64; tile = lattice (-10,5) of the ADR 0203 plan; definition only, not built)",
    ),
    "dw671-tykocin-05": Region(
        id="dw671-tykocin-05",
        title="DW671 w stronę Tykocina 05 — km 4,2–4,9",
        candidate="T_dw671_tykocin",
        bbox=(754443.0, 605439.0, 756491.0, 607487.0),
        origin=(755467.0, 606463.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0231, owner D63/D64; tile = lattice (-11,5) of the ADR 0203 plan; definition only, not built)",
    ),
    "dw671-tykocin-06": Region(
        id="dw671-tykocin-06",
        title="DW671 w stronę Tykocina 06 — km 4,9–7,0 (w kaflu Zygmunty)",
        candidate="T_dw671_tykocin",
        bbox=(754443.0, 603391.0, 756491.0, 605439.0),
        origin=(755467.0, 604415.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0231, owner D63/D64; tile = lattice (-11,4) of the ADR 0203 plan; definition only, not built)",
    ),
    "dw671-tykocin-07": Region(
        id="dw671-tykocin-07",
        title="DW671 w stronę Tykocina 07 — km 7,0–8,0 (w kaflu Morusy)",
        candidate="T_dw671_tykocin",
        bbox=(752395.0, 603391.0, 754443.0, 605439.0),
        origin=(753419.0, 604415.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0231, owner D63/D64; tile = lattice (-12,4) of the ADR 0203 plan; definition only, not built)",
    ),
    "dw671-tykocin-08": Region(
        id="dw671-tykocin-08",
        title="DW671 w stronę Tykocina 08 — km 8,0–9,7",
        candidate="T_dw671_tykocin",
        bbox=(752395.0, 601343.0, 754443.0, 603391.0),
        origin=(753419.0, 602367.0),
        teryt_powiat="2008",
        teryt_powiat_extra=('2002',),
        status="WORKING_ASSUMPTION (ADR 0231, owner D63/D64; tile = lattice (-12,3) of the ADR 0203 plan; definition only, not built)",
    ),
    "dw671-tykocin-09": Region(
        id="dw671-tykocin-09",
        title="DW671 w stronę Tykocina 09 — km 9,7–10,8 (w kaflu Tatary)",
        candidate="T_dw671_tykocin",
        bbox=(750347.0, 601343.0, 752395.0, 603391.0),
        origin=(751371.0, 602367.0),
        teryt_powiat="2002",
        teryt_powiat_extra=('2008',),
        status="WORKING_ASSUMPTION (ADR 0231, owner D63/D64; tile = lattice (-13,3) of the ADR 0203 plan; definition only, not built)",
    ),
    "tykocin": Region(
        id="tykocin",
        title="Tykocin — DW671 przez miasto i most na Narwi, km 10,8–13,3",
        candidate="T_dw671_tykocin",
        bbox=(750347.0, 599295.0, 752395.0, 601343.0),
        origin=(751371.0, 600319.0),
        teryt_powiat="2002",
        status="WORKING_ASSUMPTION (ADR 0231, owner D63/D64; tile = lattice (-13,2) of the ADR 0203 plan; definition only, not built)",
    ),
    "dw671-jasionowka-01": Region(
        id="dw671-jasionowka-01",
        title="DW671 w stronę Jasionówki 01 — Grodzieńska na północ od Knyszyna, km 0,0–2,4",
        candidate="J_dw671_jasionowka",
        bbox=(760587.0, 613631.0, 762635.0, 615679.0),
        origin=(761611.0, 614655.0),
        teryt_powiat="2008",
        status="WORKING_ASSUMPTION (ADR 0231, owner D63/D64; tile = lattice (-8,9) of the ADR 0203 plan; definition only, not built)",
    ),
}

TILE_SIZE_M = 2048.0
WORK_CRS = "EPSG:2180"
# Compound horizontal + vertical CRS of GUGiK NMT/NMPT/LiDAR (PL-1992 + PL-EVRF2007-NH).
HEIGHT_CRS = "EPSG:9651"   # EVRF2007-PL height (= GUGiK "PL-EVRF2007-NH")
COMPOUND_CRS = "EPSG:2180+9651"  # no single EPSG code exists for CS92 + EVRF2007-PL (checked in PROJ db)


def source_pins(region_id: str) -> dict:
    """ADR 0209: optional authored source pins of a region (Data/Regions/<id>/sources.authored.json), e.g.
    {"nmt_year": "2022"} = take that NMT survey year instead of the newest one. Empty dict when absent."""
    import json
    from pathlib import Path
    p = Path(__file__).resolve().parents[2] / "Data" / "Regions" / region_id / "sources.authored.json"
    return json.loads(p.read_text(encoding="utf-8")).get("pins", {}) if p.exists() else {}


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
