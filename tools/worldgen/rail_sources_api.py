"""ADR 0223: rail_sources.json of a tile from OSM API 0.6 XML cut-outs (instead of the pbf snapshot).

Why: the rail stage (ADR 0217) normally extracts `railway=*` from the Geofabrik pbf in Data/raw (build_region.py).
The cloud agents have no Data/raw, so the line-38 tiles (dk65-01..04, dw671-tykocin-01) were cut from the live
OSM API in small requests (tile + 200 m `/map?bbox=`, `/way/<id>/full` of the rail ways, `/relation/<id>` of the line)
and written in the SAME schema (`truck-sim-pl/rail-sources/1`, `osm` block byte-compatible with extract_osm). A later
`build_region.py --region <id>` (pbf canonical) overwrites the file with the pbf extract - the `osm` block must stay
the same unless OSM was edited between the pbf snapshot and the API retrieval (diff it; ADR 0223 "Odtworzenie").

Raw XML stays out of git: Data/raw/osm_api/<file>.osm (sha256 + URL + time in the source manifest
Data/SourceManifests/osm-api-0.6-rail-l38.json). No bulk querying: one request per tile + one per rail way, with a
pause; generic User-Agent.

  uv run --project tools/worldgen tools/worldgen/rail_sources_api.py --region dk65-01 [--fetch]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import yaml  # noqa: E402

from streetscape import rail as RL  # noqa: E402

REPO = HERE.parents[1]
RAW = REPO / "Data" / "raw" / "osm_api"
MANIFEST = REPO / "Data" / "SourceManifests" / "osm-api-0.6-rail-l38.json"
API = "https://api.openstreetmap.org/api/0.6"
UA = "osm-research-client/1.0"
FETCH_MARGIN_M = 200.0
# OSM ways of railway line 38 (route=railway ref=38, relation 2316318) that cross the enabled tiles; full geometry
# so a long segment crossing a tile corner is never cut short by the /map bbox.
LINE38_RELATION = 2316318
LINE38_WAYS = (41533341, 166369632, 173466803, 406675496)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tile_bbox_wgs84(bb: dict, margin=FETCH_MARGIN_M):
    from pyproj import Transformer
    tr = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    pts = [tr.transform(x, y) for x in (bb["xmin"] - margin, bb["xmax"] + margin)
           for y in (bb["ymin"] - margin, bb["ymax"] + margin)]
    return [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)]


def files_for(region_id: str, bb: dict) -> list[tuple[Path, str]]:
    lo = tile_bbox_wgs84(bb)
    out = [(RAW / f"{region_id}.osm", f"{API}/map?bbox=" + ",".join(f"{v:.6f}" for v in lo))]
    out += [(RAW / f"way_{w}.osm", f"{API}/way/{w}/full") for w in LINE38_WAYS]
    out.append((RAW / f"relation_{LINE38_RELATION}.osm", f"{API}/relation/{LINE38_RELATION}"))
    return out


def fetch(path: Path, url: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    for a in range(4):
        r = subprocess.run(["curl", "-sS", "-f", "-A", UA, "-o", str(path), url])
        if r.returncode == 0:
            break
        time.sleep(2 ** (a + 1))
    else:
        raise RuntimeError(f"download failed: {url}")
    time.sleep(1.5)


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}


def build(region_id: str, do_fetch=False) -> dict:
    ry = yaml.safe_load((REPO / "Data" / "Regions" / region_id / "region.yaml").read_text(encoding="utf-8"))
    bb = ry["bbox"]
    files = files_for(region_id, bb)
    man = manifest().get("files", {})
    used = []
    for p, url in files:
        if not p.exists():
            if not do_fetch:
                raise SystemExit(f"{p} missing - run with --fetch (or copy the cut-out listed in {MANIFEST.name})")
            fetch(p, url)
        rec = man.get(p.name)
        if rec and rec["sha256"] != sha256(p):
            print(f"[rail_sources_api] WARNING {p.name}: sha256 differs from the manifest (newer OSM state)")
        used.append({"file": p.name, "url": url, "sha256": sha256(p),
                     "retrieved_utc": (rec or {}).get("retrieved_utc")})
    xml = [p for p, _ in files if p.name.endswith(".osm") and not p.name.startswith("relation_")]
    bbox = (bb["xmin"], bb["ymin"], bb["xmax"], bb["ymax"])
    return {"schema": RL.SCHEMA, "crs": "EPSG:2180", "bbox": list(bbox), "margin_m": 100.0,
            "license": {"osm": "ODbL 1.0, © OpenStreetMap contributors"},
            "provenance": {"source": "osm-api-0.6", "manifest": f"Data/SourceManifests/{MANIFEST.name}",
                           "route_relation": f"osm:relation/{LINE38_RELATION} (route=railway ref=38)",
                           "files": used, "adr": "0223"},
            "osm": RL.extract_osm_xml(bbox, xml)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True, action="append")
    ap.add_argument("--fetch", action="store_true", help="download missing cut-outs from the OSM API 0.6")
    a = ap.parse_args()
    for rid in a.region:
        data = build(rid, a.fetch)
        p = RL.write(rid, data)
        print(f"[rail_sources_api] {rid}: {len(data['osm']['ways'])} way parts, {len(data['osm']['nodes'])} nodes "
              f"-> {p.relative_to(REPO)}")


if __name__ == "__main__":
    main()
