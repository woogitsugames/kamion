"""Numeric design values for road geometry and horizontal markings, with their sources.

Every value is either cited (regulation + paragraph / figure) or marked WORKING_VALUE (our choice,
to be confirmed by the owner's photos or a measurement). Nothing in the generator uses a magic
number for road dimensions that is not defined here.

Sources (texts read 2026-11-09):
  [PTB2022]  Rozporządzenie Ministra Infrastruktury z dnia 24 czerwca 2022 r. w sprawie przepisów
             techniczno-budowlanych dotyczących dróg publicznych (Dz.U. 2022 poz. 1518),
             https://eli.gov.pl/eli/DU/2022/1518/ogl/pol/pdf . Amended by Dz.U. 2025 poz. 1352
             (concerns lane width on curves, § 17 ust. 5) – values used here are unaffected.
  [ZNAKI-Z2] Załącznik nr 2 „Szczegółowe warunki techniczne dla znaków drogowych poziomych i warunki
             ich umieszczania na drogach” do rozporządzenia Ministra Infrastruktury z dnia 3 lipca 2003 r.
             w sprawie szczegółowych warunków technicznych dla znaków i sygnałów drogowych oraz urządzeń
             bezpieczeństwa ruchu drogowego i warunków ich umieszczania na drogach (t.j. Dz.U. 2019
             poz. 2311 with later amendments). Copy read: KRBRD PDF (consolidated, 381 pages). Dimensions
             below are read from the figures (rys.) of that annex.
"""

from __future__ import annotations

# --------------------------------------------------------------------------------------------
# Road class mapping. OSM `highway` -> Polish technical class (PTB2022 § 11). WORKING_VALUE:
# the mapping is ours (OSM classes are functional, not technical). Urban Białystok assumed.
OSM_TO_CLASS = {
    "motorway": "A", "motorway_link": "A",
    "trunk": "GP", "trunk_link": "GP",
    "primary": "G", "primary_link": "G",
    "secondary": "G", "secondary_link": "G",
    "tertiary": "Z", "tertiary_link": "Z",
    "unclassified": "L", "residential": "L",
    "living_street": "D", "service": "D",
}

# PTB2022 § 17 ust. 1 – lane width on a carriageway with >= 2 lanes: (standard, difficult conditions)
LANE_WIDTH = {
    "A": (3.75, 3.50), "S": (3.50, 3.25), "GP": (3.50, 3.25), "G": (3.50, 3.00),
    "Z": (3.00, 2.75), "L": (2.75, 2.50), "D": (2.50, 2.25),
}
# PTB2022 § 17 ust. 3 – single-lane carriageway: < two lanes but >= 3.50 m.
SINGLE_LANE_MIN = 3.50
SINGLE_LANE_DEFAULT = 4.00          # WORKING_VALUE (between 3.50 and 2 x lane)
# Widths of lanes are measured between line axes ([ZNAKI-Z2] pkt 2.2.1).

# Edge strip (opaska) between the outer lane line axis and the kerb face. PTB2022 § 23 ust. 7-8: opaska
# zewnętrzna/wewnętrzna GP 0.75 m standard, 0.50 m in difficult conditions; G/Z 0.50 m. On kerbed
# streets § 23 ust. 4 allows other solutions. WORKING_VALUE: GP 0.50 m (urban, difficult), G 0.25 m,
# lower classes 0 (lane runs to the kerb).
EDGE_STRIP = {"A": 0.75, "S": 0.75, "GP": 0.50, "G": 0.25, "Z": 0.0, "L": 0.0, "D": 0.0}

# PTB2022 § 20 ust. 2 – max longitudinal grade by design speed (km/h): (standard, difficult)
MAX_GRADE_BY_VP = [(130, 0.04, 0.05), (110, 0.05, 0.06), (90, 0.06, 0.07), (70, 0.07, 0.08),
                   (60, 0.08, 0.10), (50, 0.09, 0.11), (0, 0.10, 0.12)]
