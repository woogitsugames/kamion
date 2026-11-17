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
  ground shoulder 1.25 m beside a pas awaryjny.
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
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
REGIONS = REPO / "Data" / "Regions"
TILES = ("s8-01", "s8-02", "s8-03", "s8-04", "s8-05")
BEGIN = "  # ---- BEGIN generated: tools/worldgen/qa/s8_xsec_overrides.py (ADR 0288) - do not edit between the markers ----"
END = "  # ---- END generated: tools/worldgen/qa/s8_xsec_overrides.py ----"

INNER_STRIP_M = 0.20        # WORKING_VALUE: median edge of the carriageway to the inner edge line axis
LANE_M = 3.50               # PTB2022 § 17 ust. 1 (class S)
OUTER_PAVED_M = 2.75        # PTB2022 § 23 ust. 6 (2.50 m) + 0.25 m to the line axis (WORKING_VALUE)
GROUND_SHOULDER_M = 1.25    # PTB2022 § 23 ust. 10 pkt 1
LANE_AXIS_LEFT_M = 0.25     # WORKING_VALUE: centre of the two through lanes left of the OSM way (QA row 78)


def section(lanes: int) -> tuple[list[float], float, float]:
    """(lane_edges, width, center_offset) of a carriageway with `lanes` lanes (>= 2); offsets positive = left."""
    le = [round(INNER_STRIP_M + LANE_M * i, 2) for i in range(lanes + 1)]
    width = round(le[-1] + OUTER_PAVED_M, 2)
    through_axis = INNER_STRIP_M + LANE_M              # centre of lanes 1-2, from the median edge
    return le, width, round(LANE_AXIS_LEFT_M - (width / 2.0 - through_axis), 3)


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
        le, width, off = section(n)
        rows += [
            f"  - id: s8-xsec-w{way}",
            f"    target: {{osm_way: {way}}}",
            f"    reason: \"S8 carriageway, {n} lanes (OSM): class S section instead of the class A rule centred on the "
            f"OSM way - see tools/worldgen/qa/s8_xsec_overrides.py (QA 2026-11-16 rows 78, 81, 82; PTB2022 § 17, § 23).\"",
            "    confidence: medium (widths: orthophoto +-0.3 m at 3 stations; lateral position: WORKING_VALUE)",
            "    verify: orthophoto cross-section per way (tools/worldgen/qa/ortho_xsec.py) / owner drive",
            f"    set: {{lane_edges: {le}, width: {width}, center_offset: {off}, "
            f"shoulder_right: {{kind: ground, paved_m: 0.05, ground_m: {GROUND_SHOULDER_M}}}}}",
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
    if a.check and stale:
        print("STALE:", stale)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
