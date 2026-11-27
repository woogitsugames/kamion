"""ADR 0224: road cross-section across tile seams (DK65 corridor Białystok -> Knyszyn and its side tiles).

For every pair of tiles that share an edge (bbox from region.yaml) the tool finds the roads that cross the shared edge
and compares, at the seam, the cross-section the generator builds on both sides:

  carriageway width (2 x half-width at the chain end, after overrides + tapers: `pipeline.build_network`), lanes and
  lane width, edge lines (spacing axis to axis, which sides, solid/broken), centre line, side profile (rural paved
  shoulder + gravel + ditch / kerb / sidewalk: `network.assign_sides`, SECOND pass with the junction trims - the one the
  generator meshes, ADR 0304; `--pass1` = the first pass as before), lighting rule, axis position
  (centre of the carriageway on the seam), terrain height at the axis (graph `z_terrain`, NMT) and the carriageway width
  of the last build (`generated/roads_qa.json`, may be stale against the overrides).

Every value carries its source: `derived:network` (generator code on graph + overrides of this checkout, no build),
`generated:roads_qa` (last build_world, in git), `graph:z_terrain` (NMT at the node), `rule:ADR0220` (edge_line_spacing,
modelled after markings.edge_lines of PR #98 when an override carries the key). Road surface height (Y of the built
axis) is NOT in any generated/*.json - the glb chunks live in Data/raw - so the height row compares NMT at the axis.

ADR 0275: the tool applies the seam transitions of roads.seam_taper exactly as pipeline.build_network / build do (each
tile blends towards the neighbour's nominal section), so the width rows compare what is BUILT on the seam; a road whose
nominal sections differ gets a row `przejście szerokości (ADR 0275)` with status PRZEJŚCIE (data differ, the generator
bridges them) and the nominal values. The asphalt edge (half-width + paved shoulder of a kerbless edge) has its own rows
with the tighter tolerance EDGE_TOL_M. Lane width is the LOCAL one (`EdgeSection.lane_w_at`, ADR 0233): a section
with `lanes_follow_width` is compared by the lanes it paints at the seam, not by the lane width of its widest station.

Tolerance: +-0.1 m on lengths (TOL_M), categories must be equal. Reference ranges (research K1, ADR 0212) are checked on
the route road of the corridor seams (`REFERENCE`), shifted by two lane allowances of
GAMEPLAY_LANE_WIDEN_M (D94); the measured range and its tolerance stay unchanged.

  uv run --project tools/worldgen python -m tools.worldgen.qa.seams [--tiles a,b,...] [--overrides-ref <git ref>]
        [--json out.json] [--md out.md] [--compare-ref origin/dk65-k1-0220]

`--overrides-ref` reads overrides.yaml from a git ref for the tiles that ref changes against `--base` (default
origin/main, merge base; the rest from the checkout) = "this checkout + that PR"; `--compare-ref` runs twice (checkout
and checkout + ref) and adds the ref's result to every row. The generator code is always the checkout's, except the
ADR 0220 key `edge_line_spacing` (PR #98), modelled here when an override carries it.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[3]
REG = ROOT / "Data" / "Regions"
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))

from roads import markings as MK  # noqa: E402
from roads import network as Nw  # noqa: E402
from roads import seam_taper as ST  # noqa: E402
from roads import standards as S  # noqa: E402

TOL_M = 0.10                  # task D3: +-0.1 m
EDGE_TOL_M = 0.02             # ADR 0275: step of the asphalt edge across a seam (both tiles build the same edge)
SEAM_EPS_M = ST.SEAM_EPS_M    # a chain end lies on the seam line within this distance
MATCH_M = 5.0                 # chain ends of the same road on both sides of a seam: within this distance
DASH_SNAP_M = 1.5             # markings.EDGE_DASHED_SNAP_M (PR #98)
EDGE_LINE_MIN_INSET = 0.12    # markings.EDGE_LINE_MIN_INSET (PR #98, WORKING_VALUE)

# Chain of task D3 (cloud D, s21). bialystok-industrial-c / -dojlidy do not touch dk65-01 (bbox, region.yaml): the
# city tile on the east edge of dk65-01 (x = 770827) is bialystok-knyszynska.
TILES = ["bialystok-industrial-c", "bialystok-dojlidy", "bialystok-kleeberga", "bialystok-maczka", "bialystok-knyszynska",
         "dk65-01", "dk65-02", "dk65-03", "dk65-04", "dk65-05", "dk65-06", "dk65-07", "dk65-08", "dk65-09", "dk65-10",
         "dk65-11", "knyszyn-s", "knyszyn", "knyszyn-w", "dk65-monki-01", "dw671-tykocin-01"]
DK65_SEAMS = [("bialystok-knyszynska", "dk65-01"), ("dk65-01", "dk65-02"), ("dk65-02", "dk65-03"),
              ("dk65-03", "dk65-04"), ("dk65-04", "dk65-05"), ("dk65-05", "dk65-06"), ("dk65-06", "dk65-07"),
              ("dk65-07", "dk65-08"), ("dk65-08", "dk65-09"), ("dk65-09", "dk65-10"), ("dk65-10", "dk65-11"),
              ("dk65-11", "knyszyn-s"), ("knyszyn-s", "knyszyn"), ("knyszyn", "knyszyn-w"),
              ("knyszyn-w", "dk65-monki-01")]
_K1 = "research K1 (research/dk65-knyszyn-refs/README.md, tabela per kafel)"
# Expected edge-line spacing (axis to axis) of the route road at a corridor seam: (lo, hi, source).
REFERENCE = {
    ("bialystok-knyszynska", "dk65-01"): (6.0, 6.4, _K1 + ": km 8,8 = 6,3 m"),
    ("dk65-01", "dk65-02"): (6.0, 6.4, _K1 + ": km 9,0 = 6,2 m, km 10,0 = 6,4 m"),
    ("dk65-02", "dk65-03"): (6.0, 6.4, _K1 + ": km 11,5 = 6,1 m, km 12,0 = 6,1 m"),
    ("dk65-03", "dk65-04"): (6.0, 6.4, _K1 + ": km 12,0 = 6,1 m, km 12,5 = 6,2 m"),
    ("dk65-04", "dk65-05"): (6.0, 6.4, _K1 + ": km 14,0 = 6,2 m, km 14,5 = 6,2 m"),
    ("dk65-05", "dk65-06"): (6.0, 6.4, _K1 + ": km 16,0 = 6,2 m, km 17,0 = 6,1 m"),
    ("dk65-06", "dk65-07"): (6.0, 6.4, _K1 + ": km 18,0 = 6,0 m, km 19,0 = 6,4 m"),
    ("dk65-07", "dk65-08"): (6.0, 6.4, _K1 + ": km 19,0 = 6,4 m, km 20,0 = 6,0 m"),
    ("dk65-08", "dk65-09"): (6.0, 6.4, _K1 + ": km 21,0 = 6,25 m, km 21,65 = 6,1 m"),
    ("dk65-09", "dk65-10"): (6.0, 6.4, _K1 + ": km 21,65 = 6,1 m, km 22,0 = 6,1 m"),
    ("dk65-10", "dk65-11"): (6.0, 6.4, _K1 + ": km 24,0 = 6,1 m, km 24,6 = 6,0 m (mediana korytarza 6,2)"),
    ("dk65-11", "knyszyn-s"): (6.0, 6.4, _K1 + ": km 24,6 = 6,0 m, km 25,0 = 6,1 m"),
    ("knyszyn-s", "knyszyn"): (6.6, 7.0, _K1 + ": km 26,0 / 27,0 = 6,8 m (Obozowa); ADR 0212: 6,8 m"),
    ("knyszyn", "knyszyn-w"): (6.6, 7.0, "ADR 0212 p.1: DK65 na Mońki 6,8 m linia-linia (ortofoto 0,1 m 2025)"),
    ("knyszyn-w", "dk65-monki-01"): (6.6, 7.0, "ADR 0212 p.1: 6,8 m linia-linia (dk65-monki-01, 7 przekrojów)"),
}
SIDE_KIND = {Nw.URBAN: "krawężnik", Nw.ISLAND: "wyspa (rondo)",
             Nw.RURAL: "wiejski: utw. %s + żwir %s + rów" % (f"{S.PAVED_SHOULDER:.2f}".replace(".", ","),
                                                             f"{S.SHOULDER_W['GP']:.2f}".replace(".", ",")),
             Nw.MEDIAN_RURAL: "pas dzielący wiejski"}


# ----------------------------------------------------------------------------------------------- tile data
@dataclass
class Tile:
    id: str
    region: dict
    graph: dict
    overrides: list
    roads_qa: dict | None = None
    ctx: dict | None = None
    streetscape: dict | None = None
    route_edges: set = field(default_factory=set)
    overrides_src: str = "checkout"

    @property
    def bbox(self):
        b = self.region["bbox"]
        return (float(b["xmin"]), float(b["ymin"]), float(b["xmax"]), float(b["ymax"]))

    @property
    def origin(self):
        return (float(self.region["origin"]["x"]), float(self.region["origin"]["y"]))


def _git_show(ref: str, rel: str) -> str | None:
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"{ref}:{rel}"], capture_output=True, text=True,
                       encoding="utf-8")
    return r.stdout if r.returncode == 0 else None


def changed_tiles(ref: str, base: str = "origin/main") -> set:
    """Tiles whose overrides.yaml the ref changes against its merge base with `base` (a PR's own changes)."""
    r = subprocess.run(["git", "-C", str(ROOT), "diff", "--name-only", f"{base}...{ref}", "--", "Data/Regions"],
                       capture_output=True, text=True, encoding="utf-8")
    return {Path(f).parts[2] for f in r.stdout.split() if f.endswith("/overrides.yaml")}


def load_tile(tid: str, overrides_ref: str | None = None) -> Tile:
    d = REG / tid
    rj = lambda p: json.loads(p.read_text(encoding="utf-8")) if p.exists() else None  # noqa: E731
    region = yaml.safe_load((d / "region.yaml").read_text(encoding="utf-8"))
    graph = rj(d / "roads.graph.json")
    src = "checkout"
    text = None
    if overrides_ref:
        text = _git_show(overrides_ref, f"Data/Regions/{tid}/overrides.yaml")
        src = overrides_ref if text is not None else "checkout (brak w ref)"
    if text is None and (d / "overrides.yaml").exists():
        text = (d / "overrides.yaml").read_text(encoding="utf-8")
    ov = ((yaml.safe_load(text) or {}).get("overrides") or []) if text else []
    route = rj(d / "route_start.json")
    return Tile(id=tid, region=region, graph=graph, overrides=ov, roads_qa=rj(d / "generated" / "roads_qa.json"),
                ctx=rj(d / "generated" / "osm_context.json"), streetscape=rj(d / "generated" / "streetscape_sources.json"),
                route_edges=set(route["edge"]) if route else set(), overrides_src=src)


# ----------------------------------------------------------------------------------------------- geometry
shared_edge = ST.shared_edge      # one definition for the generator and the QA tool (ADR 0275)


def adjacent_pairs(tiles: list[Tile]):
    out = []
    for i, a in enumerate(tiles):
        for b in tiles[i + 1:]:
            se = shared_edge(a.bbox, b.bbox)
            if se:
                out.append((a, b, se))
    return out


_on_seam = ST.on_seam


# ----------------------------------------------------------------------------------------------- network
def build_plain(t: Tile):
    """The network a tile builds on its own (graph + overrides + fork passes), no seam transitions, no sides."""
    return ST.plain_network(t.graph, t.origin, t.overrides)


def add_sides(t: Tile, net, trims: bool = False):
    """network.assign_sides, first pass (no junction trims): same inputs as roads.pipeline.build. trims=True (ADR 0304):
    then the junctions are built (`junctions.build_junctions` on the osm_context points, as pipeline.build) and the
    second pass runs - the side profile the generator meshes."""
    foot, walk, yards = ST.side_inputs(t.ctx, t.streetscape, t.overrides, t.origin)   # = roads.pipeline.build
    net.region_id, net.authored = t.id, t.overrides       # implied sidewalks (ADR 0237 D38), as pipeline.build
    Nw.assign_sides(net, foot, built_up=True, walkways=walk, yards=yards)
    net.sides_pass = 2 if trims else 1
    if trims:
        from roads import junctions as J
        ST.apply_shoulders(net, getattr(net, "seam_tapers", []))
        o2 = np.array(t.origin)
        pts = [dict(p, e=p["x"] - o2[0], n=p["y"] - o2[1]) for p in (t.ctx or {}).get("points", [])]
        J.build_junctions(net, pts)
        Nw.assign_sides(net, foot, built_up=True, walkways=walk, yards=yards, trims=True)
    return net


def build_nets(ts: list, pairs: list, taper: bool = True, trims: bool = False) -> dict:
    """{tile id: network} as the generator builds them: every tile on its own, then the seam transitions of ADR 0275
    planned from the nominal chain ends of both tiles of a pair (roads.seam_taper.plan), widths, sides, shoulders.
    Each network carries `seam_tapers` (list of ST.Taper) and `nominal_ends` ({(chain, end): ST.End})."""
    nets = {t.id: build_plain(t) for t in ts}
    ends = {tid: ST.ends(n) for tid, n in nets.items()}
    others = {t.id: {} for t in ts}
    for a, b, se in pairs:
        ea, eb = ([e for e in ends[x.id] if e.on_seam(se)] for x in (a, b))
        others[a.id][b.id] = others[a.id].get(b.id, []) + eb
        others[b.id][a.id] = others[b.id].get(a.id, []) + ea
    # seams-side-s24: nominal side profiles of the seam ends (plain network + junctions + second assign_sides pass,
    # roads.seam_taper.nominal_sides), the same for both tiles of a pair, agreed per side and imposed on each end
    sides = {}
    if taper and trims:
        for t in ts:
            sides[t.id] = ST.nominal_sides(t.graph, t.origin, t.overrides, t.ctx, t.streetscape, t.id)
    side_others = {t.id: {} for t in ts}
    for a, b, se in pairs:
        if a.id in sides and b.id in sides:
            for x, y in ((a, b), (b, a)):
                ye, ys = sides[y.id]
                prev = side_others[x.id].get(y.id, ([], {}))
                side_others[x.id][y.id] = (prev[0] + [e for e in ye if e.on_seam(se)], {**prev[1], **ys})
    for t in ts:
        net = nets[t.id]
        net.nominal_ends = {(e.chain, e.end): e for e in ends[t.id]}
        net.seam_tapers = ST.plan(ends[t.id], others[t.id]) if taper else []
        ST.apply_widths(net, net.seam_tapers)
        add_sides(t, net, trims=trims)
        net.seam_sides = ST.plan_sides(sides[t.id][0], sides[t.id][1], side_others[t.id]) if t.id in sides else []
        net.seam_sides_report = ST.apply_sides(net, net.seam_sides)
        ST.apply_shoulders(net, net.seam_tapers)
    return nets


def build_net(t: Tile, sides: bool = True):
    """One tile on its own (no neighbours, so no seam transitions)."""
    net = build_plain(t)
    net.seam_tapers, net.nominal_ends = [], {(e.chain, e.end): e for e in ST.ends(net)}
    return add_sides(t, net) if sides else net


def _ov_for(t: Tile, osm_way, key):
    val, oid = None, None
    for ov in t.overrides:
        if ov.get("kind"):
            continue
        tg, st = ov.get("target", {}) or {}, ov.get("set", {}) or {}
        ways = tg.get("osm_way")
        ways = ways if isinstance(ways, list) else ([ways] if ways is not None else [])
        if osm_way in {int(w) for w in ways} and key in st:
            val, oid = st[key], ov["id"]
    return val, oid


def _dashed_sides(t: Tile, p_local, hw):
    """{'left'|'right' in line_en direction: (override id, tangent)} of edge_line_dashed spans passing the point."""
    out = []
    for ov in t.overrides:
        if ov.get("kind") != "edge_line_dashed":
            continue
        pts = np.asarray(ov.get("line_en") or [], float).reshape(-1, 2)
        if len(pts) < 2:
            continue
        best = None
        for a, b in zip(pts, pts[1:]):
            ab = b - a
            L2 = float(ab @ ab) or 1e-12
            u = float(np.clip((p_local - a) @ ab / L2, 0, 1))
            dist = float(np.hypot(*(a + u * ab - p_local)))
            if best is None or dist < best[0]:
                best = (dist, ab / np.sqrt(L2))
        if best and best[0] <= hw + DASH_SNAP_M:
            out.append((ov.get("side"), best[1], ov["id"]))
    return out


@dataclass
class Crossing:
    tile: str
    chain: str
    osm_way: int
    highway: str
    xy: tuple                 # EPSG:2180 point of the carriageway centre on the seam
    on_route: bool
    params: dict              # name -> (value, source)
    geo: dict = field(default_factory=dict)   # chain_len_m, cos_normal (|cos| of the axis vs the seam normal)


def crossings(t: Tile, se, net=None) -> list[Crossing]:
    """Every generated chain end at a seam cut (boundary node before lateral placement), with its cross-section in the a -> b travel frame
    (L / P = left / right looking from tile a into tile b)."""
    net = net or build_net(t)
    o = np.array(t.origin)
    nab = np.array(se["normal_ab"])
    out = []
    qa = {c["id"]: c for c in (t.roads_qa or {}).get("chains", [])}
    for c in net.chains:
        for end in (0, -1):
            pg = c.line.p[end] + o
            # D94 can shift an oblique carriageway end off the tile plane by centimetres.
            # Membership belongs to the boundary node; keep the generated position below
            # so real placement / cross-section differences still fail their own rows.
            node = net.nodes.get(c.node_a if end == 0 else c.node_b, {})
            boundary_xy = np.asarray(node.get("xy", c.line.p[end])) + o
            if not (_on_seam(pg, se) or (node.get("boundary") and _on_seam(boundary_xy, se))):
                continue
            s = float(c.line.s[end])
            i_sec = int(c.sec_idx[end])
            sec = net.sec_list[i_sec]
            hw = float(c.hw[end])
            tan = c.line.t[end]
            # travel frame a -> b: chain direction agrees with nab -> chain-left = L
            flip = float(np.dot(tan, nab)) < 0
            P = {}
            src_n = "derived:network"
            P["szerokość jezdni [m]"] = (round(2 * hw, 3), src_n)
            # ADR 0233: the lanes painted at the seam (local share of the width on `lanes_follow_width` sections)
            lw_loc = float(np.asarray(Nw.lane_w_of(sec, hw)))
            src_lw = src_n if abs(lw_loc - float(sec.lane_w)) < 5e-3 else (
                f"derived:network (lanes_follow_width: lokalnie, sekcja {sec.lane_w:.2f})")
            P["pasy × szer. pasa [m]"] = (f"{sec.lanes} × {lw_loc:.2f}", src_lw)
            P["opaska (edge_strip) [m]"] = (round(float(sec.edge_strip), 3), src_n)
            # edge lines (markings.edge_lines of this checkout, + ADR 0220 edge_line_spacing when an override has it)
            lines = MK.edge_lines(sec, hw, int(c.dirn[end]) or 1) if sec.highway in MK.MARKED else []
            lats = sorted(float(np.asarray(lat)) for lat, _k in lines)
            sp, sp_id = _ov_for(t, int(sec.edge_id.split(":")[0].lstrip("w")), "edge_line_spacing")
            src_l = src_n
            if sp is not None and lines and S.road_class(sec.highway) not in ("A", "S", "GP") and \
                    not getattr(sec, "edge_line_spacing", None):
                off = min(0.5 * float(sp), hw - EDGE_LINE_MIN_INSET)
                lats = sorted(np.sign(lat) * off for lat in lats)
                src_l = f"rule:ADR0220 ({sp_id})"
            elif getattr(sec, "edge_line_spacing", None):
                src_l = f"derived:network ({sec.provenance.get('edge_line_spacing', 'edge_line_spacing')})"
            sides_present = []
            for lat in lats:
                left_of_chain = lat > 0
                sides_present.append("L" if left_of_chain != flip else "P")
            spacing = round(lats[-1] - lats[0], 3) if len(lats) == 2 else None
            P["rozstaw linii krawędziowych [m]"] = (spacing, src_l)
            P["szer. linii krawędziowej [m]"] = (MK.edge_line_width(sec) if lines else None, src_n)
            dashed = {"L": "ciągła", "P": "ciągła"}
            for side, dvec, oid in _dashed_sides(t, c.line.p[end], hw):
                # side of the span in its own direction -> a->b frame
                same = float(np.dot(dvec, nab)) > 0
                k = ("L" if side == "left" else "P") if same else ("P" if side == "left" else "L")
                dashed[k] = f"przerywana ({oid})"
            P["linia krawędziowa L"] = (dashed["L"] if "L" in sides_present else "brak", src_n)
            P["linia krawędziowa P"] = (dashed["P"] if "P" in sides_present else "brak", src_n)
            # centre line (markings._build_markings rule)
            if sec.oneway or sec.highway not in MK.MARKED or sec.width < S.SEGREGATION_MIN_CARRIAGEWAY:
                cl = "brak"
            elif sec.lanes >= 4:
                cl = "P-4 podwójna ciągła"
            else:
                cl = "P-1a przerywana (4/8)" if (sec.maxspeed or 50) > 70 else "P-1b przerywana (2/4)"
            P["linia środkowa"] = (cl, src_n)
            # side profile
            for side_c in ("L", "R"):
                sd = (c.side or {}).get(side_c)
                k = ("L" if side_c == "L" else "P") if not flip else ("P" if side_c == "L" else "L")
                if not sd:
                    P[f"pobocze {k}"] = (None, "brak (assign_sides)")
                    continue
                kind = SIDE_KIND.get(int(sd["kind"][end]), str(int(sd["kind"][end])))
                sh = ST.shoulder_at(c, side_c, end)            # ADR 0272 widths of the station (after ADR 0275)
                paved = S.PAVED_SHOULDER if int(sd["kind"][end]) == Nw.RURAL else 0.0
                if sh is not None:
                    paved = sh[0]
                    kind = "wiejski: utw. %s + grunt %s + rów" % (f"{sh[0]:.2f}".replace(".", ","),
                                                                  f"{sh[1]:.2f}".replace(".", ","))
                P[f"krawędź asfaltu {k} [m od osi]"] = (round(hw + paved, 3), "derived:network (hw + pobocze utwardzone)")
                if int(sd["kind"][end]) == Nw.URBAN:
                    w = float(sd["raw"]["w"][end])
                    kind += f" + chodnik {w:.2f}" if bool(sd["walk"][end]) and w > 0 else (
                        " (płasko)" if float(sd["raw"]["h"][end]) < 0.05 else "")
                P[f"pobocze {k}"] = (kind, "derived:network (assign_sides, %d. przebieg)" % getattr(net, "sides_pass", 1))
            P["oświetlenie"] = ("brak (override)" if sec.provenance.get("no_lamps") else "reguła klasy", src_n)
            P["oś jezdni E [m]"] = (round(float(pg[0]), 3), src_n)
            P["oś jezdni N [m]"] = (round(float(pg[1]), 3), src_n)
            node = net.nodes.get(c.node_a if end == 0 else c.node_b, {})
            z = node.get("z_terrain")
            nmt = str(t.graph.get("sources", {}).get("z_terrain"))
            P["wys. terenu w osi Z [m]"] = (z, f"graph:z_terrain (NMT {nmt})" if z is not None else
                                             f"brak (z_terrain = null na krawędzi S/E kafla; NMT {nmt})")
            q = qa.get(c.id)
            ws = sorted({float(w) for w in (q or {}).get("width_m") or []})
            hit = [w for w in ws if abs(w - float(sec.width)) <= 0.011]
            if sec.width_profile and abs(2 * hw - float(sec.width)) > 0.011:
                # roads_qa carries the section width = the widest station of the profile, not the width at the seam
                gw, gsrc = None, (f"generated:roads_qa: sekcja z profilem szerokości (roads_qa niesie maksimum "
                                  f"{float(sec.width):.2f} m, na szwie {2 * hw:.2f} m) — nieporównywalne")
            elif hit:
                gw, gsrc = hit[0], "generated:roads_qa"
            elif len(ws) == 1:
                gw, gsrc = ws[0], "generated:roads_qa (≠ szerokość sekcji teraz: build nieaktualny?)"
            else:
                gw, gsrc = None, (f"generated:roads_qa: łańcuch ma szerokości {ws}, żadna ≠ sekcji" if q else
                                  "brak łańcucha w roads_qa")
            P["szer. jezdni ostatni build [m]"] = (gw, gsrc)
            geo = {"chain_len_m": round(float(c.line.s[-1]), 2), "cos_normal": round(abs(float(np.dot(tan, nab))), 3)}
            tp = next((x for x in getattr(net, "seam_tapers", []) if x.chain == c.id and x.end == end), None)
            if tp is not None:
                geo["taper"] = tp.report()
            out.append(Crossing(tile=t.id, chain=c.id, geo=geo, osm_way=int(sec.edge_id.split(":")[0].lstrip("w")),
                                highway=sec.highway, xy=(float(pg[0]), float(pg[1])),
                                on_route=any(e[0] in t.route_edges for e in c.edges),
                                params=P))
    return out


# ----------------------------------------------------------------------------------------------- comparison
EDGE_ROWS = {"krawędź asfaltu L [m od osi]", "krawędź asfaltu P [m od osi]"}
NUMERIC = EDGE_ROWS | {"szerokość jezdni [m]", "opaska (edge_strip) [m]", "rozstaw linii krawędziowych [m]",
           "szer. linii krawędziowej [m]", "wys. terenu w osi Z [m]", "szer. jezdni ostatni build [m]"}
POSITION = ("oś jezdni E [m]", "oś jezdni N [m]")


def match(ca: list[Crossing], cb: list[Crossing]):
    """Match same-way ends first across the entire seam, then use proximity for remaining ends."""
    ca = sorted(ca, key=lambda c: (c.osm_way, c.xy, c.chain))
    cb = sorted(cb, key=lambda c: (c.osm_way, c.xy, c.chain))
    matched, used = {}, set()
    # A nearby branch without its own mate must leave the continuation of another way available.
    for same_way_only in (True, False):
        for i, a in enumerate(ca):
            if i in matched:
                continue
            best = None
            for j, b in enumerate(cb):
                if j in used or (same_way_only and a.osm_way != b.osm_way):
                    continue
                d = float(np.hypot(a.xy[0] - b.xy[0], a.xy[1] - b.xy[1]))
                if d <= MATCH_M and (best is None or (d, j) < best):
                    best = (d, j)
            if best is not None:
                matched[i] = best[1]
                used.add(best[1])
    pairs = [(a, cb[matched[i]] if i in matched else None) for i, a in enumerate(ca)]
    pairs += [(None, b) for j, b in enumerate(cb) if j not in used]
    return pairs


STUB_M = 15.0      # a chain shorter than this at the seam (junction stub) does not carry a comparable cross-section
OBLIQUE_COS = 0.5  # |cos(axis, seam normal)| below this: the road runs along the seam (> 60 deg off the normal)


def _weak(c: Crossing | None):
    if c is None:
        return None
    if c.geo.get("chain_len_m", 1e9) < STUB_M:
        return f"{c.tile}: łańcuch {c.geo['chain_len_m']:.1f} m (< {STUB_M:.0f} m, kikut przy węźle)"
    if c.geo.get("cos_normal", 1.0) < OBLIQUE_COS:
        return f"{c.tile}: oś biegnie wzdłuż szwu (|cos| = {c.geo['cos_normal']:.2f})"
    return None


def compare_pair(a: Crossing | None, b: Crossing | None, tol: float = TOL_M, dropped: dict | None = None):
    """Rows for one road crossing the seam. FAIL on a junction stub or a road running along the seam becomes UWAGA
    (listed, but the cross-section there is not a seam of one carriageway)."""
    rows = []
    weak = "; ".join(w for w in (_weak(a), _weak(b)) if w)
    if a is None or b is None:
        x = a or b
        other = "prawej" if a else "lewej"
        note = "droga urywa się na szwie (brak końca łańcucha po %s stronie w ±%.0f m)" % (other, MATCH_M)
        if dropped and x.osm_way in dropped:
            note += f"; way wycięty z grafu w {dropped[x.osm_way]} (graph_filter.authored.json)"
        rows.append({"param": "droga po drugiej stronie", "left": x.chain if a else None, "right": x.chain if b else None,
                     "delta": None, "status": "UWAGA" if weak else "FAIL", "source": "derived:network",
                     "note": note + (f"; {weak}" if weak else "")})
        return rows
    rows = _compare_rows(a, b, tol)
    if weak:
        for r in rows:
            if r["status"] == "FAIL":
                r["status"] = "UWAGA"
                r["note"] = weak
    return rows


def _compare_rows(a: Crossing, b: Crossing, tol: float):
    rows = []
    for k in a.params:
        (va, sa), (vb, sb) = a.params[k], b.params.get(k, (None, "brak"))
        src = sa if sa == sb else f"{sa} | {sb}"
        if k in POSITION:
            continue
        if k == "wys. terenu w osi Z [m]":
            if va is None or vb is None:
                st, d = "N/D", None
                ya, yb = (_nmt_year(sa), _nmt_year(sb))
                note = ("Y drogi nie ma w generated/*.json (chunki glb w Data/raw); z_terrain tylko po jednej stronie. "
                        + (f"Oba kafle: NMT {ya} - ta sama siatka, próbka na szwie wspólna (ADR 0214 test_seam_terrain, "
                           "wymaga Data/raw)" if ya and ya == yb else
                           f"Różne roczniki NMT ({ya or '?'} / {yb or '?'}): możliwy skok terenu ≤ 0,5 m (ADR 0214)"))
                rows.append({"param": k, "left": va, "right": vb, "delta": None, "status": st, "source": f"{sa} | {sb}",
                             "note": note})
                continue
            else:
                d = round(vb - va, 3)
                st = "OK" if abs(d) <= tol else "FAIL"
        elif k == "szer. jezdni ostatni build [m]":
            if va is None or vb is None:
                st, d = "N/D", None
            else:
                d = round(vb - va, 3)
                st = "OK" if abs(d) <= tol else "FAIL"
                if st == "FAIL" and (a.geo.get("taper") or b.geo.get("taper")):
                    # roads_qa lists the nominal section widths; the transition of ADR 0275 bridges them
                    rows.append({"param": k, "left": va, "right": vb, "delta": d, "status": "PRZEJŚCIE", "source": src,
                                 "note": "szerokości sekcji (nominalne) — różnicę niesie przejście ADR 0275"})
                    continue
        elif k in NUMERIC:
            if va is None and vb is None:
                st, d = "OK", None
            elif va is None or vb is None:
                st, d = "FAIL", None
            else:
                d = round(vb - va, 3)
                st = "OK" if abs(d) <= (min(tol, EDGE_TOL_M) if k in EDGE_ROWS else tol) + 1e-9 else "FAIL"
        else:
            d = None
            st = "OK" if _cat(va) == _cat(vb) else "FAIL"
        rows.append({"param": k, "left": va, "right": vb, "delta": d, "status": st, "source": src})
    ta, tb = a.geo.get("taper"), b.geo.get("taper")
    if ta or tb:
        def _d(x):
            if not x:
                return None
            s = f"jezdnia {x['width_own']:.2f} → {x['width_seam']:.2f} m na {x['in_tile_m']:.1f} m"
            if x.get("axis_offset_m"):
                s += f"; oś do środka między osiami nominalnymi (odsunięcie {x['axis_offset_m']:.3f} m, np. D94)"   # seams-w10
            for side, v in (x.get("shoulder_cm") or {}).items():
                s += (f"; pobocze {side} utw./grunt {v['own'][0]}/{v['own'][1]} → {v['seam'][0]}/{v['seam'][1]} cm")
            return s + (f" [bez przejścia jezdni: {x['skipped']}]" if x.get("skipped") else "")
        x = ta or tb
        rows.append({"param": "przejście szerokości (ADR 0275)", "left": _d(ta), "right": _d(tb), "delta": x["step_m"],
                     "status": "PRZEJŚCIE", "source": "derived:seam_taper",
                     "note": f"przekroje nominalne różnią się (największy skok krawędzi {x['step_m']:.3f} m); krzywa S "
                             f"{x['length_m']:.1f} m, połowa w każdym kaflu"})
    dpos = round(float(np.hypot(a.xy[0] - b.xy[0], a.xy[1] - b.xy[1])), 3)
    rows.append({"param": "położenie osi na szwie [m]", "left": [round(v, 2) for v in a.xy],
                 "right": [round(v, 2) for v in b.xy], "delta": dpos, "status": "OK" if dpos <= tol else "FAIL",
                 "source": "derived:network"})
    return rows


def _nmt_year(src: str):
    import re
    m = re.search(r"nmt-(\d{4})", src or "")
    return m.group(1) if m else None


def _cat(v):
    """Category for comparison: the override id of a broken span is provenance, not the type."""
    return v.split(" (")[0] if isinstance(v, str) and v.startswith("przerywana") else v


def run(tiles: list[str] | None = None, overrides_ref: str | None = None, tol: float = TOL_M,
        loaded: list[Tile] | None = None, base: str | None = "origin/main", taper: bool = True,
        trims: bool = True) -> dict:
    """overrides_ref: overrides.yaml of the tiles that ref changes against `base` (merge base) are read from ref, the
    rest from the checkout = "checkout + that PR's overrides" (base=None: every tile from ref)."""
    only = changed_tiles(overrides_ref, base) if overrides_ref and base else None
    ts = loaded or [load_tile(t, overrides_ref if (only is None or t in only) else None)
                    for t in (tiles or TILES) if (REG / t / "region.yaml").exists()]
    pairs = adjacent_pairs(ts)
    used = {t.id for a, b, _ in pairs for t in (a, b)}
    nets = build_nets([t for t in ts if t.id in used], pairs, taper=taper, trims=trims)
    seams = []
    for a, b, se in pairs:
        ca, cb = crossings(a, se, nets[a.id]), crossings(b, se, nets[b.id])
        dropped = {}
        for t in (a, b):
            f = REG / t.id / "graph_filter.authored.json"
            if f.exists():
                for w in json.loads(f.read_text(encoding="utf-8")).get("drop_osm_ways", []):
                    dropped[int(w)] = t.id
        roads = []
        for x, y in match(ca, cb):
            rows = compare_pair(x, y, tol, dropped)
            ref = x or y
            road = {"osm_way": ref.osm_way, "highway": ref.highway, "chain_left": x.chain if x else None,
                    "chain_right": y.chain if y else None, "on_route": bool((x and x.on_route) or (y and y.on_route)),
                    "xy": [round(v, 2) for v in ref.xy], "rows": rows}
            refr = REFERENCE.get((a.id, b.id)) or REFERENCE.get((b.id, a.id))
            if refr and road["on_route"]:
                lo, hi, why = refr
                # K1 / ADR 0212 describe measured two-lane cross-sections.
                # D94 adds the gameplay allowance once to each lane.
                extra = 2 * S.GAMEPLAY_LANE_WIDEN_M
                lo, hi = lo + extra, hi + extra
                if extra:
                    why += f"; ADR 0306 D94: +{S.GAMEPLAY_LANE_WIDEN_M:g} m/pas (2 pasy)"
                for side_name, c in (("lewa", x), ("prawa", y)):
                    v = c.params["rozstaw linii krawędziowych [m]"][0] if c else None
                    rows.append({"param": f"referencja rozstawu linii ({side_name}) {lo:.1f}–{hi:.1f} m",
                                 "left": v if side_name == "lewa" else None, "right": v if side_name == "prawa" else None,
                                 "delta": None, "status": "OK" if v is not None and lo - 1e-9 <= v <= hi + 1e-9 else "FAIL",
                                 "source": why})
            roads.append(road)
        seams.append({"a": a.id, "b": b.id, "edge": se, "roads": roads,
                      "fail": sum(r["status"] == "FAIL" for rd in roads for r in rd["rows"]),
                      "warn": sum(r["status"] == "UWAGA" for rd in roads for r in rd["rows"]),
                      "taper": sum(r["status"] == "PRZEJŚCIE" for rd in roads for r in rd["rows"]),
                      "overrides_src": {a.id: a.overrides_src, b.id: b.overrides_src}})
    not_adjacent = sorted({t.id for t in ts} - {s[k] for s in seams for k in ("a", "b")})
    return {"schema": "truck-sim-pl/seams-qa/1", "tolerance_m": tol, "overrides_ref": overrides_ref,
            "seam_taper": bool(taper), "sides_pass": 2 if trims else 1, "edge_tolerance_m": min(tol, EDGE_TOL_M), "tiles": [t.id for t in ts], "not_adjacent": not_adjacent, "seams": seams,
            "summary": {"seams": len(seams), "roads": sum(len(s["roads"]) for s in seams),
                        "fail_rows": sum(s["fail"] for s in seams), "warn_rows": sum(s["warn"] for s in seams),
                        "taper_rows": sum(s["taper"] for s in seams)}}


def fail_keys(rep: dict) -> set:
    return {(s["a"], s["b"], rd["osm_way"], tuple(rd["xy"]), r["param"]) for s in rep["seams"] for rd in s["roads"]
            for r in rd["rows"] if r["status"] == "FAIL"}


# ----------------------------------------------------------------------------------------------- output
def _f(v):
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.3f}".rstrip("0").rstrip(".") if abs(v) < 1e5 else f"{v:.2f}"
    if isinstance(v, list):
        return "(" + ", ".join(_f(x) for x in v) + ")"
    return str(v).replace("|", "/")


