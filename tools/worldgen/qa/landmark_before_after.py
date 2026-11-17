"""Before / after table of landmark buildings: what the generator builds without and with the knyszyn-look overrides.

  uv run --project tools/worldgen python tools/worldgen/qa/landmark_before_after.py --region knyszyn \
      --out docs/reports/knyszyn-look/before_after_knyszyn.json

"before" = overrides.yaml without the entries whose id starts with `look-` and without overrides.ortho_roofs.json;
"after" = roads.pipeline.load_overrides. Per building: render class, subtype, storeys, wall and roof materials of LOD0.
Also the roof-material histogram of all houses (the palette rule vs the orthophoto).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools/worldgen"))
sys.path.insert(0, str(REPO / "tests/gis"))

import yaml  # noqa: E402

from roads import pipeline  # noqa: E402
from streetscape import buildings_mesh as BM  # noqa: E402
from test_buildings_0167 import _build  # noqa: E402

LANDMARKS = {
    "knyszyn": {
        "kosciol (wlasny generator, ADR 0227)": "bdot:2002917F-8DAE-5C99-E053-CC2BA8C01CFC",
        "poczta": "bdot:2002917F-AB81-5C99-E053-CC2BA8C01CFC",
        "dom narozny Grodzienska/Rynek": "bdot:2002917F-2E17-5C99-E053-CC2BA8C01CFC",
        "biblioteka (BDOT: policja)": "bdot:2002917F-46DA-5C99-E053-CC2BA8C01CFC",
        "Dom Klattow (drewniany, zabytek)": "bdot:2002917F-2F22-5C99-E053-CC2BA8C01CFC",
        "dyskont, Szkolna": "bdot:2002917F-468D-5C99-E053-CC2BA8C01CFC",
        "budynek uslugowy 2 kond., Szkolna": "bdot:e3f1f933-d35e-402b-8880-f5dd66ff45a7",
        "blok 3 kond. przy Szkolnej (pld.)": "bdot:2002917F-46DE-5C99-E053-CC2BA8C01CFC",
        "blok 3 kond. za Szkolna (pln.)": "bdot:2002917F-2F9A-5C99-E053-CC2BA8C01CFC",
        "dom pogrzebowy (Rynek pln.)": "bdot:2002917F-465F-5C99-E053-CC2BA8C01CFC",
        "szkola, budynek glowny": "bdot:2002917F-4818-5C99-E053-CC2BA8C01CFC",
        "szkola, sala": "bdot:2002917F-4819-5C99-E053-CC2BA8C01CFC",
        "bank": "bdot:2002917F-46D9-5C99-E053-CC2BA8C01CFC",
        "remiza OSP": "bdot:3f5a0f0a-0000-0000-0000-79297f75c4a5",
    }
}
ROOFS = ("roof_tiles_red", "roof_tiles_brown", "roof_metal_graphite", "roof_sheet_grey")
SKIP = {"facade_atlas", "plinth_dark", "downpipe", "hall_flashing", "soffit_boards", "chimney_brick", "gutter", "glass",
        "reveal_plaster", "window_frame", "door_wood", "steel_painted", "concrete_step"}


def describe(b):
    buf = _build(b)
    tris = {}
    for p in buf.parts:
        if p.layer == "buildings":
            tris[p.mat] = tris.get(p.mat, 0) + len(p.T)
    roofs = sorted(m for m in tris if m in ROOFS)
    walls = sorted((m for m in tris if m not in ROOFS and m not in SKIP and (m.startswith(("plaster", "wood", "brick",
                    "panel", "hall_wall")))), key=lambda m: -tris[m])
    return {"class": b["typ"], "subtype": b["sub"], "storeys_data": b["props"].get("storeys"),
            "height_m": b["props"].get("height_m"), "walls": walls[:2], "pitched_roof": roofs or None,
            "overrides": sorted(b["ovr"])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    reg = REPO / "Data/Regions" / a.region
    ry = yaml.safe_load((reg / "region.yaml").read_text(encoding="utf-8"))
    origin = (float(ry["origin"]["x"]), float(ry["origin"]["y"]))
    fc = json.loads((reg / "buildings.geojson").read_text(encoding="utf-8"))
    base = [o for o in yaml.safe_load((reg / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
            if not str(o.get("id", "")).startswith("look-")]
    before = {b["id"]: b for b in BM.load(fc, origin, base)}
    after = {b["id"]: b for b in BM.load(fc, origin, pipeline.load_overrides(a.region))}
    pal0, pal1 = BM.house_palette(list(before.values())), BM.house_palette(list(after.values()))
    hist = {"before": {}, "after": {}}
    for bid, b in after.items():
        if b["typ"] != "house":
            continue
        r0, r1 = pal0[bid][1], b["ovr"].get("roof_material", pal1[bid][1])
        hist["before"][r0] = hist["before"].get(r0, 0) + 1
        hist["after"][r1] = hist["after"].get(r1, 0) + 1
    rows = {}
    for name, bid in LANDMARKS.get(a.region, {}).items():
        if bid in before:
            rows[name] = {"id": bid, "before": describe(before[bid]), "after": describe(after[bid])}
    out = {"region": a.region, "house_roofs": hist, "landmarks": rows}
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(hist))
    for n, r in rows.items():
        print(n, "|", r["before"], "->", {k: v for k, v in r["after"].items() if r["before"][k] != v})


if __name__ == "__main__":
    main()
