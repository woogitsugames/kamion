"""M29 / ADR 0144 pkt 3 + ADR 0141 P2: audit of barrier rows on the region data in the repo (read-only).

Two questions, answered on data committed in the repo (no world regeneration):

- free deck ends: ends of bridge (deck) barrier runs with no other run end within
  RAIL_CONTINUE_M (2.5 m) - in the game these show as gaps at the structure entrances
  (ADR 0144 pkt 3: 34 such ends on the r7d build, incl. the Putry viaduct E -740..-690);
- overlapping rows: pairs of barrier rows that run parallel (< OVERLAP_GAP_M = 0.5 m apart)
  with a common span > OVERLAP_COMMON_M = 0.5 m (ADR 0141 P2: two closure rows at edge-west,
  the Maczka carriageway and its trunk_link, stood 0.5 m and 0.9 m apart).

Run sources, in order:
1. `generated/streetscape_qa.json` -> `furniture.guardrail_runs` (canonical: every built W-beam
   run with 1 m points E, N, foot z, deck flag - present once the leader regenerates the world);
2. reconstruction from `roads.graph.json` + `overrides.yaml` via `pipeline.build_network` (works
   on today's committed data, no raw NMT needed): deck barrier runs (contiguous bridge stretches,
   both cap edges) and authored guardrail runs. Ground rule runs (embankment / beside a structure)
   need the NMT and are not reconstructed here - a deck end continued by such a run is counted as
   continued in the full build, so the reconstruction can only over-count free ends.

Region-edge closures (the "zapory") are NOT audited here any more (ADR 0169): they are built by the Unity
importer (`WorldEdgeBuilder.ReadExits` -> `ResolveClosures`), which is their only source. The Python copy of
ReadExits that lived here reported the raw graph closures (before the importer merges them) and so kept an
xfail alive for a defect the importer had already removed. The duplicate check is the EditMode test
`WorldEdgeClosureDuplicateTests` on the committed graph.

CLI: `uv run --project tools/worldgen python -m roads.barrier_audit --region bialystok-industrial-c`
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]

FREE_END_CONTINUE_M = 2.5      # ADR 0144: a deck end with another run end this close carries on
FREE_END_ON_RAIL_M = 0.6        # ADR 0159: ... or the body of another rail this close (the end was led onto it)
FREE_END_DZ = 0.8               # ... at a similar level
OVERLAP_GAP_M = 0.5             # M29: parallel rows closer than this overlap
OVERLAP_COMMON_M = 0.5          # ... with a common span longer than this
OVERLAP_ANGLE_DEG = 25.0        # ADR 0141 r6d: headings within this are parallel


# --------------------------------------------------------------------------------------------- runs
def load_runs_from_qa(region_dir: Path):
    """guardrail_runs of the generated streetscape_qa.json: [{key, pts: [[e, n, z, deck], ...]}]."""
    p = region_dir / "generated" / "streetscape_qa.json"
    if not p.exists():
        return None
    r = json.loads(p.read_text(encoding="utf-8")).get("furniture", {}).get("guardrail_runs")
    if not r:
        return None
    return [{"key": x["key"], "pts": np.asarray(x["pts"], float)} for x in r]


def deck_and_authored_runs(region_id: str):
    """Reconstruct deck barrier runs (contiguous bridge stretches of every chain, both cap edges, post
    line at the BRIDGE_BARRIER_EDGE offset) and authored guardrail runs from committed data only."""
    from roads import meshing as M
    from roads import pipeline
    from roads import standards as S
    net, _graph, overrides, _stats = pipeline.build_network(region_id)
    runs = []
    for c in net.chains:
        br = np.asarray(c.bridge, bool)
        if not br.any() or c.meta.get("absorbed"):
            continue
        idx = np.where(br)[0]
        cap = M.bridge_cap_w(c)
        for run in np.split(idx, np.where(np.diff(idx) > 1)[0] + 1):
            if len(run) < 2:
                continue
            s = c.line.s
            for side, sgn in (("L", 1.0), ("R", -1.0)):
                edge = (np.clip(cap - (S.BRIDGE_BARRIER_FACE_M + 0.0), S.BRIDGE_BARRIER_EDGE_MIN_M, S.BRIDGE_BARRIER_EDGE_M)
                        if cap < 1.3 else S.BRIDGE_BARRIER_EDGE_M)
                off = c.hw[run] + S.KERB_TOP_W + cap - edge
                P = c.line.offset_point(s[run], sgn * off)
                pts = np.column_stack([P[:, 0].round(2), P[:, 1].round(2), np.full(len(run), np.nan),
                                       np.ones(len(run))])
                runs.append({"key": f"{c.id}:{side}", "pts": pts, "deck": True})
    for o in overrides:
        if o.get("kind") != "guardrail":
            continue
        q = np.asarray(o.get("polyline_en") or [], float)      # already region-local E/N
        if q.ndim != 2 or len(q) < 2:
            continue
        sq = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(q, axis=0).T))])
        u = np.arange(0.0, sq[-1], 1.0)
        P = np.column_stack([np.interp(u, sq, q[:, 0]), np.interp(u, sq, q[:, 1])])
        pts = np.column_stack([P[:, 0].round(2), P[:, 1].round(2), np.full(len(P), np.nan), np.zeros(len(P))])
        runs.append({"key": f"authored:{o['id']}", "pts": pts, "deck": False})
    return runs


def load_runs(region_id: str):
    """Canonical QA runs when the world was regenerated, else the graph reconstruction."""
    region_dir = REPO / "Data" / "Regions" / region_id
    runs = load_runs_from_qa(region_dir)
    source = "generated/streetscape_qa.json:guardrail_runs"
    if runs is None:
        runs = deck_and_authored_runs(region_id)
        source = "reconstruction from roads.graph.json + overrides.yaml"
    return runs, source


# --------------------------------------------------------------------------------------------- detectors
def _seg_seg_dist(p1, p2, p3, p4):
    d1, d2, r = p2 - p1, p4 - p3, p1 - p3
    a, e_ = d1 @ d1, d2 @ d2
    b, c_, f = d1 @ d2, d1 @ r, d2 @ r
    denom = a * e_ - b * b
    s = np.clip((b * f - c_ * e_) / denom, 0, 1) if denom > 1e-9 else 0.0
    t = np.clip((b * s + f) / e_, 0, 1) if e_ > 1e-9 else 0.0
    return float(np.hypot(*(p1 + d1 * s - (p3 + d2 * t))))


def _polyline(P):
    P = np.asarray(P, float)
    return P[:, :2]


def _common_span(a, b):
    """Length of the span of polyline b projected onto the axis of polyline a, inside a's extent."""
    A, B = _polyline(a), _polyline(b)
    sa = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(A, axis=0).T))])
    if sa[-1] < 1e-9:
        return 0.0
    u = (A[-1] - A[0]) / sa[-1]
    t = (B - A[0]) @ u
    return float(min(t.max(), sa[-1]) - max(t.min(), 0.0))


