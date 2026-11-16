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


def entries() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
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
