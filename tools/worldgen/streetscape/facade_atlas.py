"""Layout of the building atlases (ADR 0081) - the contract between the texture builder
(art-source/world/materials/_src/sets_buildings.py) and the mesh generator (buildings_mesh / facade_kit / furniture).

facade_atlas   calibrated PBR strip atlas, 16 x 16 m, mesh UV0 in atlas metres (materials.M["facade_atlas"], set_tile).
               One cell = one complete element: a window with its frame and what is behind the glass (net curtain,
               drapes, roller blind, plants, a dark or a lit room), a balcony door, an entrance, a garage door, a
               balcony balustrade, an AC unit ... Cells of one kind have the same size, so the generator only picks a
               variant. A 5 cm gutter of edge colour surrounds every cell (mips, half-float UV).
facade_far     modulation set (neutral wall = 0.5, tinted by the wall colour), 24 m x FAR_H: one row = one storey of
               8 window bays (3.0 m) composed from the same cells; LOD1 walls draw one quad per storey with a row and
               a bay offset picked per storey, LOD0 picks its cells from the same row, so the two LODs agree.
fence_concrete calibrated strip atlas 16 x 4.5 m: 2.0 x 2.0 m bays of prefabricated concrete fence (4 plates),
               posts, cap.
Pure Python (no numpy): imported by both sides and by the tests.
"""
from __future__ import annotations

import hashlib

ATLAS_M = (16.0, 16.0)
GUTTER = 0.05

# kind: (width m, height m, variants)
KINDS = {
    "w2": (1.5, 1.45, 10),        # two-sash PVC window (block, 3.0 m bay)
    "w1": (0.9, 1.45, 6),         # single sash (kitchen / bathroom)
    "w3": (2.1, 1.45, 3),         # three-sash living-room window
    "bdoor": (0.9, 2.2, 5),       # balcony door
    "bwin": (1.1, 1.35, 5),       # window next to the balcony door (parapet below is wall)
    "stair": (1.2, 1.2, 3),       # stairwell window
    "base": (0.9, 0.45, 3),       # basement window with a grille
    "off": (1.5, 1.6, 5),         # office window
    "house": (1.2, 1.4, 4),       # house window
    "hallw": (2.0, 1.0, 3),       # hall strip window
    "indw": (3.0, 1.8, 2),        # old industrial steel-sash window
    "door_block": (1.6, 2.25, 3), # block entrance (aluminium, glazed, intercom side panel)
    "door_steel": (1.0, 2.1, 3),  # steel personnel door
    "door_house": (1.0, 2.25, 3),
    "garage": (2.5, 2.15, 6),     # garage doors: double-leaf sheet steel, up-and-over
    "balf": (2.6, 1.05, 8),       # balcony balustrade front
    "balg": (2.6, 1.45, 3),       # balcony glazing-in above the balustrade
    "ac": (0.85, 0.6, 2),         # AC outdoor unit front
    "vent": (0.5, 0.5, 2),        # wall louvre
    "elbox": (0.6, 0.8, 2),       # meter / gas cabinet door
    "plate": (0.3, 0.4, 2),       # intercom panel, blank number plate
}
SWATCHES = ["pvc_white", "alu_sill", "concrete", "steel_grey", "steel_dark", "galv", "wood", "pvc_brown",
            "cloth_white", "cloth_red", "cloth_blue", "cloth_dark", "cloth_yellow", "cloth_green", "dish", "rubber",
            "glass_dark", "roof_felt", "terracotta", "leaf"]
SWATCH_M = 0.25


def _pack():
    """Shelf packing, tallest kinds first; returns {(kind, variant): (u0, v0, w, h)} (v up from the atlas bottom)."""
    items = []
    for k, (w, h, n) in KINDS.items():
        items += [(h, w, k, i) for i in range(n)]
    items += [(SWATCH_M, SWATCH_M, "sw_" + s, 0) for s in SWATCHES]
    items.sort(key=lambda t: (-t[0], t[2], t[3]))
    cells = {}
    u, v, shelf = GUTTER, GUTTER, 0.0
    for h, w, k, i in items:
        if u + w + GUTTER > ATLAS_M[0]:
            u, v, shelf = GUTTER, v + shelf + 2 * GUTTER, 0.0
        cells[(k, i)] = (round(u, 4), round(v, 4), w, h)
        u += w + 2 * GUTTER
        shelf = max(shelf, h)
    if v + shelf + GUTTER > ATLAS_M[1]:
        raise ValueError(f"facade atlas overflow: {v + shelf + GUTTER:.2f} m > {ATLAS_M[1]} m")
    return cells


CELLS = _pack()


def cell(kind, variant=0):
    return CELLS[(kind, variant % KINDS[kind][2])] if kind in KINDS else CELLS[(kind, 0)]