def _parallel(A, B, angle_deg):
    a = A[-1] - A[0]
    b = B[-1] - B[0]
    na, nb = np.hypot(*a), np.hypot(*b)
    if na < 1e-9 or nb < 1e-9:
        return False
    return abs(float(a @ b) / (na * nb)) >= np.cos(np.radians(angle_deg))


def _densify(P, step=0.25):
    P = _polyline(P)
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    if s[-1] < 1e-9:
        return P
    u = np.arange(0.0, s[-1], step)
    return np.column_stack([np.interp(u, s, P[:, 0]), np.interp(u, s, P[:, 1])])


def find_overlapping_rows(rows, max_gap_m=OVERLAP_GAP_M, min_common_m=OVERLAP_COMMON_M,
                          angle_deg=OVERLAP_ANGLE_DEG, join_zone_m=0.0):
    """[{a, b, gap_m, common_m, at}] of row pairs that run parallel (within angle_deg),
    come closer than max_gap_m and share a common span longer than min_common_m.
    join_zone_m: for rail runs, proximity within this of an end of either run is an intended
    join (V / Y at a nose, ADR 0123), not an overlap - excluded from the gap test."""
    from scipy.spatial import cKDTree
    out = []
    lines = [r["row"] if "row" in r else _polyline(r["pts"]) for r in rows]
    keys = [r.get("road", r.get("key")) + (f" ({r['edge_id']})" if "edge_id" in r else "") for r in rows]
    dense = [_densify(ln) for ln in lines]
    trees = [cKDTree(d) for d in dense]
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            A, B = lines[i], lines[j]
            if not _parallel(A, B, angle_deg):
                continue
            d, _ = trees[j].query(dense[i])
            if join_zone_m > 0:
                sa = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(dense[i], axis=0).T))])
                sb = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(dense[j], axis=0).T))])
                _, kj = trees[j].query(dense[i])
                inner = ((sa > join_zone_m) & (sa < sa[-1] - join_zone_m)
                         & (sb[kj] > join_zone_m) & (sb[kj] < sb[-1] - join_zone_m))
                d = np.where(inner, d, np.inf)
            gap = float(d.min())
            if gap >= max_gap_m:
                continue
            common = _common_span(A, B)
            if common <= min_common_m:
                continue
            p = dense[i][int(np.argmin(d))]
            out.append({"a": keys[i], "b": keys[j], "gap_m": round(gap, 2), "common_m": round(common, 1),
                        "at": [round(float(p[0]), 1), round(float(p[1]), 1)]})
    return out