# PTB2022 § 62 ust. 2 – ramps (łącznice) of WB/WC interchanges: <= 7 %.
MAX_GRADE_RAMP = 0.07
# Service roads / yards: not regulated as public roads. WORKING_VALUE.
MAX_GRADE_SERVICE = 0.12

# Vertical curve minimum radii (convex/concave), metres. The 2022 regulation is performance-based
# (§ 20 ust. 1 "załamania niwelety wyokrągla się krzywymi") and gives no table -> WORKING_VALUE.
# Kept moderate so the profile follows the surveyed road (NMT error 0.09 m) instead of an idealised
# design: with 1500 m on GP the profile left the NMT by up to 1.5 m on Andersa (rendered + measured).
VCURVE_MIN_R = {"GP": 800.0, "G": 600.0, "Z": 400.0, "L": 250.0, "D": 150.0, "A": 2000.0, "S": 1500.0}

# Crossfall. PTB2022 § 18 is performance-based ("zapewnić skuteczne odwodnienie"). 2 % is common Polish
# practice for asphalt (and was the value of the repealed 1999 regulation) -> WORKING_VALUE.
CROSSFALL = 0.02
CROSSFALL_CURVE = 0.025             # WORKING_VALUE: one-sided superelevation on curves R < CURVE_R
CURVE_R = 400.0                     # WORKING_VALUE
CROSSFALL_RAMP_SIGMA_M = 10.0       # WORKING_VALUE: smoothing of the crossfall change (rampa przechyłkowa)

# Kerb ("krawężnik"). Height 0.12-0.15 m in Polish urban practice; PTB2022 § 89 ust. 2 pkt 1 treats a
# kerb >= 0.12 m as a (barrier-relevant) raised kerb. 0.13 m = WORKING_VALUE. Standard 15 x 30 cm kerb -> top width 0.15 m.
KERB_HEIGHT = 0.13
KERB_TOP_W = 0.15
KERB_HEIGHT_APRON = 0.04            # WORKING_VALUE: roundabout truck apron kerb (mountable)
# Sidewalk. PTB2022 § 29 ust. 1: >= 1.80 m. 2.00 m = WORKING_VALUE. Crossfall towards the road
# <= 3 % (PTB2022 § 33); we use 2 %.
SIDEWALK_W = 2.00
SIDEWALK_CROSSFALL = 0.02
VERGE_W = 1.00                      # WORKING_VALUE: grass strip behind the kerb when no sidewalk
FLANGE_DEPTH = 0.50                 # vertical skirt under the outer edge (hides terrain/road seams)
TERRAIN_UNDER_ROAD = 0.35           # terrain pushed this far below the road surface inside footprint
# Rural profile (outside built-up area), PTB2022 § 23 ust. 10 pkt 3-5: unpaved shoulder
# 1.25 (G) / 1.00 (Z) / 0.75 (L, D) standard.
SHOULDER_W = {"A": 1.25, "S": 1.25, "GP": 1.25, "G": 1.25, "Z": 1.00, "L": 0.75, "D": 0.75}
PAVED_SHOULDER = 1.00              # WORKING_VALUE: paved shoulder (pobocze utwardzone) of the rural GP profile
PAVED_SHOULDER_MEDIAN = 0.50       # WORKING_VALUE: inner paved strip next to a grass median (no kerb)
RURAL_MIN_SPEED = 70.0             # WORKING_VALUE: GP/G sections at >= 70 km/h without footways get the rural profile
RURAL_FOOT_M = 7.0                 # WORKING_VALUE: no footway/path within this distance of the carriageway edge
SHOULDER_CROSSFALL = 0.06           # WORKING_VALUE (unpaved shoulder, § 24 ust. 3: "skuteczne odwodnienie")
DITCH_DEPTH = 0.60                  # WORKING_VALUE
DITCH_SLOPE = 1.5                   # 1 : 1.5, WORKING_VALUE
DITCH_BOTTOM_W = 0.40               # WORKING_VALUE
EMBANKMENT_SLOPE = 1.5              # 1 : 1.5 cut/fill slopes, WORKING_VALUE (§ 25 is performance-based)
BERM_W = 1.0                        # flat strip next to the road before the embankment slope starts

