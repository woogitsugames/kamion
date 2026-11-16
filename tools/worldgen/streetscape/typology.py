"""Building typology of Białystok (ADR 0238): the rule that picks a building's type from the footprint data, and the
proportions / palette / roof of every type with the status of each number.

Two levels:
  typ      render class of streetscape.buildings_mesh (hall, office, block, house, shed, roof) - unchanged, every
           other generator keys on it (plots, life, far field, QA cameras);
  subtype  what the building is within its class (SUBTYPES). The subtype tunes the facade, never the class.

Choice (subtype()): authored override `typology` > OSM tags joined to the footprint (`osm_building`, when the
buildings.geojson carries them) > BDOT10k function + storeys + LoD1 height + measured LoD2 roof rise. An override
may name a render class (as before: hall / office / block / house / shed) or a subtype (kamienica, pawilon, ...).

Roof (roof_shape()): authored override `roof_shape` > OSM `roof:shape` (`roof_shape_osm`) > LoD2 2017 roof type with
the MEASURED rise (ridge - eave). The LoD2 type code alone is not used for buildings that are not houses: in the two
regions in git every multi-family building coded 1030 ("gable" in streetscape.roofs) but one has a rise of 0.3-0.8 m,
i.e. a low-slope roof behind an attic (measured on Data/Regions/*/buildings.geojson, tests/gis/test_typology_0238.py).

Status of the numbers (docs/adr/0238): SOURCED = quoted source, MEASURED = computed from the data in git,
ESTIMATED = read off licensed photographs (sample size given), WORKING_VALUE = not sourced, to be checked.
Research: research/cloud2/bialystok-building-typology (R4, PR #64, review REVIEW-2026-11-15-s21-cloudD-64) and
research/mistral/p3-buildings-2 (M53: facade colours of blocks, MPZP Białostoczek).
"""
from __future__ import annotations

import hashlib

# ------------------------------------------------------------------------------------------- subtypes
# subtype: render class
SUBTYPES = {
    "wielka_plyta": "block",     # multi-family block (large-panel systems OWT-67 / OWT-75 and later flat-roofed blocks)
    "kamienica": "block",        # tenement / low multi-family house with a pitched roof
    "biurowiec": "office",       # office / public service building
    "pawilon": "office",         # single-storey trade / service pavilion
    "dom": "house",              # single-family house
    "dom_drewniany": "house",    # wooden Podlasie house (boarding), chosen in buildings_mesh.build (footprint rule)
    "hala": "hall",              # warehouse / production hall / large retail box
    "gospodarczy": "shed",       # outbuilding, garage, transformer station
    "wiata": "roof",             # canopy on columns (OSM building=roof)
}
DEFAULT_SUBTYPE = {"block": "wielka_plyta", "office": "biurowiec", "house": "dom", "hall": "hala",
                   "shed": "gospodarczy", "roof": "wiata"}
TYPES = tuple(DEFAULT_SUBTYPE)

# BDOT10k PRZEWAZAJACAFUNKCJABUDYNKU / OSM building=* values of trade and service pavilions
PAVILION_FUNCS = {"obiekt handlowo-usługowy", "dom towarowy lub handlowy", "restauracja", "apteka", "stacja paliw",
                  "supermarket", "retail", "kiosk", "commercial", "shop"}
# a pavilion is ONE storey: BDOT10k storeys == 1, or no storey count and a LoD1 height up to PAVILION_MAX_H.
# MEASURED: single-storey BDOT10k trade / service buildings under 1500 m2 of the two Białystok regions in git have a
# LoD1 height p10 / p50 / p90 3.0 / 4.2 / 6.8 m, n = 71 (test_typology_0238.test_pavilion_heights_measured); above PAVILION_MAX_H the
# "one storey" is a tall box (workshop, showroom with a gallery) and keeps the office rule.
PAVILION_MAX_H = 7.5
PAVILION_MAX_H_NO_STOREYS = 6.0          # WORKING_VALUE: OSM-only footprints with a default height are not pavilions
OSM_PAVILION = {"retail", "kiosk", "commercial", "supermarket"}
OSM_HOUSE = {"house", "detached", "semidetached_house", "terrace", "bungalow"}
OSM_BLOCK = {"apartments", "residential", "dormitory"}

