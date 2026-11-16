"""Writes the measured carriageway-width overrides of the DK19 route tiles (ADR 0278 tiles 5-7, method of ADR 0272).

Input: the ortho_xsec station files under artifacts/dk19-tiles-s23/xsec/ (GUGiK orthophoto WMS, numbers only) and the
road graphs. For every GROUP (street, tile, way filter) the override targets every one-way 2-lane way of the street
whose graph width equals `graph_w`; the reason text carries the station count and medians of the measured ways
(dk19_xsec_summary rules). Ways crossing a seam with a locked built tile are left out (the neighbour keeps the BDOT width).

  uv run --project tools/worldgen python tools/worldgen/qa/dk19_xsec_overrides.py          # prints the yaml entries
  uv run --project tools/worldgen python tools/worldgen/qa/dk19_xsec_overrides.py --write  # rewrites overrides.yaml
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
XS = REPO / "artifacts" / "dk19-tiles-s23" / "xsec"
PLAUSIBLE, WINDOW = (5.0, 16.0), 13.9
SET = {"lanes": 2, "lane_width": 3.5, "edge_strip": 0.5}       # 8.0 m between kerbs
GROUPS = [
    {"id": "dk19-piastowska-70-carriageway-width", "tile": "bialystok-bojary", "street": "Piastowska", "graph_w": 7.0,
     "ref": "19", "skip": (), "files": ("bojary40.json", "bojary40b.json"),
     "where": "DK19 Piastowska, the two one-way carriageways of the 70 km/h section north of the 50 km/h zone"},
    {"id": "dk19-branickiego-carriageway-width", "tile": "bialystok-mickiewicza", "street": "Jana Klemensa Branickiego",
     "graph_w": 7.0, "ref": "19", "skip": (), "files": ("mickiewicza40.json", "mickiewicza40b.json"),
     "where": "DK19 Branickiego between pl. Antonowicza and rondo Meyera, both one-way carriageways (ref 19 only; the 8 t part NW of the square is not touched)"},
    {"id": "dw678-ciolkowskiego-carriageway-width", "tile": "bialystok-mickiewicza", "street": "Konstantego Ciołkowskiego",
     "graph_w": 7.0, "ref": "678", "skip": (279881972, 279876738), "files": ("mickiewicza40.json", "mickiewicza40b.json"),
     "where": "DW678 Ciolkowskiego from rondo Meyera towards Dojlidy, both one-way carriageways; the two ways crossing the south seam (279881972, 279876738) keep the BDOT width of the locked neighbour bialystok-dojlidy (7.0 m) so the seam has one width"},
]


# Hand-written entries (seam bialystok-bojary | bialystok-mickiewicza on DK19 Piastowska, y = 593151). Stations:
# artifacts/dk19-tiles-s23/xsec/{boj_seam,mick_seam}.json (ortho_xsec, step 10 / 6 m).
SEAM = {
    "bialystok-bojary": [
        "  - id: dk19-piastowska-seam-s-widening\n"
        "    target: {osm_way: [1329465432]}\n"
        "    reason: >-\n"
        "      DK19 Piastowska southbound, last 79 m before the south seam with bialystok-mickiewicza: the carriageway\n"
        "      widens from 2 lanes to the 4-lane approach of the junction that lies in the next tile (OSM way 440321719,\n"
        "      lanes=4). GUGiK orthophoto WMS cross-sections (ortho_xsec, step 10 m): asphalt run 9.05 m at s = 25 m,\n"
        "      10.90 m at 35 m, 13.45 m at 45 m; the 4-lane way behind the seam 13.60-14.15 m (2 stations). Without the\n"
        "      profile this tile ends 8.0 m wide and the neighbour starts mid-transition (qa/seams.py: 8.00 | 10.82 m).\n"
        "      Profile t = 0..1 along the edge (north to the seam): 8.0 m to t 0.25, 13.6 m at t 0.63, 14.0 m at the seam.\n"
        "    confidence: medium\n"
        "    verify: tools/worldgen/qa/seams.py row w1329465432 (both tiles equal on the seam)\n"
        "    set: {width: [[0.0, 8.0], [0.25, 8.0], [0.63, 13.6], [1.0, 14.0]]}\n",
        "  - id: dk19-piastowska-seam-n-transition\n"
        "    target: {osm_way: [440321721]}\n"
        "    reason: >-\n"
        "      DK19 Piastowska northbound, first 65 m after the south seam (3 lanes, BDOT rule 9.5 m): the neighbour\n"
        "      bialystok-mickiewicza is still inside its 15 m width transition from the 2-lane way before (8.0 m) on the\n"
        "      seam (qa/seams.py: 9.50 | 9.04 m). The profile continues that transition here (t = 0 at the seam; 8.9 m gives 9.04 m after the 15 m smoothing). The\n"
        "      orthophoto run at s = 25 m is 10.3 m (one station, bus bay beside it): width itself not changed.\n"
        "    confidence: low\n"
        "    verify: tools/worldgen/qa/seams.py row w440321721\n"
        "    set: {width: [[0.0, 8.9], [0.15, 9.5], [1.0, 9.5]]}\n",
    ],
    "bialystok-mickiewicza": [
        "  - id: dk19-piastowska-seam-s-approach-width\n"
        "    target: {osm_way: [1329465432, 440321719, 564770249]}\n"
        "    reason: >-\n"
        "      DK19 Piastowska southbound from the north seam with bialystok-bojary: 4-lane approach (OSM lanes=4,\n"
        "      left|through|through|right; way 1329465432 is its 1.3 m stub inside this tile). BDOT10k gives 8.0 m (rejected\n"
        "      by the generator, standard 4 x 3.5 + 0.5 = 14.5 m). GUGiK orthophoto WMS cross-sections (ortho_xsec, step\n"
        "      6 m, 2 usable stations on way 440321719): asphalt run 13.60 and 14.15 m incl. the kerb line. Set to 14.0 m\n"
        "      (WORKING_VALUE inside the measured range) = the width bialystok-bojary reaches on the seam\n"
        "      (dk19-piastowska-seam-s-widening).\n"
        "    confidence: medium\n"
        "    verify: tools/worldgen/qa/seams.py row w1329465432\n"
        "    set: {width: 14.0}\n",
    ],
}


def entries() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {t: list(v) for t, v in SEAM.items()}
    for G in GROUPS:
        g = json.loads((REPO / "Data" / "Regions" / G["tile"] / "roads.graph.json").read_text(encoding="utf-8"))
        ways = set()
        for e in g["edges"]:
            a = {k: d.get("v") for k, d in e["attrs"].items()}
            if (a.get("name") == G["street"] and a.get("lanes") == 2 and a.get("oneway") == "yes" and a.get("width") == G["graph_w"]
                    and a.get("ref") == G["ref"] and e["osm_way"] not in G["skip"]):
                ways.add(e["osm_way"])
        rows = [r for f in G["files"] for r in json.loads((XS / f).read_text(encoding="utf-8")) if r["way"] in ways]
        per, both = {}, []
        for r in rows:
            if PLAUSIBLE[0] <= r["asphalt_w"] <= PLAUSIBLE[1] and r["asphalt_L"] < WINDOW and r["asphalt_R"] > -WINDOW:
                per.setdefault(r["way"], []).append(r["asphalt_w"])
                lf, rt = [v for v in r["lines"] if v > 2.4], [v for v in r["lines"] if v < -2.4]
                if lf and rt:
                    both.append(round(min(lf) - max(rt), 2))      # innermost bright line either side of the axis
        allw = sorted(w for v in per.values() for w in v)
        med = statistics.median(allw)
        q1, q3 = allw[len(allw) // 4], allw[(3 * len(allw)) // 4]
        txt = (f"  - id: {G['id']}\n"
               f"    target: {{osm_way: [{', '.join(str(w) for w in sorted(ways))}]}}\n"
               f"    reason: >-\n"
               f"      {G['where']}. BDOT10k gives {G['graph_w']:.1f} m per carriageway.\n"
               f"      GUGiK orthophoto WMS cross-sections (tools/worldgen/qa/ortho_xsec.py, step 40 m, ADR 0272):\n"
               f"      {len(allw)} usable stations on {len(per)} of the {len(ways)} ways, asphalt run incl. the kerb line median\n"
               f"      {med:.2f} m (quartiles {q1:.2f}-{q3:.2f} m, reading +-0.3 m); innermost bright lines left and right of the\n"
               f"      axis {statistics.median(both):.2f} m apart (median of {len(both)} stations). Set to 2 x 3.50 m + 2 x 0.50 m = 8.00 m between kerbs (WORKING_VALUE inside the measured range,\n"
               f"      kerbstones not resolved at the WMS resolution). Lanes = OSM lanes=2. Turn-pocket ways (3-4 lanes) keep\n"
               f"      the generator rule. Stations: artifacts/dk19-tiles-s23/xsec/*40*.json.\n"
               f"    confidence: medium\n"
               f"    verify: owner drive or a street-level photo of the section (Panoramax returned 0 photos on 2026-11-16)\n"
               f"    set: {{lanes: {SET['lanes']}, lane_width: {SET['lane_width']}, edge_strip: {SET['edge_strip']}}}\n")
        out.setdefault(G["tile"], []).append(txt)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    for tile, ents in entries().items():
        p = REPO / "Data" / "Regions" / tile / "overrides.yaml"
        head = "".join(ln for ln in p.read_text(encoding="utf-8").splitlines(keepends=True) if ln.startswith("#"))
        text = head + "overrides:\n" + "".join(ents)
        print(f"# {tile}\n{text}")
        if a.write:
            p.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
