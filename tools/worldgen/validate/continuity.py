"""Check 2 (M37): continuity of linear features.

  suspicious_gap        two segments of the same source feature (one OSM way / BDOT object split into parts,
                        or neighbouring same-kind features) with a gap < gap_m between their endpoints;
  duplicate_parallel    two distinct linear features running parallel < duplicate_parallel_m apart for
                        >= duplicate_run_m.

Exclusion (per M37): gap findings whose endpoints lie within bridge_end_exempt_m of a bridge deck edge are
skipped - ends of bridge (pomost) barriers are handled by M29 (ADR 0144 open 3: 34 deck barrier ends).

Kerbs are mesh-only (no kerb polylines are committed in git), so kerb continuity is covered by the existing
roads/consistency.py kerb_on_carriageway; this module checks what IS in the data: fences, walls, noise
barriers, retaining walls, tree rows, sidewalks/footways (OSM + BDOT10k + osm_context footways).
"""

from __future__ import annotations

import shapely
from shapely.geometry import Point

from .common import (BRIDGE_END_EXEMPT_M, DUPLICATE_PARALLEL_M, DUPLICATE_RUN_M, GAP_M, Finding, World,
                     bridge_polygons)

LINEAR_KINDS = ("fence", "wall", "retaining_wall", "noise_barrier", "barrier", "sidewalk", "footway")


def _near_deck(w: World, decks, e: float, n: float) -> bool:
    pt = Point(e, n)
    return any(float(d.distance(pt)) <= BRIDGE_END_EXEMPT_M for d in decks)


def check(w: World) -> list[Finding]:
    findings: list[Finding] = []
    lines = [l for l in w.lines if l["kind"] in LINEAR_KINDS and l["line"].length > 0.5]
    decks = bridge_polygons(w)

    # ---- suspicious gaps inside one source feature (segments of the same source_id)
    by_source: dict[str, list[dict]] = {}
    for l in lines:
        by_source.setdefault(l["source_id"] + "|" + l["kind"], []).append(l)
    for key, segs in sorted(by_source.items()):
        if len(segs) < 2:
            continue
        ends = []
        for s in segs:
            cs = list(s["line"].coords)
            ends.append((s, Point(cs[0]), Point(cs[-1])))
        for i in range(len(ends)):
            for j in range(i + 1, len(ends)):
                for pa in (ends[i][1], ends[i][2]):
                    for pb in (ends[j][1], ends[j][2]):
                        d = float(pa.distance(pb))
                        if 0.05 < d < GAP_M:
                            if decks and (_near_deck(w, decks, pa.x, pa.y) or _near_deck(w, decks, pb.x, pb.y)):
                                continue  # M29: barrier ends on pomost decks
                            mx, my = (pa.x + pb.x) / 2, (pa.y + pb.y) / 2
                            findings.append(Finding("suspicious_gap", mx, my,
                                                    f"{ends[i][0]['id']}|{ends[j][0]['id']}",
                                                    f"gap {d:.2f} m between segments of {key} "
                                                    f"(< {GAP_M:.1f} m)", severity="warn",
                                                    extra={"gap_m": round(d, 2), "source": key}))

    # ---- duplicate parallel features (different source ids, any linear kinds)
    if len(lines) >= 2:
        bufs = [l["line"].buffer(DUPLICATE_PARALLEL_M / 2.0) for l in lines]
        tree = shapely.STRtree(bufs)
        pi, ti = tree.query([l["line"] for l in lines], predicate="intersects")
        seen = set()
        for a, b in zip(pi.tolist(), ti.tolist()):
            if a >= b:
                continue
            la, lb = lines[a], lines[b]
            if la["source_id"] == lb["source_id"] and la["kind"] == lb["kind"]:
                continue
            key = (la["id"], lb["id"])
            if key in seen:
                continue
            seen.add(key)
            run = float(la["line"].intersection(bufs[b]).length)
            if run >= DUPLICATE_RUN_M:
                inter = la["line"].intersection(bufs[b])
                c = inter.interpolate(0.5, normalized=True) if not inter.is_empty else la["line"].centroid
                fam_a = "osm" if la["source_id"].startswith("osm:") else "bdot"
                fam_b = "osm" if lb["source_id"].startswith("osm:") else "bdot"
                # cross-source duplicates (OSM way vs BDOT object digitised twice, e.g. wall vs noise
                # barrier) are data-source duplicates, not double geometry - info, not warn
                sev = "warn" if fam_a == fam_b else "info"
                findings.append(Finding("duplicate_parallel", c.x, c.y, f"{la['id']}|{lb['id']}",
                                        f"{la['kind']} and {lb['kind']} run parallel < {DUPLICATE_PARALLEL_M:.2f} m "
                                        f"for {run:.1f} m", severity=sev,
                                        extra={"a": la["id"], "b": lb["id"], "run_m": round(run, 1),
                                               "kind_a": la["kind"], "kind_b": lb["kind"]}))
    return findings
