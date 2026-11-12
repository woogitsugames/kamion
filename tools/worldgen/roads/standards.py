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
CROSSFALL_MATCH_M = 20.0            # WORKING_VALUE: ramp length matching crossfall of through chains at a node

# Kerb ("krawężnik"). Height 0.12-0.15 m in Polish urban practice; PTB2022 § 89 ust. 2 pkt 1 treats a
# kerb >= 0.12 m as a (barrier-relevant) raised kerb. 0.13 m = WORKING_VALUE. Standard 15 x 30 cm kerb -> top width 0.15 m.
KERB_HEIGHT = 0.13
KERB_TOP_W = 0.15
# network._tight_side: chains sharing a node are left to the junction patch within this distance of it (WORKING_VALUE,
# about the largest junction cluster radius, junctions.py max cluster diameter 30 m)
ADJ_NODE_SKIP_M = 30.0
# profile.adjacent_targets: a chain solved after a parallel ground road whose edge it touches (gap < ADJ_TOUCH_M)
# takes that road's surface height at the shared edge, weight ADJ_WEIGHT against 1 for an NMT sample (WORKING_VALUEs)
ADJ_TOUCH_M = 0.5
ADJ_WEIGHT = 400.0
KERB_HEIGHT_APRON = 0.04            # WORKING_VALUE: roundabout truck apron kerb (mountable)
# Sidewalk. PTB2022 § 29 ust. 1: >= 1.80 m. 2.00 m = WORKING_VALUE. Crossfall towards the road
# <= 3 % (PTB2022 § 33); we use 2 %.
SIDEWALK_W = 2.00
SIDEWALK_CROSSFALL = 0.02
VERGE_W = 1.00                      # WORKING_VALUE: grass strip behind the kerb when no sidewalk
VERGE_SKIRT_SLOPE = 2.0              # WORKING_VALUE (ADR 0110): run per unit fall of the grass skirt of a verge strip
MEDIAN_VERGE_MAX = 3.00             # WORKING_VALUE (ADR 0110): grass strip behind a median kerb (two meet in the middle)
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
CHAMFER_RATIO = 4.0                 # WORKING_VALUE: kerb chamfer 1:4 where a carriageway narrows at a split (gate islands)
SWALE_DEPTH = 0.20                  # WORKING_VALUE: shallow swale instead of a ditch where a set-back path runs < 7 m away
DITCH_DEPTH = 0.60                  # WORKING_VALUE
DITCH_SLOPE = 1.5                   # 1 : 1.5, WORKING_VALUE
DITCH_BOTTOM_W = 0.40               # WORKING_VALUE
EMBANKMENT_SLOPE = 1.5              # 1 : 1.5 cut/fill slopes, WORKING_VALUE (§ 25 is performance-based)
BERM_W = 1.0                        # flat strip next to the road before the embankment slope starts

# Curb-return radii at junctions (promień łuku krawężnika), metres. WORKING_VALUE, chosen for a
# 16.5 m articulated truck; the regulation (§ 58 ust. 3) only requires passage of the design vehicle.
CURB_RADIUS = {"A": 20.0, "S": 20.0, "GP": 15.0, "G": 12.0, "Z": 10.0, "L": 8.0, "D": 8.0}
NOSE_MAX_ANGLE_DEG = 25.0           # corners narrower than this get a median/splitter nose
# Junction patch collision fill spacing (m). Was 6 m: on long patches (fork trims of 65-68 m) the linear 6 m facets
# left 5-6 cm steps under the wheels (route_start s = 1422 m, test_route_corridor). WORKING_VALUE.
PATCH_COLLISION_SPACING_M = 2.0
NOSE_MIN_GAP_M = 0.5                # ... if the clear width between the carriageways is at least this (WORKING_VALUE)
STRAIGHT_MIN_ANGLE_DEG = 155.0      # corners wider than this are a straight kerb (no fillet)
FORK_STRAIGHT_DEG = 150.0          # WORKING_VALUE: two chains this close to collinear at a node = one road
TAPER_RATIO = 10.0                 # WORKING_VALUE: taper length = 10 x width change (skos 1:10)
TAPER_MIN_M = 15.0                 # WORKING_VALUE
TAPER_MAX_DHW = 1.25               # WORKING_VALUE: larger half-width changes are lane additions (kept as is)
JUNCTION_MIN_TRIM = 2.0             # m, minimal junction size along each arm

