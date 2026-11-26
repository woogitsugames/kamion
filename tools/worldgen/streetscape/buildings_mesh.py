"""Building meshes from footprints + heights (BDOT10k/OSM footprints, GUGiK LoD1 heights, LoD2 roof types)
with typology-driven facades.

Typologies (classify()):
  hall      warehouses, production halls, large retail boxes: sandwich-panel walls (vertical ribbing in the
            material, UV u = metres along the wall, v = metres above the reference ground), concrete plinth,
            graphite attic flashing, flat membrane roof with an attic, roof skylights on big halls, personnel
            doors, optional ribbon windows; warehouses facing a paved yard get loading docks
            (sectional door, dock shelter, bumpers, leveller lip with hazard stripes, dock number plate,
            wheel guides, dock light) and a concrete apron in front (handed to streetscape.paved).
  office    office / service buildings: plaster, window grid per storey (3.5 m), entrance door.
  block     multi-family blocks (Białystok wielka płyta): storey 2.8 m, window rhythm 3.0 m, flat roof.
  house     single-family houses: gable roof (LoD2 roof type / eave height when known), 2-3 windows per facade.
  shed      outbuildings, garages, transformer stations: plain walls, garage doors, flat roof.
Openings are real holes in the wall (column decomposition) with reveals, so close cameras see depth.
LOD0 (layer 'buildings') carries the detail; LOD1 ('buildings_low') is a plain prism with the same wall
materials; 'collision' gets the LOD1 prism as material 'collision_building'.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np
import shapely
from shapely.geometry import Polygon

from roads import standards as S

from . import facade_atlas as FA
from . import facade_kit as FK
from . import frontage as FR
from . import roofs as RF
from . import typology as TY

HALL_FUNCS = {"magazyn", "produkcyjny", "warsztat remontowo-naprawczy", "elektrociepłownia", "spalarnia śmieci",
              "industrial", "warehouse", "silos", "stacja pomp", "straż pożarna", "construction"}
WAREHOUSE_FUNCS = {"magazyn", "produkcyjny", "warehouse", "industrial"}
RETAIL_FUNCS = {"obiekt handlowo-usługowy", "centrum handlowe", "supermarket"}
BLOCK_FUNCS = {"budynek wielorodzinny", "hotel"}
HOUSE_FUNCS = {"budynek jednorodzinny", "dom letniskowy"}
SHED_FUNCS = {"budynek gospodarczy", "garaż", "garages", "shed", "carport", "stacja transformatorowa", "garbage_shed",
              "transformer_tower", "service"}

HALL_WALLS = ["hall_wall_grey", "hall_wall_silver", "hall_wall_white", "hall_wall_ivory"]
# Białystok after thermo-modernisation (2000s-2010s): warm light pastels dominate (cream, light yellow, peach,
# sage), cool grey / blue less often; offices in the Andersa / Kwadrat Park industrial area: light grey and
# beige render, a few PRL-era plant offices in brick. WORKING_VALUE palette, to be checked against the owner's
# photo session (docs/map-decisions.md). Far (LOD1) variants: streetscape.materials._FAR_WALLS.
OFFICE_WALLS = ["plaster_light", "plaster_grey", "plaster_beige", "plaster_white", "plaster_light", "plaster_grey",
                "brick_red"]                     # brick 1 in 7 (v3.1 render: two neighbouring brick offices)
# ADR 0238: the block palette is the observed one (typology.BLOCK_WALLS: 9 photographed blocks + the MPZP colour
# rule); before: seven equal WORKING_VALUE pastels (cream, grey, blue, light, yellow, peach, sage)
BLOCK_WALLS = TY.BLOCK_WALLS
# ADR 0094 (review s9 P2-1 "every house white + anthracite roof"): the same four materials (a fifth tone is one more
# draw per house chunk and LOD: r1 / r2 of this ADR had 7 tones and +1.0...1.3 % draws on two cameras), beige and cream
# 4 of 6, white and light grey 2 of 6 (was 2 of 4); roofs: red / brown tile 5 of 7, graphite sheet 2 of 7 (was 2 of 5)
HOUSE_WALLS = ["plaster_beige", "plaster_cream", "plaster_light", "plaster_grey", "plaster_cream", "plaster_beige"]
# pitched roofs: ceramic / concrete tile and pressed metal tile sheet (blachodachowka, the commonest re-roofing in
# Podlasie); shares WORKING_VALUE
ROOFS_PITCHED = ["roof_tiles_red", "roof_metal_graphite", "roof_tiles_brown", "roof_tiles_red", "roof_tiles_brown",
                 "roof_metal_graphite", "roof_tiles_red"]
# ADR 0097 (review 0094 P2-a "5/5 bliskich domów kremowe"): the same four wall tones and three roofs, but assigned
# against the neighbours (house_palette): a house never takes the wall or the roof of its two nearest already-coloured
# neighbours and leans to the other tone family (warm beige / cream vs neutral light / grey) than its four nearest;
# family shares warm 45 % / neutral 55 % (WORKING_VALUE; the review asked cream + beige <= 50 %)
HOUSE_TONES = [("plaster_light", 0.30, "n"), ("plaster_grey", 0.25, "n"), ("plaster_beige", 0.25, "w"),
               ("plaster_cream", 0.20, "w")]
HOUSE_ROOFS = [("roof_tiles_red", 0.40), ("roof_tiles_brown", 0.32), ("roof_metal_graphite", 0.28)]


# roofs an authored / orthophoto-read override may name (knyszyn-look-s23): the palette of the rule plus the light
# grey sheet (fibre cement, galvanised sheet) that the rule never picks, so regions without overrides do not change
ROOF_OVERRIDES = {name for name, _ in HOUSE_ROOFS} | {"roof_sheet_grey", "roof_karp_red", "roof_cement_grey",
                                                      "roof_tiles_old"}
# ADR 0336 (Podlasie small-town roof palette, opt-in via facade_rules small_town: true): reuses existing roof PBR sets
# (0 new texture sets) so adjacent roofs vary across red S-tile, karpiowka, weathered old tile, brown tile, grey cement
# tile, graphite metal and weathered grey sheet. Shares WORKING_VALUE.
SMALL_TOWN_ROOFS = [
    ("roof_tiles_red", 0.28),
    ("roof_tiles_brown", 0.18),
    ("roof_cement_grey", 0.15),
    ("roof_metal_graphite", 0.16),
    ("roof_sheet_grey", 0.14),
    ("roof_tiles_old", 0.09),
]
SMALL_TOWN_ROOFS_PITCHED = ["roof_tiles_red", "roof_tiles_brown", "roof_cement_grey",
                            "roof_metal_graphite", "roof_sheet_grey", "roof_tiles_old"]
REVEAL_SMALL_TOWN = 0.10        # ADR 0336/0348: rural / small-town masonry window reveal 10 cm (8-12 cm WORKING_VALUE)
REVEAL_SMALL_TOWN_WOOD = 0.08   # ADR 0348: wooden house window reveal 8 cm (8-12 cm WORKING_VALUE)
SMALL_TOWN_PLINTH_HS = (0.35, 0.42, 0.50, 0.58)   # ADR 0336/0348: 0.35-0.58 m plinth band (0.3-0.6 m WORKING_VALUE)
SMALL_TOWN_LOD1_FRAME_M = 0.10  # ADR 0336: thin LOD1 house window frame on small-town tiles (0 extra draws)
SMALL_TOWN_SILL_CLEAN = 0.22    # ADR 0348: subtle sill runoff on ~78 % of rural/small-town house windows (WORKING_VALUE)
# ADR 0238 d. props-fix-s24 (rural outbuildings, opt-in per region via `facade_rules: rural_outbuildings: true`): a BDOT10k outbuilding
# ("budynek gospodarczy": barn, shed, cowshed, summer kitchen) was one flat-roofed box of grey / cream plaster with a
# garage door - from the road a white block without windows (review s24 wave 11, P1 8). Rule: the roof the LoD2 model
# gives (gable / hip / skillion; type 1000 stays flat), boarding / brick / block wall, a concrete plinth band, small
# barred windows and a personnel door, roof covering of the farm yards of Podlasie (trapezoidal sheet, cement-fibre
# sheet, ceramic tile). Shares WORKING_VALUE (no survey; photos Commons / owner frames of DK65 sheds).
# Draw-call budget (lead, s24: <= +2 per camera): ONLY materials the houses of the same chunks already use (plaster_*, the
# three ROOFS_PITCHED coverings, plinth_dark, facade_atlas windows); variety comes from COLOR_0 (_FACADE_TINT, 0 extra
# draws), wooden / brick walls (own materials, own wall generator) are not used for outbuildings.
RURAL_SHED_WALLS = (("plaster_grey", 0.34), ("plaster_light", 0.22), ("plaster_cream", 0.22), ("plaster_beige", 0.22))
RURAL_SHED_ROOFS = (("roof_metal_graphite", 0.34), ("roof_tiles_brown", 0.33), ("roof_tiles_red", 0.33))
RURAL_SHED_REVEAL_M = 0.0                # flat atlas opening: the window is the atlas cell, not geometry (wall_with_openings)
RURAL_SHED_TINT = (0.58, 0.86)            # luminance range of the plaster tint (darker than the houses 0.92-1.08)
RURAL_SHED_MIN_AREA_M2 = 18.0
RURAL_SHED_NO_ROOF_FUNCS = {"stacja transformatorowa", "transformer_tower", "garbage_shed"}   # keep their flat box
RURAL_SHED_WIN = (0.80, 0.50, 1.50)      # window width, height, sill above the reference ground, m (WORKING_VALUE)


def rural_shed_shades(key):
    """COLOR_0 shades of a plaster outbuilding (main wall, gable, side wall, plinth): darker and dirtier than a house."""
    lo, hi = RURAL_SHED_TINT
    lum = lo + (hi - lo) * FK.hfloat(key, "rs_lum")
    warm = (FK.hfloat(key, "rs_warm") - 0.5) * 0.08

    def c(l):
        return [round(max(0.4, l * (1 + warm)) * 0.5, 4), round(l * 0.5, 4), round(max(0.4, l * (1 - warm)) * 0.5, 4), 1.0]
    return c(lum), c(lum * 0.94), c(lum * 1.04), [round(max(0.5, lum - 0.12) * 0.5, 4)] * 3 + [1.0]


def rural_shed_pick(key, table, salt):
    u, acc = FK.hfloat(key, salt), 0.0
    for mat, share in table:
        acc += share
        if u < acc:
            return mat
    return table[-1][0]


# ADR 0316: coverings of the ceramic tile roofs. The palette (house_palette) still deals red tile / brown tile / metal
# sheet, so the neighbour rule and every earlier choice hold; a red tile roof is then, by the house's own hash,
#   - on a wooden house mostly the old hand-laid S-tile with moss and lichen (`roof_tiles_old`, owner photos of Dom
#     Klattow: the old wooden houses of Knyszyn / Tykocin kept their first roofs),
#   - otherwise for KARP_SHARE of the houses the plain tile (karpiowka), else the S-tile (esowka).
# Shares WORKING_VALUE (no survey). ROOF_LOD1: the LOD1 covering of a variant whose colour is its base material's.
KARP_SHARE = 0.22
OLD_TILE_SHARE = 0.7
ROOF_LOD1 = {"roof_karp_red": "roof_tiles_red"}
ROOF_LOD1_SMALL_TOWN = {"roof_karp_red": "roof_tiles_red", "roof_tiles_old": "roof_tiles_red"}


# weathering-s24 (ADR 0238 / 0348 addendum, opt-in per region: `kind: facade_rules`, `roof_weathering: true`): roof
# covering COLOR_0 for Kamion/World PBR _ROOF_WEATHER - dirt runs down the slope, moss / lichen at the eave and the
# ridge, odd (soaked / replaced) tiles. The age class follows the rule of the plots (plots.age_class: BDOT10k has no
# year of construction; footprint + storeys) and the covering itself (old hand-laid tile, shingles, cement tile of the
# old Podlasie houses = old; a pressed metal / sheet roof is younger unless it covers a farm outbuilding).
# (age lo, age hi), moss: WORKING_VALUE (no survey; refs Data/raw/refs/posesje, tykocin-rynek-commons: old tile roofs
# carry green-grey moss along the eave and in the laps of the north slope, 1990s+ roofs only a dust film).
ROOF_WEATHER_AGE = {"old": (0.70, 1.00), "prl": (0.40, 0.72), "new": (0.15, 0.35)}
ROOF_WEATHER_MOSS = {"old": 1.0, "prl": 0.60, "new": 0.20}
ROOF_WEATHER_OLD_MATS = ("roof_tiles_old", "roof_shingles_grey", "roof_cement_grey")
ROOF_WEATHER_YOUNG_MATS = ("roof_metal_", "roof_sheet_")


def roof_age_class(b, key, rmat, wooden=False, rural_shed=False):
    """'old' / 'prl' / 'new' of a pitched roof (weathering-s24; see ROOF_WEATHER_AGE)."""
    if rmat in ROOF_WEATHER_OLD_MATS or wooden:
        return "old"
    if rural_shed:
        return "old" if FK.hfloat(key, "rwshed") < 0.6 else "prl"
    if rmat.startswith(ROOF_WEATHER_YOUNG_MATS):
        return "new" if FK.hfloat(key, "rwmetal") < 0.7 else "prl"
    p = b["props"]
    st = p.get("storeys") or 1
    h = p.get("height_m") or 6.0
    area = b["poly"].area
    base = "old" if (area < 95.0 and st <= 1) else "new" if (area >= 150.0 or (st >= 2 and h >= 8.5 and area >= 120.0)) else "prl"
    x = FK.hfloat(key, "rwage")
    if x < 0.12:
        return {"old": "prl", "prl": "old", "new": "prl"}[base]
    if x > 0.90:
        return {"old": "prl", "prl": "new", "new": "new"}[base]
    return base


def roof_weather(b, key, rmat, wooden=False, rural_shed=False):
    """(age 0..1, moss 0..1, seed 0..1) of a pitched roof for roofs.build(weather=...), deterministic per building."""
    cls = roof_age_class(b, key, rmat, wooden, rural_shed)
    lo, hi = ROOF_WEATHER_AGE[cls]
    age = lo + (hi - lo) * FK.hfloat(key, "rwa")
    moss = ROOF_WEATHER_MOSS[cls] * (0.6 + 0.4 * FK.hfloat(key, "rwm"))
    return round(age, 4), round(moss, 4), round(FK.hfloat(key, "rws"), 4)


def roof_variant(key, material, wooden, small_town=False):
    """The covering of a rule-chosen tile roof (see KARP_SHARE); other materials pass through."""
    if material != "roof_tiles_red":
        return material
    if wooden:
        return "roof_tiles_old" if hfloat(key, "roofold") < OLD_TILE_SHARE else material
    if small_town:
        u = hfloat(key, "roofkarp")
        if u < KARP_SHARE:
            return "roof_karp_red"
        if u < KARP_SHARE + 0.24:
            return "roof_tiles_old"
        return material
    return "roof_karp_red" if hfloat(key, "roofkarp") < KARP_SHARE else material
# overrides that leave the facade to the rules (a building that only has these still gets e.g. the rule shopfront)
OVR_ROOF_ONLY = {"roof_material"}
# house walls an authored override may name (read off a licensed street-level photo): the rule tones plus boarding
HOUSE_WALL_OVERRIDES = {m for m, _, _ in HOUSE_TONES} | {"plaster_white", "plaster_yellow", "plaster_peach",
                                                      "plaster_sage", "brick_red", "wood_planks", "wood_planks_green",
                                                      "wood_planks_red", "wood_planks_graphite",
                                                      "wood_planks_white"}       # ADR 0305: white-painted boards
# ADR 0298 (review 2026-11-18 N5): boarding colour of a rule wooden house - painted red-brown / graphite as on owner
# photo 7, the stained brown and green of ADR 0287 kept for a share. Shares WORKING_VALUE (no survey of Knyszyn houses).
WOOD_PAINTS = (("wood_planks_red", 0.32), ("wood_planks_graphite", 0.24), ("wood_planks", 0.26), ("wood_planks_green", 0.18))


def wood_paint(key):
    u, acc = FK.hfloat(key, "woodc"), 0.0
    for mat, share in WOOD_PAINTS:
        acc += share
        if u < acc:
            return mat
    return WOOD_PAINTS[-1][0]


def house_roof_material(building, default):
    """Opt-in roof colour for a sourced building with a pitched roof; preserve the rule palette otherwise."""
    material = building.get("ovr", {}).get("roof_material", default)
    if material not in ROOF_OVERRIDES:
        raise ValueError(f"building {building['id']}: unsupported roof_material {material!r}")
    return material
HOUSE_NEAR_M = 40.0
STOREY_H = {"office": 3.5, "block": 2.8, "house": 2.9}
# window reveal depth of rendered walls, m: the frame sits in the old wall plane, the thermal insulation (12-15 cm of
# EPS + render) is added in front of it (WORKING_VALUE; r10 had 0.14 and the opening read flat from the street)
REVEAL_ETICS = 0.22
ZBASE = {"block": 1.0, "office": 0.45}       # ground floor level above the ground (blocks: high basement), m
BALCONY_SUN = np.array([-0.5, -0.866])       # towards SSW (E, N)
# plinth (cokół) height above the reference ground by typology, m (ADR 0091; WORKING_VALUE within the 0.6-1.2 m the
# review asked for): blocks = the raised ground floor over the basement, offices 0.6, houses 0.45-0.6, sheds 0.3
PLINTH_H = {"block": None, "office": 0.6, "house": 0.45, "shed": 0.3}
PLINTHS = ["plinth_dark"]
# Share of blocks with ETICS (insulated, rendered); the rest (30 %) show bare `panel_concrete`. WORKING_VALUE without
# a source: the block sample of research/mistral/p3-buildings-2 (M53, n = 9) has 0 unclad blocks (ADR 0238 Otwarte 3,
# review s22 #123 P2). Kept at the pre-0238 value - a change re-colours blocks and needs a render + visual-critic.
BLOCK_ETICS_SHARE = 0.7
BAL_EXCEPT_PCT = 12           # ADR 0097: share of balconies with another balustrade than the building's (WORKING_VALUE)
BAL_EXCEPT = (4, 7, 0)         # balf variants of the exceptions: bars + flowers, faded grey-green plastic, perforated
                               # (r1 also brown: read orange on r10_block_3; ADR 0107, review 0097 P2-i: the reed
                               # mat (5) read yellow / ochre from 60 m - exceptions stay near-neutral)
ESTATE_M = 250.0               # ADR 0097: estate cell for the balustrade types (<= 2 types per cell), m (WORKING_VALUE)
# ADR 0097 r2: the paved apron round blocks is OFF - draped on the height field it sank under the terrain mesh along
# most of the wall and showed as loose light patches where the slope dips (r2 r10_block_5); needs the terrain mesh's
# own heights (or a terrain cut) first. Open.
BLOCK_APRON = False
SILL_RUNOFF = True             # ADR 0097: streaks under window sills (TEXCOORD_1.v + 64, shader ADR 0092)      # ADR 0094: one tone (r3 had two; every material is a draw per chunk on both LODs)


def storey_plan(typ, h, p, sub=None):
    """(storeys, storey height, ground floor level) - BDOT10k LICZBAKONDYGNACJI (`storeys`) when it fits the
    LoD1 height (2.6-3.8 m per storey for blocks, 2.8-4.6 m for offices), else derived from the height.
    sub (ADR 0238): a subtype whose proportions differ from its class (typology.PROPORTIONS: kamienica)."""
    sh = STOREY_H.get(typ, 4.0)
    zb = ZBASE.get(typ, 0.3)
    lo, hi = (2.6, 3.8) if typ == "block" else (2.8, 4.6)
    if sub == "kamienica":
        pr = TY.PROPORTIONS[sub]
        sh, zb, (lo, hi) = pr["storey_m"], pr["plinth_m"], pr["storey_fit_m"]
    n = max(1, int(round((h - 1.0) / sh)))
    nb = p.get("storeys")
    if typ in ("office", "block") and nb:
        shb = (h - zb - 0.8) / float(nb)
        if p.get("storeys_fixed"):        # ADR 0242: authored count kept whatever the storey height (tall plant offices)
            return int(nb), shb, zb
        # lo, hi set above (ADR 0238: kamienica uses its own storey_fit_m) - do not reset them here
        if lo <= shb <= hi:
            return int(nb), shb, zb
    if typ in ZBASE and n * sh + zb + 0.6 > h:
        n = max(1, int((h - zb - 0.6) // sh))
    return n, sh, zb


def house_palette(blds, roofs=None):
    """{building id: (wall material, roof material)} for every house (ADR 0097). Deterministic: houses in id order,
    each scored against the already assigned houses within HOUSE_NEAR_M (nearest first)."""
    roof_opts = roofs if roofs is not None else HOUSE_ROOFS
    hs = sorted((b for b in blds if b["typ"] == "house"), key=lambda b: b["id"])
    if not hs:
        return {}
    cen = np.array([b["poly"].centroid.coords[0] for b in hs])
    out, done = {}, []
    fam = {m: f for m, _, f in HOUSE_TONES}
    for i, b in enumerate(hs):
        near = []
        if done:
            dd = np.hypot(*(cen[done] - cen[i]).T)
            order = np.argsort(dd)
            near = [hs[done[j]]["id"] for j in order[:4] if dd[j] < HOUSE_NEAR_M]
        key = b["id"]

        def pick(opts, used2, salt, famw=None):
            best = None
            for k_, (m, w, *f) in enumerate(opts):
                pen = 10.0 * sum(1 for n_ in used2 if n_ == m)
                if famw is not None:
                    pen += 2.0 * famw.get(f[0], 0)
                sc = pen - w * 3.0 * hfloat(key, f"{salt}{k_}")          # weight-biased random tie break
                if best is None or sc < best[0]:
                    best = (sc, m)
            return best[1]
        walls_n = [out[n_][0] for n_ in near]
        famw = {}
        for m in walls_n:
            famw[fam[m]] = famw.get(fam[m], 0) + 1
        wall = pick(HOUSE_TONES, walls_n[:2], "tone", famw)
        roof = pick(roof_opts, [out[n_][1] for n_ in near[:2]], "roofp")
        out[key] = (wall, roof)
        done.append(i)
    return out


def hpick(key, seq, salt=""):
    h = int(hashlib.sha1((key + salt).encode()).hexdigest()[:8], 16)
    return seq[h % len(seq)]


def hfloat(key, salt=""):
    return int(hashlib.sha1((key + salt).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def classify(p, area, ovr):
    """Render class of a building. Override `typology`: a class or a subtype of streetscape.typology (ADR 0238:
    kamienica, pawilon, ... -> its class; the subtype itself is kept by load() as b["sub"])."""
    if ovr.get("typology"):
        cls = TY.render_class(ovr["typology"])
        if cls is None:
            raise ValueError(f"override typology {ovr['typology']!r}: expected one of {sorted(TY.TYPES + tuple(TY.SUBTYPES))}")
        return cls
    f = p.get("function")
    h = p.get("height_m") or 6.0
    if f in HALL_FUNCS or (f in RETAIL_FUNCS and area > 1500):
        return "hall"
    if f in BLOCK_FUNCS:
        return "block"
    if f in HOUSE_FUNCS:
        return "house"
    if f in SHED_FUNCS or (area < 60 and h < 5):
        return "shed"
    return "office"


# ------------------------------------------------------------------------------------------- geometry
class Acc:
    """Triangle accumulator per (layer, material)."""

    def __init__(self):
        self.d = {}

    def add(self, layer, mat, V, T, UV=None, UV1=None, COL=None):
        V = np.asarray(V, float)
        if UV is None:
            UV = V[:, :2]
        lst = self.d.setdefault((layer, mat), [])
        lst.append((V, np.asarray(T, np.int64).reshape(-1, 3), np.asarray(UV, float),
                    None if UV1 is None else np.asarray(UV1, float),
                    None if COL is None else np.asarray(COL, float)))

    def quad(self, layer, mat, a, b, c, d, uv=None, uv1=None, col=None):
        """CCW quad a-b-c-d (seen from the front)."""
        V = np.array([a, b, c, d], float)
        if uv is None:
            e1 = V[1] - V[0]
            L = np.linalg.norm(e1)
            H = np.linalg.norm(V[3] - V[0])
            uv = [[0, 0], [L, 0], [L, H], [0, H]]
        COL = None
        if col is not None:
            ca = np.asarray(col, float)
            COL = np.tile(ca, (4, 1)) if ca.ndim == 1 else ca
        self.add(layer, mat, V, [[0, 1, 2], [0, 2, 3]], uv, uv1, COL)

    def box(self, layer, mat, c, ax, ay, az, skip=()):
        """Box centred at c with half-axis vectors ax, ay, az (all 6 faces, outward). skip: face indices left out
        (0 -az, 1 +az, 2 -ay, 3 +ay, 4 -ax, 5 +ax), for the cheap LOD1 silhouette pieces whose hidden faces never show."""
        c, ax, ay, az = (np.asarray(x, float) for x in (c, ax, ay, az))
        P = [c + sx * ax + sy * ay + sz * az for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
        faces = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
        if np.dot(np.cross(ax, ay), az) < 0:
            faces = [f[::-1] for f in faces]
        for k, f in enumerate(faces):
            if k not in skip:
                self.quad(layer, mat, *[P[i] for i in f])

    # parapet run-off coverage (REVIEW G3 wires-streaks-v2): hall_wall_* triangles with / without wall-top TEXCOORD_1
    runoff_tris = {"with_uv1": 0, "without_uv1": 0}

    def flush(self, buf, src):
        for (layer, mat), items in sorted(self.d.items()):
            if str(mat).startswith("hall_wall"):
                for it in items:
                    Acc.runoff_tris["with_uv1" if it[3] is not None else "without_uv1"] += len(it[1])
            V = np.concatenate([it[0] for it in items])
            UV = np.concatenate([it[2] for it in items])
            UV1 = (np.concatenate([it[3] if it[3] is not None else np.zeros((len(it[0]), 2)) for it in items])
                   if any(it[3] is not None for it in items) else None)
            has_col = any(len(it) > 4 and it[4] is not None for it in items)
            COL = (np.concatenate([it[4] if (len(it) > 4 and it[4] is not None) else np.zeros((len(it[0]), 4))
                                   for it in items]) if has_col else None)
            off = np.cumsum([0] + [len(it[0]) for it in items[:-1]])
            T = np.concatenate([it[1] + o for it, o in zip(items, off)])
            if COL is not None:
                buf.add(layer, mat, V, UV, T, src=src, UV1=UV1, COL=COL)
            else:
                buf.add(layer, mat, V, UV, T, src=src, UV1=UV1)


class _L0Only(Acc):
    """View of an accumulator that drops the LOD1 layer (ADR 0238: eaves gutters / downpipes of a pitched block or
    office are LOD0 detail, so its LOD1 costs no more than the flat-roofed LOD1 it replaces)."""

    def __init__(self, acc):
        self.d = acc.d

    def add(self, layer, *a, **k):
        if layer != "buildings_low":
            super().add(layer, *a, **k)


def cells(kind, *variants):
    """Opening infill drawn from the facade atlas (ADR 0081): one cell per variant, side by side across the opening.
    ("atlas", [(u0, v0, w, h) ...], fu0, fu1, fv0, fv1) - the f* fractions are the part of the opening a wall piece
    keeps (facade_kit.wall_pieces clips openings)."""
    return ("atlas", [FA.cell(kind, v) for v in variants], 0.0, 1.0, 0.0, 1.0)


RUNOFF_PERIOD_M = 24.0       # u period of the parapet_runoff layer (art-source/world/materials, sets_facade)


def runoff_uv1(runoff, ua, ub, za, zb):
    """TEXCOORD_1 of a wall quad [ua, ub] x [za, zb] for the parapet run-off streaks (Kamion/World PBR _RUNOFF):
    (u_offset + u, 1 + (z_top - z) / length_scale). The engine stores TEXCOORD_1 as half floats (WorldMeshBake), so u is
    shifted per quad by a whole number of layer periods: the pattern is unchanged (the layer tiles in u) but |u| stays
    below period + quad length (< 1/16 m half-float step) instead of the building perimeter (0.25-1 m steps -> pattern
    seams and smeared streaks on big halls). None when runoff is None."""
    if runoff is None:
        return None
    zt_r, uo, ls = runoff[:3]                     # a 4th value = block table (ADR 0196, runoff_cells)
    a = uo + ua
    sh = RUNOFF_PERIOD_M * math.floor(a / RUNOFF_PERIOD_M)
    a, b = a - sh, uo + ub - sh
    ka, kb = 1 + (zt_r - za) / ls, 1 + (zt_r - zb) / ls
    return [[a, ka], [b, ka], [b, kb], [a, kb]]


# ADR 0196 (review s19-0179 P2 "zacieki pod attyka to ten sam wzor powtarzany co modul"): the run-off layer tiles every
# RUNOFF_PERIOD_M, so a 133 m wall showed the same streak group 5.5 times. Opt-in per region (override
# `kind: facade_rules`, `runoff_shuffle: true`): the wall top is cut into the blocks of the layer between its QUIET
# columns (texture u where nothing but the drip band is drawn within +-0.25 m: a seam there cuts no streak) and the
# blocks are laid along the wall in a hashed order, half of them mirrored, each with its own streak length - no two
# stretches of a wall repeat in step, and a fifth of the blocks carry short streaks only. Mesh only (TEXCOORD_1), no
# shader or texture change. Quiet columns measured on T_parapet_runoff.png (High, 1024 px; sets_facade.parapet_runoff
# seed 521): column mean of R + G below the drip band, max over +-0.25 m <= 0.004 (layer mean 0.017).
RUNOFF_QUIET_U_ALL = (0.98, 2.60, 4.27, 6.61, 8.91, 10.88, 14.44, 16.20, 20.55, 23.25)
# six of the ten are used (blocks of 2.3-6.1 m, mean 4 m): ten blocks cost +30 % LOD1 triangles on the Dojlidy tile
RUNOFF_QUIET_U = (0.98, 4.27, 6.61, 10.88, 14.44, 20.55)
RUNOFF_BLOCKS = tuple((a, (b - a) % RUNOFF_PERIOD_M) for a, b in zip(RUNOFF_QUIET_U, RUNOFF_QUIET_U[1:] + RUNOFF_QUIET_U[:1]))
RUNOFF_SHUFFLE_DEPTH_M = 4.0   # the layer is 4 m deep (x length scale); below it the wall needs no cuts
RUNOFF_SHORT_SHARE = 0.2       # blocks with short streaks only (length scale x 0.3)
RUNOFF_LEN_MUL = (0.65, 1.25)  # streak length factor of the other blocks


def runoff_blocks(key, length):
    """Hashed block sequence covering [0, length] of a building's wall perimeter:
    [(u0, u1, tex_u0, tex_u1, length_scale_factor)] - tex_u0 > tex_u1 for a mirrored block. Never the same block twice
    in a row; deterministic per building key."""
    out, u, prev, i = [], 0.0, -1, 0
    nb = len(RUNOFF_BLOCKS)
    while u < length:
        k = int(hfloat(key, f"rob{i}") * nb) % nb
        if k == prev:
            k = (k + 1 + int(hfloat(key, f"rob2{i}") * (nb - 1)) % (nb - 1)) % nb
        a, w = RUNOFF_BLOCKS[k]
        mirror = hfloat(key, f"rom{i}") < 0.5
        mul = (0.3 if hfloat(key, f"ros{i}") < RUNOFF_SHORT_SHARE
               else RUNOFF_LEN_MUL[0] + (RUNOFF_LEN_MUL[1] - RUNOFF_LEN_MUL[0]) * hfloat(key, f"rol{i}"))
        out.append((u, u + w, a + w if mirror else a, a if mirror else a + w, mul))
        u += w
        prev = k
        i += 1
    return out


def runoff_cells(runoff, ua, ub, za, zb, mat="hall_wall"):
    """Sub-quads of a wall quad [ua, ub] (absolute perimeter u) x [za, zb] with their run-off TEXCOORD_1:
    [(u0, u1, z0, z1, uv1)]. Without a block table (runoff of 3 values, or None) the quad itself (runoff_uv1); so are
    pieces that are not hall cladding (plinth: metres below the streaks on any hall worth looking at)."""
    if runoff is None or len(runoff) < 4 or not runoff[3] or not str(mat).startswith("hall_wall"):
        return [(ua, ub, za, zb, runoff_uv1(runoff, ua, ub, za, zb))]
    zt_r, _uo, ls, blocks = runoff[:4]
    zs = zt_r - RUNOFF_SHUFFLE_DEPTH_M * ls * RUNOFF_LEN_MUL[1] - 0.05
    out = []
    if za < zs - 0.05:                         # below the layer: one quad; depth beyond the layer samples its empty row
        zc = min(zs, zb)
        out.append((ua, ub, za, zc, [[0.0, 9.0], [ub - ua, 9.0], [ub - ua, 9.0], [0.0, 9.0]]))
        if zc >= zb - 1e-6:
            return out
        za = zc
    for b0, b1, t0, t1, mul in blocks:
        c0, c1 = max(ua, b0), min(ub, b1)
        if c1 - c0 < 1e-4:
            continue
        f0, f1 = (c0 - b0) / (b1 - b0), (c1 - b0) / (b1 - b0)
        a, b = t0 + (t1 - t0) * f0, t0 + (t1 - t0) * f1
        ka, kb = 1 + (zt_r - za) / (ls * mul), 1 + (zt_r - zb) / (ls * mul)
        out.append((c0, c1, za, zb, [[a, ka], [b, ka], [b, kb], [a, kb]]))
    return out


LOD1_HOUSE_OPENINGS = True     # ADR 0124 r2: windows / door of houses on the LOD1 prism (dark quads, no new material)
LOD1_HOUSE_FRAME_M = 0.0                       # ADR 0132: frame round a LOD1 opening of a house, m. OFF (0): r2 measured +31 k
                                               # triangles in the Low variant (worst house-street camera +29 k) while A16 Low
                                               # fails its GPU budget; 0.12 turns it back on (0 extra draws)
LOD1_HOUSE_FRAME_MATS = ("plaster_white", "plaster_light", "downpipe")      # first one the chunk's LOD1 has and the wall is not
LOD1_HOUSE_OPENING_FALLBACK = "downpipe"       # 0.30 grey: gutters of every pitched house on LOD1
_CHUNK_M = 256.0                               # terrain_mesh.chunks.CHUNK_M (chunk bounds are multiples of it)
LOD1_HOUSE_OPENING_MAT = "hall_flashing"       # 0.045 graphite sheet: already on the LOD1 of every pitched house (verge / fascia)
SILL_CLEAN = 0.40              # ADR 0107: share of windows whose sill left no mark (review 0097 P1-f: 30-50 %)


def _sill_code(sills, za, zb, oa, zfrac):
    """(rnd 0-7, length scale m) of the mark of one window sill, or None (a clean sill: SILL_CLEAN of the windows)."""
    uo, ls = sills[0], sills[1]
    clean = sills[2] if len(sills) > 2 else SILL_CLEAN
    wk = f"{uo:.3f}:{oa:.2f}:{zb:.2f}"
    if FK.hfloat(wk, "sill_clean") < clean:
        return None
    rnd = int(FK.hfloat(wk, "sill_rnd") * 8) % 8
    lsw = max(ls * (1.3 - 0.6 * min(max(zfrac, 0.0), 1.0)) * (0.8 + 0.4 * FK.hfloat(wk, "sill_len")), (zb - za) / 6.5)
    return rnd, lsw


def sill_marks(sills, ua, ub, za, zb, oa, ob, zfrac):
    """ADR 0107 (review 0097 P1-f; replaces the ADR 0097 `sill_uv1`): TEXCOORD_1 of the wall under a window sill, the
    column [ua, ub] of the opening [oa, ob], top zb = the sill. [(u0, u1, uv1)] - the column split at the sill centre -
    or None (this sill left no mark: SILL_CLEAN of the windows). Shader contract (Kamion/World PBR _RUNOFF, v >= 112):
    u = signed metres from the nearer sill end (left half < 0), v = 128 + 8 * rnd + 1 + depth / length scale, rnd 0-7
    per window. Lower storeys carry longer marks (zfrac = height of the sill in the wall, 0 bottom ... 1 top).
    Half floats (WorldMeshBake): |u| < 4 m -> 1/256 m steps; v < 192 -> exact at the sill, 1/8 unit at the bottom.
    ADR 0114: the wall BESIDE the sill end carries the other half of the whisker (sill_strip_uv1, |u| >= SILL_OUT)."""
    code = _sill_code(sills, za, zb, oa, zfrac)
    if code is None:
        return None
    rnd, lsw = code
    v0 = 129.0 + 8.0 * rnd
    kb = v0 + (zb - za) / lsw
    om = 0.5 * (oa + ob)
    out = []
    for c0, c1, sg in ((ua, min(ub, om), -1.0), (max(ua, om), ub, 1.0)):
        if c1 - c0 < 1e-4:
            continue
        e0, e1 = (c0 - oa, c1 - oa) if sg < 0 else (ob - c0, ob - c1)
        e0, e1 = max(e0, 1e-3), max(e1, 1e-3)              # 0 would lose the side sign
        out.append((c0, c1, [[sg * e0, kb], [sg * e1, kb], [sg * e1, v0], [sg * e0, v0]]))
    return out


SILL_STRIP_M = 0.12            # ADR 0114: width of the wall strip beside a sill end that carries the whisker, m
SILL_OUT = 2.0                 # |u| offset of that strip in TEXCOORD_1 (sills are narrower than 2 x this)


def sill_strip_uv1(sills, za, zb, oa, ob, zfrac, side):
    """ADR 0114 (review 0107 P1-r7-g: "prostokąt z cienkimi krawędziami", the whisker ended on the column edge):
    TEXCOORD_1 of the wall strip SILL_STRIP_M wide just outside the left (side < 0) / right end of the sill of the
    opening [oa, ob]: |u| = SILL_OUT + metres from the sill end, sign = side, v as in sill_marks (same rnd and length
    scale, so the two halves of a whisker meet). Corners of the quad (c0, za) (c1, za) (c1, zb) (c0, zb), c0 < c1.
    None for a clean sill."""
    code = _sill_code(sills, za, zb, oa, zfrac)
    if code is None:
        return None
    rnd, lsw = code
    v0 = 129.0 + 8.0 * rnd
    kb = v0 + (zb - za) / lsw
    near, far = SILL_OUT + 1e-3, SILL_OUT + SILL_STRIP_M
    e0, e1 = (far, near) if side < 0 else (near, far)
    sg = -1.0 if side < 0 else 1.0
    return [[sg * e0, kb], [sg * e1, kb], [sg * e1, v0], [sg * e0, v0]]


_HOUSE_CELLS = tuple((k, FA.cell("house", k)) for k in range(FA.KINDS["house"][2]))


def _house_shades(key):
    """ADR 0348: 2-3 deterministic plaster shades + plinth shade per house from seed (COLOR_0 = rgb*0.5, a=1.0 ->
    WorldPBR _FACADE_TINT multiplies albedo by rgb*2). Subtle realistic Podlasie shifts (+0 draws / +0 materials)."""
    def _c(lum, warm):
        r = max(0.72, min(1.22, lum * (1.0 + warm)))
        g = max(0.72, min(1.22, lum))
        b = max(0.72, min(1.22, lum * (1.0 - warm)))
        return [round(r * 0.5, 4), round(g * 0.5, 4), round(b * 0.5, 4), 1.0]
    lum_m = 0.92 + 0.16 * FK.hfloat(key, "sh_m")
    warm_m = (FK.hfloat(key, "sh_mw") - 0.5) * 0.06
    g_dir = 1.0 if FK.hfloat(key, "sh_gd") < 0.62 else -1.0
    lum_g = max(0.76, min(1.18, lum_m + g_dir * (0.09 + 0.07 * FK.hfloat(key, "sh_g"))))
    warm_g = (FK.hfloat(key, "sh_gw") - 0.5) * 0.07
    lum_s = max(0.78, min(1.16, lum_m - g_dir * (0.07 + 0.06 * FK.hfloat(key, "sh_s"))))
    warm_s = (FK.hfloat(key, "sh_sw") - 0.5) * 0.05
    lum_p = 0.78 + 0.24 * FK.hfloat(key, "sh_p")
    return _c(lum_m, warm_m), _c(lum_g, warm_g), _c(lum_s, warm_s), [round(lum_p * 0.5, 4)] * 3 + [1.0]


def _house_frame_3d(acc, layer, A, B, C, D, back, d3, n3, w, h, rect):
    """ADR 0348: 3D recessed window frame + central mullion (slupek) + transom/muntin (slemie) inside the 8-12 cm
    reveal, mapped to facade_atlas swatches (4-vertex quads only -> +0 draw calls, compatible with UV cell checks)."""
    hv = next((k for k, r_ in _HOUSE_CELLS if r_ == rect), None)
    if hv is None or w < 0.55 or h < 0.55:
        return
    sw = ("pvc_white", "pvc_brown", "pvc_white", "wood")[hv]
    uv = FA.swatch_uv(sw)
    dep = min(0.026, float(np.linalg.norm(back)) * 0.45)
    fr = back + n3 * dep
    fw = min(0.068, w * 0.14, h * 0.14)
    Ao, Bo, Co, Do = A + fr, B + fr, C + fr, D + fr
    Ai, Bi = Ao + d3 * fw + [0, 0, fw], Bo - d3 * fw + [0, 0, fw]
    Ci, Di = Co - d3 * fw - [0, 0, fw], Do + d3 * fw - [0, 0, fw]
    acc.quad(layer, "facade_atlas", Ao, Bo, Bi, Ai, uv=uv)
    acc.quad(layer, "facade_atlas", Bo, Co, Ci, Bi, uv=uv)
    acc.quad(layer, "facade_atlas", Co, Do, Di, Ci, uv=uv)
    acc.quad(layer, "facade_atlas", Do, Ao, Ai, Di, uv=uv)
    bk = -n3 * dep
    if w >= 0.85:                                             # central vertical mullion (slupek) + depth cheeks
        mw = 0.026
        M0 = 0.5 * (Ai + Bi)
        M1 = 0.5 * (Di + Ci)
        Ml0, Mr0 = M0 - d3 * mw, M0 + d3 * mw
        Ml1, Mr1 = M1 - d3 * mw, M1 + d3 * mw
        acc.quad(layer, "facade_atlas", Ml0, Mr0, Mr1, Ml1, uv=uv)
        acc.quad(layer, "facade_atlas", Ml0 + bk, Ml0, Ml1, Ml1 + bk, uv=uv)
        acc.quad(layer, "facade_atlas", Mr0, Mr0 + bk, Mr1 + bk, Mr1, uv=uv)
    if h >= 0.85:                                             # horizontal transom / muntin (slemie / szpros)
        th = 0.024
        t_frac = 0.68 if hv in (2, 3) else 0.50
        T0 = Ai + (Di - Ai) * t_frac
        T1 = Bi + (Ci - Bi) * t_frac
        Tb0, Tt0 = T0 - [0, 0, th], T0 + [0, 0, th]
        Tb1, Tt1 = T1 - [0, 0, th], T1 + [0, 0, th]
        acc.quad(layer, "facade_atlas", Tb0, Tb1, Tt1, Tt0, uv=uv)
        acc.quad(layer, "facade_atlas", Tb0 + bk, Tb1 + bk, Tb1, Tb0, uv=uv)
        acc.quad(layer, "facade_atlas", Tt0, Tt1, Tt1 + bk, Tt0 + bk, uv=uv)


def wall_with_openings(acc, layer, mat, p0, d, nout, L, zb, zt, openings, u0=0.0, vref=0.0, runoff=None, reveal=None,
                       ground=None, sills=None, bold_sill=False, col=None, frame_3d=False, sill_mat=None):
    """Wall rectangle [0, L] x [zb, zt] in the vertical plane through p0 along d, minus rectangular
    openings [(ua, ub, va, vb, depth, kind, mat_in)]. Adds reveals and the recessed infill.
    runoff = (z_top, u_offset, length_scale): the wall face gets TEXCOORD_1 = (u_offset + u, 1 + (z_top - z) /
    length_scale) for the parapet run-off streaks of halls (Kamion/World PBR _RUNOFF); otherwise no UV1.
    ground(u) = terrain height at u (same u as UV0): plinth_* pieces take UV0.v = metres above the terrain at the wall
    instead of above the building's reference level, so the splash zone (_SPLASH) follows a sloping ground and a
    plinth standing 2 m out of a slope is not one flat tone (ADR 0094, review s9 P2-5)."""
    gnd = ground if ground is not None and (str(mat).startswith("plinth") or mat == "fieldstone_plinth") else None
    p0, d, nout = (np.asarray(x, float) for x in (p0, d, nout))
    ops = sorted([o for o in openings if o[1] > o[0] + 0.05 and o[3] > o[2] + 0.05], key=lambda o: o[0])
    us = sorted({0.0, L, *[o[0] for o in ops], *[o[1] for o in ops]})
    # ADR 0114: wall strips beside the sill ends of marked windows (the outer half of the two whiskers)
    strips = {}
    if sills is not None and not str(mat).startswith("plinth"):
        for o in ops:
            if o[5] not in ("window", "ribbon"):
                continue
            za_o = max([q[3] for q in ops if q is not o and q[0] < o[1] - 1e-3 and q[1] > o[0] + 1e-3 and q[3] <= o[2] + 1e-6] + [zb])
            if o[2] - za_o <= 0.15:
                continue
            for side, c0, c1 in ((-1, o[0] - SILL_STRIP_M, o[0]), (1, o[1], o[1] + SILL_STRIP_M)):
                if c0 < 0.0 or c1 > L or any(q[0] < c1 - 1e-3 and q[1] > c0 + 1e-3 for q in ops):
                    continue
                uv1 = sill_strip_uv1(sills, za_o, o[2], o[0], o[1], (o[2] - zb) / max(zt - zb, 1e-6), side)
                if uv1 is not None:
                    strips.setdefault((round(c0, 4), round(c1, 4)), []).append((za_o, o[2], uv1))
        us = sorted(set(us) | {u for k in strips for u in k})
        us = [u for i, u in enumerate(us) if i == 0 or u - us[i - 1] > 1e-4]

    def P(u, z):
        return [p0[0] + d[0] * u, p0[1] + d[1] * u, z]

    for ua, ub in zip(us, us[1:]):
        if ub - ua < 1e-4:
            continue
        um = 0.5 * (ua + ub)
        cov = sorted([(o[2], o[3], o[5], o[0], o[1]) for o in ops if o[0] <= um <= o[1]])
        z = zb
        segs = []
        for va, vb, kd, oa, ob in cov:
            if va > z:
                segs.append((z, va, kd, oa, ob))
            z = max(z, vb)
        if z < zt:
            segs.append((z, zt, None, 0.0, 0.0))
        marked = strips.get((round(ua, 4), round(ub, 4)))
        if marked and not cov:                  # a strip beside sill ends: cut it at the sills it serves
            cuts, z = [], zb
            for s0, s1, uv1 in sorted(marked, key=lambda m: m[1]):
                s0 = max(s0, z)
                if s1 - s0 < 0.05:
                    continue
                if s0 > z:
                    cuts.append((z, s0, None))
                cuts.append((s0, s1, uv1))
                z = s1
            if z < zt:
                cuts.append((z, zt, None))
            for za, zb2, uv1 in cuts:
                va_, vb_ = (gnd(u0 + ua), gnd(u0 + ub)) if gnd else (vref, vref)
                acc.quad(layer, mat, P(ua, za), P(ub, za), P(ub, zb2), P(ua, zb2),
                         uv=[[u0 + ua, za - va_], [u0 + ub, za - vb_], [u0 + ub, zb2 - vb_], [u0 + ua, zb2 - va_]],
                         uv1=uv1 if uv1 is not None else runoff_uv1(runoff, u0 + ua, u0 + ub, za, zb2), col=col)
            continue
        for za, zb2, kd, oa, ob in segs:
            # the wall under a window sill is marked from the sill (ADR 0097 / 0107); elsewhere the parapet run-off
            marks = None
            if sills is not None and kd in ("window", "ribbon") and zb2 - za > 0.15 and not str(mat).startswith("plinth"):
                marks = sill_marks(sills, ua, ub, za, zb2, oa, ob, (zb2 - zb) / max(zt - zb, 1e-6))
            if marks is None and runoff is not None and len(runoff) > 3 and runoff[3]:
                # ADR 0196: the run-off block table cuts the quad (runoff_cells); regions without the table take the
                # line below unchanged (bit-identical output)
                marks = [(q0 - u0, q1 - u0, uv1, z0_, z1_)
                         for q0, q1, z0_, z1_, uv1 in runoff_cells(runoff, u0 + ua, u0 + ub, za, zb2, mat)]
            if marks is None:
                marks = [(ua, ub, runoff_uv1(runoff, u0 + ua, u0 + ub, za, zb2))]
            for c0, c1, uv1, *zz in marks:
                z0_, z1_ = zz if zz else (za, zb2)
                va_, vb_ = (gnd(u0 + c0), gnd(u0 + c1)) if gnd else (vref, vref)
                acc.quad(layer, mat, P(c0, z0_), P(c1, z0_), P(c1, z1_), P(c0, z1_),
                         uv=[[u0 + c0, z0_ - va_], [u0 + c1, z0_ - vb_], [u0 + c1, z1_ - vb_], [u0 + c0, z1_ - va_]],
                         uv1=uv1, col=col)
    n3 = np.append(nout[:2], 0.0)
    d3 = np.append(d[:2], 0.0)
    for (ua, ub, va, vb, depth, kind, mat_in) in [o[:7] for o in ops]:
        back = -n3 * depth
        A, B, C, D = (np.array(P(ua, va)), np.array(P(ub, va)), np.array(P(ub, vb)), np.array(P(ua, vb)))
        if depth <= 0.0 and isinstance(mat_in, tuple):
            # props-fix-s24: FLAT atlas opening (depth 0) - the cell carries frame, grille and glass, no reveal / sill
            # geometry (2 triangles instead of ~18); used by the outbuildings of rural tiles to stay inside the
            # triangle budget. Every other opening has depth > 0 and takes the path below unchanged.
            _, rects, fa, fb, ga, gb = mat_in
            nr = len(rects)
            for j, (cu, cv, cw, ch) in enumerate(rects):
                a0, a1 = max(fa, j / nr), min(fb, (j + 1) / nr)
                if a1 - a0 < 1e-6:
                    continue
                t0, t1 = (a0 - fa) / (fb - fa), (a1 - fa) / (fb - fa)
                Pa, Pb = A + (B - A) * t0, A + (B - A) * t1
                lu0, lu1 = cu + cw * (a0 * nr - j), cu + cw * (a1 * nr - j)
                lv0, lv1 = cv + ch * ga, cv + ch * gb
                acc.quad(layer, "facade_atlas", Pa, Pb, Pb + (D - A), Pa + (D - A),
                         uv=[[lu0, lv0], [lu1, lv0], [lu1, lv1], [lu0, lv1]])
            continue
        rv = reveal or "reveal_" + ("hall" if mat.startswith("hall") else "plaster")
        # reveals (facing into the opening)
        acc.quad(layer, rv, A, B, B + back, A + back)          # sill (faces up)
        acc.quad(layer, rv, D + back, C + back, C, D)          # head (faces down)
        acc.quad(layer, rv, A + back, D + back, D, A)          # left jamb (faces +d)
        acc.quad(layer, rv, B, C, C + back, B + back)          # right jamb (faces -d)
        w, h = ub - ua, vb - va
        atlas = isinstance(mat_in, tuple)
        if atlas:                    # the cell carries frame, sashes, glass and what is behind it: no frame geometry
            _, rects, fa, fb, ga, gb = mat_in
            nr = len(rects)
            for j, (cu, cv, cw, ch) in enumerate(rects):
                a0, a1 = max(fa, j / nr), min(fb, (j + 1) / nr)
                if a1 - a0 < 1e-6:
                    continue
                t0, t1 = (a0 - fa) / (fb - fa), (a1 - fa) / (fb - fa)
                Pa, Pb = A + back + (B - A) * t0, A + back + (B - A) * t1
                lu0, lu1 = cu + cw * (a0 * nr - j), cu + cw * (a1 * nr - j)
                lv0, lv1 = cv + ch * ga, cv + ch * gb
                acc.quad(layer, "facade_atlas", Pa, Pb, Pb + (D - A), Pa + (D - A),
                         uv=[[lu0, lv0], [lu1, lv0], [lu1, lv1], [lu0, lv1]])
        else:
            acc.quad(layer, mat_in, A + back, B + back, C + back, D + back, uv=[[0, 0], [w, 0], [w, h], [0, h]])
        if atlas:
            if frame_3d and kind in ("window", "ribbon") and len(rects) == 1 and fb - fa > 0.9 and gb - ga > 0.9:
                _house_frame_3d(acc, layer, A, B, C, D, back, d3, n3, w, h, rects[0])
        elif kind in ("window", "balcony", "ribbon"):         # frame around the glass (PVC/alu profile, 7 cm face)
            fw = min(0.07, w / 5, h / 5)
            fr = back + n3 * 0.035
            Ao, Bo, Co, Do = A + fr, B + fr, C + fr, D + fr
            Ai, Bi = Ao + d3 * fw + [0, 0, fw], Bo - d3 * fw + [0, 0, fw]
            Ci, Di = Co - d3 * fw - [0, 0, fw], Do + d3 * fw - [0, 0, fw]
            fm = "hall_flashing" if mat.startswith("hall") else "window_frame"
            acc.quad(layer, fm, Ao, Bo, Bi, Ai)
            acc.quad(layer, fm, Bo, Co, Ci, Bi)
            acc.quad(layer, fm, Co, Do, Di, Ci)
            acc.quad(layer, fm, Do, Ao, Ai, Di)
        if not atlas and kind in ("window", "balcony") and w > 1.25:      # mullion
            um = 0.5 * (ua + ub)
            c = np.array(P(um, 0.5 * (va + vb))) + back + n3 * 0.04
            acc.box(layer, "window_frame", c, d3 * 0.035, n3 * 0.035, [0, 0, h / 2])
        if not atlas and kind == "ribbon":                   # ribbon window: mullions every ~1.35 m + transom
            k = max(1, int(round(w / 1.35)))
            for i in range(1, k):
                c = np.array(P(ua + w * i / k, 0.5 * (va + vb))) + back + n3 * 0.04
                acc.box(layer, "window_frame", c, d3 * 0.03, n3 * 0.035, [0, 0, h / 2])
            c = np.array(P(0.5 * (ua + ub), va + h * 0.72)) + back + n3 * 0.04
            acc.box(layer, "window_frame", c, d3 * (w / 2), n3 * 0.03, [0, 0, 0.025])
        if kind in ("window", "ribbon"):                     # transom + sill flashing
            # sheet sill over the whole reveal bottom with a 5 cm drip nose (r11: was a 10 cm strip at the wall face);
            # ADR 0336/0348 (bold_sill): bright exterior sill (reveal_plaster, +0 draws) projecting 4.2 cm proud with
            # top, front nose and underside drip shadow on small-town / rural houses (WORKING_VALUE).
            s_ext = 0.065 if bold_sill else 0.04
            s_nose = 0.042 if bold_sill else 0.025
            s_hh = 0.026 if bold_sill else 0.02
            s_mat = sill_mat or ("hall_flashing" if mat.startswith("hall") else ("reveal_plaster" if bold_sill else "window_sill"))
            c = np.array(P(0.5 * (ua + ub), va)) + n3 * (s_nose - depth / 2)
            acc.box(layer, s_mat, c, d3 * (w / 2 + s_ext),
                    n3 * (depth / 2 + s_nose), [0, 0, s_hh], skip=(2, 4, 5) if bold_sill else (0, 2, 4, 5))

# ---------------------------------------------------------------- boarded wooden house of Podlasie (ADR 0295, P1-1/P1-2)
# Review 2026-11-18 (docs/reports/REVIEW-2026-11-18-s24-knyszyn.md): a wooden house was "a wood texture on a box" and
# its boards repeated every tile. Every `dom_drewniany` now gets, on LOD0: boarded corners, vertical clamp battens
# (lisice) that cut long walls into runs shorter than the plank tile, a drip board over the plinth, a board at the
# eave line of a gable with VERTICAL boarding above it, and board surrounds with a head board round every opening.
# All sizes WORKING_VALUE (the review's 0.12-0.15 m corners / 0.10 m surrounds; no measured Knyszyn house in the repo).
WOOD_TILE_M = (6.0, 2.6)        # set_tile_m of wood_planks* (materials.py) - the UV0 period of the boarding, m
# joints between the board rows of the wood_siding set as fractions of the tile height (v up), measured on
# art-source/world/materials/wood_siding/High/T_wood_siding_BaseColor.png (row-mean minima; the two faint joints at
# 0.548 and 0.706 interpolated). tests/gis/test_wood_house_p1_s24.py re-measures them when the set is built.
WOOD_JOINT_V = (0.0317, 0.0815, 0.1343, 0.1870, 0.2388, 0.2876, 0.3394, 0.3940, 0.4438, 0.4966, 0.5484, 0.6001,
                0.6499, 0.7061, 0.7622, 0.8188, 0.8745, 0.9224, 0.9761)
WOOD_ROW_M = WOOD_TILE_M[1] / len(WOOD_JOINT_V)     # mean board pitch, m (0.137)
WOOD_CORNER_W = 0.14            # corner board face, m
WOOD_BATTEN_W = 0.12            # clamp batten (lisica), m
WOOD_PROUD = 0.03               # boards stand this far off the boarding, m
WOOD_RUN_M = 4.6                # target wall run between battens, m: every run < WOOD_TILE_M[0], so no run shows the
WOOD_RUN_MAX_M = 5.6            # tile twice (measured by the test: longest run of the Knyszyn houses)
WOOD_PLINTH_BOARD_H = 0.11      # drip board over the plinth, m
WOOD_GABLE_BOARD_H = 0.14       # board at the eave line of a gable end, m
WOOD_SURROUND_W = 0.10          # window / door surround boards, m
WOOD_HEAD_H = 0.16              # head board (nadokiennik) with a 3 cm cap that stands 3 cm further out
WOOD_TRIM_MAT = "wood_trim_white"


class _WoodUV:
    """Acc proxy for one run of boarding: UV0 of wood_planks* faces shifted by (du, dv) metres, and swapped when the
    boards run up the wall (gable). Every other material passes through unchanged."""

    def __init__(self, acc, du=0.0, dv=0.0, swap=False):
        self.acc, self.off, self.swap = acc, np.array([du, dv]), swap

    def _uv(self, mat, uv):
        if uv is None or not str(mat).startswith("wood_planks"):
            return uv
        uv = np.asarray(uv, float) + self.off
        return uv[:, ::-1] if self.swap else uv

    def add(self, layer, mat, V, T, UV=None, UV1=None, COL=None):
        self.acc.add(layer, mat, V, T, self._uv(mat, UV), UV1, COL)

    def quad(self, layer, mat, a, b, c, d, uv=None, uv1=None, col=None):
        self.acc.quad(layer, mat, a, b, c, d, self._uv(mat, uv), uv1, col)

    def box(self, *a, **k):
        self.acc.box(*a, **k)


def wood_phase(*key):
    """(du, dv) of one run of boarding: any shift along the boards, whole board rows across them (so the rows of
    neighbouring runs stay level, as the courses of a real wall do)."""
    return (WOOD_TILE_M[0] * FK.hfloat(*key, "wu"),
            WOOD_ROW_M * int(FK.hfloat(*key, "wv") * len(WOOD_JOINT_V)))


def wood_runs(L, ops, key):
    """Batten positions [u] that cut a boarded wall of length L into runs of about WOOD_RUN_M (never over
    WOOD_RUN_MAX_M when the openings leave room), off the openings and their surrounds."""
    if L <= WOOD_RUN_MAX_M:
        return []
    n = int(np.ceil(L / WOOD_RUN_M))
    wide = [(o[0] - WOOD_SURROUND_W - 0.12, o[1] + WOOD_SURROUND_W + 0.12, *o[2:]) for o in ops]
    out = []
    for j in range(1, n):
        u = FK.safe_u(L * j / n + (FK.hfloat(key, j, "lis") - 0.5) * 0.6, wide, L)
        if u is not None and WOOD_CORNER_W + 0.4 < u < L - WOOD_CORNER_W - 0.4 and all(abs(u - q) > 1.0 for q in out):
            out.append(float(u))
    return out


def wood_board(acc, mat, a, d, nout, u0, u1, z0, z1, proud, key, back=0.0, layer="buildings"):
    """One board [u0, u1] x [z0, z1] on the wall plane through `a` along `d`: its face `proud` m in front of the wall,
    both ends and the top edge (8 triangles; the underside is never seen from the street). A wood_planks* board takes
    ONE board row of the set (between two measured joints), its grain along the longer side; other materials are flat
    colours. back: the plane the board stands on is this far in front of the footprint wall. Returns the triangles."""
    if u1 - u0 < 0.02 or z1 - z0 < 0.02:
        return 0
    a, d, nout = (np.asarray(x, float) for x in (a, d, nout))
    W = lambda u, z: np.array([a[0] + d[0] * u + nout[0] * back, a[1] + d[1] * u + nout[1] * back, z])
    n3 = np.array([nout[0], nout[1], 0.0]) * proud
    F = lambda u, z: W(u, z) + n3
    uvs = [None] * 4
    if str(mat).startswith("wood_planks"):
        k = int(FK.hfloat(key, "row") * len(WOOD_JOINT_V)) % len(WOOD_JOINT_V)
        j0 = WOOD_JOINT_V[k]
        j1 = WOOD_JOINT_V[k + 1] if k + 1 < len(WOOD_JOINT_V) else WOOD_JOINT_V[0] + 1.0
        va, vb = (j0 + 0.008) * WOOD_TILE_M[1], (j1 - 0.008) * WOOD_TILE_M[1]
        s0 = WOOD_TILE_M[0] * FK.hfloat(key, "along")
        if z1 - z0 > u1 - u0:              # upright board: grain up
            lz = z1 - z0
            uvs[0] = [[s0, va], [s0, vb], [s0 + lz, vb], [s0 + lz, va]]
            uvs[1] = [[s0, va], [s0 + lz, va], [s0 + lz, vb], [s0, vb]]
            uvs[2] = [[s0, va], [s0 + lz, va], [s0 + lz, vb], [s0, vb]]
            uvs[3] = [[s0, va], [s0, vb], [s0 + proud, vb], [s0 + proud, va]]
        else:
            lu = u1 - u0
            uvs[0] = [[s0, va], [s0 + lu, va], [s0 + lu, vb], [s0, vb]]
            uvs[1] = [[s0, va], [s0, vb], [s0 + proud, vb], [s0 + proud, va]]
            uvs[2] = [[s0, va], [s0, vb], [s0 + proud, vb], [s0 + proud, va]]
            uvs[3] = [[s0, va], [s0 + lu, va], [s0 + lu, vb], [s0, vb]]
    acc.quad(layer, mat, F(u0, z0), F(u1, z0), F(u1, z1), F(u0, z1), uv=uvs[0])              # face
    acc.quad(layer, mat, F(u0, z0), F(u0, z1), W(u0, z1), W(u0, z0), uv=uvs[1])              # end at u0 (faces -d)
    acc.quad(layer, mat, W(u1, z0), W(u1, z1), F(u1, z1), F(u1, z0), uv=uvs[2])              # end at u1 (faces +d)
    acc.quad(layer, mat, F(u0, z1), F(u1, z1), W(u1, z1), W(u0, z1), uv=uvs[3])              # top edge
    return 8


def wood_surround(acc, a, d, nout, L, o, ztop, key, mat=WOOD_TRIM_MAT):
    """Board surround of one opening of a boarded wall: two jamb boards, a sill board under a window, a head board
    with a cap (nadokiennik). ztop: the wall top above the opening (where the head board with its cap does not fit
    under it, a plain head board; none when even that runs into the eave). Returns the triangle count."""
    u0, u1, z0, z1 = o[:4]
    w = WOOD_SURROUND_W
    if u0 - w < 0.02 or u1 + w > L - 0.02:
        return 0
    n = 0
    pr = WOOD_PROUD - 0.005         # 5 mm under the corner boards / battens: no coplanar faces where they meet
    zs = z0 - 0.09 if o[5] == "window" else z0
    n += wood_board(acc, mat, a, d, nout, u0 - w, u0, zs, z1, pr, key)
    n += wood_board(acc, mat, a, d, nout, u1, u1 + w, zs, z1, pr, key)
    if o[5] == "window":
        n += wood_board(acc, mat, a, d, nout, u0, u1, zs, z0 - 0.025, pr, key)
    if z1 + WOOD_HEAD_H + 0.03 <= ztop - 0.03:
        e = max(0.0, min(0.04, u0 - w - 0.02, L - 0.02 - u1 - w))
        n += wood_board(acc, mat, a, d, nout, u0 - w - e, u1 + w + e, z1, z1 + WOOD_HEAD_H, WOOD_PROUD + 0.01, key)
        n += wood_board(acc, mat, a, d, nout, u0 - w - e, u1 + w + e, z1 + WOOD_HEAD_H, z1 + WOOD_HEAD_H + 0.03,
                        WOOD_PROUD + 0.04, key)
    elif z1 + w <= ztop - 0.01:
        n += wood_board(acc, mat, a, d, nout, u0 - w, u1 + w, z1, z1 + w, pr, key)
    return n


def wood_wall(acc, wall, plinth, a, d, nout, L, zbot, zpl, zt, zref, u_acc, ops, prof, aw, ground, key, corners,
              runs_out=None, bold_sill=False, frame_3d=False):
    """LOD0 wall of a boarded house on one outline edge (ADR 0295, review 2026-11-18 P1-1 / P1-2).
    Boarding: horizontal boards up to the eave line zt in runs between clamp battens, every run with its own UV phase
    (wood_phase), so no two runs - and no two houses - show the same boards; above the eave line of a gable end the
    boards run up (UV0 swapped), with the loft window `aw` (attic_window) in its column. Boards on top (the wall's own
    material unless noted): corner boards at the convex ends `corners` = (start, end), battens, a drip board over the
    plinth, a board along the eave line of a gable, surrounds of the openings (WOOD_TRIM_MAT).
    prof: roof profile over the edge [(u, z)] or None (flat top). Returns the triangle count of the boards on top."""
    n = 0
    mat_fn = lambda u0, u1, z0, z1: plinth if z1 <= zpl + 1e-6 else wall
    sill_m = WOOD_TRIM_MAT if bold_sill else None
    bat = wood_runs(L, ops, key)
    us = [0.0] + bat + [L]
    for j, (s0, s1) in enumerate(zip(us, us[1:])):
        du, dv = wood_phase(key, j)
        FK.wall_pieces(wall_with_openings, _WoodUV(acc, du, dv), a + d * s0, d, nout, s1 - s0, zbot, zt,
                       [(o[0] - s0, o[1] - s0, *o[2:]) for o in ops], u_acc + s0, zref, [zpl], [], mat_fn,
                       ground=ground, bold_sill=bold_sill, frame_3d=frame_3d, sill_mat=sill_m)
        if runs_out is not None:
            runs_out.append(float(s1 - s0))
    gable = (prof is not None and len(prof) == 3 and abs(prof[0][1] - prof[2][1]) < 0.3
             and prof[1][1] - max(prof[0][1], prof[2][1]) > 0.8)
    if prof is not None:
        g = _WoodUV(acc, *wood_phase(key, "top"), swap=gable)
        base_z, pr = (lambda u: zt), prof
        if aw and gable:
            base_z = lambda u: aw["zband"] if aw["u0"] < u < aw["u1"] else zt
            pr = sorted(set(prof) | {(u, _prof_z(prof, u)) for u in (aw["u0"], aw["u1"])})
            o = aw["op"]
            FK.wall_pieces(wall_with_openings, g, a + d * aw["u0"], d, nout, aw["u1"] - aw["u0"], zt, aw["zband"],
                           [(o[0] - aw["u0"], o[1] - aw["u0"], *o[2:])], u_acc + aw["u0"], zref, [], [],
                           lambda *_: wall, bold_sill=bold_sill, frame_3d=frame_3d, sill_mat=sill_m)
            n += wood_surround(acc, a, d, nout, L, o, aw["zband"] + 0.4, f"{key}:aw")
        wall_top_fill(g, "buildings", wall, a, d, pr, base_z, u_acc, zref)
    ztop = lambda u: _prof_z(prof, min(max(u, 0.0), L)) if prof is not None else zt
    e0, e1 = (WOOD_PROUD if corners[0] else 0.0), (WOOD_PROUD if corners[1] else 0.0)
    if L > 2 * WOOD_CORNER_W + 0.3:
        if corners[0]:
            n += wood_board(acc, wall, a, d, nout, -e0, WOOD_CORNER_W, zpl, min(ztop(0.0), ztop(WOOD_CORNER_W)),
                            WOOD_PROUD, f"{key}:c0")
        if corners[1]:
            n += wood_board(acc, wall, a, d, nout, L - WOOD_CORNER_W, L + e1, zpl,
                            min(ztop(L), ztop(L - WOOD_CORNER_W)), WOOD_PROUD, f"{key}:c1")
    for j, u in enumerate(bat):
        n += wood_board(acc, wall, a, d, nout, u - WOOD_BATTEN_W / 2, u + WOOD_BATTEN_W / 2, zpl,
                        zt if gable else min(ztop(u - WOOD_BATTEN_W / 2), ztop(u + WOOD_BATTEN_W / 2)), WOOD_PROUD,
                        f"{key}:b{j}")
    # drip board over the plinth, left out under the doors
    cuts = sorted((o[0] - 0.02, o[1] + 0.02) for o in ops if o[5] == "door" and o[2] < zpl + WOOD_PLINTH_BOARD_H)
    u = -e0 - 0.015 if corners[0] else 0.0
    for c0, c1 in cuts + [(L + (e1 + 0.015 if corners[1] else 0.0), None)]:
        n += wood_board(acc, wall, a, d, nout, u, min(c0, L + e1 + 0.015), zpl - 0.02, zpl - 0.02 + WOOD_PLINTH_BOARD_H,
                        WOOD_PROUD + 0.015, f"{key}:p{u:.1f}")
        if c1 is None:
            break
        u = max(u, c1)
    if gable:
        n += wood_board(acc, wall, a, d, nout, -e0 - 0.01 if corners[0] else 0.0, L + (e1 + 0.01 if corners[1] else 0.0),
                        zt - WOOD_GABLE_BOARD_H / 2, zt + WOOD_GABLE_BOARD_H / 2, WOOD_PROUD + 0.01, f"{key}:g")
    for j, o in enumerate(ops):
        if o[5] in ("window", "door") and o[1] - o[0] >= 0.4 and o[3] <= zt + 1e-6:
            n += wood_surround(acc, a, d, nout, L, o, min(ztop(o[0]), ztop(o[1])), f"{key}:s{j}")
    return n


def ring_edges(ring):
    c = np.asarray(ring.coords)[:-1]
    keep = []
    n = len(c)
    for i in range(n):              # drop nearly collinear / tiny vertices
        a, b, cc = c[i - 1], c[i], c[(i + 1) % n]
        v1, v2 = b - a, cc - b
        cr = abs(v1[0] * v2[1] - v1[1] * v2[0]) / max(np.linalg.norm(v1) * np.linalg.norm(v2), 1e-9)
        if cr > 0.03 or np.linalg.norm(v1) > 6:
            keep.append(b)
    c = np.asarray(keep) if len(keep) >= 3 else c
    return [(c[i], c[(i + 1) % len(c)]) for i in range(len(c))]


def roof_flat(acc, layer, poly, z, mat="roof_membrane", attic=0.3, skylights=False, key=""):
    inner = poly.buffer(-0.25, join_style="mitre")
    if inner.is_empty or attic <= 0:
        inner, attic = poly, 0.0
    for g in getattr(inner, "geoms", [inner]):
        if g.geom_type != "Polygon":
            continue
        tri = shapely.constrained_delaunay_triangles(g)
        T = np.array([np.asarray(t.exterior.coords)[:3] for t in tri.geoms])
        if not len(T):
            continue
        cr = (T[:, 1, 0] - T[:, 0, 0]) * (T[:, 2, 1] - T[:, 0, 1]) - (T[:, 1, 1] - T[:, 0, 1]) * (T[:, 2, 0] - T[:, 0, 0])
        T[cr < 0] = T[cr < 0][:, [0, 2, 1]]
        V = np.concatenate([T.reshape(-1, 2), np.full((len(T) * 3, 1), z - attic)], axis=1)
        acc.add(layer, mat, V, np.arange(len(V)).reshape(-1, 3), V[:, :2])
        if attic > 0:   # attic: inner faces + cap
            for ring in [g.exterior, *g.interiors]:
                cc = np.asarray(ring.coords)
                if ring.is_ccw != (ring is g.exterior):
                    cc = cc[::-1]
                for a, b in zip(cc, cc[1:]):
                    # inner face looks into the roof (left of CCW travel)
                    acc.quad(layer, "hall_flashing", [b[0], b[1], z - attic], [a[0], a[1], z - attic],
                             [a[0], a[1], z], [b[0], b[1], z])
        cap = poly.difference(g)
        for cg in getattr(cap, "geoms", [cap]):
            if cg.geom_type != "Polygon" or cg.area < 1e-3:
                continue
            tri = shapely.constrained_delaunay_triangles(cg)
            T = np.array([np.asarray(t.exterior.coords)[:3] for t in tri.geoms])
            if not len(T):
                continue
            cr = (T[:, 1, 0] - T[:, 0, 0]) * (T[:, 2, 1] - T[:, 0, 1]) - (T[:, 1, 1] - T[:, 0, 1]) * (T[:, 2, 0] - T[:, 0, 0])
            T[cr < 0] = T[cr < 0][:, [0, 2, 1]]
            V = np.concatenate([T.reshape(-1, 2), np.full((len(T) * 3, 1), z)], axis=1)
            acc.add(layer, "hall_flashing", V, np.arange(len(V)).reshape(-1, 3), V[:, :2])
    if skylights and poly.area > 3000:
        core = poly.buffer(-8.0)
        if core.is_empty:
            return
        # ADR 0238 D39: the grid starts 3 m in from one corner of the rotated core; the two directions of the long
        # axis (ang, ang - pi) start it from opposite corners. Both are built and the one with fewer skylights is used
        # (equal: ang) - the same pick whatever corner shapely starts its rectangle at, never more than before.
        ang = _angle(poly)
        grids = [_skylight_grid(core, a) for a in (ang, ang - math.pi)]
        for cx, cy, ca, sa in min(grids, key=len):
            acc.box(layer, "skylight", [cx, cy, z - attic + 0.25], [ca * 1.5, sa * 1.5, 0], [-sa * 1.0, ca * 1.0, 0],
                    [0, 0, 0.25])


def _skylight_grid(core, ang):
    """Skylight centres (x, y, cos, sin): a 12 x 9 m grid along ang from the corner of the rotated core, inside it."""
    ca, sa = math.cos(ang), math.sin(ang)
    x0, y0, x1, y1 = shapely.affinity.rotate(core, -ang, origin=(0, 0), use_radians=True).bounds
    out = []
    for gx in np.arange(x0 + 3, x1 - 3, 12.0):
        for gy in np.arange(y0 + 3, y1 - 3, 9.0):
            cx, cy = gx * ca - gy * sa, gx * sa + gy * ca
            if core.contains(shapely.Point(cx, cy)):
                out.append((cx, cy, ca, sa))
    return out


def _angle(poly):
    """Direction of the long side of the minimum rotated rectangle (roofs.stable_rect), modulo pi, in [0, pi) (ADR 0238
    D39: the same side walked the other way round - which one shapely starts the ring at moves with float noise - gave
    the skylight grid another origin: Dojlidy `…BAD2` 600 / 660 triangles under a 1e-12 m translation). An edge within
    RF.RECT_TIE_RAD of east-west counts as east (not 0 on one machine and pi - 1e-16 on another)."""
    r = np.asarray(RF.stable_rect(poly).exterior.coords)
    d = np.diff(r, axis=0)
    k = int(np.argmax(np.hypot(d[:, 0], d[:, 1])))
    a = math.atan2(d[k, 1], d[k, 0]) % math.pi
    return a - math.pi if a > math.pi - RF.RECT_TIE_RAD else a


def gable(acc, layer, rect, zeave, zridge, wall_mat, roof_mat):
    """Gable roof over a rectangle (ridge along the long side) + gable-end wall triangles."""
    c = np.asarray(rect.exterior.coords)[:4]
    if not Polygon(c).exterior.is_ccw:
        c = c[::-1]
    e = [np.linalg.norm(c[(i + 1) % 4] - c[i]) for i in range(4)]
    k = 0 if e[0] >= e[1] else 1          # c[k]->c[k+1] is a long side
    a, b, cc, d = (c[(k + i) % 4] for i in range(4))
    m1, m2 = 0.5 * (a + d), 0.5 * (b + cc)  # ridge ends above the short sides
    ov = 0.4
    t = (b - a) / np.linalg.norm(b - a)
    m1o, m2o = m1 - t * ov, m2 + t * ov
    def P(p, z):
        return [p[0], p[1], z]
    # slopes with overhang
    nn1 = (a - m1) / max(np.linalg.norm(a - m1), 1e-6)
    nn2 = (cc - m2) / max(np.linalg.norm(cc - m2), 1e-6)
    drop = ov * (zridge - zeave) / max(np.linalg.norm(a - m1), 1e-6)
    ao, bo = a - t * ov + nn1 * ov, b + t * ov + nn1 * ov
    co, do = cc + t * ov + nn2 * ov, d - t * ov + nn2 * ov
    acc.quad(layer, roof_mat, P(ao, zeave - drop), P(bo, zeave - drop), P(m2o, zridge), P(m1o, zridge))
    acc.quad(layer, roof_mat, P(co, zeave - drop), P(do, zeave - drop), P(m1o, zridge), P(m2o, zridge))
    # gable triangles (short sides): b->cc and d->a
    for p, q, m in ((b, cc, m2), (d, a, m1)):
        V = [P(p, zeave), P(q, zeave), P(m, zridge)]
        L = np.linalg.norm(q - p)
        acc.add(layer, wall_mat, V, [[0, 1, 2]], [[0, zeave], [L, zeave], [L / 2, zridge]])


def _prof_z(prof, u):
    for (u0, z0), (u1, z1) in zip(prof, prof[1:]):
        if u0 - 1e-9 <= u <= u1 + 1e-9:
            return z0 + (z1 - z0) * (u - u0) / max(u1 - u0, 1e-9)
    return prof[-1][1]


def wall_top_fill(acc, layer, mat, a, d, prof, base, u_acc, zref, col=None):
    """Wall between a stepped base line and a sloping top (gable ends, walls under a hip / mono-pitch roof):
    prof = [(u, z_top)] linear between entries, base(u) = z of the rectangle below (constant between entries).
    Same UV0 as wall_with_openings (u along the wall, v above the reference ground)."""
    for (u0, z0), (u1, z1) in zip(prof, prof[1:]):
        zb = base(0.5 * (u0 + u1))
        pts = [(u0, zb), (u1, zb)] + ([(u1, z1)] if z1 - zb > 1e-3 else []) + ([(u0, z0)] if z0 - zb > 1e-3 else [])
        if len(pts) < 3 or u1 - u0 < 1e-4:
            continue
        V = [[a[0] + d[0] * u, a[1] + d[1] * u, z] for u, z in pts]
        UV = [[u_acc + u, z - zref] for u, z in pts]
        COL = np.tile(col, (len(V), 1)) if col is not None else None
        acc.add(layer, mat, V, [[0, 1, 2]] if len(pts) == 3 else [[0, 1, 2], [0, 2, 3]], UV, COL=COL)


def attic_window(prof, zmin, zref, zbase, sh, storeys, key, small_town=False, joinery=None, wooden=False):
    """Window in a gable end above the eave line (ADR 0091): the attic storey of a house whose BDOT10k storey count
    does not fit under the eave gets a full window, a cold loft a small light (60 %). Returns None or
    {"op": opening, "u0", "u1": the wall column that rises to "zband" as a rectangle (the opening sits in it)}."""
    if len(prof) != 3 or abs(prof[0][1] - prof[2][1]) > 0.3 or prof[1][1] - zmin < 1.9:
        return None
    um, zm = prof[1]
    ns = sum(1 for s_ in range(storeys) if min(zref + zbase + s_ * sh + 2.3, zmin - 0.22) - (zref + zbase + s_ * sh) >= 1.5)
    attic = storeys > ns
    if not attic and (zm - zmin < 2.3 or FA.hint(key, "loft") % 5 >= 3):
        return None
    rv = REVEAL_SMALL_TOWN_WOOD if (small_town and wooden) else REVEAL_SMALL_TOWN if small_town else REVEAL_ETICS
    wv = joinery[FA.hint(key, "aw") % len(joinery)] if joinery else FA.hint(key, "aw")
    for w, hgt in (((1.2, 1.4), (0.9, 1.1)) if attic else ((0.6, 0.6),)):
        sill = zref + zbase + ns * sh + 0.9 if attic else zmin + 0.42 * (zm - zmin)
        sill = max(sill, zmin - 0.9)
        zband = min(_prof_z(prof, um - w / 2 - 0.3), _prof_z(prof, um + w / 2 + 0.3))
        if um - w / 2 - 0.3 > prof[0][0] + 0.2 and sill + hgt + 0.3 <= zband:
            return {"op": (um - w / 2, um + w / 2, sill, sill + hgt, rv, "window", cells("house", wv)),
                    "u0": um - w / 2 - 0.3, "u1": um + w / 2 + 0.3, "zband": zband}
    return None


# ------------------------------------------------------------------------------------------- facades
def _house_rows(zref, zbase, sh, storeys, ztop):
    """Window rows of a house wall that fit under ztop - the same rule as facade_openings (ADR 0348)."""
    n = 0
    for s in range(storeys):
        z0 = zref + zbase + s * sh
        head = min(z0 + 2.3, ztop - 0.22)
        sill = max(z0 + 0.9 - max(0.0, 1.15 - (head - z0 - 0.9)), z0 + 0.6)
        if head - sill < 0.9:
            break
        n += 1
    return n


def facade_openings(typ, L, zref, ztop, storeys, key, is_main, docks_here, variant=None, sh=None, zbase=0.3):
    """Openings for one wall edge (u along the edge from its start), in absolute z:
    (ua, ub, va, vb, depth, kind, infill[, meta]). infill: a material name or atlas cells (cells()).
    variant: ribbon (office: ribbon windows on the upper storeys), balcony (block: balcony doors every second
    bay from the 1st floor), drive_door (hall: one 4.0 x 4.5 m sectional door on the main facade), main.
    Blocks and offices read the storey rows of the facade_far set (FA.far_plan), so LOD0 and LOD1 show the same
    windows; sill and window height scale with the storey height (k = sh / FA.FAR_ROW_H) on both."""
    variant = variant or {}
    ops = []
    hv = lambda *k: FA.hint(key, *k)
    if typ == "hall":
        if docks_here:
            return ops
        if is_main and L > 6:
            n = max(1, int(L // 40))
            for i in range(n):
                um = (i + 0.5) * L / n + (2.5 if i % 2 else -2.5)
                ops.append((um - 0.5, um + 0.5, zref + 0.15, zref + 2.25, 0.08, "door", cells("door_steel", hv("pd", i))))
        if L > 18 and hfloat(key, "win") < 0.55 and variant.get("hall_windows", True):
            zw = min(zref + 3.2, ztop - 1.6)
            pitch = 6.0
            n = int((L - 6) // pitch)
            wv = hv("hw")                       # one window type per wall
            for i in range(n):
                um = (L - (n - 1) * pitch) / 2 + i * pitch
                if any(abs(um - (o[0] + o[1]) / 2) < 1.6 for o in ops):
                    continue
                ops.append((um - 1.0, um + 1.0, zw, zw + 1.0, 0.12, "window", cells("hallw", wv)))
        if variant.get("drive_door") and variant.get("main") and L > 25 and ztop - zref > 5.5:
            um = L - 7.0
            ops = [o for o in ops if o[1] < um - 2.6 or o[0] > um + 2.6]
            ops.append((um - 2.0, um + 2.0, zref + 0.02, zref + 4.5, 0.2, "door", "garage_door"))
        return ops
    if typ == "shed":
        rural = variant.get("rural")
        if is_main and L > 3.2 and hfloat(key, "gar") < (0.85 if rural else 0.6):
            n = max(1, min(2 if rural else 4, int(L // 3.2)))
            for i in range(n):
                um = (i + 0.5) * L / n
                ops.append((um - 1.25, um + 1.25, zref + 0.05, zref + 2.2, 0.1, "door", cells("garage", hv("g", i))))
        elif is_main and L > 2:
            ops.append((L / 2 - 0.5, L / 2 + 0.5, zref + 0.05, zref + 2.15, 0.06, "door", cells("door_steel", hv("sd"))))
        if rural and L >= 3.6:
            # ADR 0238 d. props-fix-s24: small barred windows (the `base` cell: 0.9 x 0.45 m window with a grille), one per 3.5-7.5 m of
            # wall, never beside a door, under the eave; walls shorter than 3.6 m stay blank
            ww, wh, ws = RURAL_SHED_WIN
            nw = 1 if L < 5.5 else 2 if L < 9.5 else 3
            for i in range(nw):
                if hfloat(key, f"rw{i}") > (0.92 if is_main else 0.8):
                    continue
                um = (i + 0.5) * L / nw + (hfloat(key, f"rwj{i}") - 0.5) * 0.8
                z0 = zref + ws
                if z0 + wh > ztop - 0.25 or um - ww / 2 < 0.5 or um + ww / 2 > L - 0.5:
                    continue
                if any(um + ww / 2 + 0.5 > o[0] and um - ww / 2 - 0.5 < o[1] for o in ops):
                    continue
                ops.append((um - ww / 2, um + ww / 2, z0, z0 + wh, RURAL_SHED_REVEAL_M, "window", cells("base", hv("rw", i))))
        return ops
    sh = sh or {"office": 3.5, "block": 2.8, "house": 2.9}[typ]
    pitch = {"office": 3.0, "block": 3.0, "house": 2.7}[typ]    # house: 2 windows from 6.4 m, 3 from 9.1 m (ADR 0091)
    n = int((L - 1.0) // pitch)
    if typ == "house":
        n = min(n, 3)
        if n == 0 and L > 2.6:
            n = 1
    if n < 1:
        return ops
    um0 = (L - (n - 1) * pitch) / 2
    door_i = n // 2 if is_main else -1
    if typ == "house":
        rv = (REVEAL_SMALL_TOWN_WOOD if (variant.get("small_town") and variant.get("wooden"))
              else REVEAL_SMALL_TOWN if variant.get("small_town") else REVEAL_ETICS)
        jn = variant.get("joinery")
        for s in range(storeys):
            z0 = zref + zbase + s * sh
            head = min(z0 + 2.3, ztop - 0.22)       # low eaves: the window head goes right under the wall plate
            sill = max(z0 + 0.9 - max(0.0, 1.15 - (head - z0 - 0.9)), z0 + 0.6)
            if head - sill < 0.9:
                break
            for i in range(n):
                um = um0 + i * pitch
                if s == 0 and i == door_i:
                    # ADR 0097 (review 0094 P2-b): the door sill sits on the plinth top (floor level), the plinth runs
                    # on under it and build() adds the landing / steps; was zref + 0.15, cut through the plinth
                    zd = max(zref + 0.15, min(variant.get("door_z", zref + 0.15), ztop - 0.25 - 2.25))
                    ops.append((um - 0.5, um + 0.5, zd, zd + 2.25, 0.15, "door", cells("door_house", hv("hd"))))
                    continue
                if not is_main and n > 1 and hv("hx", s, i) % 5 == 0:     # blank bay (side / north walls), 1 in 5
                    continue
                wv = jn[hv("hw", s, i) % len(jn)] if jn else hv("hw", s, i)
                ops.append((um - 0.6, um + 0.6, sill, head, rv, "window", cells("house", wv)))
        return ops
    k = sh / FA.FAR_ROW_H
    if typ == "block" and variant.get("basement") and zbase >= 0.8:   # basement windows in the high plinth
        for i in range(n):
            if i == door_i or hv("bs", i) % 3 == 0:
                continue
            um = um0 + i * pitch
            ops.append((um - 0.45, um + 0.45, zref + 0.25, zref + 0.70, 0.10, "window", cells("base", hv("b", i))))
    groups = FA.far_groups(typ, storeys, variant.get("balcony"), variant.get("ribbon"), key.rsplit(":", 1)[0])
    if variant.get("town_windows"):                  # ADR 0336: small-town low/pitched offices keep framed windows
        groups = ["office" if g == "office_d" else g for g in groups]
    ns = FA.far_storeys(groups, sh, ztop - 0.3 - zref - zbase)
    plan = FA.far_plan(groups[:ns], key)
    jn = variant.get("joinery")
    for s in range(ns):
        z0 = zref + zbase + s * sh
        group, row, off = FA.far_storey(plan, s)
        if group == "ribbon":
            vs = [v for i in range(n) for v in (FA.far_entry(group, row, off, i)[1],) * 2]
            ops.append((um0 - 1.5, um0 + (n - 1) * pitch + 1.5, z0 + 0.9 * k, z0 + 2.5 * k, 0.12, "ribbon", cells("off", *vs)))
            continue
        for i in range(n):
            um = um0 + i * pitch
            if i == door_i:
                if s == 0:
                    ops.append((um - 0.8, um + 0.8, zref + 0.15, zref + 2.4, 0.15, "door",
                                cells("door_block", hv("db") if typ == "block" else 1 + hv("db") % 2)))
                    continue
                if typ == "block":                # stairwell axis above the entrance
                    ops.append((um - 0.6, um + 0.6, z0 + 0.9 * k, z0 + 2.1 * k, REVEAL_ETICS, "window", cells("stair", hv("st"))))
                    continue
            if variant.get("town_windows") and jn:   # ADR 0336: Podlasie small-town offices use muntined house frames
                wv = jn[hv("tw", s, i) % len(jn)]
                ops.append((um - 0.65, um + 0.65, z0 + 0.9 * k, z0 + (0.9 + 1.45) * k, REVEAL_SMALL_TOWN, "window",
                            cells("house", wv)))
                continue
            ck, cv = FA.far_entry(group, row, off, i)
            if ck == "bal":                       # balcony door + window; the balcony itself: build() (meta)
                # ADR 0097 (review 0094 P1-b): the balustrade is the building's type (row group); 12 % of the balconies
                # are what the tenants did to theirs (bars with flower boxes, reed mat, a repainted or replaced sheet)
                bv = FA.bal_type(group)
                if hv("balx", s, i) % 100 < BAL_EXCEPT_PCT:
                    bv = BAL_EXCEPT[hv("balxv", s, i) % len(BAL_EXCEPT)]
                ops.append((um - 1.05, um - 0.15, z0 + 0.05, z0 + 0.05 + 2.2 * k, REVEAL_ETICS, "bdoor", cells("bdoor", cv), bv))
                ops.append((um - 0.15, um + 0.95, z0 + 0.05 + 0.85 * k, z0 + 0.05 + 2.2 * k, REVEAL_ETICS, "window", cells("bwin", cv)))
                continue
            w = FA.KINDS[ck][0]
            ops.append((um - w / 2, um + w / 2, z0 + 0.9 * k, z0 + (0.9 + FA.KINDS[ck][1]) * k, REVEAL_ETICS, "window", cells(ck, cv)))
    return ops


def authored_openings(rule, wins, L, zref, key, door):
    """LOD0 openings of an authored office wall (ADR 0180, frontage.facade_windows): ribbon bands and stair-column
    windows with the facade-atlas cells of their far rows (so LOD0 and LOD1 show the same joinery), the entrance on
    the main facade."""
    ops = []
    if door:
        um = FR.facade_door_u(rule, L)
        ops.append((um - 0.8, um + 0.8, zref + 0.15, zref + 2.4, 0.15, "door", cells("door_block", 1 + FA.hint(key, "db") % 2)))
    rv = rule["reveal_m"]
    for u0, u1, z0, z1, g, row, off, lights in wins:
        if g == "ribbon":
            n = FR.ribbon_lights(u1 - u0)                           # one `off` cell per light, two lights per bay
            vs = [FA.far_entry(g, row, off, i // 2)[1] for i in range(n)]
            ops.append((u0, u1, z0, z1, rv, "ribbon", cells("off", *vs)))
        elif lights:                                                # light band (ADR 0190): one office-row window
            rects = []                                              # per light, cropped as on LOD1 (FR.band_lights)
            for li_, (lrow, lbay, crop) in enumerate(lights):
                if lrow == FR.BLIND_ROW:
                    rects.append(FR.blind_rect(lbay))
                    continue
                cu, cv_, cw, ch = FA.cell(*FA.FAR_ROWS[g][lrow][lbay])
                half = FR.sash_half(li_, rule.get("sashes", 2))        # ADR 0200: one sash per light
                if half is not None:
                    cu, cw = cu + half * cw / 2, cw / 2
                rects.append((cu, cv_ + ch * crop, cw, ch * (1.0 - crop)))
            ops.append((u0, u1, z0, z1, rv, "ribbon", ("atlas", rects, 0.0, 1.0, 0.0, 1.0)))
        else:
            ck, cv = FA.far_entry(g, row, off, 0)
            ops.append((u0, u1, z0, z1, rv, "window", cells(ck, cv)))
    return ops


def docks_for(b, poly, yard, hero, zsample):
    """Dock positions along yard-facing facades of a warehouse hall."""
    out = []
    if yard is None or yard.is_empty:
        return out
    ring = poly.exterior
    edges = ring_edges(ring)
    if not ring.is_ccw:
        edges = [(q, p) for p, q in edges[::-1]]
    num = 1
    for ei, (p, q) in enumerate(edges):
        L = float(np.linalg.norm(q - p))
        if L < 16:
            continue
        d = (q - p) / L
        nout = np.array([d[1], -d[0]])
        strip = Polygon([p + nout * 2, q + nout * 2, q + nout * 14, p + nout * 14])
        if strip.intersection(yard).area / strip.area < 0.6:
            continue
        n = int((L - 8) // S.DOCK_PITCH)
        if hero:
            n = min(n, hero.get("max_docks_per_facade", 24))
        else:
            n = min(n, 12)
        if n < 2:
            continue
        u0 = (L - (n - 1) * S.DOCK_PITCH) / 2
        mid = p + d * (L / 2) + nout * 3
        zy = float(zsample(np.array([mid[0]]), np.array([mid[1]]))[0])
        docks = []
        for i in range(n):
            u = u0 + i * S.DOCK_PITCH
            docks.append({"u": u, "num": num})
            num += 1
        a0 = p + d * (u0 - 2.5)
        a1 = p + d * (u0 + (n - 1) * S.DOCK_PITCH + 2.5)
        apron = Polygon([a0, a1, a1 + nout * S.DOCK_APRON_L, a0 + nout * S.DOCK_APRON_L])
        out.append({"id": f"{b['id']}:docks{ei}", "edge": (p, q), "docks": docks, "yard_z": zy, "apron": apron})
    return out


def build_dock(acc, layer, p, d, nout, u, zy, num):
    """One loading dock at u along the wall (yard level zy)."""
    zf = zy + S.DOCK_FLOOR_H
    c = p + d * u
    W, _H = S.DOCK_DOOR_W, S.DOCK_DOOR_H
    def P(off_u, z, out=0.0):
        q = c + d * off_u + nout * out
        return np.array([q[0], q[1], z])
    # shelter: two side curtains + header (black PVC), proud of the wall
    sw, sh, sd = S.DOCK_SHELTER_W, S.DOCK_SHELTER_H, S.DOCK_SHELTER_D
    side = (sw - W) / 2 + 0.05
    for sgn in (-1, 1):
        cc = P(sgn * (W / 2 + side / 2), zf + sh / 2 - 0.1, sd / 2)
        acc.box(layer, "dock_shelter", cc, np.append(d * side / 2, 0), np.append(nout * sd / 2, 0), [0, 0, sh / 2 - 0.1])
        # yellow guide stripe on the curtain face
        acc.box(layer, "paint_yellow", P(sgn * (W / 2 + side / 2), zf + sh / 2 - 0.1, sd + 0.005),
                np.append(d * 0.05, 0), np.append(nout * 0.005, 0), [0, 0, sh / 2 - 0.3])
    acc.box(layer, "dock_shelter", P(0, zf + sh - 0.35, sd / 2), np.append(d * (sw / 2 + 0.05), 0),
            np.append(nout * sd / 2, 0), [0, 0, 0.35])
    # leveller lip (steel) + hazard stripes front, bumpers
    acc.box(layer, "steel_checker", P(0, zf - 0.03, 0.2), np.append(d * 1.0, 0), np.append(nout * 0.2, 0), [0, 0, 0.03])
    acc.quad(layer, "hazard_stripes", P(-1.0, zf - 0.33, 0.405), P(1.0, zf - 0.33, 0.405), P(1.0, zf - 0.06, 0.405),
             P(-1.0, zf - 0.06, 0.405), uv=[[0, 0], [2.0, 0], [2.0, 0.27], [0, 0.27]])
    acc.box(layer, "steel_checker", P(0, zf - 0.2, 0.2), np.append(d * 1.0, 0), np.append(nout * 0.2, 0), [0, 0, 0.14])
    for sgn in (-1, 1):
        acc.box(layer, "rubber_black", P(sgn * 1.15, zf - 0.25, 0.06), np.append(d * 0.13, 0), np.append(nout * 0.06, 0),
                [0, 0, 0.25])
        # wheel guide (yellow steel tube on the apron)
        acc.box(layer, "paint_yellow", P(sgn * 1.35, zy + 0.12, 2.6), np.append(d * 0.06, 0), np.append(nout * 2.2, 0),
                [0, 0, 0.12])
    # number plate above the shelter (white plate, black digits: atlas UV)
    s = str(num)
    pw = 0.32 * len(s)
    z0 = zf + sh + 0.15
    acc.quad(layer, "plate_white", P(-pw / 2 - 0.06, z0 - 0.06, 0.03), P(pw / 2 + 0.06, z0 - 0.06, 0.03),
             P(pw / 2 + 0.06, z0 + 0.46, 0.03), P(-pw / 2 - 0.06, z0 + 0.46, 0.03))
    for k, ch in enumerate(s):
        x0 = -pw / 2 + k * 0.32
        dgt = int(ch)
        acc.quad(layer, "dock_digits", P(x0, z0, 0.035), P(x0 + 0.32, z0, 0.035), P(x0 + 0.32, z0 + 0.4, 0.035),
                 P(x0, z0 + 0.4, 0.035), uv=[[dgt / 10, 0], [(dgt + 1) / 10, 0], [(dgt + 1) / 10, 1], [dgt / 10, 1]])
    # dock signal light (red/green box) right of the door
    acc.box(layer, "dock_light", P(W / 2 + side + 0.35, zf + 1.4, 0.08), np.append(d * 0.12, 0), np.append(nout * 0.08, 0),
            [0, 0, 0.22])
    # dock floodlight on a short wall arm above the shelter, left of centre (LED head tilted to the apron)
    zl = zf + sh + 0.75
    acc.box(layer, "steel_galv", P(-0.9, zl, 0.25), np.append(d * 0.025, 0), np.append(nout * 0.25, 0), [0, 0, 0.025])
    acc.box(layer, "luminaire_housing", P(-0.9, zl - 0.06, 0.55), np.append(d * 0.16, 0), np.append(nout * 0.1, 0),
            [0, 0, 0.05])
    acc.quad(layer, "lamp_glass", P(-1.04, zl - 0.115, 0.47), P(-0.76, zl - 0.115, 0.47), P(-0.76, zl - 0.115, 0.63),
             P(-1.04, zl - 0.115, 0.63))


def build_dock_lod1(acc, p, d, nout, u, zy, num, layer="buildings_low"):
    """LOD1 counterpart of build_dock (Low / Medium away from the route, High beyond the LOD switch): the same
    silhouette - black shelter frame (two curtains + header) with the yellow guide stripes, leveller block,
    wheel guides on the apron - as boxes without their wall-side / bottom faces, in materials LOD1 draws anyway
    (FK.L1_MAT: one draw per material per chunk). Hazard stripes, number plate, bumpers, signal light and floodlight
    are LOD0 detail. review r6 / HANDOVER pkt 7 (Low and High show the same docks)."""
    zf = zy + S.DOCK_FLOOR_H
    c = p + d * u
    W = S.DOCK_DOOR_W

    def P(off_u, z, out=0.0):
        q = c + d * off_u + nout * out
        return np.array([q[0], q[1], z])
    sw, sh, sd = S.DOCK_SHELTER_W, S.DOCK_SHELTER_H, S.DOCK_SHELTER_D
    side = (sw - W) / 2 + 0.05
    shelter = FK.L1_MAT["dock_shelter"]
    for sgn in (-1, 1):
        cc = P(sgn * (W / 2 + side / 2), zf + sh / 2 - 0.1, sd / 2)
        acc.box(layer, shelter, cc, np.append(d * side / 2, 0), np.append(nout * sd / 2, 0),
                [0, 0, sh / 2 - 0.1], skip=(0, 2))
        x = sgn * (W / 2 + side / 2)
        acc.quad(layer, "paint_yellow", P(x - 0.05, zf + 0.1, sd + 0.005), P(x + 0.05, zf + 0.1, sd + 0.005),
                 P(x + 0.05, zf + sh - 0.5, sd + 0.005), P(x - 0.05, zf + sh - 0.5, sd + 0.005))
    acc.box(layer, shelter, P(0, zf + sh - 0.35, sd / 2), np.append(d * (sw / 2 + 0.05), 0),
            np.append(nout * sd / 2, 0), [0, 0, 0.35], skip=(2,))
    # leveller block (lip + front in one box: top, front, ends)
    steel = FK.L1_MAT["steel_checker"]
    acc.box(layer, steel, P(0, zf - 0.17, 0.2), np.append(d * 1.0, 0), np.append(nout * 0.2, 0),
            [0, 0, 0.17], skip=(0, 2))
    for sgn in (-1, 1):            # wheel guides on the apron: top, both sides, the far end
        acc.box(layer, "paint_yellow", P(sgn * 1.35, zy + 0.12, 2.6), np.append(d * 0.06, 0), np.append(nout * 2.2, 0),
                [0, 0, 0.12], skip=(0, 2))


# ------------------------------------------------------------------------------------------- main
def load(fc, origin, overrides, hero=None):
    ox, oy = origin
    ovr = target_sets(overrides)
    datum = lod1_base_datum(overrides)
    small_town_ov = next((o for o in overrides if o.get("kind") == "facade_rules" and o.get("small_town")), None)
    small_town = small_town_ov is not None
    small_town_roofs = bool(small_town_ov.get("small_town_roofs", True)) if small_town else False
    out = []
    for f in fc["features"]:
        p = f["properties"]
        for k, poly in enumerate(f["geometry"]["coordinates"]):
            pl = Polygon(np.asarray(poly[0]) - [ox, oy], [np.asarray(h) - [ox, oy] for h in poly[1:]])
            pl = shapely.make_valid(pl)
            if pl.geom_type != "Polygon":
                pl = max(getattr(pl, "geoms", [pl]), key=lambda g: g.area if g.geom_type == "Polygon" else 0)
                if pl.geom_type != "Polygon":
                    continue
            pl = shapely.orient_polygons(pl) if hasattr(shapely, "orient_polygons") else shapely.geometry.polygon.orient(pl)
            bid = f["id"] if k == 0 else f"{f['id']}#{k}"
            o = ovr.get(f["id"], {})
            if hero and f["id"] in hero:      # replaced by an authored asset (streetscape.hero_building)
                o = {**o, "hero_asset": hero[f["id"]]}
            if o.get("footprint_open_m"):     # ADR 0180: authored straightening of the outline - a morphological
                d_ = float(o["footprint_open_m"])        # opening drops protrusions narrower than 2 x d (mitred corners)
                # + steps under 0.15 m; ADR 0200 `footprint_simplify_m`: authored tolerance - near-collinear edges
                # of one photographed wall become one edge (a facade rule sees the whole wall)
                op = pl.buffer(-d_, join_style=2).buffer(d_, join_style=2).simplify(
                    float(o.get("footprint_simplify_m", 0.15)))
                if op.geom_type == "Polygon" and not op.is_empty:
                    pl = shapely.geometry.polygon.orient(op)
            if o.get("height_m"):             # ADR 0167: authored height (structures with no LoD1 / BDOT height)
                p = {**p, "height_m": float(o["height_m"])}
            if o.get("storeys"):              # ADR 0185: authored storey count (read off a photo)
                p = {**p, "storeys": int(o["storeys"])}
            out.append({"id": bid, "poly": pl, "props": p, "ovr": o, "typ": "roof" if p.get("is_roof_only") else
                        classify(p, pl.area, o)})
            out[-1]["sub"] = TY.subtype(out[-1]["typ"], p, pl.area, o, small_town=small_town)
            if datum:
                out[-1]["lod1_datum"] = True
    out = out + building_parts(out, overrides, ovr, datum)
    wall_gates(out, overrides)
    if hall_openings_at_ground(overrides):        # ADR 0242, opt-in per region
        for b in out:
            b["hall_openings_ground"] = True
    if any(o.get("kind") == "facade_rules" and o.get("runoff_shuffle") for o in overrides):
        for b in out:
            b["runoff_shuffle"] = True
    if any(o.get("kind") == "facade_rules" and o.get("rural_outbuildings") for o in overrides):
        for b in out:                             # ADR 0238 d. props-fix-s24, opt-in per region (class `shed` only)
            if (b["typ"] == "shed" and not b["ovr"].get("typology") and b["poly"].area >= RURAL_SHED_MIN_AREA_M2
                    and b["props"].get("function") not in RURAL_SHED_NO_ROOF_FUNCS):
                b["rural_outbuilding"] = True
    if any(o.get("kind") == "facade_rules" and o.get("roof_weathering") for o in overrides):
        for b in out:                             # weathering-s24, opt-in per region (roof COLOR_0)
            b["roof_weather"] = True
    if small_town:                                # ADR 0336, opt-in per region
        for b in out:
            b["small_town"] = True
            if not small_town_roofs:
                b["small_town_roofs"] = False
    return out


GATE_SNAP_M = 2.0              # an authored gate point may lie this far from the wall line it belongs to


def wall_gates(blds, overrides):
    """ADR 0196: authored sectional gates on hall walls (override `kind: wall_gates`, `gates: [{at_en: [E, N], width_m,
    height_m}]`). A gate is positional - it goes to the hall wall nearest to its point (within GATE_SNAP_M), so it
    survives a re-cut of the footprint by `building_part` overrides. Plain sectional door, no lettering. A gate with
    no hall wall in reach is an authoring error (never silently dropped)."""
    for o in overrides:
        if o.get("kind") != "wall_gates":
            continue
        for k, g in enumerate(o.get("gates") or []):
            pt = shapely.Point(*[float(x) for x in g["at_en"]])
            best = None
            for b in blds:
                if b["typ"] != "hall" or b["ovr"].get("hero_asset") or b["ovr"].get("frontage"):
                    continue
                dd = b["poly"].exterior.distance(pt)
                if dd <= GATE_SNAP_M and (best is None or dd < best[0]):
                    best = (dd, b)
            if best is None:
                raise ValueError(f"wall_gates {o['id']} gate {k}: no hall wall within {GATE_SNAP_M} m of {g['at_en']}")
            best[1].setdefault("gates", []).append({"p": np.array(pt.coords[0]), "w": float(g.get("width_m", 4.0)),
                                                    "h": float(g.get("height_m", 4.5)), "id": f"{o['id']}:{k}"})


def gate_openings(gates, a, d, L, zref, zt, ops):
    """Openings of the authored gates that sit on the wall edge a + d * [0, L] (kind `gate`, the dock door material:
    LOD1 of a hall chunk draws it already where there are docks). Rule openings a gate overlaps are dropped."""
    nout = np.array([d[1], -d[0]])
    for g in gates or ():
        if g.get("done"):
            continue
        rel = g["p"] - a
        u, off = float(rel @ d), abs(float(rel @ nout))
        w = g["w"]
        if off > GATE_SNAP_M + 1e-6 or not (w / 2 + 0.6 <= u <= L - w / 2 - 0.6):
            continue
        h = min(g["h"], zt - zref - 1.2)
        if h < 2.5:
            continue
        ops[:] = [o_ for o_ in ops if o_[1] < u - w / 2 - 0.8 or o_[0] > u + w / 2 + 0.8]
        ops.append((u - w / 2, u + w / 2, zref + 0.02, zref + h, 0.2, "gate", "dock_door"))
        g["done"] = True


def hall_openings_at_ground(overrides):
    """ADR 0242, override `kind: building_rules` / `hall_openings_at_ground: true` (opt-in per region; regions without
    the key keep their output byte for byte)."""
    return any(o.get("kind") == "building_rules" and o.get("hall_openings_at_ground") for o in overrides)


HALL_DOOR_SILL_M = 0.15        # personnel door sill above the ground under it (the rule's zref + 0.15)
HALL_GATE_SILL_M = 0.02        # drive door / sectional gate (the rule's zref + 0.02)


def openings_to_ground(ops, ground, zt):
    """ADR 0242 (review s20-0185 P1-5, "drzwi 1,2-1,7 m nad gruntem"): the doors and gates of a hall wall stand on the
    ground UNDER THEM instead of the median ground of the whole outline (zref) - on a sloping plot the doors of the
    low side hung in the wall and those of the high side were buried. ground(u) = terrain level at u along the edge;
    the sill is the highest of the two jambs and the middle (never buried). An opening that would come within 0.6 m
    of the wall top is cut down; one left under 2.0 m keeps its rule position. Windows, docks (yard level) and
    louvres are not touched."""
    out = []
    for o in ops:
        if o[5] not in ("door", "gate"):
            out.append(o)
            continue
        g = max(float(ground(u)) for u in (o[0], (o[0] + o[1]) / 2, o[1]))
        z0 = g + (HALL_DOOR_SILL_M if o[5] == "door" and o[6] != "garage_door" else HALL_GATE_SILL_M)
        h = min(o[3] - o[2], zt - 0.6 - z0)
        out.append((o[0], o[1], z0, z0 + h, *o[4:]) if h >= 2.0 else o)
    return out


def target_sets(overrides):
    """{building id: set} of the `target: {building}` overrides. ADR 0185: several overrides may target one building
    (the regions' overrides.yaml is merged block by block from parallel branches) - their sets are merged in file
    order, a later key replacing an earlier one (before: the last override replaced the earlier sets whole). A
    building_part is targeted as `override:<its id>`."""
    out = {}
    for o in overrides:
        bid = (o.get("target") or {}).get("building")
        if bid:
            out[bid] = {**out.get(bid, {}), **(o.get("set") or {})}
    return out


def lod1_base_datum(overrides):
    """ADR 0185, override `kind: building_rules` / `lod1_base_datum: true` (opt-in per region). The LoD1 2024
    `measuredHeight` is the height of the LoD1 solid above its bottom face (`ground_z_evrf2007` = the lowest ground of
    the outline), while build() stands a building on the median ground of its outline: on a slope a large hall came
    out 2-3.5 m taller than surveyed (bialystok-dojlidy: median +0.22 m, p95 +1.42 m, max +3.52 m over 329 buildings
    with a LoD1 base). With the rule the roof is at LoD1 base + height."""
    return any(o.get("kind") == "building_rules" and o.get("lod1_base_datum") for o in overrides)


LOD1_DATUM_MIN = 0.6           # the datum rule never cuts a building below this share of its LoD1 height


def roof_height(b, zref):
    """Height of the roof above the reference ground zref (median ground of the outline). Default: the height of the
    footprint data. With the LoD1 base datum rule (lod1_base_datum) and a known base level: base + height - zref."""
    p = b["props"]
    h = float(p.get("height_m") or 6.0)
    base = p.get("ground_z_evrf2007")
    if not b.get("lod1_datum") or base is None or not str(p.get("height_source", "")).startswith(
            ("gugik_lod1", "authored_override")):
        return h
    return max(float(base) + h - zref, LOD1_DATUM_MIN * h, 2.5)


def building_parts(blds, overrides, target=None, datum=False):
    """ADR 0179: authored volumes the footprint data merges into one outline (override `kind: building_part`): a
    BDOT10k hall whose office block is three times the LoD1 height of the hall gets the block as its own building.
    `polygon_en` (region-local E/N ring, traced on the orthophoto), `height_m`, optional `function` / `storeys`,
    `cut_from` (building ids whose footprint loses the ring, so the two volumes do not overlap) and `set` (the
    keys of a `target: {building}` override). Regions without such overrides get an empty list."""
    out = []
    for o in overrides:
        if o.get("kind") != "building_part":
            continue
        pl = shapely.make_valid(Polygon(np.asarray(o["polygon_en"], float)))
        if pl.geom_type != "Polygon" or pl.area < 1.0:
            raise ValueError(f"building_part {o['id']}: polygon_en is not a simple ring")
        pl = shapely.orient_polygons(pl) if hasattr(shapely, "orient_polygons") else shapely.geometry.polygon.orient(pl)
        for b in list(blds):
            if b["id"] in (o.get("cut_from") or []):
                rest = shapely.make_valid(b["poly"].difference(pl.buffer(0.05)))
                parts = sorted((g for g in getattr(rest, "geoms", [rest]) if g.geom_type == "Polygon" and g.area > 1.0),
                               key=lambda g: -g.area)
                parts = [shapely.orient_polygons(g) if hasattr(shapely, "orient_polygons")
                         else shapely.geometry.polygon.orient(g) for g in parts]
                b["poly"] = parts[0]
                for k, g in enumerate(parts[1:], 1):       # the part splits its host: every piece stays a building
                    out.append({**b, "id": f"{b['id']}#cut{k}", "poly": g})
        p = {"function": o.get("function"), "height_m": float(o["height_m"]), "storeys": o.get("storeys"),
             "height_source": "authored_override", "name": o.get("name")}
        # ADR 0185: `target: {building: "override:<id>"}` overrides add to / replace keys of the part's own set;
        # `ground_z_evrf2007` = level the height is measured from (with the region's lod1_base_datum rule; default:
        # the median ground of the ring, as before)
        s = {**(o.get("set") or {}), **((target or {}).get(f"override:{o['id']}") or {})}
        if s.get("height_m"):
            p["height_m"] = float(s["height_m"])
        if s.get("storeys"):
            p["storeys"] = int(s["storeys"])
        if s.get("storeys_fixed"):            # ADR 0242 (opt-in per part): storey_plan keeps the authored count
            p["storeys_fixed"] = True
        if o.get("ground_z_evrf2007") is not None:
            p["ground_z_evrf2007"] = float(o["ground_z_evrf2007"])
        out.append({"id": f"override:{o['id']}", "poly": pl, "props": p, "ovr": s, "typ": classify(p, pl.area, s)})
        out[-1]["sub"] = TY.subtype(out[-1]["typ"], p, pl.area, s)
        if datum:
            out[-1]["lod1_datum"] = True
    return out


def lod1_wall(acc, typ, wall, a, c_, nout, L, zbot, zref, zt, u_acc, storeys, sh, zbase, kind, pitched, zone_wall=None,
              runoff=None, pieces=None, fkey="", balcony=False, plinth="plinth_dark", ground=None, authored=None,
              small_town=False, zpl_override=None, town_windows=False, col=None, col_plinth=None):
    """LOD1 wall edge: cheap (8-14 triangles) but not a box face - plinth, window zone (office / block: far facade
    material, UV1 = (bay, storey) grid), wall above, projecting coping at the attic. runoff: as wall_with_openings
    (hall_wall_* bands get the same wall-top TEXCOORD_1 as LOD0, so the streaks do not pop at the LOD switch).
    pieces(layer): draws the wall zbot..zt itself (halls: the LOD0 plinth / colour bands / dock openings, see build());
    lod1_wall then only adds the coping ledge."""
    lay = "buildings_low"

    def P(q, z):
        return [float(q[0]), float(q[1]), float(z)]

    def band(z0, z1, mat, uv1=None, bcol=None):
        if z1 - z0 < 0.02:
            return
        if uv1 is None and str(mat).startswith("hall_wall"):
            uv1 = runoff_uv1(runoff, u_acc, u_acc + L, z0, z1)
        acc.quad(lay, mat, P(a, z0), P(c_, z0), P(c_, z1), P(a, z1),
                 uv=[[u_acc, z0 - zref], [u_acc + L, z0 - zref], [u_acc + L, z1 - zref], [u_acc, z1 - zref]],
                 uv1=uv1, col=bcol)
    # ADR 0238: a pitched block / office (kamienica) keeps the window rows of the far set on LOD1 - only the coping
    # ledge goes (the roof closes the wall top). ADR 0336 (small_town): pitched houses keep a plinth band on LOD1 too.
    if (pitched and typ == "house") or typ not in ("hall", "office", "block") or L < 3.0:     # short jogs: plain
        if small_town and typ == "house" and L >= 3.0 and zpl_override is not None and zpl_override - zbot >= 0.05 and zt > zpl_override + 0.2:
            if ground is not None:
                ga, gb = ground(u_acc), ground(u_acc + L)
                acc.quad(lay, "plinth_dark", P(a, zbot), P(c_, zbot), P(c_, zpl_override), P(a, zpl_override),
                         uv=[[u_acc, zbot - ga], [u_acc + L, zbot - gb], [u_acc + L, zpl_override - gb], [u_acc, zpl_override - ga]],
                         col=col_plinth)
            else:
                band(zbot, zpl_override, "plinth_dark", bcol=col_plinth)
            band(zpl_override, zt, wall, bcol=col)
            return
        band(zbot, zt, wall, bcol=col)
        return
    zpl = (zpl_override if zpl_override is not None
           else zref + (0.6 if typ == "hall" else zbase - 0.1 if typ == "block" else PLINTH_H.get(typ, 0.35)))
    if pieces is not None:
        pieces(lay)
        z = zt
    else:
        if typ != "hall" and ground is not None and zpl - zbot >= 0.02:     # plinth: v above the terrain (as LOD0)
            ga, gb = ground(u_acc), ground(u_acc + L)
            acc.quad(lay, plinth, P(a, zbot), P(c_, zbot), P(c_, zpl), P(a, zpl),
                     uv=[[u_acc, zbot - ga], [u_acc + L, zbot - gb], [u_acc + L, zpl - gb], [u_acc, zpl - ga]])
        else:
            band(zbot, zpl, "hall_plinth" if typ == "hall" else plinth)
        z = zpl
    if authored is not None and authored[0]["far"]:
        # ADR 0180: authored facade (override `facades`) - the plain strip of the far material with one quad per
        # window / band, the same rectangles LOD0 cuts as openings
        FR.lod1_facade(acc, authored[0], authored[1], np.asarray(a, float), (np.asarray(c_, float) - a) / L, L, z, zt)
        z = zt
    elif typ in ("office", "block") and L > 2.5 and authored is None:
        # ADR 0081: the window zone is drawn from the storey rows of the facade_far set - one quad per chunk of
        # storeys that are consecutive rows (FA.far_plan, the plan LOD0 reads its cells from) and per 8 bays (one
        # atlas period: half-float UV), UV0 in row atlas metres; the wall left and right of the bays takes the plain
        # strip of the same material (same tone as the zone)
        n = int((L - 1.0) // FA.FAR_PITCH)
        zw0 = zref + zbase
        groups = FA.far_groups(typ, storeys, balcony, kind == "ribbon", fkey.rsplit(":", 1)[0])
        if town_windows:                             # ADR 0336: light-framed rows on LOD1 too
            groups = ["office" if g == "office_d" else g for g in groups]
        ns = FA.far_storeys(groups, sh, zt - 0.3 - zw0)
        if n >= 1 and ns >= 1:
            far = f"{zone_wall or wall}__far_{kind}"
            ua = (L - n * FA.FAR_PITCH) / 2
            ub = ua + n * FA.FAR_PITCH
            zw1 = min(zw0 + ns * sh, zt - 0.3)
            d_ = (c_ - a) / L
            pv0, pv1 = FA.FAR_PLAIN_V

            def fq(u0, u1, z0, z1, uv):
                acc.quad(lay, far, P(a + d_ * u0, z0), P(a + d_ * u1, z0), P(a + d_ * u1, z1), P(a + d_ * u0, z1), uv=uv)
            pu0, pu1 = FA.FAR_PLAIN_U          # ADR 0184: a bay without a balcony slab edge
            plain = [[pu0, pv0], [pu1, pv0], [pu1, pv1], [pu0, pv1]]
            kk = sh / FA.FAR_ROW_H
            plan = FA.far_plan(groups[:ns], fkey)
            # the wall above the last storey (attic band) rides on the last chunk when the atlas is plain above its row
            fold = FA.far_plain_above(plan[-1][2], plan[-1][3] + plan[-1][1] - 1) and zt - zw1 < 0.85 * kk
            ztop = zt if fold else zw1
            fq(0.0, ua, z, ztop, plain)
            fq(ub, L, z, ztop, plain)
            for s0, cnt, g, r0, off in plan:
                z0 = z if s0 == 0 else zw0 + s0 * sh
                z1 = ztop if s0 + cnt == ns else zw0 + (s0 + cnt) * sh
                vr = FA.far_row_v(g, r0)
                v0, v1 = vr + (z0 - zw0 - s0 * sh) / kk, vr + (z1 - zw0 - s0 * sh) / kk
                # one quad for all bays: the atlas repeats every 8 bays; half-float u only rounds the two ends
                x0 = off * FA.FAR_PITCH
                fq(ua, ub, z0, z1, [[x0, v0], [x0 + ub - ua, v0], [x0 + ub - ua, v1], [x0, v1]])
            z = ztop
    if z < zt:
        band(z, zt, wall)
    if pitched:
        return
    # coping ledge over the top 0.25 m: one face leaning 0.12 m out at its foot (drip edge) and meeting the wall line
    # 5 cm above the roof, so it closes against the roof polygon without a top face (r10: -2 triangles per edge, pays
    # for the storey-row quads of ADR 0081)
    o = nout * 0.12
    za, zb_ = zt - 0.25, zt + 0.05
    acc.quad(lay, "hall_flashing", P(a + o, za), P(c_ + o, za), P(c_, zb_), P(a, zb_))


def build(buf, blds, hf, zsample, yard_union, roads_poly, report, sign_out=None, heroes=None):
    """Generate building meshes into buf; returns dock descriptions (for the paved aprons).
    heroes: streetscape.hero_depot.plan() result - a hero building takes its dock rows from the asset spec and, when
    the asset is ready, keeps only its collision prism (the visible hall is the asset, ADR 0071)."""
    all_docks = []
    counts = {}
    subtypes = {}
    roofs_other = {}
    pav_fronts = 0
    roof_kinds = {}
    canopy_skipped = 0
    wood_stats = {"runs": [], "tris": 0}        # ADR 0295 P1-2: boarding runs of the wooden houses, m
    lod1_house_openings = 0
    l1_pending, l1_cells, l1_fallback = [], set(), 0
    l1_frame_cells, l1_framed = {}, 0
    bal_count = 0
    frontages = 0
    frontage_props = []
    roof_masts_report = []
    btree = shapely.STRtree([b["poly"] for b in blds])
    any_st = any(b.get("small_town") for b in blds)
    any_st_roofs = any(b.get("small_town") and b.get("small_town_roofs", True) for b in blds)
    st_stats = {"buildings": 0, "stone_plinths": 0, "dormers": 0, "window_trim_tris": 0,
                "joinery_white": 0, "joinery_brown": 0, "roof_materials": {}}
    rw_stats = {"old": 0, "prl": 0, "new": 0}         # weathering-s24: roof age classes (report only when opted in)
    house_pal = house_palette(blds, roofs=SMALL_TOWN_ROOFS if any_st_roofs else None)
    Acc.runoff_tris = {"with_uv1": 0, "without_uv1": 0}
    signs = []
    for b in blds:
        poly, p, typ = b["poly"], b["props"], b["typ"]
        st_mode = bool(b.get("small_town"))
        rural_shed = typ == "shed" and bool(b.get("rural_outbuilding"))      # ADR 0238 d. props-fix-s24
        sub = b.get("sub") or TY.DEFAULT_SUBTYPE.get(typ, typ)
        counts[typ] = counts.get(typ, 0) + 1
        ring = np.asarray(poly.exterior.coords)
        zg = hf.sample(ring[:, 0], ring[:, 1])
        zref = float(np.median(zg))
        zbot = float(np.min(zg)) - 0.5
        h = roof_height(b, zref)
        ztop = zref + h
        key = b["id"]
        acc = Acc()
        if b["ovr"].get("hero_asset"):      # authored asset: only the collision prism of the footprint
            counts[typ] -= 1
            counts["hero_asset"] = counts.get("hero_asset", 0) + 1
            for a, c_ in ring_edges(poly.exterior):
                acc.quad("collision", "collision_building", [a[0], a[1], zbot], [c_[0], c_[1], zbot],
                         [c_[0], c_[1], ztop], [a[0], a[1], ztop])
            roof_flat(acc, "collision", poly, ztop, mat="collision_building", attic=0.0)
            acc.flush(buf, key)
            continue
        if typ == "roof":            # canopy on columns (fuel station, market / parking roof)
            # Both layers (W-H4): the LOD1 tier draws the same deck, fascia and columns, so
            # a tier switch never removes a roof structure from the street.
            zc = zref + min(max(h, 4.8), 6.0)
            cc = np.asarray(RF.stable_rect(poly).exterior.coords)[:4]
            cen = np.asarray(poly.centroid.coords[0])
            for layer in ("buildings", "buildings_low"):
                roof_flat(acc, layer, poly, zc + 0.6, mat="hall_flashing", attic=0.0)
                for a, c_ in ring_edges(poly.exterior):      # 0.6 m fascia band all round (was a 1 cm box)
                    acc.quad(layer, "canopy_fascia", [a[0], a[1], zc], [c_[0], c_[1], zc], [c_[0], c_[1], zc + 0.6],
                             [a[0], a[1], zc + 0.6])
                for q in cc:
                    v = cen + (q - cen) * 0.7
                    acc.box(layer, "steel_painted", [v[0], v[1], (zref + zc) / 2], [0.15, 0, 0], [0, 0.15, 0],
                            [0, 0, (zc - zref) / 2 + 0.3])
            acc.flush(buf, key)
            continue
        if typ == "hall":
            wall = b["ovr"].get("wall_material") or hpick(key, HALL_WALLS)
        elif typ == "block":
            wall = b["ovr"].get("wall_material") or hpick(key, TY.KAMIENICA_WALLS if sub == "kamienica" else BLOCK_WALLS)
        elif typ == "house":
            wall = b["ovr"].get("wall_material") or house_pal[key][0]
            if wall not in HOUSE_WALL_OVERRIDES:
                raise ValueError(f"building {b['id']}: unsupported house wall_material {wall!r}")
        elif typ == "shed":
            wall = (rural_shed_pick(key, RURAL_SHED_WALLS, "rswall") if rural_shed          # ADR 0238 d. props-fix-s24
                    else hpick(key, ["plaster_grey", "plaster_light", "brick_red", "hall_wall_silver"]))
        else:
            wall = b["ovr"].get("wall_material") or hpick(key, TY.PAVILION_WALLS if sub == "pawilon" else OFFICE_WALLS)
        # ADR 0126: authored frontage of a trade pavilion (override `frontage`): its own walls on both LODs
        front = FR.plan(b["ovr"].get("frontage")) if typ in ("office", "hall", "shed") else None
        if front:
            wall = front["wall"]
            frontages += 1
        # ADR 0180: authored window rule per facing of an office (override `facades`): blank gable with a stair
        # column, one window band per storey, a second wall colour
        facades = FR.facade_rules(b["ovr"].get("facades"), wall) if typ == "office" and not front else None
        hero = b["ovr"].get("hero")
        docks = []
        if typ == "hall" and (p.get("function") in WAREHOUSE_FUNCS or b["ovr"].get("docks")) and poly.area > 800:
            hero_h = (heroes or {}).get(b["id"])
            docks = hero_h["docks"] if hero_h else docks_for(b, poly, yard_union, b["ovr"] if hero else None, zsample)
            all_docks += docks
        storeys, sh, zbase = storey_plan(typ, h, p, sub)
        wooden = typ == "house" and storeys == 1 and poly.area < 120 and FK.hfloat(key, "wood") < 0.12
        if typ == "house" and (b["ovr"].get("typology") or b["ovr"].get("wall_material")):
            # authored (knyszyn-look-s23): `typology: dom_drewniany` or a boarding wall = wooden; any other authored
            # house subtype / wall = not wooden, whatever the footprint rule says
            wooden = (b["ovr"].get("typology") == "dom_drewniany"
                      or str(b["ovr"].get("wall_material", "")).startswith("wood_planks"))
        if rural_shed and str(wall).startswith("wood_planks"):
            wooden = True                    # ADR 0238 d. props-fix-s24: boarded outbuilding uses the board-wall generator
        if wooden and not rural_shed:
            sub = "dom_drewniany"
        subtypes[sub] = subtypes.get(sub, 0) + 1
        roof = None
        # ADR 0238: roof shape from an authored `roof_shape`, OSM roof:shape, or (blocks / offices) a LoD2 gable / hip
        # with a measured rise; None = the rule of the class (houses: roofs.plan from the LoD2 type, others: flat)
        rshape, rsrc = TY.roof_shape(typ, p, b["ovr"], small_town=st_mode)
        if typ == "house":          # ADR 0091: pitched roof over the real footprint (gable / hip / mono-pitch)
            near = [blds[j]["poly"] for j in btree.query(poly.buffer(0.6)) if blds[j] is not b]
            roof = RF.plan(poly, p, h, zref, lambda salt: FK.hfloat(key, salt), near, wooden, shape=rshape,
                           pitch_var=st_mode)
        elif rural_shed and rshape != "flat":
            # ADR 0238 d. props-fix-s24: the LoD2 roof type decides (1000 = flat stays flat); no LoD2 -> gable over >= 36 m2, else skillion
            near = [blds[j]["poly"] for j in btree.query(poly.buffer(0.6)) if blds[j] is not b]
            shp = rshape or (None if p.get("roof_type_lod2") else ("gable" if poly.area >= 36 else "mono"))
            roof = RF.plan(poly, p, h, zref, lambda salt: FK.hfloat(key, salt), near, False, shape=shp)
        elif typ in ("block", "office") and rshape in ("gable", "hip", "mono") and not front and not facades:
            near = [blds[j]["poly"] for j in btree.query(poly.buffer(0.6)) if blds[j] is not b]
            roof = RF.plan(poly, p, h, zref, lambda salt: FK.hfloat(key, salt), near, False, shape=rshape,
                           max_area=TY.KAMIENICA_MAX_AREA, pitch_var=st_mode)
        pitched = roof is not None
        if typ == "house":
            rk = f"{roof.kind}:{roof.source}" if pitched else "flat"
            roof_kinds[rk] = roof_kinds.get(rk, 0) + 1
        elif pitched or rsrc:
            rk = f"{sub}:{roof.kind if pitched else 'flat'}:{rsrc}"
            roofs_other[rk] = roofs_other.get(rk, 0) + 1
        if pitched and typ != "house":      # storeys fit under the eave (the LoD1 height includes a part of the roof)
            storeys, sh, zbase = storey_plan(typ, roof.zeave - zref + 0.5, p, sub)
        # ADR 0238: rule shopfront of a pavilion on the wall nearest to a road - only for buildings with no authored
        # set (an override keeps the facade its review approved)
        pav = sub == "pawilon" and not front and not facades and not (set(b["ovr"]) - OVR_ROOF_ONLY) and not pitched
        rect = RF.stable_rect(poly)
        rc_ = np.asarray(rect.exterior.coords)[:4]
        re_ = [float(np.linalg.norm(rc_[(i + 1) % 4] - rc_[i])) for i in range(4)]
        rk_ = 0 if re_[0] >= re_[1] else 1
        rect_along = (rc_[(rk_ + 1) % 4] - rc_[rk_]) / max(re_[rk_], 1e-6)
        rect_short = min(re_[0], re_[1])
        work = poly
        zeave = ztop
        if pitched:
            zeave, ztop = roof.zeave, roof.zridge
        # main facade = edge closest to a road
        edges = ring_edges(work.exterior)
        dist = [roads_poly.distance(shapely.Point(*(0.5 * (a + c_)))) if roads_poly is not None else 0 for a, c_ in edges]
        main = int(np.argmin(dist)) if dist else 0
        lens = [float(np.linalg.norm(c_ - a)) for a, c_ in edges]
        # ADR 0295 (P1-1): outer corners of the outline (turn of more than ~25 degrees) - a boarded house gets its
        # corner boards there; convex[i] = the corner at the START of edge i
        convex = []
        for i_ in range(len(edges)):
            dp_, dc_ = edges[i_ - 1][1] - edges[i_ - 1][0], edges[i_][1] - edges[i_][0]
            convex.append(float(dp_[0] * dc_[1] - dp_[1] * dc_[0]) > 0.42 * max(lens[i_ - 1] * lens[i_], 1e-9))
        # block: balconies on the long side(s) away from the main (entrance) facade
        # ADR 0091: balconies on the sunny long side (living rooms of the PRL blocks face S / W; WORKING_VALUE rule,
        # no per-building data) and on both long sides of 35 % of the blocks, on every wall run of at least one bay -
        # r10 put them on the two edges farthest from any road, so the blocks along the route showed none
        # ADR 0094 (review s9 P1-3): the sunny rule moved the balconies off the facades that had them (r10: the two
        # long edges farthest from a road, not the entrance side) instead of adding to them - both rules now apply, so
        # no facade loses its balconies; the CC0 photos of the Putry blocks show galleries on whole long sides
        bal_edges = set()
        if typ == "block" and storeys >= 3 and lens and b["ovr"].get("balconies", True) and sub != "kamienica":
            rn = np.array([rect_along[1], -rect_along[0]])
            sun = rn if float(rn @ BALCONY_SUN) >= 0 else -rn
            # ADR 0097 (review 0094 P1-d "gołe długie elewacje"): both long sides of every block (the CC0 photos of the
            # Putry / Bieżeństwa blocks show balconies along whole long sides); was 25 % of the blocks
            both = True
            for i, (ea_, ec_) in enumerate(edges):
                if lens[i] < 5.5:
                    continue
                de_ = (ec_ - ea_) / lens[i]
                ne_ = np.array([de_[1], -de_[0]])
                if abs(float(de_ @ rect_along)) > 0.7 and (both or float(ne_ @ sun) > 0.7):
                    bal_edges.add(i)
            for i in sorted(range(len(edges)), key=lambda i: -dist[i])[:2]:
                if lens[i] > 12 and i != main:
                    bal_edges.add(i)
        bal_group = None
        if bal_edges:
            cx_, cy_ = poly.centroid.coords[0]
            ek_ = f"estate:{int(cx_ // ESTATE_M)}:{int(cy_ // ESTATE_M)}"
            pair_ = (FA.BAL_GROUPS[FA.hint(ek_, "a") % len(FA.BAL_GROUPS)], FA.BAL_GROUPS[FA.hint(ek_, "b") % len(FA.BAL_GROUPS)])
            bal_group = pair_[0] if FK.hfloat(key, "balg") < 0.7 else pair_[1]
        variant = {"rural": rural_shed, "ribbon": typ == "office" and FK.hfloat(key, "ribbon") < 0.5,
                   "drive_door": typ == "hall" and FK.hfloat(key, "drive") < 0.5, "basement": typ == "block"}
        if typ == "hall" and b["ovr"].get("hall_windows") is False:     # ADR 0185: authored - the photographed
            variant["hall_windows"] = False                             # hall has no row of small windows
        if typ == "office" and b["ovr"].get("ribbon") is not None:      # ADR 0171: authored window type (the far
            variant["ribbon"] = bool(b["ovr"]["ribbon"])                # ribbon rows carry grey spandrels)
        # ADR 0336 (small-town Podlasie): consistent white or warm-brown muntined joinery per building, and low/pitched
        # town offices (Urzad Miasta, Biblioteka, shops) drop corporate anthracite/ribbon windows for traditional frames.
        st_joinery = None
        st_town_win = False
        st_surround = False
        if st_mode and typ in ("house", "office") and not front and not facades:
            is_brown = FK.hfloat(key, "joinery") < (0.45 if (wooden or storeys == 1) else 0.30)
            st_joinery = (1, 3) if is_brown else (0, 2)
            st_surround = (not wooden) and (FK.hfloat(key, "surround") < 0.55)
            variant["small_town"] = True
            variant["wooden"] = wooden
            variant["joinery"] = st_joinery
            if typ == "office" and not pav and (pitched or storeys <= 2) and b["ovr"].get("ribbon") is None:
                variant["ribbon"] = False
                variant["town_windows"] = True
                st_town_win = True
            if typ == "house" or st_town_win:
                st_stats["buildings"] += 1
                st_stats["joinery_brown" if is_brown else "joinery_white"] += 1
        scheme = FK.hall_scheme(key, wall) if typ == "hall" else None
        if scheme and b["ovr"].get("hall_bands") is False:      # ADR 0179: authored - the photographed hall is
            scheme = {**scheme, "low": None, "top": None}       # one cladding colour (no hashed plinth / top band)
        insulated = typ == "block" and (FK.hfloat(key, "etics") < BLOCK_ETICS_SHARE or bool(b["ovr"].get("wall_material")))
        # v3.1 horizontal bands: insulated blocks (35 %) get the window rows in the accent colour from the 1st
        # floor up; punched-window offices with >= 2 storeys (40 %) get darker spandrel bands between the rows
        # ribbon-window offices of >= 3 storeys (60 %): dark spandrel panels between the ribbons (1970s office
        # towers of the Białystok plants)
        bands = ((insulated and storeys >= 3 and FK.hfloat(key, "bands") < 0.35) or
                 (typ == "office" and not st_town_win and not variant["ribbon"] and storeys >= 2 and FK.hfloat(key, "spandrel") < 0.4) or
                 (typ == "office" and variant["ribbon"] and storeys >= 3 and FK.hfloat(key, "spandrel") < 0.6))
        if b["ovr"].get("bands") is not None:        # ADR 0126: authored (a photographed facade has them or not);
            bands = bool(b["ovr"]["bands"])          # false = one wall colour: no accent gable / stairwell field either
        one_tone = b["ovr"].get("bands") is False
        if typ == "block" and not insulated:
            wall = "panel_concrete"
        accent = FK.hpick(FK.ACCENT_PLASTER, key, "accent")
        plinth = FK.hpick(PLINTHS, key, "plinth") if typ in ("block", "office") else "plinth_dark"   # draws (Low)
        plinth_lod1 = plinth
        st_zpl = None
        if st_mode and typ in ("house", "office") and not front:
            pl_h = SMALL_TOWN_PLINTH_HS[FA.hint(key, "plh_st") % len(SMALL_TOWN_PLINTH_HS)]
            zg85 = float(np.percentile(zg, 85))
            zpl_cap = min(zref + (0.95 if typ == "house" else 0.75),
                          max(zref + 0.35, zeave - (2.35 if typ == "house" else 2.55)))
            st_zpl = min(max(zref + pl_h, zg85 + 0.35), zpl_cap)
            if typ == "house" and FK.hfloat(key, "stone_pl") < (0.45 if (storeys == 1 or wooden) else 0.25):
                plinth = "fieldstone_plinth"
                st_stats["stone_plinths"] += 1
            if typ == "house":
                # ADR 0348: the slope-safe plinth raises the floor line only while every window row still fits under
                # the eave - otherwise the top row went and left a blank 1-1.5 m band under the roof (dw09_house_close)
                zb_st = max(zbase, st_zpl - zref)
                if _house_rows(zref, zb_st, sh, storeys, zeave) >= _house_rows(zref, zbase, sh, storeys, zeave):
                    zbase = zb_st
                else:
                    st_stats["rows_kept"] = st_stats.get("rows_kept", 0) + 1
        if wooden and not rural_shed:
            wall = (b["ovr"]["wall_material"] if str(b["ovr"].get("wall_material", "")).startswith("wood_planks")
                    else wood_paint(key))
        # ADR 0348: 2-3 deterministic plaster shades + plinth shade per rural / small-town plaster house (+0 draws via COLOR_0)
        shades = (_house_shades(key)
                  if (st_mode and typ in ("house", "office") and not wooden and not front and not facades
                      and str(wall).startswith("plaster_"))
                  else None)
        if shades is None and rural_shed and str(wall).startswith("plaster_"):
            shades = rural_shed_shades(key)                          # darker, per-building tint (COLOR_0, 0 draws)
        u_acc = 0.0
        ro_blocks = (runoff_blocks(key, float(sum(lens)) + 1.0)
                     if b.get("runoff_shuffle") and typ == "hall" and not front else None)
        dock_edges = {tuple(np.round(dk["edge"][0], 2)): dk for dk in docks}
        # ADR 0238 D39: gate_openings marks a placed gate `done`; on a copy, so build() leaves the input as it was (a
        # second build of the same building - QA harness, regression tests - drew hall `…BC59` without its 2 gates)
        gates_b = [dict(g) for g in b.get("gates") or ()]
        nouts = []
        signed = laddered = False
        for ei, (a, c_) in enumerate(edges):
            L = float(np.linalg.norm(c_ - a))
            if L < 0.05:
                nouts.append(np.array([0.0, 0.0]))
                continue
            d = (c_ - a) / L
            nout = np.array([d[1], -d[0]])
            nouts.append(nout)
            rule = FR.facade_rule(facades, nout, L)
            wall_e = rule["wall"] if rule else wall  # wall colour of this edge (ADR 0180)
            lod1_main, lod1_zone = wall_e, None      # LOD1 colours follow what dominates the LOD0 wall (W-H4)
            lod1_wins = None
            lod1_pieces = None
            lod1_gfn = None
            edge_col = col_plinth = None
            dk = dock_edges.get(tuple(np.round(a, 2)))
            zt = zeave
            prof = None
            if pitched:                         # wall top = roof plane above this edge (ADR 0091)
                prof = roof.profile(a, c_)
                zt = min(z for _, z in prof)
            is_main = ei == main or (typ == "hall" and L > 30)
            door_z = (st_zpl if st_zpl is not None
                      else zref + PLINTH_H["house"] + 0.15 * round(FK.hfloat(key, "plh"))) if typ == "house" else None
            if rule:                                 # authored facade: the same rectangles on both LODs
                door_ = ei == main if rule.get("door") is None else rule["door"]      # ADR 0200: authored entrance
                lod1_wins = FR.facade_windows(rule, L, zref, zbase, sh, zt, storeys, f"{key}:{ei}", door=door_)
                ops = authored_openings(rule, lod1_wins, L, zref, f"{key}:{ei}", door_)
                n3_ = np.array([nout[0], nout[1], 0.0])
                for lu0, lu1, lz0, lz1 in FR.facade_lintels(rule, lod1_wins):       # ADR 0190: dark lintel line
                    lu0, lu1 = max(lu0, 0.0), min(lu1, L)
                    c0_, c1_ = np.array([*(a + d * lu0), lz0]), np.array([*(a + d * lu1), lz0])
                    p0_, p1_ = (n3_ * x_ for x_ in FR.LINTEL_PROUD_M)
                    up_ = np.array([0.0, 0.0, lz1 - lz0])
                    acc.quad("buildings", FR.LINTEL_MAT, c0_ + p0_, c1_ + p0_, c1_ + p0_ + up_, c0_ + p0_ + up_)
                    acc.quad("buildings", FR.LINTEL_MAT, c0_, c1_, c1_ + p0_, c0_ + p0_)                 # soffit
                    acc.quad("buildings", FR.LINTEL_MAT, c0_ + p0_ + up_, c1_ + p0_ + up_, c1_ + up_, c0_ + up_)
                    acc.quad("buildings_low", FR.LINTEL_MAT, c0_ + p1_, c1_ + p1_, c1_ + p1_ + up_, c0_ + p1_ + up_)
            else:
                ops = facade_openings(typ, L, zref, zt, storeys, f"{key}:{ei}", is_main, dk is not None,
                                      dict(variant, balcony=bal_group if ei in bal_edges else False, main=ei == main,
                                           door_z=door_z), sh=sh, zbase=zbase)
            if typ == "hall" and not front and gates_b:              # ADR 0196: authored sectional gates
                gate_openings(gates_b, a, d, L, zref, zt, ops)
            if typ == "hall" and not front and b.get("hall_openings_ground"):     # ADR 0242: sills on the ground
                ops = openings_to_ground(
                    ops, lambda u, a=a, d=d: hf.sample(np.array([a[0] + d[0] * u]), np.array([a[1] + d[1] * u]))[0], zt)
            if dk:
                zf = dk["yard_z"] + S.DOCK_FLOOR_H
                for dock in dk["docks"]:
                    ops.append((dock["u"] - S.DOCK_DOOR_W / 2, dock["u"] + S.DOCK_DOOR_W / 2, zf, zf + S.DOCK_DOOR_H,
                                0.25, "dock", "dock_door"))
            front_e = front
            pav_e = False
            if pav and ei == main and L >= TY.PAVILION_FRONT["min_len_m"]:
                front_e = FR.plan(TY.pavilion_front(wall, nout, zt - zref))
                pav_e = front_e is not None
                pav_fronts += pav_e
            if front_e:
                def gfn(uabs, a=a, d=d, ua0=u_acc):
                    q_ = a + d * (uabs - ua0)
                    return float(hf.sample(np.array([q_[0]]), np.array([q_[1]]))[0])
                if pav_e:                      # ADR 0238: LOD1 of a rule shopfront costs what the office wall did
                    FR.wall(acc, wall_with_openings, front_e, a, c_, nout, L, zbot, zref, zt, u_acc, ground=gfn,
                            layers=(FK.L0,))
                    FR.wall_lod1_flat(acc, front_e, a, c_, nout, L, zbot, zref, zt, u_acc, ground=gfn)
                else:
                    FR.wall(acc, wall_with_openings, front_e, a, c_, nout, L, zbot, zref, zt, u_acc, ground=gfn)
                sg = front_e["sign"]                   # functional fascia sign (facade_sign_<code>, no brands)
                if sg and not signed and L >= 8 and FR.faces(nout, sg["facing"]):
                    signs.append(FK.sign_instance(sg["code"], a, d, nout, L * float(sg.get("u", 0.5)),
                                                  zref + float(sg["z_m"]), f"{key}:{ei}"))
                    if float(sg.get("scale", 1.0)) != 1.0:      # ADR 0129: a fascia board legible from the road
                        signs[-1]["sz"] = round(float(sg["scale"]), 3)
                    signed = True
            elif typ == "hall":
                # plinth (concrete, up to dock floor) + cladding scheme + coping on top
                zpl = (dk["yard_z"] + S.DOCK_FLOOR_H) if dk else zref + 0.6
                # ADR 0185: authored plinth top (m, height datum) of a hall on a slope - the rule plinth is 0.6 m
                # above the MEDIAN ground of the outline, i.e. 2-3 m of dark wall on the low side of a large hall
                if not dk and b["ovr"].get("hall_plinth_z") is not None:
                    zpl = min(float(b["ovr"]["hall_plinth_z"]), zt - 1.0)
                zlow = FK.safe_z(zref + scheme["low"][1], ops, zpl, zt - 0.4, 0.45) if scheme["low"] else None
                ztopb = FK.safe_z(zt - 0.4 - scheme["top"][1], ops, zpl, zt - 0.4) if scheme["top"] else None

                def hall_mat(u0, u1, z0, z1, zpl=zpl, zlow=zlow, ztopb=ztopb):
                    if z1 <= zpl + 1e-6:
                        return "hall_plinth"
                    if zlow is not None and z1 <= zlow + 1e-6:
                        return scheme["low"][0]
                    if ztopb is not None and z0 >= ztopb - 1e-6:
                        return scheme["top"][0]
                    return wall
                # parapet run-off streaks (zacieki pod attyką): wall-top space in UV1, per-building pattern offset
                # (one constant shift per building, so u stays continuous round the corners) and streak length
                # scale (gutter halls shorter: the gutter takes most of the water)
                ro = (zt - 0.4, RUNOFF_PERIOD_M * FK.hfloat(key, "runoff_u"),
                      (0.55 if scheme["gutter"] else 0.8) + 0.7 * FK.hfloat(key, "runoff_l"))
                lod1_ro = (zt - 0.25, ro[1], ro[2])                  # LOD1: coping ledge over the top 0.25 m
                if ro_blocks is not None:                            # ADR 0196: shuffled run-off blocks, both LODs
                    ro, lod1_ro = (*ro, ro_blocks), (*lod1_ro, ro_blocks)
                FK.wall_pieces(wall_with_openings, acc, a, d, nout, L, zbot, zt - 0.4, ops, u_acc, zref,
                               [zpl, zlow, ztopb], [], hall_mat, runoff=ro)

                # LOD1 hall wall (HANDOVER pkt 7): the same plinth height, colour bands and dock doors as LOD0
                # (dock doors as recessed openings, ~10 triangles each; windows / personnel doors stay LOD0
                # detail), so Low and High show the same hall. Before: one ivory band, the red top band of this
                # hall and every dock existed on High only.
                def lod1_pieces(lay, a=a, d=d, nout=nout, L=L, zt=zt, hall_mat=hall_mat, zs=[zpl, zlow, ztopb],
                                dock_ops=[o for o in ops if o[5] in ("dock", "gate")], ro=lod1_ro):
                    FK.wall_pieces(wall_with_openings, acc, a, d, nout, L, zbot, zt, dock_ops, u_acc, zref, zs, [],
                                   hall_mat, layer=lay, runoff=ro, reveal=FK.L1_MAT["reveal_hall"])
                P3 = lambda q, z: [q[0], q[1], z]
                acc.quad("buildings", "hall_flashing", P3(a + nout * 0.03, zt - 0.4), P3(c_ + nout * 0.03, zt - 0.4),
                         P3(c_ + nout * 0.03, zt), P3(a + nout * 0.03, zt))
                if scheme["gutter"] and L > 20:
                    FK.gutter(acc, a, c_, nout, zt - 0.02)
                    for u in FK.downpipe_positions(L, ops, f"{key}:{ei}", 18.0):
                        FK.downpipe(acc, a, d, nout, u, zbot + 0.4, zt - 0.12, hopper=False)
                else:
                    FK.coping(acc, a, c_, nout, zt)
                    for u in FK.downpipe_positions(L, ops, f"{key}:{ei}", 22.0):
                        FK.downpipe(acc, a, d, nout, u, zbot + 0.4, zt - 0.75, hopper=True)
                # ADR 0081 hall kit: wall louvres (half of the dockless walls), one caged roof ladder per bigger hall
                if not dk and L > 14 and zt - zref > 5.0 and FK.hfloat(key, ei, "louvre") < 0.5:
                    for j in range(1 + int(L > 40)):
                        u = FK.safe_u(2.6 if j == 0 else L - 2.6, [(o[0] - 0.7, o[1] + 0.7, *o[2:]) for o in ops], L)
                        if u is not None:
                            FK.wall_louvre(acc, a, d, nout, u, min(zref + 3.4, zt - 1.6), 1.0, FA.hint(key, ei, "lv"))
                if not dk and not laddered and ei != main and L > 10 and zt - zref > 6.0 and poly.area > 600:
                    u = FK.safe_u(L - 1.6, [(o[0] - 0.8, o[1] + 0.8, *o[2:]) for o in ops], L)
                    if u is not None and u > L / 2:
                        FK.cage_ladder(acc, a, d, nout, u, zref + 0.25, zt)
                        laddered = True
                for o in ops:                                         # canopies over personnel doors
                    if o[5] == "door" and o[6] != "garage_door":
                        FK.canopy(acc, a, d, nout, (o[0] + o[1]) / 2, o[1] - o[0] + 0.8, o[3] + 0.35, 0.9)
                if dk:
                    for dock in dk["docks"]:
                        build_dock(acc, "buildings", a, d, nout, dock["u"], dk["yard_z"], dock["num"])
                        build_dock_lod1(acc, a, d, nout, dock["u"], dk["yard_z"], dock["num"])
                    # canopy over the dock row (steel, typical) only for hero buildings
                    if hero:
                        u0d, u1d = dk["docks"][0]["u"] - 2.2, dk["docks"][-1]["u"] + 2.2
                        cz = zf + S.DOCK_SHELTER_H + 0.9
                        cm = a + d * (0.5 * (u0d + u1d)) + nout * 1.0
                        for lay_, sk_ in (("buildings", ()), ("buildings_low", (2,))):
                            acc.box(lay_, "steel_painted", [cm[0], cm[1], cz], np.append(d * (u1d - u0d) / 2, 0),
                                    np.append(nout * 1.0, 0), [0, 0, 0.08], skip=sk_)
                        signs.append(FK.sign_instance("dostawy", a, d, nout, u0d - 3.0 if u0d > 6 else u1d + 3.0,
                                                      cz + 1.2, f"{key}:{ei}"))
                # ADR 0185: `hall_sign: false` - no rule board on a photographed hall (its real sign is a brand)
                if is_main and not signed and L > 25 and (hero or FK.hfloat(key, "sign") < 0.6) and b["ovr"].get(
                        "hall_sign", True):
                    code = "hala_a" if hero else FK.hpick(["hala_b", "hala_c", "hala_d", "magazyn"], key, "code")
                    u = FK.safe_u(L * (0.18 if FK.hfloat(key, "su") < 0.5 else 0.82), ops, L)
                    if u is not None and zt - zref > 6.5:
                        signs.append(FK.sign_instance(code, a, d, nout, u, zt - 1.6, f"{key}:{ei}"))
                        signed = True
            else:
                zpl = (st_zpl if st_zpl is not None else
                       zref + (zbase - 0.1 if typ == "block" else PLINTH_H.get(typ, 0.35) + (
                           0.15 * round(FK.hfloat(key, "plh")) if typ == "house" else 0.0)))
                usplits = []
                if insulated and ei == main and L > 12 and not one_tone:   # accent field on the stairwell axis
                    door = [o for o in ops if o[5] == "door"]
                    if door:
                        um = (door[0][0] + door[0][1]) / 2
                        usplits = [FK.safe_u(um - 1.6, ops, L), FK.safe_u(um + 1.6, ops, L)]
                lod1_ro = ((zt, RUNOFF_PERIOD_M * FK.hfloat(key, "runoff_u"), 0.6 + 0.7 * FK.hfloat(key, "runoff_l"))
                           if str(wall).startswith("hall_wall") else None)
                # r10 r2: flat-roofed blocks and offices streak under the attic coping too (LOD0 only: the LOD1 window
                # zone is the row atlas, it has no wall-top UV1)
                lod0_ro = lod1_ro
                if lod0_ro is None and typ in ("block", "office") and not pitched:
                    lod0_ro = (zt, RUNOFF_PERIOD_M * FK.hfloat(key, "runoff_u"), 0.5 + 0.6 * FK.hfloat(key, "runoff_l"))
                # accent colour on the gable ends only: an edge across the long axis, about as long as the block is
                # deep (before r10 every edge < 16 m qualified, so stepped blocks came out accent-coloured all round)
                gable_accent = (insulated and L < 16 and FK.hfloat(key, "gable") < 0.6 and L > 0.7 * rect_short and
                                abs(float(d @ rect_along)) < 0.3 and not one_tone)
                band_z = []                                            # (z0, z1) of each band
                if bands and ei not in bal_edges and not gable_accent and typ in ("block", "office") and not rule:
                    kk_ = sh / FA.FAR_ROW_H                               # sill 0.9 k, head 2.35 k / 2.5 k (facade_openings)
                    ns_ = FA.far_storeys(FA.far_groups(typ, storeys, False, variant["ribbon"], key), sh, zt - 0.3 - zref - zbase)
                    for st_ in range(ns_):
                        z0_ = zref + zbase + st_ * sh
                        if typ == "block" and st_ >= 1:
                            band_z.append((z0_ + 0.9 * kk_ - 0.12, min(z0_ + 2.35 * kk_ + 0.12, zt - 0.2)))
                        if typ == "office" and st_ + 1 < ns_:
                            band_z.append((z0_ + 2.5 * kk_ + 0.08, z0_ + sh + 0.9 * kk_ - 0.08))
                band_mat = accent if typ == "block" else "plaster_band_grey"
                if gable_accent:
                    lod1_main = accent
                elif band_z and typ == "block":
                    lod1_zone = band_mat                 # accent window rows -> accent window zone on LOD1

                def plaster_mat(u0, u1, z0, z1, usplits=usplits, gable_accent=gable_accent, zpl=zpl, band_z=band_z,
                                wall=wall_e):
                    if z1 <= zpl + 1e-6:
                        return plinth
                    if gable_accent:
                        return accent
                    if len(usplits) == 2 and None not in usplits and usplits[0] - 1e-6 <= u0 and u1 <= usplits[1] + 1e-6:
                        return accent
                    zm = 0.5 * (z0 + z1)
                    if any(b0 <= zm <= b1 for b0, b1 in band_z):
                        return band_mat
                    return wall
                # ADR 0097 + ADR 0348: sill streaks on rendered / panel walls (small_town: subtle streaks under ~78 % of sills)
                sills_ = (((RUNOFF_PERIOD_M * FK.hfloat(key, "sill_u"),
                            0.46 + 0.30 * FK.hfloat(key, "sill_l"), SMALL_TOWN_SILL_CLEAN) if st_mode
                           else (RUNOFF_PERIOD_M * FK.hfloat(key, "sill_u"), 0.55 + 0.35 * FK.hfloat(key, "sill_l")))
                          if SILL_RUNOFF and typ in ("block", "office", "house") and not wooden else None)

                def gfn(uabs, a=a, d=d, ua0=u_acc):
                    q_ = a + d * (uabs - ua0)
                    return float(hf.sample(np.array([q_[0]]), np.array([q_[1]]))[0])
                lod1_gfn = gfn
                # ADR 0348: 2-3 subtle plaster shades per small_town plaster house (main wall, side/frieze, gable, plinth)
                edge_col = col_gable = col_sec = col_plinth = col_fn = None
                z_frieze = None
                if shades is not None and str(wall_e).startswith("plaster_"):
                    col_main, col_gable, col_sec, col_plinth = shades
                    edge_col = col_sec if (ei != main and (ei % 2 == 1 or FK.hfloat(key, "sh_side") < 0.72)) else col_main
                    if typ == "house" and FK.hfloat(key, "sh_frieze") < 0.65 and zt - zpl > 2.6:
                        z_frieze = FK.safe_z(zt - 0.52, ops, zpl + 1.4, zt - 0.18)
                cols = [(0.0, L, zt)]
                aw = None
                if wooden:
                    aw = attic_window(prof, zt, zref, zbase, sh, storeys, f"{key}:{ei}",
                                      small_town=st_mode, joinery=st_joinery, wooden=True) if (pitched and not rural_shed) else None
                    if aw and aw["op"][2] < zt + 0.12:       # a window across the eave line: no gable window
                        aw = None
                    wood_stats["tris"] += wood_wall(acc, wall, plinth, a, d, nout, L, zbot, zpl, zt, zref, u_acc, ops,
                                                    prof if pitched else None, aw, gfn, f"{key}:{ei}",
                                                    (convex[ei], convex[(ei + 1) % len(edges)]), wood_stats["runs"],
                                                    bold_sill=st_mode, frame_3d=st_mode)
                    if aw:
                        ops.append(aw["op"])
                    if pitched:
                        wall_top_fill(acc, "buildings_low", wall, a, d, prof, lambda u, zt=zt: zt, u_acc, zref)
                    cols = []
                elif pitched:
                    aw = (None if rural_shed else
                          attic_window(prof, zt, zref, zbase, sh, storeys, f"{key}:{ei}",
                                       small_town=st_mode, joinery=st_joinery, wooden=False))
                    base_z = lambda u, zt=zt: zt
                    pr = prof
                    if aw:                      # gable end: the column under the ridge rises as a rectangle with the window
                        ops.append(aw["op"])
                        cols = [(0.0, aw["u0"], zt), (aw["u0"], aw["u1"], aw["zband"]), (aw["u1"], L, zt)]
                        base_z = lambda u, zt=zt, aw=aw: aw["zband"] if aw["u0"] < u < aw["u1"] else zt
                        pr = sorted(set(prof) | {(u, _prof_z(prof, u)) for u in (aw["u0"], aw["u1"])})
                        # ADR 0348: if an opening straddles eave zt we cannot split at zt; match gable to wall to avoid a vertical seam
                        if col_gable is not None and not all(o[3] <= zt - 0.02 or o[2] >= zt + 0.02 for o in ops):
                            col_gable = edge_col
                            z_frieze = None
                    wall_top_fill(acc, "buildings", wall, a, d, pr, base_z, u_acc, zref, col=col_gable)
                    wall_top_fill(acc, "buildings_low", wall, a, d, prof, lambda u, zt=zt: zt, u_acc, zref, col=col_gable)
                if edge_col is not None:
                    def col_fn(u0, u1, z0, z1, mat_, ec=edge_col, cg=col_gable, cs=col_sec, cp=col_plinth, zt_=zt, zf_=z_frieze):
                        if mat_ == "plinth_dark":
                            return cp
                        if not str(mat_).startswith("plaster_"):
                            return None
                        if z0 >= zt_ - 1e-4:
                            return cg
                        if zf_ is not None and z0 >= zf_ - 1e-4:
                            return cs
                        return ec
                bold_sill_ = st_mode and (typ == "house" or st_town_win) and not wooden
                zsplits_ = [zpl] + [z for b in band_z for z in b] + ([z_frieze] if z_frieze is not None else [])
                # ADR 0348: split the middle attic-window column at eave height zt only when _FACADE_TINT col_fn is active
                if col_fn is not None and aw and all(o[3] <= zt - 0.02 or o[2] >= zt + 0.02 for o in ops):
                    zsplits_.append(zt)
                for cu0, cu1, czt in cols:
                    FK.wall_pieces(wall_with_openings, acc, a + d * cu0, d, nout, cu1 - cu0, zbot, czt,
                                   ops if cu0 == 0.0 else [(o[0] - cu0, o[1] - cu0, *o[2:]) for o in ops], u_acc + cu0, zref,
                                   zsplits_,
                                   [u for u in usplits if u is not None] if None not in usplits else [], plaster_mat,
                                   runoff=lod0_ro, ground=gfn,   # sheds / small halls clad in sheet; plaster of blocks / offices
                                   sills=sills_, bold_sill=bold_sill_, col_fn=col_fn, frame_3d=bold_sill_)
                if bold_sill_:
                    for o in ops:
                        if o[5] == "window":
                            zt_o = aw["zband"] if (aw and o is aw["op"]) else zt
                            st_stats["window_trim_tris"] += FK.window_trim(
                                acc, a, d, nout, L, o, zt_o, mat="reveal_plaster", surround=st_surround)
                if typ in ("block", "office", "house") and not wooden and zpl > zbot + 0.6:
                    FK.plinth_drip(acc, a, d, nout, L, zpl, ops)
                    if typ in ("block", "office"):       # ADR 0107 (P2-k): joints of a tall plinth on a slope
                        FK.plinth_joints(acc, a, d, nout, L, zpl, zbot, ops, lambda u, ua0=u_acc: gfn(ua0 + u),
                                         FK.hfloat(key, ei, "pj"))
                if typ in ("block", "office") and not pitched:       # attic coping (obróbka attyki): silhouette
                    FK.coping(acc, a, c_, nout, zt, mat="hall_flashing")
                if typ == "block":
                    if L > 8 and not pitched:                        # downpipes at the wall ends (pitched: eaves)
                        for u in (0.35, L - 0.35):
                            FK.downpipe(acc, a, d, nout, u, zbot + 0.4, zt - 0.4, hopper=True)
                    for o in ops:
                        okey = f"{key}:{ei}:{o[0]:.1f}:{o[2]:.1f}"
                        if o[5] == "bdoor":
                            bal_count += 1
                            FK.balcony(acc, a, d, nout, o[0] + 1.05, 2.4, o[2] - 0.03, variant=o[7], key=okey,
                                       inner=o[2] - zref < 4.5)
                        elif o[5] == "window" and o[1] - o[0] > 1.0 and o[2] > zref + zbase:
                            FK.window_kit(acc, a, d, nout, o, okey, 0.05)
                        elif o[5] == "door":
                            FK.canopy(acc, a, d, nout, (o[0] + o[1]) / 2, 2.6, o[3] + 0.3, 1.4, mat="balcony_slab")
                elif typ == "office":
                    for o in ops:
                        if o[5] == "window":
                            FK.window_kit(acc, a, d, nout, o, f"{key}:{ei}:{o[0]:.1f}:{o[2]:.1f}", 0.10)
                        if o[5] == "door":
                            FK.canopy(acc, a, d, nout, (o[0] + o[1]) / 2, 3.2, o[3] + 0.45, 1.6, posts=False)
                            if not signed and zt - zref > 4.0:
                                code = FK.hpick(["biuro", "recepcja", "serwis", "biuro"], key, "osign")
                                signs.append(FK.sign_instance(code, a, d, nout, (o[0] + o[1]) / 2, o[3] + 1.05,
                                                              f"{key}:{ei}"))
                                signed = True
                    # ADR 0190: authored `downpipes: false` - a tower with roof drains inside (no pipes on the
                    # photographed walls); the hashed rule puts one at either end of every edge, so two collinear
                    # footprint edges show a pair of pipes in the middle of a wall
                    if L > 8 and b["ovr"].get("downpipes", True) and not pitched:      # pitched: eaves downpipes
                        for u in (0.35, L - 0.35):
                            FK.downpipe(acc, a, d, nout, u, zbot + 0.4, zt - 0.4, hopper=True)
                elif typ == "house":
                    for o in ops:
                        if o[5] == "door":
                            # ADR 0094 (review s9 P1-1): no canopy when the roof underside over the door (wall line and
                            # the edge of the overhang) is lower than the lintel + 0.4 m - the canopy (lintel + 0.25 m,
                            # 0.9 m deep) came out through the roof slope, and such an eave shelters the door itself
                            um_ = (o[0] + o[1]) / 2
                            if pitched:
                                pts_ = [a + d * u_ + nout * off_ for u_ in (um_ - 0.8, um_, um_ + 0.8)
                                        for off_ in (0.0, RF.OVERHANG)]
                                if float(np.min(roof.z(np.array(pts_)))) - RF.T_SOFFIT < o[3] + 0.4:
                                    canopy_skipped += 1
                                    continue
                            FK.canopy(acc, a, d, nout, um_, 1.6, o[3] + 0.25, 0.9,
                                      mat="roof_metal_graphite" if not wooden else "wood_planks")
                    for o in ops:                    # ADR 0097 (P2-b): landing + steps + threshold at the house door
                        if o[5] == "door":
                            FK.door_steps(acc, a, d, nout, (o[0] + o[1]) / 2, o[2], gfn(u_acc + (o[0] + o[1]) / 2),
                                          mat="wood_planks" if wooden else "plinth_dark")
            # collision: plain wall
            acc.quad("collision", "collision_building", [a[0], a[1], zbot], [c_[0], c_[1], zbot], [c_[0], c_[1], zt],
                     [a[0], a[1], zt])
            # LOD1 (v3.1): plinth band, window zone with the far facade material (window grid in UV1), wall above,
            # projecting coping at the attic; pitched houses keep the plain wall (or plinth band on small_town tiles)
            if not front_e:          # a frontage drew its LOD1 wall itself (FR.wall)
                lod1_wall(acc, typ, lod1_main, a, c_, nout, L, zbot, zref, zt, u_acc, storeys, sh, zbase,
                          "ribbon" if variant["ribbon"] else typ, pitched, zone_wall=lod1_zone, runoff=lod1_ro,
                          pieces=lod1_pieces, fkey=f"{key}:{ei}", balcony=bal_group if ei in bal_edges else False,
                          plinth=plinth_lod1, ground=lod1_gfn, authored=(rule, lod1_wins) if rule else None,
                          small_town=st_mode, zpl_override=st_zpl, town_windows=st_town_win,
                          col=edge_col if typ != "hall" else None, col_plinth=col_plinth if typ != "hall" else None)
            if typ == "house" and LOD1_HOUSE_OPENINGS:
                # ADR 0124 r2: the LOD1 prism of a house carries its windows and door as dark quads 5 cm proud of the
                # wall, in a material the LOD1 of a house chunk already has (no new draw). The Low scene shows LOD1
                # everywhere beyond 60 m of the route: house streets were blank boxes with a canopy over no door.
                for o in ops:
                    if o[5] not in ("window", "door") or o[1] - o[0] < 0.4 or o[3] - o[2] < 0.4:
                        continue
                    q0, q1 = a + d * o[0] + nout * 0.05, a + d * o[1] + nout * 0.05
                    l1_pending.append((key, [[q0[0], q0[1], o[2]], [q1[0], q1[1], o[2]], [q1[0], q1[1], o[3]],
                                             [q0[0], q0[1], o[3]]], str(wall), st_mode))
                    lod1_house_openings += 1
            u_acc += L
        if typ == "block" and BLOCK_APRON:                         # ADR 0097 (P2-g): paved apron
            FK.wall_apron(acc, poly, hf)
        if front:
            frontage_props += [dict(q_, building=key) for q_ in FR.props(
                acc, front, edges, lambda e_, n_: float(hf.sample(np.array([e_]), np.array([n_]))[0]))]
        for g_ in gates_b:
            if not g_.get("done"):
                raise ValueError(f"wall gate {g_['id']}: does not fit the wall it snaps to (building {key})")
        if typ == "hall" and not front and len(edges) >= 3:         # corner flashings
            for i, (a, c_) in enumerate(edges):
                FK.corner_trim(acc, a, nouts[i - 1], nouts[i], zref + 0.6, zeave - 0.4)
        # courtyard walls (holes), plain
        hole_ro = ((zeave, RUNOFF_PERIOD_M * FK.hfloat(key, "runoff_u"), 0.6 + 0.7 * FK.hfloat(key, "runoff_l"))
                   if str(wall).startswith("hall_wall") else None)   # courtyard sheet walls streak as well
        for hole in poly.interiors if not pitched else []:
            uh = 0.0
            for a, c_ in ring_edges(hole):
                L = float(np.linalg.norm(c_ - a))
                acc.quad("buildings", wall, [a[0], a[1], zbot], [c_[0], c_[1], zbot], [c_[0], c_[1], zeave], [a[0], a[1], zeave],
                         uv1=runoff_uv1(hole_ro, uh, uh + L, zbot, zeave))
                uh += L
        if pitched:
            st_roofs = st_mode and b.get("small_town_roofs", True)
            default_rmat = (house_pal[key][1] if typ == "house"
                            else rural_shed_pick(key, RURAL_SHED_ROOFS, "rsroof") if rural_shed
                            else hpick(key, SMALL_TOWN_ROOFS_PITCHED if st_roofs else ROOFS_PITCHED, "roof"))
            rmat = house_roof_material(b, default_rmat)
            if typ == "house":      # ADR 0316; also over an orthophoto-read colour (it says red tile, not which tile)
                rmat = roof_variant(key, rmat, wooden, small_town=st_roofs)
            if st_mode:
                st_stats["roof_materials"][rmat] = st_stats["roof_materials"].get(rmat, 0) + 1
            # ADR 0094 (review s9 P1-4): the soffit is light boarding (`soffit_boards`), not the graphite flashing
            # (0.045) that read 24-26 sRGB under the verge of r10_house_2 next to a wall of 140. Measured there
            # (High overcast): white `reveal_plaster` 72, the wall material 70-73, `plinth_dark` (0.20) 38 - the engine
            # halves the ambient of faces that look down (sky_occ), so no existing material reaches the 90 the review
            # asked for; `soffit_boards` is exempt from that halving. Its draw call is paid for by the eaves gutters,
            # which now share the downpipe material (same colour) on LOD0 as they already did on LOD1.
            # fascia / verge board: white boards with a tile roof, sheet flashing in the roof tone with a metal roof
            # (review s9 P2-3 "thick black verge board")
            roof_l1_map = ROOF_LOD1_SMALL_TOWN if st_roofs else ROOF_LOD1
            eaves = RF.build(acc, roof, poly, rmat, soffit_mat="soffit_boards",
                             fascia_mat=(wall if wooden else "hall_flashing" if rmat.startswith("roof_metal")
                                         else "soffit_boards"),
                             step_mat=wall,       # ADR 0107: wall faces closing the steps of a MultiRoof
                             low_mat=roof_l1_map.get(rmat),
                             weather=(roof_weather(b, key, rmat, wooden, rural_shed) if b.get("roof_weather") else None))
            if b.get("roof_weather"):
                rw_stats[roof_age_class(b, key, rmat, wooden, rural_shed)] += 1
            # ADR 0097 (review 0094 P2-c "wiatrownica biała vs szara"): with a tile roof the fascia / verge boards are
            # the soffit boarding material, so main roof and wing show one board colour (was white reveal_plaster
            # fascia next to the grey soffit_boards under the short wing overhang)
            eaves.sort(key=lambda e_: -float(np.hypot(*(e_[1] - e_[0]))))
            acc_g = acc if typ == "house" else _L0Only(acc)
            for k_, (ea, eb, ze) in enumerate([] if rural_shed else eaves):   # eaves gutters (none on a farm outbuilding)
                le = float(np.hypot(*(eb - ea)))
                de = (eb - ea) / le
                ne = np.array([de[1], -de[0]])
                FK.gutter(acc_g, ea, eb, ne, ze - 0.10, proud=-0.02)
                if k_ < 2:
                    ue = 0.35 + RF.OVERHANG if FK.hfloat(key, "dp", k_) < 0.5 else le - 0.35 - RF.OVERHANG
                    wp = ea + de * ue - ne * RF.OVERHANG
                    if poly.exterior.distance(shapely.Point(*wp)) < 0.2:
                        FK.downpipe(acc_g, ea - ne * RF.OVERHANG, de, ne, ue, zbot + 0.4, ze - 0.3, hopper=False)
            nch = 1 + int(storeys >= 2 and FK.hfloat(key, "chim2") < 0.5)
            if (wooden and FK.hfloat(key, "wchim") >= 0.8) or typ != "house":      # ADR 0238: no rule chimney on a
                nch = 0                                                             # pitched block / office
            chims = RF.chimney_spots(roof, poly, lambda salt: FK.hfloat(key, salt), nch)
            for cp in chims:
                FK.chimney(acc, cp, roof.eu, float(roof.z(cp)) - 0.25, max(roof.zridge + 0.45, float(roof.z(cp)) + 0.9),
                           apron=lambda q_: float(roof.z(q_)) + RF.T_TOP)
            if st_mode and typ in ("house", "office", "block"):                     # ADR 0336: Podlasie roof dormers
                main_nout = nouts[main] if main < len(nouts) else None
                dspots = RF.dormer_spots(roof, poly, lambda salt: FK.hfloat(key, salt),
                                         chimneys=chims, prefer_dir=main_nout)
                dwin = st_joinery[0] if st_joinery else 0
                dfascia = wall if wooden else ("hall_flashing" if rmat.startswith("roof_metal") else "soffit_boards")
                for sp in dspots:
                    FK.dormer(acc, sp, wall, rmat, "reveal_plaster", dwin, fascia_mat=dfascia)
                    st_stats["dormers"] += 1
        else:
            roof_flat(acc, "buildings", poly, zeave, attic=0.3 if typ in ("hall", "office", "block") else 0.15,
                      skylights=typ == "hall" and not front, key=key)
            # LOD1 roof stays one flat polygon (an attic inset is invisible from the road and cost 1.3 MiB in Low);
            # the coping ledge (5 cm above the roof) reads as the attic rim
            roof_flat(acc, "buildings_low", poly, zeave, attic=0.0)
            # lift / plant rooms break the box top; ADR 0200: authored `machine_rooms: false` - the photographed
            # roof has none (masts and cable trays only)
            tall_office = typ == "office" and storeys >= 5 and b["ovr"].get("machine_rooms", True)
            if typ == "block" or tall_office:
                FK.machine_rooms(acc, poly, zeave, "buildings_low")
            roof_flat(acc, "collision", poly, zeave, mat="collision_building", attic=0.0)
            if typ == "hall" and poly.area > 600 and not front:
                FK.roof_vents(acc, poly, zeave - 0.3, key, "hall")
            elif typ == "block":
                FK.roof_vents(acc, poly, zeave - 0.3, key, "block")
            elif tall_office:
                FK.machine_rooms(acc, poly, zeave - 0.3, "buildings")
            masts = FR.roof_mast_specs(b["ovr"].get("roof_masts"))       # ADR 0190: authored antenna masts
            if masts:
                roof_masts_report += [dict(q_, building=key) for q_ in FR.roof_masts(acc, masts, edges, zeave - 0.3)]
        hero_h = (heroes or {}).get(key)
        if hero_h and hero_h["meta"] is not None:       # the authored asset replaces the visible hall
            acc.d = {k: v for k, v in acc.d.items() if k[0] not in ("buildings", "buildings_low")}
            l1_pending[:] = [q for q in l1_pending if q[0] != key]
        for it in acc.d.get(("buildings_low", LOD1_HOUSE_OPENING_MAT), ()):
            l1_cells.update(map(tuple, np.floor(it[0][it[1]].mean(1)[:, :2] / _CHUNK_M).astype(int).tolist()))
        for fm in LOD1_HOUSE_FRAME_MATS:                     # ADR 0132: materials a frame may use, per chunk cell
            for it in acc.d.get(("buildings_low", fm), ()):
                for cell in sorted(set(map(tuple, np.floor(it[0][it[1]].mean(1)[:, :2] / _CHUNK_M).astype(int).tolist()))):
                    l1_frame_cells.setdefault(cell, set()).add(fm)
        acc.flush(buf, key)
    # ADR 0124 r2: LOD1 openings of houses, in the dark sheet material where the LOD1 of that chunk has it anyway and in
    # the gutter grey elsewhere (2 chunks of bialystok-industrial-c) - never a draw of their own
    by_key = {}
    for k_, quad, wall_, st_q in l1_pending:
        cell = tuple(np.floor(np.mean(quad, axis=0)[:2] / _CHUNK_M).astype(int).tolist())
        mat = LOD1_HOUSE_OPENING_MAT if cell in l1_cells else LOD1_HOUSE_OPENING_FALLBACK
        l1_fallback += mat != LOD1_HOUSE_OPENING_MAT
        # ADR 0132 (review 0124 P2-d: black rectangles without frames read as a burnt-out house from close by): a
        # frame of LOD1_HOUSE_FRAME_M round the dark pane, in the same plane (4 quads, no overlap -> no z-fight), in
        # a light material the LOD1 of that chunk already draws and that is not the wall of this house
        q = np.asarray(quad, float)
        # every chunk cell the opening touches must already draw the frame material (chunks cut per triangle centroid:
        # r1 put one frame triangle of an opening on a chunk border into a chunk without it, +1 submesh)
        qcells = {tuple(np.floor(c_[:2] / _CHUNK_M).astype(int).tolist()) for c_ in q}
        fm = next((m_ for m_ in LOD1_HOUSE_FRAME_MATS if m_ != wall_ and m_ != mat
                   and all(m_ in l1_frame_cells.get(c_, ()) for c_ in qcells)), None)
        wq, hq = float(np.linalg.norm(q[1] - q[0])), float(q[3][2] - q[0][2])
        frame_m = SMALL_TOWN_LOD1_FRAME_M if st_q else LOD1_HOUSE_FRAME_M
        f_ = min(frame_m, 0.2 * wq, 0.2 * hq)
        acc_ = by_key.setdefault(k_, Acc())
        if fm is None or f_ < 0.03:
            acc_.quad("buildings_low", mat, *quad)
            continue
        eu = (q[1] - q[0]) / wq * f_
        ez = np.array([0.0, 0.0, f_])
        inner = [q[0] + eu + ez, q[1] - eu + ez, q[2] - eu - ez, q[3] + eu - ez]
        acc_.quad("buildings_low", mat, *[list(v_) for v_ in inner])
        for i_ in range(4):
            j_ = (i_ + 1) % 4
            acc_.quad("buildings_low", fm, list(q[i_]), list(q[j_]), list(inner[j_]), list(inner[i_]))
        l1_framed += 1
    for k_, a_ in by_key.items():
        a_.flush(buf, k_)
    report.update({"typologies": counts, "docks": sum(len(d["docks"]) for d in all_docks),
                   "dock_facades": [d["id"] for d in all_docks], "facade_signs": len(signs),
                   "hall_wall_runoff_tris": dict(Acc.runoff_tris),
                   "house_roofs": dict(sorted(roof_kinds.items())),
                   "subtypes": dict(sorted(subtypes.items())), "roofs_other": dict(sorted(roofs_other.items())),
                   "pavilion_fronts": int(pav_fronts),
                   "house_canopies_under_eave_skipped": canopy_skipped, "balconies": bal_count,
                   "wooden_houses": {"boarding_runs": len(wood_stats["runs"]),
                                     "longest_run_m": round(max(wood_stats["runs"], default=0.0), 2),
                                     "runs_over_tile": sum(1 for r_ in wood_stats["runs"] if r_ > WOOD_TILE_M[0]),
                                     "board_tris_lod0": int(wood_stats["tris"])},
                   "lod1_house_openings": lod1_house_openings, "lod1_house_openings_fallback_mat": int(l1_fallback),
                   "lod1_house_openings_framed": int(l1_framed),
                   "frontages": frontages, "frontage_props": frontage_props, "roof_masts": roof_masts_report})
    if any_st:
        st_stats["roof_materials"] = dict(sorted(st_stats["roof_materials"].items()))
        report["small_town"] = st_stats
    if any(b.get("roof_weather") for b in blds):
        report["roof_weathering"] = rw_stats
    if sign_out is not None:
        sign_out.extend(signs)
    return all_docks