def _key(s, rd, r):
    return (s["a"], s["b"], rd["osm_way"], tuple(rd["xy"]), r["param"])


def rows_by_key(rep: dict) -> dict:
    return {_key(s, rd, r): r for s in rep["seams"] for rd in s["roads"] for r in rd["rows"]}


def table(rep: dict, only_fail: bool = False, only_route: bool = False, ref: dict | None = None,
          ref_label: str = "po ref") -> str:
    """Markdown rows (para, droga/id, parametr, lewa, prawa, delta, wynik, zrodlo); with `ref` (another run) a column
    with that run's result and delta; only_fail keeps the rows that FAIL in either run."""
    rk = rows_by_key(ref) if ref else None
    cols = ["para", "droga / id", "parametr", "lewa", "prawa", "Δ", "wynik"] + ([ref_label] if rk else []) + ["źródło"]
    hdr = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n"
    lines = []
    for s in rep["seams"]:
        for rd in s["roads"]:
            if only_route and not rd["on_route"]:
                continue
            for r in rd["rows"]:
                r2 = rk.get(_key(s, rd, r)) if rk else None
                if only_fail and r["status"] not in ("FAIL", "UWAGA", "PRZEJŚCIE") and not (r2 and r2["status"] == "FAIL"):
                    continue
                road = f"w{rd['osm_way']} {rd['highway']}" + (" (trasa)" if rd["on_route"] else "")
                cells = [f"{s['a']} / {s['b']}", road, r["param"], _f(r["left"]), _f(r["right"]), _f(r["delta"]),
                         r["status"]]
                if rk:
                    cells.append("—" if r2 is None else (r2["status"] + ("" if r2["delta"] is None else f" (Δ {_f(r2['delta'])})")
                                                          + ("" if r2["right"] == r["right"] and r2["left"] == r["left"]
                                                             else f" [{_f(r2['left'])} / {_f(r2['right'])}]")))
                cells.append(_f(r["source"]) + (f" — {_f(r['note'])}" if r.get("note") else ""))
                lines.append("| " + " | ".join(cells) + " |")
    return hdr + "\n".join(lines) + "\n"