# Roundabouts: circulatory crossfall falls outwards (towards the outer kerb). WORKING_VALUE.
ROUNDABOUT_APRON_W = 2.0            # WORKING_VALUE: mountable apron around the central island
ROUNDABOUT_CROSSFALL = 0.02

# Bridges (low confidence: OSM only says bridge=viaduct + layer)
BRIDGE_DECK_THICKNESS = 1.20        # WORKING_VALUE
# Vertical clearance (skrajnia jezdni) under a structure: rozporządzenie Ministra Infrastruktury z dnia 24 czerwca
# 2022 r. w sprawie przepisów techniczno-budowlanych dotyczących dróg publicznych (Dz.U. 2022 poz. 1518, "PTB2022"),
# § 80 ust. 1: wysokość skrajni nie mniejsza niż 5,00 m dla jezdni drogi klasy A lub S (pkt 1) i 4,50 m dla jezdni
# drogi klasy GP, G, Z, L lub D (pkt 2); § 78 ust. 6: mierzona pionowo od nawierzchni. § 80 ust. 2 allows less only
# in difficult conditions / for existing structures with consent (not modelled). Read from the ISAP/ELI text of the
# regulation on 2026-11-09. v3 used a flat WORKING_VALUE 4.70 m (the figure of the repealed 2000 regulation on road
# engineering structures for A/S/GP, not re-read here: UNVERIFIED).
# BRIDGE_CLEARANCE_MARGIN 0.30 m: WORKING_VALUE (future overlay, crossfall, deck sag); the regulation has no such
# term. The real deck heights of the Andersa viaducts are not in the data (the NMT is the lidar ground class and
# has the ring roads, not the decks, at the crossings: checked, deck-minus-ring in the NMT 0.3-1.2 m = noise).
CLEARANCE_BY_CLASS = {"A": 5.00, "S": 5.00, "GP": 4.50, "G": 4.50, "Z": 4.50, "L": 4.50, "D": 4.50}
BRIDGE_CLEARANCE = 4.50             # minimum over the classes above (PTB2022 § 80 ust. 1 pkt 2)
BRIDGE_CLEARANCE_MARGIN = 0.30


def clearance_height(cls: str) -> float:
    return CLEARANCE_BY_CLASS.get(cls, BRIDGE_CLEARANCE)


# Raised ramps (layer >= 1, no bridge) built on retaining walls when the NMT has no fill under them
# (profile.mark_walled_ramps). WORKING_VALUE thresholds.
RAMP_WALL_MIN_H = 1.0
RAMP_WALL_FILL_FRAC = 0.35
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
# P-11 cycle crossing: two rows of squares. UNVERIFIED against [ZNAKI-Z2] pkt 4.2.2 (not at hand): 0.4 m squares,
# 0.4 m gaps, rows 2.0 m apart (inner edges) read off the GUGiK 0.08 m orthophoto at Rondo Putry (ADR 0093).
P11_SQUARE, P11_GAP, P11_CLEAR = 0.40, 0.40, 2.0
P8_MIN_LANE_W = 2.5                 # ADR 0093: no arrow in a lane narrower than this (taper of a slip lane)
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
SURFACE_OF = {"yard_paving": "paving", "yard_behaton": "paving", "sidewalk_paving": "paving", "cycle_red": "asphalt",
              "yard_concrete": "asphalt", "yard_concrete_worn": "asphalt", "yard_slabs": "asphalt", "yard_asphalt": "asphalt",
              "path_asphalt": "asphalt", "yard_gravel": "grass",
              "plot_lawn": "grass"}   # -> collision_<x> materials

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
SIGNAL_CANTILEVER_LANES = 2 # WORKING_VALUE: approaches with >= 2 lanes get a cantilever head (ADR 0069: Mapillary
                            # p42 / p45 / p47 show curved mast arms over the 2-lane entries of Rondo Putry; was 3)
