"""ADR 0222: OSM probe for roadside tree rows of the DK65 / Knyszyn tiles (OSM API 0.6, live).

The Geofabrik snapshot used by streetscape.sources (podlaskie-261108) has almost no natural=tree_row / natural=tree on
the DK65 corridor, so this probe asks the live OSM API 0.6 (`/api/0.6/map?bbox=` of each tile bbox from region.yaml)
for the same keys plus the cut features of the tree-row rule:
  natural=tree_row (ways), natural=tree (nodes)          - row / point sources
  highway=track (ways touching the tile)                 - field / forest accesses (zjazdy) not in roads.graph.json
  tunnel=culvert or culvert=yes on waterway (ways)       - culverts under a road (no tree over the culvert head)
  railway=level_crossing (nodes)                         - level crossings
Writes Data/Regions/<id>/tree_rows_osm.json (small, committed; ODbL 1.0, © OpenStreetMap contributors).

    uv run --project tools/worldgen python tools/worldgen/streetscape/tree_rows_probe.py [--region dk65-05 ...]
"""

from __future__ import annotations

import argparse
import datetime
import json
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests
import yaml
from pyproj import Transformer

REPO = Path(__file__).resolve().parents[3]
TILES = [f"dk65-{i:02d}" for i in range(1, 12)] + ["knyszyn", "knyszyn-s", "knyszyn-w"]
SCHEMA = "truck-sim-pl/tree-rows-osm/1"
UA = {"User-Agent": "osm-research-client/1.0"}


def _get(url):
    r = None
    for k in range(5):
        try:
            r = requests.get(url, headers=UA, timeout=180)
            if r.status_code == 200:
                return r
        except requests.RequestException as e:      # proxy resets: retry 2/4/8/16 s
            print("retry", k, e)
        time.sleep(2 ** (k + 1))
    raise RuntimeError(f"OSM API failed: {url} ({r.status_code if r is not None else 'no response'})")


def probe(rid: str) -> dict:
    bb = yaml.safe_load((REPO / "Data" / "Regions" / rid / "region.yaml").read_text(encoding="utf-8"))["bbox"]
    to_ll = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    to_xy = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
    lon, lat = to_ll.transform([bb["xmin"], bb["xmax"], bb["xmin"], bb["xmax"]], [bb["ymin"], bb["ymin"], bb["ymax"], bb["ymax"]])
    q = f"{min(lon):.6f},{min(lat):.6f},{max(lon):.6f},{max(lat):.6f}"
    url = f"https://api.openstreetmap.org/api/0.6/map?bbox={q}"
    r = _get(url)
    root = ET.fromstring(r.content)
    nodes = {}
    for n in root.iter("node"):
        x, y = to_xy.transform(float(n.get("lon")), float(n.get("lat")))
        nodes[n.get("id")] = (round(x, 2), round(y, 2), {g.get("k"): g.get("v") for g in n.findall("tag")})

    def inside(x, y):
        return bb["xmin"] <= x <= bb["xmax"] and bb["ymin"] <= y <= bb["ymax"]

    out = {"tree_row": [], "tree": [], "track": [], "culvert": [], "level_crossing": []}
    for nid, (x, y, tg) in sorted(nodes.items(), key=lambda kv: int(kv[0])):
        if not inside(x, y):
            continue
        if tg.get("natural") == "tree":
            out["tree"].append({"osm_node": int(nid), "xy_epsg2180": [x, y], "tags": tg})
        if tg.get("railway") == "level_crossing":
            out["level_crossing"].append({"osm_node": int(nid), "xy_epsg2180": [x, y], "tags": tg})
    for w in root.iter("way"):
        tg = {g.get("k"): g.get("v") for g in w.findall("tag")}
        pts = [list(nodes[nd.get("ref")][:2]) for nd in w.findall("nd") if nd.get("ref") in nodes]
        if len(pts) < 2:
            continue
        rec = {"osm_way": int(w.get("id")), "version": int(w.get("version")), "timestamp": w.get("timestamp"),
               "tags": tg, "line_epsg2180": pts}
        if tg.get("natural") == "tree_row":
            out["tree_row"].append(rec)
        elif tg.get("highway") == "track":
            out["track"].append(rec)
        elif "waterway" in tg and (tg.get("tunnel") == "culvert" or tg.get("culvert") == "yes"):
            out["culvert"].append(rec)
    for k in ("tree_row", "track", "culvert"):
        out[k].sort(key=lambda o: o["osm_way"])
    return {"schema": SCHEMA, "region": rid, "source": url, "api": "OpenStreetMap API 0.6 /map (live)",
            "license": "ODbL 1.0", "attribution": "© OpenStreetMap contributors",
            "fetched_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            "bbox_epsg2180": [bb["xmin"], bb["ymin"], bb["xmax"], bb["ymax"]], "bbox_wgs84": q,
            "response_bytes": len(r.content), **out}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", nargs="*", default=TILES)
    a = ap.parse_args()
    for rid in a.region:
        d = probe(rid)
        p = REPO / "Data" / "Regions" / rid / "tree_rows_osm.json"
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(rid, {k: len(d[k]) for k in ("tree_row", "tree", "track", "culvert", "level_crossing")}, flush=True)
        time.sleep(1.5)


if __name__ == "__main__":
    main()
