"""D94 / ADR 0306: does the 16.5 m tractor + 13.6 m semitrailer stay in its own lane and on the carriageway along every
corridor route (Resources/WorldStreaming/route_links.json `corridors`) and through every route link (roundabouts)?

Kinematic low-speed model of roads/swept_path.py (Combination, ADR 0218 / 0280: tridem 6.32 / 7.63 / 8.94 m behind the
kingpin): the centre of the tractor front axle follows the autopilot line exactly (route_start.json = centre of the
lane, route links); the rear axle and the trailer follow as tractrices. The truck does NOT swing out: a tyre that the
lane-centre line puts on a kerb is exactly the place where a driver has to go into the opposite lane to fit (owner,
Knyszyn DK65 x DW671). Outer tyre edges every 1 m (front, drive duals, three trailer axles, both sides) are classified:

  opposite      on a two-way carriageway of the generator network (roads.pipeline.build_network, in memory) beyond the
                centre line axis by more than OPPOSITE_TOL_M, with the vehicle part heading along that road (within
                ALIGN_DEG), outside the junction mouths (JUNCTION_SKIP_M from a node of degree >= 3);
  kerb          not on carriageway asphalt / deck / truck apron of the BUILT tile (chunk GLBs: road_* materials,
                apron_*), but on a hard surface (kerb top, sidewalk, gravel shoulder, paving);
  apron         on the truck apron of a roundabout (allowed: that is what it is built for, ADR 0218);
  off_hard      on no hard surface at all (grass, verge, island fill) - qa/link_swept_check.py's gate.

Pieces per corridor tile: the tile's start route, or the corridor's link that replaces it, or route + the link that
follows it (`after_route`); the last 45 m of the previous tile's piece are prepended (EPSG:2180 -> tile frame), so the
trailer enters a tile in its real pose. Links that no corridor uses (other ways through the Knyszyn roundabout) are
checked alone with link_swept_check.link_path (route tail or settle length).

    uv run --project tools/worldgen python tools/worldgen/qa/combo_lane_check.py [--corridor ID ...] [--tiles a,b]
        [--widen 0.0] [--dump-tile knyszyn] --out artifacts/road-widen-s24/before/combo.json

--widen sets standards.GAMEPLAY_LANE_WIDEN_M for the in-memory network (0.0 = the network the tiles of main were built
from before D94). Exit code 1 when a corridor tile has an opposite / off_hard point."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import shapely
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import link_swept_check as LS  # noqa: E402
import seam_section as SS  # noqa: E402
from roads import standards as STD  # noqa: E402
from roads.swept_path import Combination, _unit  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
# data root (built chunks, route_start, route_links) may be another checkout, e.g. main for the BEFORE numbers
import os  # noqa: E402
if os.environ.get("KAMION_DATA_ROOT"):
    ROOT = Path(os.environ["KAMION_DATA_ROOT"])
    LS.LINKS = ROOT / "game/Assets/_Project/World/Runtime/Streaming/Resources/WorldStreaming/route_links.json"
OPPOSITE_TOL_M = 0.10    # WORKING_VALUE: outer tyre edge beyond the centre line axis (line 0.12 m wide -> past its far half)
ALIGN_DEG = 30.0         # WORKING_VALUE: the vehicle part runs along the road it is tested against
JUNCTION_SKIP_M = 14.0   # WORKING_VALUE: no lane test this close to a node of degree >= 3 (turning through a junction)
TAIL_M = 45.0            # previous piece prepended (longer than tractor + trailer, 16.5 m, plus the settling of the tractrix)
SAMPLE_M, EVERY = LS.SAMPLE_M, LS.EVERY
CW_PREFIX = ("road_",)
APRON_PREFIX = ("apron_",)


def origin(tile):
    r = yaml.safe_load((ROOT / "Data/Regions" / tile / "region.yaml").read_text(encoding="utf-8"))
    return np.array([float(r["origin"]["x"]), float(r["origin"]["y"])])


def densify(P, step=SAMPLE_M):
    P = np.asarray(P, float)
    keep = np.concatenate([[True], np.hypot(*np.diff(P, axis=0).T) > 1e-6])
    P = P[keep]
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    si = np.arange(0, s[-1], step)
    return np.column_stack([np.interp(si, s, P[:, 0]), np.interp(si, s, P[:, 1])])


def route_pts(tile):
    p = ROOT / "Data/Regions" / tile / "route_start.json"
    return np.array(json.loads(p.read_text(encoding="utf-8"))["points_en"], float) if p.exists() else None


def tyre_points(path, v=Combination()):
    """(points (m,2), heading (m,2), tags [(s, axle, side)]): outer tyre edges with the heading of their vehicle part."""
    t0 = _unit(path[1] - path[0]); pr = path[0] - t0 * v.L1; pk = pr + t0 * v.c; pt = pk - t0 * v.l2
    th = v.trailer_track / 2 + v.trailer_tyre_w / 2; fo = v.front_track / 2 + v.front_tyre_w / 2
    pts, hd, tags = [], [], []
    for i in range(1, len(path)):
        pf = path[i]; u1 = _unit(pf - pr); pr = pf - u1 * v.L1; pk = pr + u1 * v.c; u2 = _unit(pk - pt); pt = pk - u2 * v.l2
        n1 = np.array([-u1[1], u1[0]]); n2 = np.array([-u2[1], u2[0]])
        if i % EVERY:
            continue
        s = i * SAMPLE_M
        for sg in (1, -1):
            side = "left" if sg > 0 else "right"
            pts += [pf + sg * n1 * fo, pr + sg * n1 * v.rear_outer_half]
            hd += [u1, u1]
            tags += [(s, "front", side), (s, "drive", side)]
            for k, d in enumerate(v.trailer_axles):
                pts.append(pk - u2 * d + sg * n2 * th); hd.append(u2); tags.append((s, f"trailer{k + 1}", side))
    return np.array(pts), np.array(hd), tags


class LaneModel:
    """Two-way carriageways of the in-memory generator network of a tile: centre line position per chain sample."""

    def __init__(self, tile):
        from roads import pipeline
        net, *_ = pipeline.build_network(tile)
        self.items = []
        geoms = []
        for c in net.chains:
            if c.closed or c.roundabout or c.dirn is None or not (c.dirn == 0).any():
                continue
            lat_c = np.zeros(len(c.line.p))
            for i in range(len(c.line.p)):
                sec = net.sec_list[int(c.sec_idx[i])]
                rev = bool(c.meta["rev"][i]) if "rev" in c.meta else False
                fc, bc = (sec.lanes_bwd, sec.lanes_fwd) if rev else (sec.lanes_fwd, sec.lanes_bwd)
                lat_c[i] = (fc - bc) * float(sec.lane_w) / 2.0
            skip_a = JUNCTION_SKIP_M if net.nodes[c.node_a]["deg"] >= 3 else 0.0
            skip_b = JUNCTION_SKIP_M if net.nodes[c.node_b]["deg"] >= 3 else 0.0
            self.items.append((c, lat_c, skip_a, skip_b))
            geoms.append(shapely.LineString(c.line.p))
        self.tree = shapely.STRtree(geoms) if geoms else None
        self.geoms = geoms

    def opposite(self, pts, hd):
        out = np.zeros(len(pts), bool)
        if self.tree is None:
            return out
        cosa = math.cos(math.radians(ALIGN_DEG))
        P = shapely.points(pts)
        idx_pt, idx_g = self.tree.query(P, predicate="dwithin", distance=12.0)
        best = {}
        for ip, ig in zip(idx_pt, idx_g):
            d = self.geoms[ig].distance(P[ip])
            if ip not in best or d < best[ip][0]:
                best[ip] = (d, ig)
        for ip, (_, ig) in best.items():
            c, lat_c, sa, sb = self.items[ig]
            s, lat = c.line.project(pts[ip])
            if s < sa or s > c.line.length - sb:
                continue
            i = c.idx(s)
            if c.dirn[i] != 0 or abs(lat) > float(c.hw[i]):
                continue
            t, _ = c.line.frame(s)
            dot = float(t @ hd[ip])
            if abs(dot) < cosa:
                continue
            lc = float(lat_c[i])
            out[ip] = (lat > lc + OPPOSITE_TOL_M) if dot > 0 else (lat < lc - OPPOSITE_TOL_M)
        return out


def surfaces(tile, path):
    """{category: triangles} of the built tile around path: cw (road_*), apron (apron_*), hard (kerb, sidewalk,
    shoulder, paving), soft (grass, verge, island fill). Islands and kerbs are laid ON the junction patch, so a point
    belongs to the category of the HIGHEST triangle over it (evaluate)."""
    c = 0.5 * (path.min(0) + path.max(0))
    rad = float(np.max(path.max(0) - path.min(0))) / 2 + 30.0
    groups = {"cw": [], "apron": [], "hard": [], "soft": []}
    for node in ("road", "paved", "bridge"):
        for k, t in SS.tris(ROOT, tile, node, c, rad=rad).items():
            if node == "bridge" and not k.startswith("road_"):
                continue
            g = ("cw" if k.startswith(CW_PREFIX) else "apron" if k.startswith(APRON_PREFIX)
                 else "soft" if any(w in k for w in LS.NOT_HARD) else "hard")
            groups[g].append(t)
    return {k: (np.concatenate(v) if v else np.zeros((0, 3, 3))) for k, v in groups.items()}


def classify_surface(surf, pts):
    """Category of the highest triangle over each point ('none' where no triangle)."""
    keys = ("cw", "apron", "hard", "soft")
    Z = np.column_stack([LS._locate(surf[k], pts) for k in keys])
    Zf = np.where(np.isnan(Z), -1e9, Z)
    # 5 mm tolerance: a patch and a ribbon meeting at the same level count as carriageway
    top = Zf.max(1)
    out = np.full(len(pts), "none", dtype=object)
    for j in range(len(keys) - 1, -1, -1):
        out[Zf[:, j] >= top - 0.005] = keys[j]
    out[top < -1e8] = "none"
    return out


SEAM_SKIP_M = 2.5   # tyre points this close to the tile bbox are not classified: the tile mesh ends at the seam
                    # (the neighbour tile carries the surface there); counted as `seam_skipped`


def classify(tile, path, surf, lanes: LaneModel, keep_s0=0.0):
    pts, hd, tags = tyre_points(path)
    bb = LS.tile_bbox(tile, ROOT, margin=0.0)
    inside = (pts[:, 0] >= bb[0]) & (pts[:, 0] <= bb[2]) & (pts[:, 1] >= bb[1]) & (pts[:, 1] <= bb[3])
    near = inside & ~((pts[:, 0] >= bb[0] + SEAM_SKIP_M) & (pts[:, 0] <= bb[2] - SEAM_SKIP_M)
                      & (pts[:, 1] >= bb[1] + SEAM_SKIP_M) & (pts[:, 1] <= bb[3] - SEAM_SKIP_M))
    s_ok = np.array([t[0] >= keep_s0 for t in tags])
    keep = s_ok & inside & ~near
    n_seam = int((s_ok & near).sum())
    pts, hd, tags = pts[keep], hd[keep], [t for t, k in zip(tags, keep) if k]
    sc = classify_surface(surf, pts)
    on_cw = sc == "cw"
    opp = lanes.opposite(pts, hd) & on_cw
    off = (sc == "soft") | (sc == "none")
    cls = np.where(opp, "opposite", np.where(off, "off_hard", np.where(sc == "hard", "kerb",
                   np.where(sc == "apron", "apron", "ok"))))
    return pts, tags, cls, n_seam


def cost(cls):
    return int(10 * (cls == "opposite").sum() + 5 * (cls == "off_hard").sum() + (cls == "kerb").sum())


def swing(path, k, left_m, half_m):
    """Driver's line: path shifted sideways (left_m > 0 = left) around path index k, raised cosine over +-half_m
    (streaming/route_links._swing, the same shape the authored link swings use)."""
    P = np.asarray(path, float).copy()
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    d = np.gradient(P, axis=0)
    d /= np.maximum(np.linalg.norm(d, axis=1), 1e-9)[:, None]
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    u = (s - s[k]) / half_m
    w = np.where(np.abs(u) < 1.0, 0.5 * (1.0 + np.cos(np.pi * u)), 0.0)
    return P + nrm * (left_m * w)[:, None]


SWING_LEFT = (-2.5, -1.5, -0.75, 0.75, 1.5, 2.5, 3.5)   # WORKING_VALUE: lateral swing candidates [m]
SWING_HALF = (15.0, 25.0, 35.0)
SWING_APEX = (-4.0, 4.0, 10.0, 16.0)                    # apex this far AHEAD of the trailer point that hit [m]


def optimise(tile, path, surf, lanes, keep_s0, events, lead_m):
    """Best driver swing per event cluster (kerb / off_hard), greedy along the path: the line may move inside its own
    lane / the junction (a swing that puts a tyre over the centre line counts as `opposite`). Returns (path, swings)."""
    swings = []
    total = cost(classify(tile, path, surf, lanes, keep_s0)[2])
    for ev in [e for e in events if e["kind"] in ("kerb", "off_hard", "opposite")]:
        s_hit = ev["s0"] + lead_m
        lo, hi = s_hit - 80.0, s_hit + 60.0
        i0, i1 = max(0, int(lo / SAMPLE_M)), min(len(path), int(hi / SAMPLE_M))
        if i1 - i0 < 40:
            continue
        win = path[i0:i1]
        ks0 = max(keep_s0 - i0 * SAMPLE_M, 25.0)
        base = cost(classify(tile, win, surf, lanes, ks0)[2])
        best = (base, None)
        if base == 0:
            continue
        for ap in SWING_APEX:
            k = int((s_hit + ap) / SAMPLE_M) - i0
            if not 0 < k < len(win) - 1:
                continue
            for lm in SWING_LEFT:
                for hm in SWING_HALF:
                    c = cost(classify(tile, swing(win, k, lm, hm), surf, lanes, ks0)[2])
                    if c < best[0]:
                        best = (c, (k + i0, lm, hm))
        if best[1] is not None:
            k, lm, hm = best[1]
            cand = swing(path, k, lm, hm)
            t2 = cost(classify(tile, cand, surf, lanes, keep_s0)[2])
            if t2 >= total:                     # the window improved, the whole path did not: keep the old line
                continue
            path, total = cand, t2
            swings.append({"s": round(k * SAMPLE_M - lead_m, 1), "left_m": lm, "half_m": hm,
                           "en": [round(float(path[k][0]), 2), round(float(path[k][1]), 2)],
                           "cost_before": base, "cost_after": best[0]})
    return path, swings


def evaluate(tile, path, lead_m, lanes: LaneModel, keep_s0=0.0, dump=False, opt=False):
    surf = surfaces(tile, path)
    pts, tags, cls, n_seam = classify(tile, path, surf, lanes, keep_s0)
    r = summarise(pts, tags, cls, lead_m, n_seam, dump, path)
    if opt and (r["kerb"] or r["off_hard"] or r["opposite"]):
        p2, sw = optimise(tile, path, surf, lanes, keep_s0, r["events"], lead_m)
        pts, tags, cls, n_seam = classify(tile, p2, surf, lanes, keep_s0)
        r["swing"] = summarise(pts, tags, cls, lead_m, n_seam, dump, p2)
        r["swing"]["swings"] = sw
    return r


def summarise(pts, tags, cls, lead_m, n_seam, dump, path):
    events = []
    for kind in ("opposite", "off_hard", "kerb"):
        sel = [i for i in range(len(pts)) if cls[i] == kind]
        cur = None
        for i in sorted(sel, key=lambda i: tags[i][0]):
            s = tags[i][0] - lead_m
            if cur and s - cur["s1"] <= 6.0:
                cur["s1"] = round(s, 1); cur["n"] += 1; cur["axles"].add(f"{tags[i][1]}:{tags[i][2]}")
            else:
                cur = {"kind": kind, "s0": round(s, 1), "s1": round(s, 1), "n": 1, "axles": {f"{tags[i][1]}:{tags[i][2]}"},
                       "en": [round(float(pts[i][0]), 1), round(float(pts[i][1]), 1)]}
                events.append(cur)
    for e in events:
        e["axles"] = sorted(e["axles"])
    r = {"tyre_points": int(len(pts)), "opposite": int((cls == "opposite").sum()), "kerb": int((cls == "kerb").sum()),
         "apron": int((cls == "apron").sum()), "off_hard": int((cls == "off_hard").sum()), "seam_skipped": n_seam,
         "events": events}
    if dump:
        r["dump"] = {"path": np.round(path, 2).tolist(), "pts": np.round(pts, 2).tolist(), "cls": cls.tolist(),
                     "axle": [t[1] for t in tags]}
    return r


def corridor_pieces(cor, links):
    """[(tile, kind, link or None)] in corridor order."""
    by_id = {L["id"]: L for L in links}
    joins = cor["joins"]
    out = []
    for t in cor["tiles"]:
        ent = next((j["entry"] for j in joins if j["to"] == t), "route")
        ext = next((j["exit"] for j in joins if j["from"] == t), "route")
        used = [by_id[x.split(":", 1)[1]] for x in (ent, ext) if x.startswith("link:")]
        rep = next((L for L in used if L.get("replacesRoute") == t), None)
        aft = next((L for L in used if L.get("afterRoute") == t), None)
        if rep is None and aft is None:
            # a link that starts at its own point (start_epsg2180) in this tile replaces the route there too
            rep = next((L for L in used if L.get("tile") == t and not L.get("afterRoute")), None)
        if rep is not None:
            out.append((t, "link:" + rep["id"], rep))
        elif aft is not None:
            out.append((t, "route+link:" + aft["id"], aft))
        else:
            out.append((t, "route", None))
    return out


def piece_path(tile, kind, L):
    if L is None:
        return route_pts(tile)
    P = np.column_stack([L["e"], L["n"]])
    if kind.startswith("route+link"):
        R = route_pts(tile)
        return np.vstack([R, P[1:]]) if R is not None else P
    return P


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corridor", action="append")
    ap.add_argument("--tiles")
    ap.add_argument("--widen", type=float)
    ap.add_argument("--dump-tile", action="append", default=[])
    ap.add_argument("--no-free-links", action="store_true")
    ap.add_argument("--swing", action="store_true", help="also search the best driver swing per kerb event")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.widen is not None:
        STD.GAMEPLAY_LANE_WIDEN_M = a.widen
    d = json.loads(LS.LINKS.read_text(encoding="utf-8"))
    links = d["links"]
    tiles_f = set(a.tiles.split(",")) if a.tiles else None
    lanes_cache, res, used_links = {}, {"widen_m": STD.GAMEPLAY_LANE_WIDEN_M, "corridors": {}, "links": {}}, set()

    def lanes(t):
        if t not in lanes_cache:
            lanes_cache[t] = LaneModel(t)
        return lanes_cache[t]
    done = {}
    for cor in d["corridors"]:
        if a.corridor and cor["id"] not in a.corridor:
            continue
        prev = None          # (tail EPSG:2180)
        rows = []
        for tile, kind, L in corridor_pieces(cor, links):
            if L is not None:
                used_links.add(L["id"])
            path = piece_path(tile, kind, L)
            if path is None or (tiles_f and tile not in tiles_f) or not LS.built(tile, ROOT):
                rows.append({"tile": tile, "piece": kind, "skipped": "filtered" if path is not None else "no route"})
                prev = None if path is None else path_tail(path, origin(tile))
                continue
            o = origin(tile)
            lead = 0.0
            if prev is not None:
                T = prev - o
                if np.hypot(*(T[-1] - path[0])) < 8.0:
                    lead = float(np.sum(np.hypot(*np.diff(T, axis=0).T)))
                    path = np.vstack([T[:-1], path])
            dp = densify(path)
            key = (tile, kind, round(lead, 1))
            if key not in done:
                settle = 0.0 if lead > 0 else Combination().L1 + Combination().kp_rear
                done[key] = evaluate(tile, dp, lead, lanes(tile), keep_s0=settle, dump=tile in a.dump_tile, opt=a.swing)
            r = dict(done[key]); r.update({"tile": tile, "piece": kind, "lead_m": round(lead, 1)})
            rows.append(r)
            if "swing" in r:
                w = r["swing"]
                print(f"{'':24s} {'':24s} {'  + driver swing':36s} opp {w['opposite']:4d} kerb {w['kerb']:4d} "
                      f"apron {w['apron']:4d} off {w['off_hard']:4d}  swings {len(w['swings'])}", flush=True)
            prev = path_tail(piece_path(tile, kind, L), o)
            print(f"{cor['id']:24s} {tile:24s} {kind:36s} opp {r['opposite']:4d} kerb {r['kerb']:4d} "
                  f"apron {r['apron']:4d} off {r['off_hard']:4d} / {r['tyre_points']}", flush=True)
        res["corridors"][cor["id"]] = rows
    if not a.no_free_links:
        for L in links:
            if L["id"] in used_links or (tiles_f and L["tile"] not in tiles_f) or not LS.built(L["tile"], ROOT):
                continue
            path, lead = LS.link_path(L, TAIL_M, 0.0, ROOT)
            settle = 0.0 if lead > 0 else Combination().L1 + Combination().kp_rear
            r = evaluate(L["tile"], path, lead, lanes(L["tile"]), keep_s0=settle, dump=L["tile"] in a.dump_tile, opt=a.swing)
            r.update({"tile": L["tile"], "piece": "link:" + L["id"], "lead_m": round(lead, 1)})
            res["links"][L["id"]] = r
            print(f"{'(free link)':24s} {L['tile']:24s} {L['id']:36s} opp {r['opposite']:4d} kerb {r['kerb']:4d} "
                  f"apron {r['apron']:4d} off {r['off_hard']:4d} / {r['tyre_points']}", flush=True)
            if "swing" in r:
                w = r["swing"]
                print(f"{'':24s} {'':24s} {'  + driver swing':36s} opp {w['opposite']:4d} kerb {w['kerb']:4d} "
                      f"apron {w['apron']:4d} off {w['off_hard']:4d}  swings {len(w['swings'])}", flush=True)
    allr = [r for rows in res["corridors"].values() for r in rows if "tyre_points" in r] + list(res["links"].values())
    keys = ("tyre_points", "opposite", "kerb", "apron", "off_hard", "seam_skipped")
    res["total"] = {k: int(sum(r[k] for r in allr)) for k in keys}
    if a.swing:
        res["total_swing"] = {k: int(sum(r.get("swing", r)[k] for r in allr)) for k in keys}
        print("TOTAL with driver swing", res["total_swing"])
    print("TOTAL", res["total"])
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
    t = res.get("total_swing", res["total"])
    return 1 if t["opposite"] or t["off_hard"] else 0


def path_tail(path, o, m=TAIL_M):
    P = np.asarray(path, float)
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    return P[s >= s[-1] - m] + o


if __name__ == "__main__":
    sys.exit(main())