# kamienica by rule: a multi-family building of at most KAMIENICA_MAX_STOREYS storeys whose roof is pitched by
# roof_shape() (OSM roof:shape or a LoD2 gable / hip type with a measured rise). WORKING_VALUE limits: no source
# separates tenements from blocks in BDOT10k (no year of construction); R4 has no tenement on the C / Dojlidy tiles.
KAMIENICA_MAX_STOREYS = 4
KAMIENICA_MAX_AREA = 900.0               # m2; above it streetscape.roofs has no roof plan anyway (WORKING_VALUE)

# ------------------------------------------------------------------------------------------- proportions
# per subtype: storey height m, ground floor level above the ground m (cokół), window axis m, [status, source]
PROPORTIONS = {
    "wielka_plyta": {
        "storey_m": 2.8, "storey_status": "SOURCED",
        "storey_source": "R4-074 / R4-077: Wikipedia 'Technologia wielkopłytowa' oldid 79506745 'Wysokość kondygnacji "
                         "mieszkalnych - 280 cm' (OWT-75, W-70); OWT-67 270 cm (oldid 72638965). R4-075 ('280 cm brutto') "
                         "is NOT used: the sentence carries '[potrzebny przypis]' (review errata E1)",
        "storey_fit_m": (2.6, 3.8),          # BDOT10k storey count accepted when LoD1 height / storeys falls here
        "plinth_m": 1.0, "plinth_status": "WORKING_VALUE",       # raised ground floor over the basement
        "axis_m": 3.0, "axis_status": "WORKING_VALUE",
        "axis_source": "bound to the facade_far row atlas (facade_atlas.FAR_PITCH); within the SOURCED wall spacings of "
                       "W-70 (240 / 360 / 480 / 600 cm; use of W-70 in Białystok UNVERIFIED); the OW-T grid 540 cm "
                       "(SOURCED, R4) holds two axes of 2.7 m (ESTIMATED) - a 2.7 m atlas is open work",
    },
    "kamienica": {
        "storey_m": 3.2, "storey_status": "WORKING_VALUE", "storey_source": "no Białystok source in R4",
        "storey_fit_m": (2.8, 4.0),
        "plinth_m": 0.6, "plinth_status": "WORKING_VALUE",
        "axis_m": 3.0, "axis_status": "WORKING_VALUE", "axis_source": "row atlas pitch (as wielka_plyta)",
    },
    "biurowiec": {
        "storey_m": 3.5, "storey_status": "WORKING_VALUE", "storey_source": "LoD1 / storey accepted in 2.8-4.6 m",
        "storey_fit_m": (2.8, 4.6),
        "plinth_m": 0.45, "plinth_status": "WORKING_VALUE",
        "axis_m": 3.0, "axis_status": "WORKING_VALUE", "axis_source": "row atlas pitch",
    },
    "pawilon": {
        "storey_m": 3.5, "storey_status": "WORKING_VALUE", "storey_source": "one storey = the LoD1 height (MEASURED p50 4.2 m, n = 71)",
        "storey_fit_m": (2.8, 4.6),
        "plinth_m": 0.45, "plinth_status": "WORKING_VALUE",
        "axis_m": 2.4, "axis_status": "WORKING_VALUE", "axis_source": "shopfront mullion pitch (frontage default, ADR 0126)",
    },
    "dom": {
        "storey_m": 2.9, "storey_status": "WORKING_VALUE",
        "storey_source": "LoD1 height / BDOT10k storey p50 3.9 m WITH the roof (R4 data/stats.json: C 3.92, Dojlidy 3.97)",
        "plinth_m": 0.45, "plinth_status": "WORKING_VALUE",
        "axis_m": 2.7, "axis_status": "WORKING_VALUE", "axis_source": "ADR 0091: 2 windows from 6.4 m, 3 from 9.1 m",
    },
}
PROPORTIONS["dom_drewniany"] = PROPORTIONS["dom"]