# Curb-return radii at junctions (promień łuku krawężnika), metres. WORKING_VALUE, chosen for a
# 16.5 m articulated truck; the regulation (§ 58 ust. 3) only requires passage of the design vehicle.
CURB_RADIUS = {"A": 20.0, "S": 20.0, "GP": 15.0, "G": 12.0, "Z": 10.0, "L": 8.0, "D": 8.0}
NOSE_MAX_ANGLE_DEG = 25.0           # corners narrower than this get a median/splitter nose
STRAIGHT_MIN_ANGLE_DEG = 155.0      # corners wider than this are a straight kerb (no fillet)
JUNCTION_MIN_TRIM = 2.0             # m, minimal junction size along each arm

# Roundabouts: circulatory crossfall falls outwards (towards the outer kerb). WORKING_VALUE.
ROUNDABOUT_APRON_W = 2.0            # WORKING_VALUE: mountable apron around the central island
ROUNDABOUT_CROSSFALL = 0.02

# Bridges (low confidence: OSM only says bridge=viaduct + layer)
BRIDGE_DECK_THICKNESS = 1.20        # WORKING_VALUE
BRIDGE_KERB_H = 0.20                # WORKING_VALUE (kapa chodnikowa)
BRIDGE_CAP_W = 1.50                 # WORKING_VALUE
BRIDGE_PARAPET_H = 1.10             # WORKING_VALUE (bariera / balustrada)
BRIDGE_PIER_SPACING = 30.0          # WORKING_VALUE
BRIDGE_PIER_W = 1.2                 # WORKING_VALUE

# --------------------------------------------------------------------------------------------
# Horizontal markings [ZNAKI-Z2]. All lengths in metres.
LINE_W_NARROW = 0.12                # rys. 2.2.1.1 / 2.2.1.2 / 2.2.1.6 (P-1a, P-1b, P-2a)
LINE_W_WIDE = 0.24                  # rys. 2.2.1.7 (P-2b), 2.2.2.2 (P-7a); pkt 2.2.2: P-7a/P-7b 0.24 m on
                                    # dual carriageways and roads with international route numbers
DASH = {                            # (dash, gap)
    "P-1a": (4.0, 8.0),             # rys. 2.2.1.1, roads > 70 km/h
    "P-1b": (2.0, 4.0),             # rys. 2.2.1.2, roads <= 70 km/h
    "P-1d": (1.0, 1.0),             # rys. 2.2.1.4, guiding through junctions
    "P-7a": (1.0, 1.0),             # rys. 2.2.2.2
}
P2A_MIN_LEN = 20.0                  # pkt 2.2.1.6: P-2a at least 20 m
P10_STRIPE = 0.50                   # rys. 4.2.1.1: stripes 0.5 m, gaps 0.5 m, <= 0.5 m from the edge
P10_GAP = 0.50
P10_EDGE_MAX = 0.50
P10_WIDTH = 4.0                     # pkt 4.2.1: crossing width s = 4.0 m (>= 2.5 m in built-up areas)
P12_W = 0.50                        # rys. 4.2.3.1: STOP line 0.5 m
P13_BASE, P13_GAP, P13_H = 0.50, 0.25, 0.70   # rys. 4.2.4.1: triangles
P14_LEN, P14_GAP, P14_DEPTH = 0.75, 0.25, 0.50  # rys. 4.2.5.1: rectangles 0.5 deep (0.375 m2/mb)
P14_BEFORE_SIGNAL = 2.0             # pkt 4.2.5: >= 2.0 m before signals beside the carriageway
P14_BEFORE_CROSSING = 2.0           # pkt 4.2.5: >= 2.0 m before a pedestrian crossing
ARROW_SHORT = {"len": 5.00, "head_len": 2.05, "head_w": 0.75, "shaft_w": 0.15}   # rys. 3.2.1.2 a)
ARROW_LONG = {"len": 7.50, "head_len": 2.05, "head_w": 0.75, "shaft_w": 0.15}    # rys. 3.2.1.2 b)
ARROW_SPACING = {"short": 15.0, "long": 30.0}   # pkt 3.2.1: 15 m (<= 70 km/h), 30 m (others)
MARKING_LIFT = 0.006                # m above the surface (paint 3 mm + bias), decal depth offset in engine
SEGREGATION_MIN_CARRIAGEWAY = 5.80  # pkt 2.2.1: no segregation lines on two-way carriageways < 5.80 m

