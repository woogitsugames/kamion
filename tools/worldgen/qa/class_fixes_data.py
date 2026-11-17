"""Building class / roof-shape fixes that follow from the footprint data of a small town -> generated override file.

  uv run --project tools/worldgen python tools/worldgen/qa/class_fixes_data.py --region knyszyn

Output: Data/Regions/<id>/overrides.class_fixes.json (read by roads.pipeline.generated_overrides before overrides.yaml,
so a hand-authored entry for the same building wins). Opt-in per region: run it only for regions where the two rules
below were checked on the orthophoto; other regions keep the class rule of streetscape.buildings_mesh.classify.

Rule A - OSM-only footprints. buildings.geojson takes footprints missing from BDOT10k (2008 here) from OSM with
  function 'yes' and the DEFAULT height 6.0 m (no LoD1). classify() makes them `office` (flat-roofed 6 m boxes):
  in Knyszyn 149 buildings, median 48 m2, 99 under 60 m2 - on the 2025 orthophoto garden sheds, garages and newer
  houses. Fix: under SHED_MAX_M2 -> `gospodarczy` with SHED_H m; SHED_MAX_M2...HOUSE_MAX_M2 -> `dom`; larger: left.
Rule B - pitched roofs of service buildings. typology.roof_shape accepts the LoD2 2017 types 1030 / 1040 / 1070 for
  office / block; a town-centre shop or office in a house-like building is mostly coded 1130 (the commonest house
  type) or 1010 and came out flat although the LoD2 model MEASURES a rise (ridge - eave) of 1.5 m or more.
  Fix: roof_shape gable (1130) / mono (1010) for office / block buildings with that measured rise up to MAX_ROOF_M2.
Status: areas, LoD2 rise = MEASURED from the data in git; SHED_H, the area limits = WORKING_VALUE.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools/worldgen"))

import yaml  # noqa: E402

from streetscape import buildings_mesh as BM  # noqa: E402
from streetscape import typology as TY  # noqa: E402

SHED_MAX_M2 = 60.0
HOUSE_MAX_M2 = 250.0
SHED_H = 3.0
MAX_ROOF_M2 = TY.KAMIENICA_MAX_AREA
SHAPE_1130 = {"1130": "gable", "1010": "mono"}


def fixes(region):
    reg = REPO / "Data/Regions" / region
    ry = yaml.safe_load((reg / "region.yaml").read_text(encoding="utf-8"))
    fc = json.loads((reg / "buildings.geojson").read_text(encoding="utf-8"))
    out, n = [], {"osm_only_shed": 0, "osm_only_house": 0, "pitched_service": 0}
    for b in BM.load(fc, (float(ry["origin"]["x"]), float(ry["origin"]["y"])), []):
        p, a = b["props"], b["poly"].area
        if "#" in b["id"]:
            continue
        if (b["typ"] == "office" and p.get("footprint_source") == "osm" and p.get("height_source") == "default"
                and p.get("function") == "yes"):
            if a < SHED_MAX_M2:
                n["osm_only_shed"] += 1
                out.append({"id": f"class-fix:{b['id']}", "target": {"building": b["id"]}, "confidence": "medium",
                            "reason": f"OSM-only footprint {a:.0f} m2, no function, default height: outbuilding, not an office",
                            "verify": "orthophoto / street-level photo", "set": {"typology": "gospodarczy", "height_m": SHED_H}})
            elif a < HOUSE_MAX_M2:
                n["osm_only_house"] += 1
                out.append({"id": f"class-fix:{b['id']}", "target": {"building": b["id"]}, "confidence": "low",
                            "reason": f"OSM-only footprint {a:.0f} m2, no function, default height: house built after "
                                      "BDOT10k, not an office", "verify": "orthophoto / street-level photo",
                            "set": {"typology": "dom"}})
            continue
        rise = TY.lod2_rise(p)
        shape = SHAPE_1130.get(p.get("roof_type_lod2"))
        if (b["typ"] in ("office", "block") and shape and rise is not None and rise >= TY.ROOF_MIN_RISE_M
                and a <= MAX_ROOF_M2 and not b["poly"].interiors):
            n["pitched_service"] += 1
            out.append({"id": f"class-fix:{b['id']}", "target": {"building": b["id"]}, "confidence": "medium",
                        "reason": f"LoD2 2017 type {p['roof_type_lod2']} with a measured rise of {rise:.1f} m "
                                  f"({p.get('function')}): pitched roof, not flat",
                        "verify": "street-level photo (gable or hip)", "set": {"roof_shape": shape}})
    return sorted(out, key=lambda o: o["id"]), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    a = ap.parse_args()
    ovs, n = fixes(a.region)
    out = {"schema": "truck-sim-pl/overrides-generated/1",
           "generator": "tools/worldgen/qa/class_fixes_data.py (do not edit by hand; hand-authored entries go to "
                        "overrides.yaml and win)",
           "status": "areas and LoD2 rise MEASURED; limits WORKING_VALUE",
           "params": {"shed_max_m2": SHED_MAX_M2, "house_max_m2": HOUSE_MAX_M2, "shed_h_m": SHED_H,
                      "roof_min_rise_m": TY.ROOF_MIN_RISE_M, "max_roof_m2": MAX_ROOF_M2},
           "summary": n, "overrides": ovs}
    p = REPO / "Data/Regions" / a.region / "overrides.class_fixes.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")
    print(a.region, n, "->", p)


if __name__ == "__main__":
    main()