# ------------------------------------------------------------------------------------------- palettes
# Hashed pick: every entry is one share. Only materials the far (LOD1) wall set already has for the render class.
#
# Blocks. ESTIMATED from the 9 block rows of research/mistral/p3-buildings-2/manifest_v2.csv with status OK /
# OK-POŚREDNIE and a described facade (photos CC0 / CC BY / CC BY-SA, Wikimedia Commons; colour = vision description,
# 3 of them confirmed by a decoded wall rectangle): white 3 (M53-020, 029, 044), light grey / grey 3 (M53-013
# [155,160,162], 014 [232,228,228], 021 [159,159,156]), beige 2 (M53-010, 012), orange 1 (M53-011). No blue, yellow or
# sage block in the sample (they stay available as `wall_material` overrides). SOURCED frame: MPZP of a part of
# os. Białostoczek, uchwała XXVII/451/26 par. 7 ust. 1 pkt 1 lit. a - "odcienie bieli, beżu, brązu i szarości".
# R4 (cloud2) has no block colours (review errata E3).
BLOCK_WALLS = ["plaster_white", "plaster_white", "plaster_white", "plaster_grey", "plaster_grey", "plaster_grey",
               "plaster_cream", "plaster_cream", "plaster_peach"]
# Tenements: WORKING_VALUE (no photographed tenement in R4 / M53); the neutral and beige block tones
KAMIENICA_WALLS = ["plaster_cream", "plaster_grey", "plaster_white"]
# Pavilions. ESTIMATED (R4 route C frames: "niskie pawilony handlowe w bieli i błękicie"; M53-019 beige-white,
# M53-045 yellow, M53-047 grey): light neutral render; the saturated fronts in the photos are company colours, which
# the game does not reproduce (CLAUDE.md rule 8) - no blue / yellow / green walls by rule.
PAVILION_WALLS = ["plaster_white", "plaster_white", "plaster_light", "plaster_grey", "plaster_beige"]
# Halls, offices, houses keep their lists in buildings_mesh (HALL_WALLS, OFFICE_WALLS, HOUSE_TONES); R4 agrees:
# halls of the Dojlidy zone white / light grey, 1 red of 6 (ESTIMATED n = 6, one author) - red stays an accent band
# (facade_kit.ACCENT_HALL) or an authored `wall_material`; houses light beige / grey render, red-brown or graphite
# roofs; offices beige, grey, white with a dark attic.

# ------------------------------------------------------------------------------------------- pavilion front
# Rule shopfront of a pavilion (the wall nearest to a road): glazed run + dark sign fascia above it, drawn by
# streetscape.frontage on both LODs. All WORKING_VALUE (no measured pavilion front in R4); no lettering, no brands.
PAVILION_FRONT = {"min_len_m": 6.0, "min_h_m": 3.2, "glass_z": (0.35, 2.75), "pitch_m": 2.4, "margin_m": 0.8,
                  "transom_m": 2.15, "fascia_m": 0.6, "fascia_material": "hall_flashing", "plinth_m": 0.3,
                  "glass": "showroom_glass", "glass_lod1": "hall_flashing"}
_BEARINGS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")

# ------------------------------------------------------------------------------------------- roofs
ROOF_SHAPES = ("flat", "gable", "hip", "mono")
# OSM roof:shape -> roof kind of streetscape.roofs (https://wiki.openstreetmap.org/wiki/Key:roof:shape; values the
# generator cannot build fall back to the data rule)
OSM_ROOF_SHAPE = {"flat": "flat", "gabled": "gable", "hipped": "hip", "half-hipped": "gable", "pyramidal": "hip",
                  "skillion": "mono", "lean_to": "mono"}
LOD2_PITCHED = {"1030": "gable", "1040": "hip", "1070": "hip"}       # as streetscape.roofs.plan reads them (UNVERIFIED
#                                                                     codes: no dictionary quoted, R4 README "Luki")
ROOF_MIN_RISE_M = 1.5          # ridge - eave of the LoD2 model below which a "pitched" code is a low-slope roof
ROOF_MIN_EAVE_SHARE = 0.5      # LoD2 eave below this share of the LoD1 height = a porch roof, not the eave


def hint(key, salt=""):
    return int(hashlib.sha1(f"{key}{salt}".encode()).hexdigest()[:8], 16)


def pick(key, seq, salt=""):
    return seq[hint(key, salt) % len(seq)]