# ============================================================================================
# Streetscape (tools/worldgen/streetscape). Sources:
#  [ZNAKI-Z1]  Załącznik nr 1 (vertical signs) to the same 2003 regulation as [ZNAKI-Z2], as amended by
#              Dz.U. 2021 poz. 2066 (Table 1.11 "Wysokość umieszczania znaków", pkt 1.5.3) – read
#              2026-11-09 at https://api.sejm.gov.pl/eli/acts/DU/2021/2066/text.html
# --------------------------------------------------------------------------------------------
# Paved areas (yards, parking lots). Not regulated geometry -> WORKING_VALUE.
PAVED_SMOOTH_M = 3.0        # sigma of the NMT smoothing under yards (NMT 1 m, sd 0.09 m) WORKING_VALUE
PAVED_BLEND_M = 12.0        # distance over which a yard blends into the adjacent road edge height WORKING_VALUE
PAVED_LIFT = 0.0            # yard surface = smoothed ground (terrain conformed TERRAIN_UNDER_ROAD below)
PAVED_FLANGE = 0.30         # vertical skirt under yard edges (hides the terrain seam)
EDGING_W = 0.08             # concrete edging (obrzeże betonowe 8 x 30 cm), common Polish practice WORKING_VALUE
EDGING_H = 0.03             # top of edging above the block paving WORKING_VALUE
SETBACK_PATH_W = 2.0        # default width of a set-back footpath without BDOT SZEROKOSC (PTB2022 § 29: >= 1.80 m)
SURFACE_OF = {"yard_paving": "paving", "sidewalk_paving": "paving", "cycle_red": "asphalt",
              "yard_concrete": "asphalt", "yard_slabs": "asphalt", "yard_asphalt": "asphalt",
              "path_asphalt": "asphalt", "yard_gravel": "grass"}   # -> collision_<x> materials

# Vertical signs [ZNAKI-Z1]. Table 1.11: lower edge >= 2.00 m in built-up areas, 2.20 m when the sign
# stands on a sidewalk; signs over the carriageway >= 5.00 m.
SIGN_H_MIN = 2.00
SIGN_H_SIDEWALK = 2.20
SIGN_H_OVERHEAD = 5.00
# Sizes ("średnie" group, used on Z/G/GP streets) – WORKING_VALUE: Table 1.1 of [ZNAKI-Z1] not yet read;
# values are common catalogue plate sizes (triangle side 900, disc 800, square 800, octagon 800 mm).
# To be verified against Tabl. 1.1 before release.
SIGN_SIZE = {"triangle": 0.90, "disc": 0.80, "square": 0.80, "octagon": 0.80, "diamond": 0.80}
SIGN_LATERAL = 0.75         # WORKING_VALUE: plate edge 0.5-1.0 m behind the kerb face (never over the kerb)
SIGN_POST_D = 0.0603        # Ø60.3 mm galvanised tube, standard Polish sign post (catalogue) WORKING_VALUE
SPEED_SIGN_AFTER_JUNCTION = 30.0  # WORKING_VALUE distance; rule: a B-33 limit ends at the next junction
                                  # (rozporządzenie o znakach i sygnałach drogowych, Dz.U. 2019 poz. 2310
                                  # § 27 ust. 1), so the sign is repeated after every junction
