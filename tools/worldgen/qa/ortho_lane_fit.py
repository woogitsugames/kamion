"""Lane layout of one-way carriageways read off the GUGiK orthophoto along the start route -> generated overrides
(ADR 0301). Writes Data/Regions/<id>/overrides.ortho_lanes.json (roads.pipeline.GENERATED_OVERRIDES: loaded before
overrides.yaml, so an authored entry for the same edge wins; edges an authored override already lays out are skipped).

  uv run --project tools/worldgen python tools/worldgen/qa/ortho_lane_fit.py --region <id> [--region <id2> ...]
         [--step 10] [--dry-run]  (pass all tiles of one route together: seam edges are pooled)
         [--out artifacts/lanes-audit-s24/fit]

Per station (every --step m of route_start.json, >= END_SKIP_M from both ends of the graph edge, one-way edges of
FIT_HIGHWAYS with >= 2 lanes): the orthophoto profile of qa/lane_width_audit.py (0.08 m cells, 25 rows +-6 m) in the
frame of the raw OSM way (x = left of travel from the way). Lane boundaries = the longest chain of paint lines spaced
LANE_GAP m; at each side the chain ends on an edge line (asphalt < one lane beyond it) or on the asphalt edge
itself when that is one lane further out; a side gap of AMBIG_GAP m (a missed line) rejects the station.
Per edge: the modal lane count among >= MIN_STATIONS stations, share >= MODE_SHARE; median boundaries and asphalt
edges of those stations; every boundary MAD <= MAX_MAD_M, else the edge keeps the generator default.
Entry: set {lane_edges (from the LEFT asphalt edge, ADR 0095), width (asphalt), center_offset (asphalt centre left of
the OSM way, ADR 0077), edge_lines}. All thresholds WORKING_VALUE. Reference only (docs/05 §3): numbers, no pixels.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
REPO = HERE.parents[3]

import lane_width_audit as LWA  # noqa: E402

FIT_HIGHWAYS = {"motorway", "trunk", "primary", "secondary", "tertiary"}
END_SKIP_M = 20.0
LANE_GAP = (2.6, 4.4)
AMBIG_GAP = (4.4, 6.0)
EDGE_NEAR_M = 1.0
MIN_STATIONS = 3
MODE_SHARE = 0.6
MAX_MAD_M = 0.25
MAX_MAD_OUTER_M = 0.40  # outer boundaries mix an edge line with the kerb a lane further out at some stations
MIN_LANE_MAIN_M = 2.9   # a narrower "lane" on trunk / primary is a line of something else (bay, hatching edge): no fit
DOUBLE_LINE_M = 0.5     # lines closer than this are one (double line P-4: 0.12 + 0.12 + 0.12 m)
STRIP_MAX_M = 1.0       # asphalt further than this beyond the outer boundary line belongs to something else
STRIP_DEFAULT_M = 0.5   # (shoulder, ramp, hatching, yard): the carriageway edge is put this far out (PTB2022 § 23 ust. 7)
OUT_NAME = "overrides.ortho_lanes.json"
LANE_KEYS = ("lane_edges", "lanes", "width", "center_offset", "lane_width")


def edge_frames(graph, origin):
    """edge id -> (P (n, 2) local in travel direction, cumulative s, attrs)."""
    out = {}
    for e in graph["edges"]:
        a = e["attrs"]
        P = np.array(e["geometry"], float) - np.array(origin)
        if (a.get("oneway") or {}).get("v") == "-1":
            P = P[::-1].copy()
        s = np.r_[0.0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
        out[e["id"]] = (P, s, a, e)
    return out


def project(P, s, q):
    """(station along P, signed lateral of q, left of the polyline direction = +)."""
    best = None
    for i in range(len(P) - 1):
        d = P[i + 1] - P[i]
        L2 = float(d @ d)
        if L2 < 1e-9:
            continue
        t = float(np.clip((q - P[i]) @ d / L2, 0, 1))
        f = P[i] + t * d
        dist = float(np.hypot(*(q - f)))
        if best is None or dist < best[0]:
            cross = d[0] * (q - P[i])[1] - d[1] * (q - P[i])[0]
            best = (dist, s[i] + t * np.sqrt(L2), dist * (1 if cross >= 0 else -1))
    return best[1], best[2]


def station_layout(asph, lines, at=None, lanes=None):
    """Boundaries (x ascending = right to left of travel), edge-line flags (right, left) or None. `at` = lateral of the
    route point (in the lane the truck drives): only chains of lines around it count. `lanes` (OSM count): where one
    side is closed (edge line / kerb) and the other opens into unmarked asphalt (a merge area, a slip road alongside),
    the missing boundaries are laid out from the closed side with the measured lane width ("extrapolated")."""
    if not asph:
        return None
    aR, aL = asph
    xs = sorted(lines)
    best = []
    i = 0
    while i < len(xs):
        ch = [xs[i]]
        j = i + 1
        while j < len(xs):
            g = xs[j] - ch[-1]
            if g <= DOUBLE_LINE_M:
                j += 1                     # second line of a double line (P-4) / noise on the same line
                continue
            if g < LANE_GAP[0]:
                break                      # hatching (P-21), island stripes, a crossing: the lanes end here
            if g <= LANE_GAP[1]:
                ch.append(xs[j])
                j += 1
                continue
            break
        near = at is None or (ch[0] - LANE_GAP[1] <= at <= ch[-1] + LANE_GAP[1])
        if near and len(ch) > len(best):
            best = ch
        i += 1
    if len(best) < 1:
        return None
    b = list(best)
    flags = [False, False]
    closed = [False, False]
    for side, edge in ((0, aR), (1, aL)):
        end = b[0] if side == 0 else b[-1]
        gap = abs(edge - end)
        if gap < LANE_GAP[0]:
            # the outermost line with asphalt less than a lane beyond it: an edge line (P-7) with the edge strip /
            # paved strip / gutter behind it (gap <= EDGE_NEAR_M: right at the kerb)
            flags[side] = closed[side] = True
        elif LANE_GAP[0] <= gap <= LANE_GAP[1]:
            closed[side] = True
            if side == 0:
                b.insert(0, aR)
            else:
                b.append(aL)
        elif AMBIG_GAP[0] < gap < AMBIG_GAP[1]:
            return None
        # gap >= AMBIG_GAP[1]: hatching / island / parking / merge area beside the lanes - lanes end on the line
    extra = 0
    if lanes and len(b) >= 2 and len(b) - 1 < lanes and closed[0] != closed[1]:
        w = (b[-1] - b[0]) / (len(b) - 1)
        if not LANE_GAP[0] <= w <= LANE_GAP[1]:
            w = None
        if w is not None:
            while len(b) - 1 < lanes:
                if closed[1]:
                    b.insert(0, b[0] - w)
                else:
                    b.append(b[-1] + w)
                extra += 1
    if len(b) < 3:
        return None
    return {"b": b, "flags": flags, "aR": aR if closed[0] or not extra else b[0] - STRIP_DEFAULT_M,
            "aL": aL if closed[1] or not extra else b[-1] + STRIP_DEFAULT_M, "extrapolated": extra}


def mad(v):
    m = statistics.median(v)
    return statistics.median([abs(x - m) for x in v])


def collect(region, step=10.0):
    """Route stations of one region: ({edge id: [station]}, edge ids an authored override lays out, frames)."""
    from fidelity import ortho as O
    from roads import pipeline
    reg = pipeline.load_region(region)
    origin = (reg["origin"]["x"], reg["origin"]["y"])
    rdir = REPO / "Data/Regions" / region
    graph = json.loads((rdir / "roads.graph.json").read_text(encoding="utf-8"))
    frames = edge_frames(graph, origin)
    authored = pipeline.load_overrides(region)
    gen_ids = {o.get("id") for o in pipeline.generated_overrides(region)}
    skip = set()
    for ov in authored:
        if ov.get("id") in gen_ids or not any(k in (ov.get("set") or {}) for k in LANE_KEYS):
            continue
        t = ov.get("target", {})
        if "edge" in t:
            skip.add(t["edge"])
        for w in (t.get("osm_way") or []) if isinstance(t.get("osm_way"), list) else [t.get("osm_way")]:
            if w is not None:
                skip |= {eid for eid, (_, _, _, e) in frames.items() if e["osm_way"] == int(w)}
    orth = O.Ortho(reg)
    per_edge = {}
    for st in LWA.route_stations(region, step):
        eid = st["edge"]
        if eid not in frames or eid in skip:
            continue
        P, s, a, e = frames[eid]
        v = lambda k: (a.get(k) or {}).get("v")
        if v("oneway") == "no" or v("highway") not in FIT_HIGHWAYS or int(v("lanes") or 1) < 2:
            continue
        se, d = project(P, s, st["xy"])
        if se < END_SKIP_M or se > s[-1] - END_SKIP_M:
            continue
        c, t = st["xy"], st["t"]
        X, Y = LWA.sample_grid(c, t)
        ox, oy = origin
        bb = (float(X.min() + ox - 1), float(Y.min() + oy - 1), float(X.max() + ox + 1), float(Y.max() + oy + 1))
        rgb, src = orth.window(bb, 0.05)
        if not src.startswith("wms"):
            continue                                    # the 0.25 m sheet is too coarse for line positions
        col = np.clip(((X + ox - bb[0]) / 0.05).astype(int), 0, rgb.shape[1] - 1)
        row = np.clip(((bb[3] - (Y + oy)) / 0.05).astype(int), 0, rgb.shape[0] - 1)
        o = LWA.ortho_profile(rgb[row, col])
        if not o["asphalt"]:
            continue
        lay = station_layout((o["asphalt"][0] + d, o["asphalt"][1] + d), [u + d for u in o["lines"]], at=d,
                             lanes=int(v("lanes") or 1))
        per_edge.setdefault(eid, []).append({"region": region, "s_edge": round(se, 1), "d": round(d, 2),
                                             "layout": lay})
    return per_edge, skip, frames


def fit(regions, step=10.0, out=None, dry=False):
    """Stations of all `regions` pooled per graph edge (an edge crossing a tile seam has the same id in both tiles and
    gets the same entry in both, so the seam sees one cross-section); entries written to every region that has it."""
    from roads import pipeline
    per_edge, skip, frames, has = {}, set(), {}, {}
    for region in regions:
        pe, sk, fr = collect(region, step)
        for k, v in pe.items():
            per_edge.setdefault(k, []).extend(v)
        skip |= sk
        frames.update(fr)
        for k in fr:
            has.setdefault(k, []).append(region)
    entries, report = [], []
    for eid in sorted(per_edge):
        if eid in skip:
            continue
        sts = per_edge[eid]
        good = [x["layout"] for x in sts if x["layout"]]
        rec = {"edge": eid, "regions": has.get(eid, []), "stations": len(sts), "usable": len(good)}
        report.append(rec)
        if len(good) < MIN_STATIONS:
            rec["result"] = "too few stations"
            continue
        counts = {}
        for g in good:
            counts[len(g["b"]) - 1] = counts.get(len(g["b"]) - 1, 0) + 1
        n, k = max(counts.items(), key=lambda kv: (kv[1], kv[0]))
        rec["lane_counts"] = counts
        if k < MIN_STATIONS or k / len(good) < MODE_SHARE:
            rec["result"] = "lane count not consistent"
            continue
        g = [x for x in good if len(x["b"]) - 1 == n]
        B = [statistics.median(x["b"][i] for x in g) for i in range(n + 1)]
        mads = [mad([x["b"][i] for x in g]) for i in range(n + 1)]
        aR = statistics.median(x["aR"] for x in g)
        aL = statistics.median(x["aL"] for x in g)
        rec.update(bounds=[round(x, 2) for x in B], mad=[round(x, 2) for x in mads], aR=round(aR, 2), aL=round(aL, 2))
        if max(mads[1:-1] + [0.0]) > MAX_MAD_M or max(mads[0], mads[-1]) > MAX_MAD_OUTER_M:
            rec["result"] = "boundaries scatter"
            continue
        aR, aL = min(aR, B[0]), max(aL, B[-1])
        if B[0] - aR > STRIP_MAX_M:
            aR = B[0] - STRIP_DEFAULT_M
            rec["right_edge"] = "asphalt continues beyond the lanes: edge strip default"
        if aL - B[-1] > STRIP_MAX_M:
            aL = B[-1] + STRIP_DEFAULT_M
            rec["left_edge"] = "asphalt continues beyond the lanes: edge strip default"
        hw_ = (frames[eid][2].get("highway") or {}).get("v")
        if hw_ in ("motorway", "trunk", "primary") and min(b - a for a, b in zip(B, B[1:])) < MIN_LANE_MAIN_M:
            rec["result"] = "lane narrower than MIN_LANE_MAIN_M"
            continue
        fl = [sum(x["flags"][i] for x in g) * 2 > len(g) for i in (0, 1)]
        le = [round(aL - x, 2) for x in reversed(B)]
        el = {(True, True): "both", (True, False): "left", (False, True): "right"}.get((fl[1], fl[0]), "none")
        e = frames[eid][3]
        osm_l = (e["attrs"].get("lanes") or {}).get("v")
        entry = {"id": f"ortho-lanes-{eid}", "target": {"edge": eid},
                 "source": "GUGiK orthophoto WMS HighResolution 0.08 m, tools/worldgen/qa/ortho_lane_fit.py (ADR 0301)",
                 "reason": (f"{len(g)} of {len(sts)} route stations: {n} lanes (OSM lanes={osm_l}), lane widths "
                            f"{', '.join(f'{b - a:.2f}' for a, b in zip(le, le[1:]))} m, asphalt {aL - aR:.2f} m, "
                            f"centre {0.5 * (aL + aR):+.2f} m left of the OSM way; boundary MAD <= {max(mads):.2f} m"),
                 "confidence": "medium" if len(g) >= 5 else "low",
                 "set": {"lane_edges": le, "width": round(aL - aR, 2), "center_offset": round(0.5 * (aL + aR), 2),
                         "edge_lines": el}}
        rec["result"] = "override"
        rec["set"] = entry["set"]
        entries.append(entry)
    docs = {}
    for region in regions:
        mine = [e for e in entries if region in has.get(e["target"]["edge"], [])]
        docs[region] = {"schema": "truck-sim-pl/overrides/1",
                        "generator": ("tools/worldgen/qa/ortho_lane_fit.py (ADR 0301), regions pooled: "
                                      + ", ".join(regions)),
                        "note": "generated - do not edit; rerun the tool. Authored overrides.yaml entries win.",
                        "overrides": mine}
        if not dry:
            (REPO / "Data/Regions" / region / OUT_NAME).write_text(
                json.dumps(docs[region], indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)
        (Path(out) / "fit_report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False),
                                                   encoding="utf-8", newline="\n")
    for r in report:
        print(json.dumps(r, ensure_ascii=False))
    return docs, report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--region", required=True, action="append")
    ap.add_argument("--step", type=float, default=10.0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    fit(a.region, a.step, a.out, a.dry_run)


if __name__ == "__main__":
    main()