def summary_table(rep: dict) -> str:
    out = "| para | szew | dróg | na trasie | FAIL | UWAGA | PRZEJŚCIE |\n|---|---|---|---|---|---|---|\n"
    for s in rep["seams"]:
        e = s["edge"]
        where = f"{e['axis']} = {e['at']:.0f}"
        out += (f"| {s['a']} / {s['b']} | {where} | {len(s['roads'])} | {sum(r['on_route'] for r in s['roads'])} | "
                f"{s['fail']} | {s['warn']} | {s['taper']} |\n")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tiles", default=",".join(TILES))
    ap.add_argument("--overrides-ref", default=None, help="read overrides.yaml from this git ref")
    ap.add_argument("--compare-ref", default=None, help="second run with overrides from this ref; FAILs that vanish")
    ap.add_argument("--base", default="origin/main", help="ref overrides only for tiles the ref changes vs this "
                    "(merge base); 'none' = all tiles from the ref")
    ap.add_argument("--tol", type=float, default=TOL_M)
    ap.add_argument("--json", default=None)
    ap.add_argument("--md", default=None, help="write the tables (FAIL + route roads) as Markdown")
    ap.add_argument("--all-rows", action="store_true", help="print every row, not only FAIL")
    ap.add_argument("--no-taper", action="store_true", help="tiles on their own, without the transitions of ADR 0275")
    ap.add_argument("--pass1", action="store_true", help="side profile of the first assign_sides pass (no junction "
                    "trims; the report before ADR 0304) instead of the second pass the generator meshes")
    a = ap.parse_args(argv)
    tiles = [t for t in a.tiles.split(",") if t]
    base = None if a.base == "none" else a.base
    rep = run(tiles, a.overrides_ref, a.tol, base=base, taper=not a.no_taper, trims=not a.pass1)
    out = {"main": rep}
    gone = None
    if a.compare_ref:
        rep2 = run(tiles, a.compare_ref, a.tol, base=base, taper=not a.no_taper, trims=not a.pass1)
        gone = fail_keys(rep) - fail_keys(rep2)
        out["ref"] = rep2
        out["fail_gone_with_ref"] = sorted([list(k[:3]) + [k[4]] for k in gone])
        out["fail_new_with_ref"] = sorted([list(k[:3]) + [k[4]] for k in fail_keys(rep2) - fail_keys(rep)])
    if a.json:
        Path(a.json).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    ref = out.get("ref")
    lab = f"po {a.compare_ref}" if a.compare_ref else "po ref"
    md = ("## Szwy — podsumowanie\n\n" + summary_table(rep) + "\n## FAIL / UWAGA / PRZEJŚCIE\n\n" + table(rep, only_fail=True, ref=ref, ref_label=lab)
          + "\n## Drogi trasy — wszystkie parametry\n\n" + table(rep, only_route=True, ref=ref, ref_label=lab))
    if a.all_rows:
        md += "\n## Wszystkie wiersze\n\n" + table(rep, ref=ref, ref_label=lab)
    if a.md:
        Path(a.md).write_text(md, encoding="utf-8")
    print(md)
    s = rep["summary"]
    print(f"seams {s['seams']}, roads {s['roads']}, FAIL rows {s['fail_rows']}, PRZEJŚCIE rows {s['taper_rows']}"
          + (f", FAIL gone with {a.compare_ref}: {len(gone)}" if gone is not None else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