def find_free_ends(runs, continue_m=FREE_END_CONTINUE_M, dz=FREE_END_DZ):
    """[{key, end, e, n, z}] of deck run ends with no other run end within continue_m (and dz where
    both heights are known) - the gaps at the structure entrances (ADR 0144 pkt 3)."""
    ends = []
    for i, r in enumerate(runs):
        P = np.asarray(r["pts"], float)
        for e in (0, -1):
            ends.append((i, e, P[e]))
    free = []
    for i, r in enumerate(runs):
        P = np.asarray(r["pts"], float)
        for e, name in ((0, "start"), (-1, "end")):
            p = P[e]
            if not (p[3] if len(p) > 3 else 0):
                continue                                    # not a deck point
            cont = False
            for j, e2, q in ends:
                if j == i:
                    continue
                if float(np.hypot(*(q[:2] - p[:2]))) > continue_m:
                    continue
                if len(p) > 3 and len(q) > 3 and np.isfinite(p[2]) and np.isfinite(q[2]) and abs(q[2] - p[2]) > dz:
                    continue
                cont = True
                break
            if not cont:
                # ADR 0159: an end led ONTO the body of another rail (the dedup cut + join of two decks that merge:
                # c:w177895177 L at E 669.4 N -781.9, c:w240542867 R at E -739.6 N 74.1) carries on along that rail -
                # it is not an end in the air although no run END is near
                for j, r2 in enumerate(runs):
                    if j == i:
                        continue
                    Q = np.asarray(r2["pts"], float)
                    dd = np.hypot(Q[:, 0] - p[0], Q[:, 1] - p[1])
                    k = int(np.argmin(dd))
                    if dd[k] > FREE_END_ON_RAIL_M:
                        continue
                    if Q.shape[1] > 3 and np.isfinite(p[2]) and np.isfinite(Q[k, 2]) and abs(Q[k, 2] - p[2]) > dz:
                        continue
                    cont = True
                    break
            if not cont:
                z = float(p[2]) if len(p) > 3 and np.isfinite(p[2]) else None
                free.append({"key": r["key"], "end": name,
                             "e": round(float(p[0]), 1), "n": round(float(p[1]), 1),
                             "z": None if z is None else round(z, 2)})
    return free


# --------------------------------------------------------------------------------------------- report
def analyze_region(region_id: str) -> dict:
    runs, run_source = load_runs(region_id)
    free = find_free_ends(runs)
    overlaps = find_overlapping_rows([{"key": r["key"], "pts": r["pts"]} for r in runs], join_zone_m=12.0)
    return {"region": region_id, "run_source": run_source, "runs": len(runs),
            "deck_run_ends_free": len(free), "free_ends": free,
            "rail_row_overlaps": len(overlaps), "rail_overlaps": overlaps,
            }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", default="bialystok-industrial-c")
    a = ap.parse_args()
    rep = analyze_region(a.region)
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    sys.exit(main())