def uv_rect(kind, variant=0, flip=False):
    """UV (atlas metres) of the 4 corners of a cell in quad order bottom-left, bottom-right, top-right, top-left."""
    u0, v0, w, h = cell(kind, variant)
    if flip:
        return [[u0 + w, v0], [u0, v0], [u0, v0 + h], [u0 + w, v0 + h]]
    return [[u0, v0], [u0 + w, v0], [u0 + w, v0 + h], [u0, v0 + h]]


def swatch_uv(name, n=4):
    """UV of a point well inside a swatch (flat-colour faces: all vertices of a face share it or a small patch)."""
    u0, v0, w, h = CELLS[("sw_" + name, 0)]
    return [[u0 + 0.05, v0 + 0.05], [u0 + w - 0.05, v0 + 0.05], [u0 + w - 0.05, v0 + h - 0.05], [u0 + 0.05, v0 + h - 0.05]][:n]


def hint(*key):
    return int(hashlib.sha1(":".join(str(k) for k in key).encode()).hexdigest()[:8], 16)


# ------------------------------------------------------------------------------------------- far rows (LOD1)
FAR_BAYS = 8
FAR_PITCH = 3.0
FAR_ROW_H = 2.8                 # one storey; the generator scales v to the real storey height
FAR_V0 = 1.0                    # rows start 1 m up: the _SPLASH zone of plaster_* reads UV0.v < 0.6 m as ground dirt
# (kind, variant) per bay; None = blank wall. "bal" = balcony (door + window + balustrade front variant).
FAR_ROWS = {
    "block": [
        [("w2", 0), ("w1", 0), ("w2", 3), ("w2", 5), ("w1", 2), ("w2", 1), ("w2", 7), ("w1", 4)],
        [("w2", 2), ("w2", 8), ("w1", 1), ("w2", 4), ("w2", 9), ("w1", 3), ("w2", 6), ("w1", 5)],
        [("w2", 9), ("w1", 5), ("w2", 1), ("w3", 0), ("w1", 0), ("w2", 6), ("w2", 2), ("w3", 2)],
        [("w1", 3), ("w2", 5), ("w2", 0), ("w1", 1), ("w2", 8), ("w3", 1), ("w1", 4), ("w2", 3)],
    ],
    "balcony": [
        [("bal", 0), ("w2", 4), ("bal", 3), ("w1", 1), ("bal", 6), ("w2", 8), ("bal", 1), ("w2", 0)],
        [("bal", 5), ("w1", 3), ("bal", 2), ("w2", 7), ("bal", 7), ("w2", 3), ("bal", 4), ("w1", 2)],
        [("bal", 2), ("w2", 9), ("bal", 6), ("w2", 1), ("bal", 0), ("w1", 5), ("bal", 5), ("w2", 6)],
        [("bal", 7), ("w2", 2), ("bal", 4), ("w1", 0), ("bal", 3), ("w2", 5), ("bal", 1), ("w1", 4)],
    ],
    # offices: one window family per building (white PVC / anthracite aluminium) - what differs from window to
    # window is the blind and the light, never the joinery (`off` variants 0, 2, 4 white, 1, 3 anthracite)
    "office": [
        [("off", 0), ("off", 2), ("off", 4), ("off", 2), ("off", 0), ("off", 4), ("off", 2), ("off", 0)],
        [("off", 4), ("off", 0), ("off", 2), ("off", 0), ("off", 4), ("off", 2), ("off", 4), ("off", 2)],
    ],
    "office_d": [
        [("off", 1), ("off", 3), ("off", 3), ("off", 1), ("off", 3), ("off", 1), ("off", 3), ("off", 3)],
        [("off", 3), ("off", 1), ("off", 3), ("off", 3), ("off", 1), ("off", 3), ("off", 1), ("off", 3)],
    ],
    "ribbon": [[("rib", 1 if (i * 3 + j) % 4 == 0 else 3) for i in range(8)] for j in range(2)],
}
# balcony rows first: every other group starts with a blank sill zone, so the row above any group's last row is plain
# wall for 0.9 m (far_plain_above) and LOD1 can run its last chunk up to the wall top
FAR_ORDER = [(g, i) for g in ("balcony", "block", "office", "office_d", "ribbon") for i in range(len(FAR_ROWS[g]))]
FAR_M = (FAR_BAYS * FAR_PITCH, FAR_V0 + FAR_ROW_H * len(FAR_ORDER))
# sill height above the floor / window height per row group (m, at FAR_ROW_H storey height)
FAR_SILL = {"block": 0.9, "balcony": 0.9, "office": 0.9, "office_d": 0.9, "ribbon": 0.9}


def far_row(group, key):
    """(row index within the group, bay offset 0..7) for one storey of one wall (key = building, edge, storey)."""
    return hint(key, "row") % len(FAR_ROWS[group]), hint(key, "off") % FAR_BAYS


