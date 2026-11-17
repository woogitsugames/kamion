"""ADR 0288: authored cross-section of the S8 carriageways in the loop tiles, written as overrides (one per OSM way).

    uv run --project tools/worldgen python tools/worldgen/qa/s8_xsec_overrides.py            # rewrite the blocks
    uv run --project tools/worldgen python tools/worldgen/qa/s8_xsec_overrides.py --check    # exit 1 when stale

Why: the class rule builds `highway=motorway` as class A centred on the OSM way (2 x 3.75 m + 2 x 0.75 m, 1.00 m paved
shoulder). The S8 is an expressway (class S) and each OSM way is drawn along the two THROUGH lanes, so the rule left a
~2.6 m gap between the carriageways, no emergency lane and, where a third lane is tagged, two 12 m carriageways whose
axes are ~12.1 m apart (they touched: deck kerbs of one bridge stood in the lane of the other, s8-01).

Numbers (docs/reports/QA-2026-11-16-mistral-s8.md, GUGiK orthophoto WMS, +-0.3 m; everything else WORKING_VALUE):
  asphalt of a 2-lane carriageway 10.35-10.65 m (rows 81, 82); inner strip ~0.5 m (row 82); gap between the inner edge
  lines 3.8-4.85 m, median ~4.5 m, gap between the asphalt edges 3.45-4.0 m (row 78); steel barrier in the median.
  PTB2022 (Dz.U. 2022 poz. 1518) § 17 ust. 1: lane 3.50 m on S; § 23 ust. 6: pas awaryjny S 2.50 m; § 23 ust. 10 pkt 1:
  ground shoulder 1.25 m (>= 0.75 m) beside a pas awaryjny.
Edge lines P-7b on both sides (`edge_lines: both`: a section with lane_edges paints only what the override names).
No ditch in the rule profile (`ditch_m: 0`, WORKING_VALUE): the 0.60 m rule ditch reached 10 m from the way and cut
half of the noise screens out (s8-01: 733 m -> 380 m).
Section, from the median edge in the direction of travel (`lane_edges`): 0.20 m strip, n x 3.50 m lanes, 2.75 m paved
(2.50 m pas awaryjny + 0.25 m to the line axis) -> carriageway 9.95 m (n = 2); the median side adds the generator's
0.50 m paved strip (standards.PAVED_SHOULDER_MEDIAN) = 10.45 m of asphalt. The centre of the two through lanes lies
LANE_AXIS_LEFT_M left of the OSM way (towards the median): with the measured axis spacing of 12.12-12.52 m (s8-02 /
s8-04, OSM) the inner edge lines are 4.6-5.0 m apart and the asphalt edges 3.2-3.6 m. A third lane (acceleration /
deceleration, OSM lanes=3) is added on the OUTSIDE: the through lanes do not move.
The entries live between the BEGIN / END markers of Data/Regions/<tile>/overrides.yaml; anything outside the markers is
kept (hand-written overrides). Input: Data/Regions/<tile>/roads.graph.json (git). Standard library only.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
REGIONS = REPO / "Data" / "Regions"
# dk65-01 (ADR 0205, main): the S8 cuts its south-west corner; same section, or the carriageways step sideways by
# 1.0-2.8 m on the seam with s8-01 (qa.seams: "droga urywa sie na szwie")
TILES = ("s8-01", "s8-02", "s8-03", "s8-04", "s8-05", "dk65-01")
BEGIN = "  # ---- BEGIN generated: tools/worldgen/qa/s8_xsec_overrides.py (ADR 0288) - do not edit between the markers ----"
END = "  # ---- END generated: tools/worldgen/qa/s8_xsec_overrides.py ----"

INNER_STRIP_M = 0.20        # WORKING_VALUE: median edge of the carriageway to the inner edge line axis
LANE_M = 3.50               # PTB2022 § 17 ust. 1 (class S)
OUTER_PAVED_M = 2.75        # PTB2022 § 23 ust. 6 (2.50 m) + 0.25 m to the line axis (WORKING_VALUE)
GROUND_SHOULDER_M = 1.00    # PTB2022 § 23 ust. 10 pkt 1: 1.25 m, >= 0.75 m; 1.00 m + a flat verge (ditch_m: 0) keeps the
#                             noise screens, 7.5-9.0 m from the OSM way (BDOT10k OT_OIKM_L / OSM, s8-01 and s8-03), outside the profile
LANE_AXIS_LEFT_M = 0.25     # WORKING_VALUE: centre of the two through lanes left of the OSM way (QA row 78)
# s24: per-way extra shift towards the median so that the gap between the inner edge lines comes out at the measured
# median (QA row 78: 3.8-4.85 m, median ~4.5 m, 8 orthophoto stations) instead of axis spacing - 7.5 m (s8-04: 12.48 m
# -> 4.98 m). The spacing is the p50 distance from the way to the nearest opposite-direction S8 carriageway, sampled
# every ~10 m over ALL tiles of TILES (one value per way, so a way crossing a seam gets the same offset on both sides).
MEDIAN_GAP_TARGET_M = 4.50  # QA 2026-11-16 row 78 (median of the gap between the inner edge lines)
EXTRA_MAX_M = 0.50          # WORKING_VALUE: cap of the extra shift (OSM way position error ~0.5 m)
JOINT_SPACING_MAX_M = 13.0  # wider p50 spacing = carriageways on separate structures / diverging at a junction:
#                             no measurement there, keep LANE_AXIS_LEFT_M (ADR 0288 Otwarte 3)
SAMPLE_M = 10.0
PAIR_SEARCH_M = 25.0


def section(lanes: int, extra: float = 0.0) -> tuple[list[float], float, float]:
    """(lane_edges, width, center_offset) of a carriageway with `lanes` lanes (>= 2); offsets positive = left.
    `extra`: additional shift of the whole carriageway towards the median (median_extra)."""
    le = [round(INNER_STRIP_M + LANE_M * i, 2) for i in range(lanes + 1)]
    width = round(le[-1] + OUTER_PAVED_M, 2)
    through_axis = INNER_STRIP_M + LANE_M              # centre of lanes 1-2, from the median edge
    return le, width, round(LANE_AXIS_LEFT_M + extra - (width / 2.0 - through_axis), 3)


def _segments() -> list[tuple[int, tuple[float, float], tuple[float, float]]]:
    out = []
    for t in TILES:
        g = json.loads((REGIONS / t / "roads.graph.json").read_text(encoding="utf-8"))
        for e in g["edges"]:
            a = e["attrs"]
            if a["highway"]["v"] != "motorway" or "S8" not in str((a.get("ref") or {}).get("v") or ""):
                continue
            geo = e["geometry"]
            geo = json.loads(geo) if isinstance(geo, str) else geo
            out += [(int(e["osm_way"]), tuple(p), tuple(q)) for p, q in zip(geo, geo[1:]) if math.dist(p, q) >= 1.0]
    return out


def _pt_seg(x: float, y: float, p, q) -> float:
    dx, dy = q[0] - p[0], q[1] - p[1]
    u = max(0.0, min(1.0, ((x - p[0]) * dx + (y - p[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - (p[0] + u * dx), y - (p[1] + u * dy))


_SPACING: dict[int, float] | None = None


def spacing() -> dict[int, float]:
    """p50 distance (m) from each S8 way to the nearest opposite-direction S8 carriageway (OSM axes), over all TILES."""
    global _SPACING
    if _SPACING is None:
        segs = _segments()
        d: dict[int, list[float]] = {}
        for w, p, q in segs:
            L = math.dist(p, q)
            hx, hy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
            k = max(1, int(L // SAMPLE_M))
            for i in range(k):
                x, y = p[0] + hx * L * (i + 0.5) / k, p[1] + hy * L * (i + 0.5) / k
                best = PAIR_SEARCH_M
                for w2, p2, q2 in segs:
                    if w2 == w:
                        continue
                    L2 = math.dist(p2, q2)
                    if ((q2[0] - p2[0]) * hx + (q2[1] - p2[1]) * hy) / L2 > -0.9:   # same direction / crossing
                        continue
                    best = min(best, _pt_seg(x, y, p2, q2))
                if best < PAIR_SEARCH_M:
                    d.setdefault(w, []).append(best)
        _SPACING = {w: round(statistics.median(v), 2) for w, v in d.items()}
    return _SPACING


def median_extra(way: int) -> float:
    """Extra shift towards the median (m, multiple of 0.05, 0..EXTRA_MAX_M) so that the inner edge lines come out
    MEDIAN_GAP_TARGET_M apart: gap = spacing - 2 x (LANE_AXIS_LEFT_M + LANE_M + extra), both carriageways alike."""
    s = spacing().get(way)
    if s is None or s > JOINT_SPACING_MAX_M:
        return 0.0
    e = (s - 2.0 * (LANE_AXIS_LEFT_M + LANE_M) - MEDIAN_GAP_TARGET_M) / 2.0
    return round(min(EXTRA_MAX_M, max(0.0, round(e / 0.05) * 0.05)), 2)


def ways(tile: str) -> list[tuple[int, int]]:
    g = json.loads((REGIONS / tile / "roads.graph.json").read_text(encoding="utf-8"))
    out = {}
    for e in g["edges"]:
        a = e["attrs"]
        if a["highway"]["v"] != "motorway" or "S8" not in str((a.get("ref") or {}).get("v") or ""):
            continue
        n = int((a.get("lanes") or {}).get("v") or 2)
        if n >= 2:
            out[int(e["osm_way"])] = n
    return sorted(out.items())


def block(tile: str) -> str:
    rows = [BEGIN]
    for way, n in ways(tile):
        ex = median_extra(way)
        le, width, off = section(n, ex)
        rows += [
            f"  - id: s8-xsec-w{way}",
            f"    target: {{osm_way: {way}}}",
            f"    reason: \"S8 carriageway, {n} lanes (OSM): class S section instead of the class A rule centred on the "
            f"OSM way - see tools/worldgen/qa/s8_xsec_overrides.py (QA 2026-11-16 rows 78, 81, 82; PTB2022 § 17, § 23). "
            f"Axis spacing p50 {spacing().get(way, 0.0):.2f} m, extra shift to the median {ex:.2f} m.\"",
            "    confidence: \"medium (widths - orthophoto +-0.3 m at 3 stations; lateral position - WORKING_VALUE)\"",
            "    verify: orthophoto cross-section per way (tools/worldgen/qa/ortho_xsec.py) / owner drive",
            f"    set: {{lane_edges: {le}, width: {width}, center_offset: {off}, edge_lines: both, "
            f"shoulder_right: {{kind: ground, paved_m: 0.05, ground_m: {GROUND_SHOULDER_M}, ditch_m: 0}}}}",
        ]
    rows.append(END)
    return "\n".join(rows) + "\n"


def render(tile: str) -> str:
    f = REGIONS / tile / "overrides.yaml"
    text = f.read_text(encoding="utf-8").replace("\r\n", "\n")
    if BEGIN in text:
        head, rest = text.split(BEGIN, 1)
        tail = rest.split(END, 1)[1].lstrip("\n")
        return head + block(tile) + tail
    if "overrides: []" in text:                       # the empty list of a freshly defined tile
        return text.replace("overrides: []", "overrides:\n" + block(tile).rstrip("\n"), 1) + ("" if text.endswith("\n") else "\n")
    return text.rstrip("\n") + "\n" + block(tile)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    stale = []
    for t in TILES:
        f = REGIONS / t / "overrides.yaml"
        new = render(t)
        if new != f.read_text(encoding="utf-8").replace("\r\n", "\n"):
            stale.append(t)
            if not a.check:
                f.write_text(new, encoding="utf-8", newline="\n")
        print(f"{t}: {len(ways(t))} S8 ways, sections {sorted({n: section(n) for _, n in ways(t)}.items())}")
        for w, n in ways(t):
            s, ex = spacing().get(w), median_extra(w)
            gap = None if s is None else round(s - 2.0 * (LANE_AXIS_LEFT_M + LANE_M + ex), 2)
            print(f"  way {w}: lanes {n}, spacing p50 {s}, extra {ex}, inner-line gap (both alike) {gap}")
    if a.check and stale:
        print("STALE:", stale)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