def render_class(name):
    """Render class of an override `typology` value (a class or a subtype); None for an unknown name."""
    if name in TYPES:
        return name
    return SUBTYPES.get(name)


def lod2_rise(p):
    """Measured roof rise of the LoD2 2017 model (ridge - eave), m, or None when the eave is missing or is a porch."""
    hr, he = p.get("height_lod2_2017_m"), p.get("lod2_eave_rel_m")
    if hr is None or he is None:
        return None
    h = float(p.get("height_m") or hr)
    if he < ROOF_MIN_EAVE_SHARE * h:
        return None
    return float(hr) - float(he)


def roof_shape(typ, p, ovr):
    """(shape, source): shape in ROOF_SHAPES, or None = the generator's own rule (houses: streetscape.roofs.plan from
    the LoD2 type; everything else: flat). source: override / osm / lod2_rise / None."""
    o = (ovr or {}).get("roof_shape")
    if o:
        if o not in ROOF_SHAPES:
            raise ValueError(f"override roof_shape {o!r}: expected one of {ROOF_SHAPES}")
        return o, "override"
    osm = OSM_ROOF_SHAPE.get(str(p.get("roof_shape_osm") or "").strip().lower())
    if osm:
        return osm, "osm"
    if typ in ("block", "office"):
        kind = LOD2_PITCHED.get(p.get("roof_type_lod2"))
        rise = lod2_rise(p)
        if kind and rise is not None and rise >= ROOF_MIN_RISE_M:
            return kind, "lod2_rise"
    return None, None


def subtype(typ, p, area, ovr=None):
    """Subtype of a building of render class typ (see the module docstring for the order of the sources)."""
    ovr = ovr or {}
    name = ovr.get("typology")
    if name in SUBTYPES and SUBTYPES[name] == typ:
        return name
    if name in TYPES:                       # an authored render class is the plain subtype of that class
        return DEFAULT_SUBTYPE[typ]
    h = float(p.get("height_m") or 6.0)
    st = p.get("storeys")
    f = p.get("function")
    osm = p.get("osm_building")
    if typ == "block":
        shape, _ = roof_shape(typ, p, ovr)
        if (shape in ("gable", "hip", "mono") and (st or 99) <= KAMIENICA_MAX_STOREYS and area <= KAMIENICA_MAX_AREA
                and f != "hotel"):
            return "kamienica"
        return "wielka_plyta"
    if typ == "office":
        trade = f in PAVILION_FUNCS or osm in OSM_PAVILION
        one = (st == 1 and h <= PAVILION_MAX_H) or (not st and h <= PAVILION_MAX_H_NO_STOREYS
                                                    and p.get("height_source") != "default")
        if trade and one and not p.get("is_roof_only"):
            return "pawilon"
        return "biurowiec"
    return DEFAULT_SUBTYPE.get(typ, typ)


def bearing_name(nout):
    """Compass name (N, NE, ...) of the direction a wall with outward normal nout (E, N) looks to."""
    import math
    deg = math.degrees(math.atan2(float(nout[0]), float(nout[1]))) % 360.0
    return _BEARINGS[int((deg + 22.5) // 45.0) % 8]


def pavilion_front(wall, nout, h):
    """`frontage` spec (streetscape.frontage.plan) of the rule shopfront of a pavilion wall looking along nout, for a
    building h m high; None when the wall is too low for a glazed run under the fascia."""
    c = PAVILION_FRONT
    if h < c["min_h_m"]:
        return None
    z1 = min(c["glass_z"][1], h - c["fascia_m"] - 0.25)
    if z1 - c["glass_z"][0] < 1.6:
        return None
    facing = bearing_name(nout)
    return {"wall": wall, "plinth_m": c["plinth_m"], "glass": c["glass"], "glass_lod1": c["glass_lod1"],
            "fascia": {"material": c["fascia_material"], "height_m": c["fascia_m"], "overhang_m": 0.0, "facings": [facing]},
            "glazing": [{"facing": facing, "z": [c["glass_z"][0], z1], "pitch_m": c["pitch_m"],
                         "min_len_m": c["min_len_m"], "margin_m": c["margin_m"],
                         **({"transom_m": c["transom_m"]} if z1 - c["transom_m"] >= 0.45 else {})}]}
