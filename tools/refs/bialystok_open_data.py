r"""Open spatial data of the City of Białystok (D43, ADR 0066): public ArcGIS Online feature services of
"Urząd Miejski w Białymstoku" (org jN5LJsqeW33UjdlH, https://bialystok.maps.arcgis.com), queried by the route bbox.

Findings (2026-11-10): there is NO public tree inventory / street-lighting / road-sign layer. Useful layers:
parks, squares, nature monuments (single trees), fire stations, CCTV, speed cameras, cycle paths, fuel stations,
paid parking. The services carry NO licence statement (licenseInfo empty): recorded as UNSPECIFIED; reference only
until the owner/legal check (LEGAL_REVIEW_REQUIRED). dane.gov.pl was unreachable from this network (connect timeout).

  uv run --project tools/refs python tools/refs/bialystok_open_data.py [--catalog] [--buffer 250]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import refs_common as rc  # noqa: E402

ORG = "jN5LJsqeW33UjdlH"
BASE = f"https://services6.arcgis.com/{ORG}/arcgis/rest/services"
SEARCH = "https://www.arcgis.com/sharing/rest/search"
LICENSE = "UNSPECIFIED (public ArcGIS Online item, licenseInfo empty); LEGAL_REVIEW_REQUIRED"
# (service, layer id, slug)
LAYERS = [
    ("Środowisko", 0, "pomniki_przyrody"), ("Środowisko", 5, "parki"), ("Środowisko", 7, "skwery_zielence"),
    ("Środowisko", 3, "lasy"), ("Bezpieczeństwo", 3, "straz_pozarna"), ("Bezpieczeństwo", 1, "monitoring"),
    ("Bezpieczeństwo", 0, "fotoradary"), ("Transport", 5, "sciezki_rowerowe"), ("Transport", 4, "stacje_paliw"),
    ("Transport", 6, "strefa_parkowania"), ("Drogi_osie", 0, "drogi_osie"),
]


def route_bbox(points, buffer_m):
    lons, lats = [p["lon"] for p in points], [p["lat"] for p in points]
    lo = rc.bbox_around(min(lons), min(lats), buffer_m)
    hi = rc.bbox_around(max(lons), max(lats), buffer_m)
    return (lo[0], lo[1], hi[2], hi[3])


def query_layer(http, service, layer, bbox, page=1000):
    feats, off = [], 0
    while True:
        body = http.get_json(f"{BASE}/{quote(service)}/FeatureServer/{layer}/query", {
            "where": "1=1", "geometry": ",".join(f"{v:.6f}" for v in bbox), "geometryType": "esriGeometryEnvelope",
            "inSR": 4326, "spatialRel": "esriSpatialRelIntersects", "outFields": "*", "outSR": 4326, "f": "geojson",
            "resultOffset": off, "resultRecordCount": page})
        if "error" in body:
            raise rc.SourceError(f"{service}/{layer}: {body['error']}")
        got = body.get("features", [])
        feats += got
        if not got or (len(got) < page and not body.get("exceededTransferLimit")):
            break
        off += len(got)
    return {"type": "FeatureCollection", "features": feats}


def catalog(http, outdir: Path):
    """All public items of the org with their licence fields (evidence for 'what is available')."""
    body = http.get_json(SEARCH, {"q": f"orgid:{ORG}", "num": 100, "f": "json"})
    rows = [{"title": r["title"], "type": r["type"], "id": r["id"], "url": r.get("url"),
             "licenseInfo": r.get("licenseInfo"), "accessInformation": r.get("accessInformation"),
             "modified": r.get("modified")} for r in body.get("results", [])]
    rows.sort(key=lambda r: r["title"])
    p = Path(outdir) / "catalog.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    return rows


def fetch(points, http, outdir: Path, buffer_m=250.0, now=None, log=print):
    outdir = Path(outdir)
    bb = route_bbox(points, buffer_m)
    entries = rc.load_manifest(outdir / "manifest.jsonl")
    for service, layer, slug in LAYERS:
        try:
            fc = query_layer(http, service, layer, bb)
        except rc.SourceError as e:
            log(f"[bialystok-open-data] {e}")
            continue
        data = json.dumps(fc, ensure_ascii=False, sort_keys=True).encode("utf-8")
        f = f"{slug}.geojson"
        (outdir / f).parent.mkdir(parents=True, exist_ok=True)
        (outdir / f).write_bytes(data)
        entries[slug] = {
            "id": slug, "source": "bialystok-arcgis-open", "title": f"{service} / layer {layer}",
            "page_url": f"{BASE}/{quote(service)}/FeatureServer/{layer}", "author": "Urząd Miejski w Białymstoku",
            "license": LICENSE, "license_key": "unspecified", "usage": "reference_only_until_legal_review",
            "crs": "EPSG:4326", "bbox_wgs84": [round(v, 6) for v in bb], "feature_count": len(fc["features"]),
            "file": f, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data),
            "fetched_at": (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")}
        log(f"[bialystok-open-data] {slug}: {len(fc['features'])} features")
    rc.write_manifest(outdir / "manifest.jsonl", entries)
    return entries


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--buffer", type=float, default=250.0)
    ap.add_argument("--catalog", action="store_true")
    ap.add_argument("--interval", type=float, default=0.6)
    ap.add_argument("--out", help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    out = Path(a.out) if a.out else rc.RAW_ROOT / "bialystok-open-data"
    http = rc.Http(cache_dir=out / ".cache", min_interval=a.interval)
    try:
        if a.catalog:
            print(f"catalog: {len(catalog(http, out))} items")
        fetch(rc.parse_photo_list(), http, out, a.buffer)
    except rc.SourceError as e:
        sys.exit(f"error: {e}")


if __name__ == "__main__":
    main()
