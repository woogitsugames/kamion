"""Gate 3 route landmarks that the rule-based furniture does not produce (ADR 0125, owner decision D51: the driver
must recognise the route). Everything is data in Data/Regions/<id>/overrides.yaml and survives a re-import:

  kind: gate3_sign    one vertical sign assembly = ONE prototype with ONE material (post, plates and backs share a small
                      texture: one draw per sign on every tier). `parts` are listed top first:
                        {face: A-30, plate: "text"}       warning triangle (upright) + yellow plate with a short text
                        {face: A-7}                       give way (triangle point down), ADR 0160
                        {face: U-4a}                      red / white chevron board on a traffic-island nose
                        {face: D-3} / {face: D-6} / {face: D-1}
                        {face: F-10}                      lane directions before a junction (straight | right), two posts
                        {face: street_name, text: "..."}  city street-name plate (teal plate, teal post)
                      Position, one of:
                        at_en: [E, N]                     region-local metres (measured on the GUGiK orthophoto)
                        along: {osm_way, before_node, distance_m, side: L|R, offset_m}   like sign_gantry: `distance_m`
                               before the node, `offset_m` behind the kerb on that side of TRAVEL
                      `travel_bearing_deg` (compass bearing of the traffic that reads the sign; the face looks the
                      other way) is required with at_en and optional with along (default: the chain's travel).
                      `lower_edge_m` (default 2.0 m, Tabl. 1.11 [ZNAKI-Z1]; U-4a boards stand lower), `mapillary` ids.

  kind: gate3_signal  traffic signals that the junction rule does not produce (ADR 0161: the rule skips ring arms, so
                      the signalised approaches inside the Rondo Putry ring had none). Existing prototypes only
                      (signal_mast / signal_pole / signal_head_<lit>), no new mesh or material:
                        at_en: [E, N]             pole foot (GUGiK orthophoto)
                        travel_bearing_deg        compass bearing of the traffic that reads the heads
                        arm_bearing_deg           optional: cantilever mast, arm from the pole in this direction
                                                  (the prototype arm is 6.0 m, head 5.0 m out, as the rule builds it)
                        lit: red | green | off    (default red)

Faces are our own schematic drawings (PIL), never pixels of a photo. Sizes are WORKING_VALUE unless a source is named.
Stale entries (way / node not found, sign on a carriageway) are reported in streetscape QA `gate3_landmarks`, never
dropped silently. Why a separate module: streetscape.{furniture,props,signs,signs_route} belong to a parallel session;
this file only needs one registration line in props.build_all and one call in stage.run.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np
from PIL import Image, ImageDraw

from roads import standards as S
from roads.network import RURAL, side_extent, side_params

from . import props as PP
from . import signs as SG

KIND = "gate3_sign"
KIND_SIGNAL = "gate3_signal"      # ADR 0161
PX_M = 420                    # texture resolution of a face, px per metre (before export resamples to 512 px width)
SWATCH_PX = 24                # post / back colour swatches, right of the faces
TEAL = (0, 126, 122)          # Białystok street-name plates and their posts (Mapillary 504348097385466, read by eye)
GALV = (150, 153, 154)
BACK = SG.GREY_BACK
FLUO = (238, 208, 0)          # yellow of warning signs / T plates
# face code -> (shape, width m, height m). Triangle side 0.9 m and D-1 0.6 m = standards.SIGN_SIZE (medium group,
# Tabela 1.1 / Tabela 5.1 of Dz.U. 2019 poz. 2311 zał. 1); D-3 0.6 m, U-4a 0.75 x 1.35 m, plates 0.6 x 0.45 m
# and the street-name plate 1.0 x 0.25 m are WORKING_VALUE read off the photos against the Ø60 mm post.
FACE_DIM = {
    "A-30": ("tri_up", S.SIGN_SIZE["triangle"], S.SIGN_SIZE["triangle"] * math.sqrt(3) / 2),
    # ADR 0160: give-way where a slip merges without an acceleration lane (no OSM give_way node, so the junction rule
    # does not see it). Same medium triangle, point down.
    "A-7": ("tri_down", S.SIGN_SIZE["triangle"], S.SIGN_SIZE["triangle"] * math.sqrt(3) / 2),
    "D-1": ("diamond", S.SIGN_SIZE["diamond"], S.SIGN_SIZE["diamond"]),
    "D-3": ("rect", 0.60, 0.60),
    "D-6": ("rect", 0.60, 0.60),
    "U-4a": ("rect", 0.75, 1.35),
    # ADR 0144: 2-lane F-10 read off Mapillary 482392746429891 (plate 140 x 85 px beside its own posts 12 px wide; with
    # the 60 mm post that is ~0.7 m, a real post of this board is thicker): 0.90 x 0.55 m WORKING_VALUE
    "F-10": ("rect", 0.90, 0.55),
    "plate": ("rect", 0.60, 0.45),
    "street_name": ("rect", 1.00, 0.25),
}
TWO_POSTS = {"F-10"}          # faces carried by two posts (0.3 x plate width either side of the middle)
PROTOS = {}                   # prototype name -> (lod0, lod1, collision), registered by build(), read by props.build_all


def prototypes():
    return dict(PROTOS)


# ------------------------------------------------------------------------------------------------- face drawings
def _fit_text(d, box, text, fill, bold_px):
    """Centre `text` (may contain newlines) in box = (x0, y0, x1, y1), shrinking the font until it fits."""
    x0, y0, x1, y1 = box
    px = bold_px
    while px > 8:
        f = SG._font(px)
        bb = d.multiline_textbbox((0, 0), text, font=f, align="center", spacing=px * 0.15)
        if bb[2] - bb[0] <= (x1 - x0) * 0.92 and bb[3] - bb[1] <= (y1 - y0) * 0.86:
            break
        px -= 2
    d.multiline_text(((x0 + x1) / 2 - (bb[2] - bb[0]) / 2 - bb[0], (y0 + y1) / 2 - (bb[3] - bb[1]) / 2 - bb[1]), text,
                     font=f, fill=fill, align="center", spacing=px * 0.15)


def draw_face(code, w_px, h_px, text=None):
    """RGB image of one face, w_px x h_px, the whole cell filled (the mesh is cut to the sign's outline, so no alpha
    is needed and no dark fringe bleeds in at the edges)."""
    if code == "A-30":                                   # warning: yellow triangle, red border, black "!"
        im = Image.new("RGB", (w_px, h_px), SG.RED)
        d = ImageDraw.Draw(im)
        b = 0.105 * w_px                                 # border width along the normal
        cx, top, bot = w_px / 2, 0.0, float(h_px)
        inner = [(cx, top + 2 * b), (w_px - b * math.sqrt(3), bot - b), (b * math.sqrt(3), bot - b)]
        d.polygon(inner, fill=FLUO)
        d.rounded_rectangle([cx - 0.035 * w_px, 0.40 * h_px, cx + 0.035 * w_px, 0.74 * h_px], radius=3, fill=SG.BLACK)
        d.ellipse([cx - 0.045 * w_px, 0.79 * h_px, cx + 0.045 * w_px, 0.79 * h_px + 0.09 * w_px], fill=SG.BLACK)
        return im
    if code == "A-7":                                    # give way: yellow triangle point down, red border, no symbol
        im = Image.new("RGB", (w_px, h_px), SG.RED)
        d = ImageDraw.Draw(im)
        b = 0.105 * w_px
        cx = w_px / 2
        d.polygon([(b * math.sqrt(3), b), (w_px - b * math.sqrt(3), b), (cx, h_px - 2 * b)], fill=FLUO)
        return im
    if code == "plate":                                  # T plate under a warning sign: black text on yellow
        im = Image.new("RGB", (w_px, h_px), SG.BLACK)
        d = ImageDraw.Draw(im)
        m = max(2, int(0.02 * w_px))
        d.rectangle([m, m, w_px - m - 1, h_px - m - 1], fill=FLUO)
        _fit_text(d, (m, m, w_px - m, h_px - m), text or "", SG.BLACK, int(h_px * 0.36))
        return im
    if code == "U-4a":                                   # separating board: red chevrons pointing up on white
        im = Image.new("RGB", (w_px, h_px), SG.WHITE)
        d = ImageDraw.Draw(im)
        m = int(0.035 * w_px)
        n, band = 3, h_px / 3.0
        t = band * 0.42                                  # chevron stroke (vertical thickness)
        rise = band * 0.50
        for k in range(n):
            yb = h_px - k * band - band * 0.04
            d.polygon([(m, yb), (w_px / 2, yb - rise), (w_px - m, yb), (w_px - m, yb - t), (w_px / 2, yb - rise - t),
                       (m, yb - t)], fill=SG.RED)
        d.rectangle([0, 0, w_px - 1, h_px - 1], outline=SG.RED, width=max(2, m // 2))
        return im
    if code == "D-3":                                    # one-way road: white arrow up on blue
        im = Image.new("RGB", (w_px, h_px), SG.WHITE)
        d = ImageDraw.Draw(im)
        m = int(0.03 * w_px)
        d.rectangle([m, m, w_px - m - 1, h_px - m - 1], fill=SG.BLUE)
        cx = w_px / 2
        d.rectangle([cx - 0.07 * w_px, 0.42 * h_px, cx + 0.07 * w_px, 0.86 * h_px], fill=SG.WHITE)
        d.polygon([(cx, 0.12 * h_px), (cx + 0.24 * w_px, 0.46 * h_px), (cx - 0.24 * w_px, 0.46 * h_px)], fill=SG.WHITE)
        return im
    if code == "F-10":                                   # lane directions: straight | right turn, dashed lane line between
        im = Image.new("RGB", (w_px, h_px), SG.WHITE)
        d = ImageDraw.Draw(im)
        m = max(2, int(0.02 * w_px))
        d.rectangle([m, m, w_px - m - 1, h_px - m - 1], fill=SG.BLUE)
        st = 0.075 * w_px                                # arrow stroke
        cx = 0.25 * w_px                                 # left lane: straight on
        d.rectangle([cx - st / 2, 0.40 * h_px, cx + st / 2, 0.84 * h_px], fill=SG.WHITE)
        d.polygon([(cx, 0.14 * h_px), (cx + 0.12 * w_px, 0.44 * h_px), (cx - 0.12 * w_px, 0.44 * h_px)], fill=SG.WHITE)
        for k in range(3):                               # lane line: three dashes
            y0 = (0.16 + 0.26 * k) * h_px
            d.rectangle([0.5 * w_px - st / 5, y0, 0.5 * w_px + st / 5, y0 + 0.15 * h_px], fill=SG.WHITE)
        x0 = 0.64 * w_px                                 # right lane: stem up, then bent to the right
        d.rectangle([x0 - st / 2, 0.42 * h_px, x0 + st / 2, 0.84 * h_px], fill=SG.WHITE)
        d.pieslice([x0 - st / 2, 0.42 * h_px - st, x0 + 1.5 * st, 0.42 * h_px + st], 180, 270, fill=SG.WHITE)
        d.rectangle([x0 + st / 2, 0.42 * h_px - st, 0.74 * w_px, 0.42 * h_px], fill=SG.WHITE)
        ya = 0.42 * h_px - st / 2
        d.polygon([(0.90 * w_px, ya), (0.73 * w_px, ya - 0.17 * h_px), (0.73 * w_px, ya + 0.17 * h_px)], fill=SG.WHITE)
        return im
    if code in ("D-6", "D-1"):                           # reuse the project's own drawings (streetscape.signs)
        src = SG.square("D-6") if code == "D-6" else SG.d1()
        bg = Image.new("RGBA", src.size, (*(SG.BLUE if code == "D-6" else SG.YELLOW), 255))
        return Image.alpha_composite(bg, src.convert("RGBA")).convert("RGB").resize((w_px, h_px), Image.LANCZOS)
    if code == "street_name":
        im = Image.new("RGB", (w_px, h_px), TEAL)
        d = ImageDraw.Draw(im)
        _fit_text(d, (0, 0, w_px, h_px), text or "", SG.WHITE, int(h_px * 0.42))
        return im
    raise KeyError(code)


def _norm_parts(parts):
    """[{face, plate?, text?}] -> [(code, text)] top first; an A-30 `plate` text becomes its own plate part."""
    out = []
    for p in parts:
        code = p["face"]
        if code not in FACE_DIM or code == "plate":
            raise KeyError(f"gate3_sign: unknown face {code!r}")
        out.append((code, p.get("text")))
        if p.get("plate"):
            out.append(("plate", str(p["plate"])))
    return out


def assembly_key(parts, post, lower):
    return "G3" + hashlib.sha1(repr((_norm_parts(parts), post, round(float(lower), 2))).encode()).hexdigest()[:8]


def atlas(parts, post):
    """(image, cells): faces stacked top to bottom, post / back swatches in a strip on the right.
    cells = [(code, w_m, h_m, shape, (x0, y0, x1, y1) px)], swatch pixel centres under "post" / "back"."""
    P = _norm_parts(parts)
    dims = [(c, t) + FACE_DIM[c] for c, t in P]
    wmax = max(d[3] for d in dims)
    W = int(round(wmax * PX_M)) + SWATCH_PX
    H = sum(int(round(d[4] * PX_M)) for d in dims)
    im = Image.new("RGB", (W, H), BACK)
    cells, y = [], 0
    for code, text, shape, w, h in dims:
        wp, hp = int(round(w * PX_M)), int(round(h * PX_M))
        im.paste(draw_face(code, wp, hp, text), (0, y))
        cells.append((code, w, h, shape, (0, y, wp, y + hp)))
        y += hp
    d = ImageDraw.Draw(im)
    x0 = W - SWATCH_PX
    d.rectangle([x0, 0, W - 1, H // 2 - 1], fill=TEAL if post == "teal" else GALV)
    d.rectangle([x0, H // 2, W - 1, H - 1], fill=BACK)
    sw = {"post": ((x0 + SWATCH_PX / 2) / W, 1 - (H / 4) / H), "back": ((x0 + SWATCH_PX / 2) / W, 1 - (3 * H / 4) / H)}
    return im, cells, sw


def _outline(shape, w, h):
    """Outline in the plate plane (x right of the sign's own left..., z up), centred on the cell, clockwise in (x, z)
    = facing +y (same rule as props.board)."""
    if shape == "tri_up":
        return [(-w / 2, -h / 2), (0.0, h / 2), (w / 2, -h / 2)]
    if shape == "tri_down":
        return [(-w / 2, h / 2), (w / 2, h / 2), (0.0, -h / 2)]
    if shape == "diamond":
        return [(-w / 2, 0.0), (0.0, h / 2), (w / 2, 0.0), (0.0, -h / 2)]
    return [(-w / 2, -h / 2), (-w / 2, h / 2), (w / 2, h / 2), (w / 2, -h / 2)]


def assembly_mesh(parts, post="galv", lower=2.0):
    """(lod0, lod1, collision) of one sign: Ø60 mm post, faces stacked from `lower` (lowest part's lower edge) with
    5 cm gaps, grey backs. Local frame as every prop: +y = the face normal, z up, origin at the ground.
    Returns also the atlas image and the overall (width, height) for the `boards` registry."""
    im, cells, sw = atlas(parts, post)
    W, H = im.size
    key = assembly_key(parts, post, lower)
    mat = f"sign_{key}"
    centres, z = [], float(lower)
    for cell in reversed(cells):
        centres.append((cell, z + cell[2] / 2))
        z += cell[2] + 0.05
    top = z
    r = S.SIGN_POST_D / 2
    out = []
    for seg, backs in ((8, True), (4, True)):
        m = PP.Mesh()
        pm = PP.Mesh()
        wide = max((c[1] for c in cells if c[0] in TWO_POSTS), default=0.0)
        for xp in ((-0.3 * wide, 0.3 * wide) if wide else (0.0,)):
            pm.tube("p", [xp, 0, -0.03], [xp, 0, top], r, None, seg)
        Vs, Ts, UVs = pm.prims["p"]
        off = 0
        for V, T in zip(Vs, Ts):                         # Mesh.add offsets T by the vertices added before
            m.add(mat, V, np.asarray(T) - off, np.tile(sw["post"], (len(V), 1)))
            off += len(V)
        yf = r + 0.012 + 0.025
        for (code, w, h, shape, (x0, y0, x1, y1)), zc in centres:
            pts = _outline(shape, w, h)
            V = [[x, yf, zc + zz] for x, zz in pts]
            # u mirrored like props.plate / props.board (seen from +y in Unity, local +x is on the viewer's left)
            UV = [((x0 + (0.5 - x / w) * (x1 - x0)) / W, 1 - (y0 + (0.5 - zz / h) * (y1 - y0)) / H) for x, zz in pts]
            n = len(pts)
            m.add(mat, V, [(0, k, k + 1) for k in range(1, n - 1)], UV)
            if backs:
                Vb = [[x, yf - 0.025, zc + zz] for x, zz in pts]
                m.add(mat, Vb, [(0, k + 1, k) for k in range(1, n - 1)], np.tile(sw["back"], (n, 1)))
        out.append(m)
    col = PP.Mesh()
    col.tube("collision_steel", [0, 0, 0], [0, 0, min(top, 2.6)], 0.05, None, 4)
    wmax = max(c[1] for c in cells)
    return out[0], out[1], col, im, (wmax + SWATCH_PX / PX_M, H / PX_M), key, top


# ------------------------------------------------------------------------------------------------------ placement
def _bearing_vec(deg):
    a = math.radians(float(deg))
    return np.array([math.sin(a), math.cos(a)])


def _locate_along(net, graph_nodes, origin, spec):
    """(point E/N, travel unit vector) for `along`, or None when the way / node is not in the network."""
    from .landmarks import _chains
    nd = graph_nodes.get(spec["before_node"])
    if nd is None:
        return None
    xy = np.array([nd["x"] - origin[0], nd["y"] - origin[1]])
    for d_, c, s_node in _chains(net, spec["osm_way"], xy):
        if d_ > 15:
            break
        dirn = int(c.dirn[c.idx(s_node)]) or 1
        s = s_node - dirn * float(spec["distance_m"])
        if not 0 < s < c.length:
            continue
        t, _ = c.line.frame(s)
        travel = t * dirn
        side = spec.get("side", "R")
        # chain-lateral sign of that side of TRAVEL (chain +lateral = left of the chain direction)
        sgn = (1.0 if side == "L" else -1.0) * (1.0 if dirn > 0 else -1.0)
        cs = "L" if sgn > 0 else "R"
        kind, h, w, depth, mat = side_params(c, cs, s)
        off = spec.get("offset_m")
        lat = float(c.hw_at(s)) + (S.KERB_TOP_W + S.SIGN_LATERAL if off is None else float(off))
        if off is None and kind == RURAL:                 # rural shoulder: behind it
            lat = float(c.hw_at(s)) + side_extent(kind, h, w, depth, mat) + 0.5
        return c.line.offset_point(s, sgn * lat), travel
    return None


UNDER_DECK_M = 2.5            # top surface this far above the terrain = a bridge deck over the point
SNAP_MAX_M = 8.0              # authored positions come from a 0.25 m orthophoto; generated islands differ by metres
SNAP_CLEAR_M = 0.6            # post axis behind the carriageway edge after a snap (plate edge stays off the kerb)


def off_carriageway(carriage, p):
    """p if it is off the carriageway, else the nearest point SNAP_CLEAR_M behind the carriageway edge when that is
    within SNAP_MAX_M (the generated island / verge differs from the orthophoto by a metre or two), else None."""
    from shapely.geometry import Point
    pt = Point(float(p[0]), float(p[1]))
    if not carriage.contains(pt):
        return np.asarray(p, float)
    b = carriage.boundary
    e = np.array(b.interpolate(b.project(pt)).coords[0])
    d = float(np.hypot(*(e - p)))
    if d > SNAP_MAX_M:
        return None
    u = (e - p) / d if d > 1e-6 else np.array([1.0, 0.0])
    q = e + u * SNAP_CLEAR_M
    return q if not carriage.contains(Point(float(q[0]), float(q[1]))) else None


def build(pl, net, graph, overrides, origin, boards, report, carriage=None, islands=()):
    """Place every `gate3_sign` override. `boards` gets the texture of each distinct assembly (exported as
    art-source/world/signs/<key>.png, material sign_<key>); the prototype sign_g3_<key> is registered in PROTOS.
    `islands` = built roads.gores.Island objects: authored kerbed islands lie ON the carriageway footprint, a sign
    whose authored position is on one stands there, on the island top (ADR 0128)."""
    from shapely.geometry import Point
    rep = {"signs": [], "stale": []}
    nodes = {n["id"]: n for n in graph["nodes"]}
    for o in overrides:
        if o.get("kind") != KIND:
            continue
        try:
            parts, post, lower = o["parts"], o.get("post", "galv"), float(o.get("lower_edge_m", S.SIGN_H_MIN))
            lod0, lod1, col, im, (wm, hm), key, top = assembly_mesh(parts, post, lower)
        except KeyError as e:
            rep["stale"].append(f"{o['id']}: {e}")
            continue
        if "along" in o:
            hit = _locate_along(net, nodes, origin, o["along"])
            if hit is None:
                rep["stale"].append(f"{o['id']}: along not found")
                continue
            p, travel = hit
            if "travel_bearing_deg" in o:
                travel = _bearing_vec(o["travel_bearing_deg"])
        else:
            p = np.asarray(o["at_en"], float)
            travel = _bearing_vec(o["travel_bearing_deg"])
        moved = 0.0
        isl = next((i for i in islands if i.poly.contains(Point(float(p[0]), float(p[1])))), None)
        if isl is not None:
            z_isl = isl.top_z(p)
        elif carriage is not None:
            q = off_carriageway(carriage, p)
            if q is None:
                rep["stale"].append(f"{o['id']}: on a carriageway at {[round(float(v), 1) for v in p]}")
                continue
            moved, p = float(np.hypot(*(q - p))), q
        proto = f"sign_g3_{key}"
        PROTOS[proto] = (lod0, lod1, col)
        boards[key] = (round(wm, 3), round(hm, 3), im)
        # under a viaduct the top surface at (E, N) is the deck: stand on the ground unless the entry says on_deck
        zs = float(pl.zsurf(np.array([p[0]]), np.array([p[1]]))[0])
        zg = float(pl.zground(np.array([p[0]]), np.array([p[1]]))[0]) if pl.zground is not None else zs
        under = (zs - zg) > UNDER_DECK_M and not o.get("on_deck")
        z = pl.add(proto, p, PP_yaw(-travel), z=z_isl if isl is not None else (zg if under else zs), src=f"override:{o['id']}")
        rep["signs"].append({"id": o["id"], "proto": proto, "at": [round(float(v), 1) for v in p], "z": round(float(z), 2),
                             "faces": [c for c, _ in _norm_parts(parts)], "top_m": round(top, 2),
                             "snapped_m": round(moved, 2), "under_deck": bool(under),
                             **({"island": isl.id} if isl is not None else {}),
                             "travel_bearing_deg": round(math.degrees(math.atan2(travel[0], travel[1])) % 360, 1),
                             "mapillary": o.get("mapillary", [])})
    _signals(pl, overrides, rep, carriage, islands)
    report["gate3_landmarks"] = rep
    return rep


def _signals(pl, overrides, rep, carriage, islands):
    """ADR 0161: `gate3_signal` overrides, placed exactly as furniture.signals places a rule signal."""
    from shapely.geometry import Point
    for o in overrides:
        if o.get("kind") != KIND_SIGNAL:
            continue
        try:
            p = np.asarray(o["at_en"], float)
            face = _bearing_vec(o["travel_bearing_deg"])
        except KeyError as e:
            rep["stale"].append(f"{o['id']}: {e}")
            continue
        moved = 0.0
        isl = next((i for i in islands if i.poly.contains(Point(float(p[0]), float(p[1])))), None)
        if isl is None and carriage is not None:
            q = off_carriageway(carriage, p)
            if q is None:
                rep["stale"].append(f"{o['id']}: on a carriageway at {[round(float(v), 1) for v in p]}")
                continue
            moved, p = float(np.hypot(*(q - p))), q
        lit = str(o.get("lit", "red"))
        src = f"override:{o['id']}"
        zkw = {"z": isl.top_z(p)} if isl is not None else {}
        if isl is not None:      # furniture.clear_carriageway works on the 2D footprint: the island is inside it
            if not hasattr(pl, "on_authored_island"):
                pl.on_authored_island = set()
            pl.on_authored_island.add((round(round(float(p[0]), 3), 2), round(round(float(p[1]), 3), 2)))
        mast = "arm_bearing_deg" in o
        if mast:
            arm = _bearing_vec(o["arm_bearing_deg"])
            z = pl.add("signal_mast", p, PP_yaw(arm), src=src, **zkw)
            pl.add(f"signal_head_{lit}", p + arm * 5.0, PP_yaw(face), z=z + S.SIGNAL_MAST_H - 1.25, src=src)
        else:
            z = pl.add("signal_pole", p, PP_yaw(face), src=src, **zkw)
        pl.add(f"signal_head_{lit}", p + face * 0.15, PP_yaw(face), z=z + 2.9, src=src)
        rep.setdefault("signals", []).append({"id": o["id"], "at": [round(float(v), 1) for v in p], "mast": mast,
                                              "snapped_m": round(moved, 2), "lit": lit})


def PP_yaw(f):
    """Yaw (rad) that turns local +y onto direction f (E, N); same convention as furniture.yaw_of."""
    return math.atan2(f[1], f[0]) - math.pi / 2