# Street lighting. PN-EN 13201-2 lighting classes do not fix geometry; WORKING_VALUE from typical
# Polish municipal practice: galvanised conical steel columns, LED luminaire on a bracket.
LAMP = {"GP": {"h": 12.0, "spacing": 36.0, "bracket": 1.5},
        "G": {"h": 10.0, "spacing": 33.0, "bracket": 1.5},
        "Z": {"h": 9.0, "spacing": 30.0, "bracket": 1.0},
        "L": {"h": 8.0, "spacing": 30.0, "bracket": 1.0},
        "D": {"h": 8.0, "spacing": 32.0, "bracket": 0.5}}
LAMP_OFFSET = 0.80          # WORKING_VALUE: column axis behind the kerb face (skrajnia >= 0.5 m)
# Traffic signals: S-1 three-aspect heads, Ø300 mm lenses (załącznik nr 3 of the 2003 regulation).
# Placement -> WORKING_VALUE until read.
SIGNAL_POLE_H = 4.0         # WORKING_VALUE
SIGNAL_MAST_H = 6.8         # WORKING_VALUE: cantilever mast, head >= 5.0 m over the carriageway
SIGNAL_CANTILEVER_LANES = 3 # WORKING_VALUE: approaches with >= 3 lanes get a cantilever head
# Road restraint systems. GDDKiA "Wytyczne stosowania drogowych barier ochronnych na drogach krajowych"
# (2010): barrier warranted on embankments higher than ~2 m – WORKING_VALUE until the text is read.
GUARDRAIL_EMBANKMENT_H = 2.0
GUARDRAIL_H = 0.75          # top of W-beam (typical SP-05 system) WORKING_VALUE
GUARDRAIL_POST_SPACING = 2.0
GUARDRAIL_OFFSET = 0.60     # behind the kerb face / edge WORKING_VALUE
RAILING_H = 1.10            # pedestrian railing U-12a WORKING_VALUE (catalogue 1.0-1.1 m)
# Fences (industrial plots) – catalogue values of 3D welded panel fences WORKING_VALUE
FENCE_PANEL_W = 2.50
FENCE_H = 2.03
FENCE_PLINTH_H = 0.20
CONCRETE_FENCE_H = 2.00     # prefabricated concrete panel fence (OSM barrier=wall around plots) WORKING_VALUE
CONCRETE_FENCE_POST = 2.00
NOISE_BARRIER_H = 4.0       # WORKING_VALUE (BDOT10k OT_OIKM_L has no height)
NOISE_BARRIER_POST = 4.0
# Loading docks (warehouse halls). WORKING_VALUE (catalogue values of dock equipment).
DOCK_FLOOR_H = 1.20         # dock floor above the yard (EUR semitrailer bed 1.1-1.3 m)
DOCK_PITCH = 4.0            # door spacing
DOCK_DOOR_W, DOCK_DOOR_H = 3.0, 3.0
DOCK_SHELTER_W, DOCK_SHELTER_H, DOCK_SHELTER_D = 3.40, 3.50, 0.60
DOCK_APRON_L = 18.0         # concrete apron in front of each dock


def road_class(highway: str) -> str:
    return OSM_TO_CLASS.get(highway, "D")


def design_speed(highway: str, maxspeed: float | None) -> float:
    v = maxspeed or 50.0
    return float(v)


def grade_limit(highway: str, maxspeed: float | None) -> tuple[float, float]:
    """(standard, difficult) max grade for a road (PTB2022 § 20 ust. 2 / § 62 ust. 2)."""
    if highway == "service" or highway == "living_street":
        return MAX_GRADE_SERVICE, MAX_GRADE_SERVICE
    if highway.endswith("_link"):
        return MAX_GRADE_RAMP, MAX_GRADE_RAMP
    vp = design_speed(highway, maxspeed)
    for v, std, diff in MAX_GRADE_BY_VP:
        if vp >= v:
            return std, diff
    return MAX_GRADE_BY_VP[-1][1:]