SIGNAL_MAST_BEND_R = 1.5    # WORKING_VALUE: bend radius of the mast arm, read off p42 against the 0.36 m head
# Road restraint systems. GDDKiA "Wytyczne stosowania drogowych barier ochronnych na drogach krajowych"
# (2010): barrier warranted on embankments higher than ~2 m – WORKING_VALUE until the text is read.
GUARDRAIL_EMBANKMENT_H = 2.0
GUARDRAIL_H = 0.75          # top of W-beam (typical SP-05 system) WORKING_VALUE
GUARDRAIL_POST_SPACING = 2.0
GUARDRAIL_OFFSET = 0.60     # behind the kerb face / edge WORKING_VALUE
GUARDRAIL_TERMINAL_M = 4    # WORKING_VALUE (ADR 0110): free ground end of a W-beam turned down to the ground over this length
GUARDRAIL_POST_SPACING_GROUND = 4.0   # WORKING_VALUE (ADR 0117): ground runs, posts every 4 m (SP-05/4 class; Mapillary
#                                       500263111404933 / 1259231227807789: 2-4 m read by eye); decks keep 2.0 m
CAP_GRIME = (1.0, 0.85)     # ADR 0123: road film on a bridge cap, COLOR_0.r at the kerb / at the outer edge (WORKING_VALUE)
BRIDGE_BARRIER_H = 0.98     # WORKING_VALUE (ADR 0117): top of the deck posts and of the upper box beam above the W-beam
#                             (Mapillary 454716650857984: W-beam low, a second beam above it; 1.10 with a handrail in 0110)
BRIDGE_BARRIER_EDGE_M = 0.40  # WORKING_VALUE: barrier post line in from the outer edge of the cap (orthophoto 0.2-0.4 m)
BRIDGE_BARRIER_EDGE_MIN_M = 0.32  # ... on a narrow cap (ADR 0117: cap 1.0 m -> beam face 0.70 m behind the kerb face)
# ADR 0123 (REVIEW s10-0117 P1-3): 0.70 -> 0.42. Measured in the exported world (xsec_glb.py, deck station E 490 N -675):
# edge-line centre -> beam face was 1.02 m, -> post feet 1.37 m; the same image-row method of the review reads 1.69 m
# for those 1.37 m and 1.47 m on Mapillary 454716650857984, i.e. the photo has the barrier ~0.25-0.3 m closer.
BRIDGE_BARRIER_FACE_M = 0.42  # kerb face -> beam face on a narrow cap (bridge_style cap_w < 1.3 m), WORKING_VALUE +-0.2
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


# Recently resurfaced carriageways (ADR 0019). There is no resurfacing date in OSM / BDOT10k, so a share of the public
# road chains (class Z and up, not roundabouts, not bridges) gets the fresh SMA wearing course (material
# road_asphalt_new, texture set asphalt_sma_fresh); junction patches keep the worn surface of the majority of their
# arms (resurfacing usually stops at the junction). The share and the classes are WORKING_VALUE; an authored override
# `surface: asphalt_new` / `surface: asphalt` on the edges wins.
NEW_ASPHALT_SHARE = 0.25
NEW_ASPHALT_CLASSES = ("A", "S", "GP", "G", "Z")
NEW_ASPHALT_MIN_LEN_M = 120.0   # WORKING_VALUE (ADR 0110): a shorter chain is never "resurfaced" on its own - a 20 m
#                                 chain between two plates (Putry N southbound, N 100-120) read as a patch rectangle


def surface_material(chain, sec):
    """Engine surface material of a carriageway chain: the section's material, with worn asphalt switched to
    road_asphalt_new for the resurfaced share (deterministic hash of the chain id)."""
    import hashlib
    m = sec.surface_mat
    if m != "road_asphalt" or sec.provenance.get("surface_override"):
        return m
    br = getattr(chain, "bridge", None)
    if chain.roundabout or sec.cls not in NEW_ASPHALT_CLASSES or (br is not None and bool(br.any())):
        return m
    if float(getattr(chain, "length", 1e9)) < NEW_ASPHALT_MIN_LEN_M:
        return m
    h = int(hashlib.sha1(f"{chain.id}:asphalt_new".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return "road_asphalt_new" if h < NEW_ASPHALT_SHARE else m


# Height of ground-standing props above their base (m), for "does it pierce a deck above" checks (ADR 0076).
# Lamps carry their height in the prototype name; the rest are WORKING_VALUEs read off the prop generator.
GROUND_PROP_H = {"signal_mast": SIGNAL_MAST_H, "signal_pole": SIGNAL_POLE_H, "sign_post": 3.6, "power_pole": 10.0,
                 "pylon": 30.0, "bollard": 1.0, "bus_shelter": 2.8, "bench": 0.9, "waste_bin": 1.0,
                 "street_cabinet": 1.4, "gantry_footing": 1.0}


def ground_prop_height(proto: str) -> float:
    import re
    if proto.startswith("lamp_"):
        m = re.search(r"_(\d+)m$", proto)
        return float(m.group(1)) if m else 10.0
    for k, v in GROUND_PROP_H.items():
        if proto.startswith(k):
            return v
    return 3.0