def far_row_v(group, row):
    """v (atlas metres) of the floor line of a row."""
    return FAR_V0 + FAR_ROW_H * FAR_ORDER.index((group, row))


def far_entry(group, row, off, bay):
    return FAR_ROWS[group][row][(bay + off) % FAR_BAYS]


FAR_TOP = {"block": 2.35, "balcony": 2.35, "office": 2.5, "office_d": 2.5, "ribbon": 2.5}      # window head above the floor (m at FAR_ROW_H)
FAR_PLAIN_V = (0.65, 0.95)      # v range of the plain wall strip below the rows (above the _SPLASH zone)


def far_groups(typ, storeys, balcony=False, ribbon=False, bkey=""):
    """Row group of every storey of one wall: blocks get balcony rows on their balcony side,
    ribbon offices get ribbon rows from the 1st floor (anthracite ground floor); other offices are white-framed or
    anthracite-framed as a whole building (bkey = building id)."""
    if typ == "block":
        return ["balcony" if balcony else "block"] * storeys     # raised ground floor: balconies from the parter up
    if ribbon:
        return ["office_d"] + ["ribbon"] * (storeys - 1)
    return ["office_d" if hint(bkey, "joinery") % 5 < 2 else "office"] * storeys


def far_storeys(groups, sh, zbase_top):
    """Number of storeys whose windows fit below zbase_top (= wall top - 0.3 m - ground floor level), counted from
    the ground floor; the storey scale k = sh / FAR_ROW_H stretches sill and window height on both LODs."""
    k = sh / FAR_ROW_H
    n = 0
    for s, g in enumerate(groups):
        if s * sh + FAR_TOP[g] * k > zbase_top:
            break
        n += 1
    return n


def far_plan(groups, key):
    """Chunks of consecutive storeys that are consecutive rows of one group in the row atlas, so LOD1 draws one quad
    per chunk: [(first storey, storeys, group, first row, bay offset)]. LOD0 reads the same plan (far_storey)."""
    out = []
    s = c = 0
    while s < len(groups):
        g = groups[s]
        rows = len(FAR_ROWS[g])
        r0 = 0
        if s == 0 or groups[s - 1] != g:
            run = 1
            while s + run < len(groups) and groups[s + run] == g:
                run += 1
            if g == "balcony":                    # end on the group's last row: the attic band folds into the chunk
                r0 = (rows - run % rows) % rows
            else:                                 # a random first row, unless it would cost one more chunk (quad)
                r0 = hint(key, g, "r0") % rows
                if -(-(run + r0) // rows) > -(-run // rows):
                    r0 = 0
        n = 1
        while s + n < len(groups) and groups[s + n] == g and r0 + n < rows:
            n += 1
        off = hint(key, g, c) % FAR_BAYS
        if g == "balcony":
            off -= off % 2                      # balconies stay on the even bays of the wall, storey above storey
        out.append((s, n, g, r0, off))
        s += n
        c += 1
    return out


def far_plain_above(group, row):
    """True when the atlas is plain wall for 0.85 m above this row (the next row starts with a blank sill zone, or the
    atlas wraps into the plain strip): LOD1 then runs the last chunk up to the wall top instead of a separate band."""
    i = FAR_ORDER.index((group, row)) + 1
    return i == len(FAR_ORDER) or FAR_ORDER[i][0] != "balcony"


def far_storey(plan, s):
    """(group, row, bay offset) of storey s."""
    for s0, n, g, r0, off in plan:
        if s0 <= s < s0 + n:
            return g, r0 + (s - s0), off
    raise IndexError(s)


# ------------------------------------------------------------------------------------------- concrete fence
FENCE_M = (16.0, 4.5)
FENCE_BAY = (2.0, 2.0)          # one bay between post axes x height above the footing line
FENCE_VARIANTS = {"plate": 8, "frame": 5}       # style -> variants (row 0: stacked plates, row 1: framed panels)


def fence_uv(style, variant):
    """(u0, v0, w, h) of a fence bay cell; posts / cap swatches: fence_post_uv()."""
    row = 0 if style == "plate" else 1
    u0 = GUTTER + (variant % FENCE_VARIANTS[style]) * (FENCE_BAY[0] + 0.0)       # bays tile: neighbours continue
    return (u0 - GUTTER + 0.0, GUTTER + row * (FENCE_BAY[1] + 2 * GUTTER), FENCE_BAY[0], FENCE_BAY[1])


def fence_post_uv():
    """Post strip: 0.30 m wide (unrolled front + side) x 2.2 m, right of the framed panels."""
    return (FENCE_VARIANTS["frame"] * FENCE_BAY[0] + 0.3, GUTTER + FENCE_BAY[1] + 2 * GUTTER, 0.30, 2.0)
