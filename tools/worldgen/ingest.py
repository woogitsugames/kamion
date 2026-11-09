"""Ingest raw sources (OSM + GUGiK only) for a region tile, with SHA256 manifests.

Usage (from repo root):
    uv run --project tools/worldgen tools/worldgen/ingest.py --region bialystok-industrial-c
    ... --dry-run                 # show what would be downloaded
    ... --refresh-index           # re-query GUGiK sheet indexes (otherwise the committed snapshot is used)
    ... --with nmpt trees lidar   # opt-in heavy datasets (NMPT ~600 MB, trees ~1.1 GB, LiDAR ~5 GB)

Default set (~370 MB): OSM Geofabrik extract (already pinned by fetch_osm.py), NMT 1 m (latest year),
orthophoto 0.25 m RGB PL-1992 (latest year), BDOT10k GPKG for the powiat, 3D buildings LoD2 (2017)
and LoD1 (2024) for the powiat.

Idempotent: files whose SHA256 matches the manifest are skipped; manifests are only rewritten when their
content changes. Sequential requests with POLITE_DELAY_S between them. No Google anything (ADR 0002).
"""

from __future__ import annotations

import argparse
import json
import sys

import shapely

import fetch_osm
import gugik_index as gi
import regions
from sources import MANIFEST_DIR, Downloader, ingest_dataset, now_utc, write_if_changed

LIC_GUGIK = {
    "license": "GUGiK open data: free of charge, download without application "
               "(ustawa Prawo geodezyjne i kartograficzne art. 40a ust. 2 pkt 1, as amended by "
               "Dz.U. 2020 poz. 782, in force since 2020-07-31)",
    "license_status": "LEGAL_REVIEW_REQUIRED (statutory basis cited from secondary sources, not from ISAP text)",
    "attribution": "Źródło danych: Główny Urząd Geodezji i Kartografii (www.geoportal.gov.pl)",
}
LIC_GUGIK_3D = {
    "license": "CC BY 4.0 (stated in GUGiK WMS GetFeatureInfo download panel, checked 2026-11-09); "
               "geoportal.gov.pl: 'dostępne bezpłatnie i możliwe do dowolnego wykorzystania'",
    "license_url": "https://creativecommons.org/licenses/by/4.0/legalcode.pl",
    "license_status": "VERIFIED_FROM_PROVIDER_UI (attribution required by CC BY 4.0)",
    "attribution": "Źródło danych: Główny Urząd Geodezji i Kartografii (www.geoportal.gov.pl), CC BY 4.0",
}
OPENDATA = "https://opendata.geoportal.gov.pl"


def availability_path(region_id: str):
    return MANIFEST_DIR / f"{region_id}.gugik-availability.json"


def load_or_query_index(region: regions.Region, refresh: bool) -> dict:
    p = availability_path(region.id)
    if p.exists() and not refresh:
        return json.loads(p.read_text(encoding="utf-8"))
    print(f"[ingest] querying GUGiK sheet indexes for {region.bbox}")
    s = gi._session()
    snap = {"region": region.id, "bbox_epsg2180": list(region.bbox), "queried_utc": now_utc(),
            "method": "WFS 1.0.0 GetFeature, BBOX in EPSG:2180, one request per product-year layer",
            "services": {k: v[0] for k, v in gi.INDEX_SERVICES.items()}, "products": {}}
    for product in gi.INDEX_SERVICES:
        sheets = gi.query(product, region.bbox, s)
        rows = gi.summarise(sheets)
        for row, sh in zip(rows, sheets):
            row["ring_bounds"] = [round(v, 2) for v in shapely.Polygon(sh.ring).bounds] if sh.ring else None
            row["ring"] = [[round(x, 2), round(y, 2)] for x, y in sh.ring]
        snap["products"][product] = sorted(rows, key=lambda r: (r.get("akt_data", ""), r.get("url_do_pobrania", "")))
    write_if_changed(p, json.dumps(snap, indent=1, ensure_ascii=False) + "\n")
    return snap


def covers(rows: list[dict], bbox) -> float:
    tile = shapely.box(*bbox)
    u = shapely.union_all([shapely.Polygon(r["ring"]) for r in rows if r.get("ring")])
    return u.intersection(tile).area / tile.area


def pick_latest(rows: list[dict], bbox, pred) -> list[dict]:
    """Latest akt_data series (all sheets with that date) satisfying `pred` that fully covers the tile."""
    cand = [r for r in rows if pred(r)]
    for date in sorted({r["akt_data"] for r in cand}, reverse=True):
        series = [r for r in cand if r["akt_data"] == date]
        if covers(series, bbox) > 0.9999:
            return sorted(series, key=lambda r: r["url_do_pobrania"])
    return []


def sheet_files(rows: list[dict]) -> list[dict]:
    keep = ("godlo", "akt_data", "akt_rok", "piksel", "char_przestrz", "kolor", "uklad_xy", "uklad_h",
            "blad_sr_wys", "blad_sr_syt", "format", "dt_pzgik")
    return [{"url": r["url_do_pobrania"], "name": r["url_do_pobrania"].rsplit("/", 1)[-1],
             **{k: r[k] for k in keep if k in r}} for r in rows]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--refresh-index", action="store_true")
    ap.add_argument("--with", dest="extra", nargs="*", default=[], choices=["nmpt", "trees", "lidar"])
    a = ap.parse_args()
    region = regions.get(a.region)
    dl = Downloader(dry_run=a.dry_run)
    used_by = f"tools/worldgen/build_region.py --region {region.id}"
    bb = region.bbox

    # 1. OSM (pinned snapshot; one file for the whole voivodeship)
    print("[ingest] osm-geofabrik-podlaskie")
    fetch_osm.download()

    idx = load_or_query_index(region, a.refresh_index)
    P = idx["products"]

    # 2. NMT 1 m, EVRF2007
    nmt = pick_latest(P["NMT"], bb, lambda r: r.get("char_przestrz") == "1.00 m"
                      and r.get("format", "").startswith("ARC/INFO") and r.get("uklad_h") == "PL-EVRF2007-NH")
    if not nmt:
        sys.exit("no NMT 1 m series fully covers the tile")
    yr = nmt[0]["akt_rok"]
    ingest_dataset(dl, {
        "id": f"gugik-nmt-{yr}-{region.id}", "name": f"GUGiK NMT (DTM) 1 m grid, {yr}, sheets covering {region.id}",
        "provider": "Główny Urząd Geodezji i Kartografii", "product": "NMT", "region": region.id,
        "index_service": gi.INDEX_SERVICES["NMT"][0], "format": "ARC/INFO ASCII GRID",
        "crs": "EPSG:2180 (PL-1992)", "vertical_crs": "PL-EVRF2007-NH (EPSG:9651 EVRF2007-PL height); compound EPSG:2180+9651",
        "resolution_m": 1.0, "accuracy": {"blad_sr_wys_m": nmt[0].get("blad_sr_wys"), "blad_sr_syt_m": nmt[0].get("blad_sr_syt")},
        "source_survey": "airborne laser scanning (zrodlo_danych: Skaning laserowy)",
        "extent": f"sheets intersecting bbox {list(bb)}", **LIC_GUGIK, "used_by": [used_by],
    }, sheet_files(nmt))

    # 3. Orthophoto 0.25 m RGB in PL-1992 (5 cm series exist but are ~1 GB/sheet; reference only)
    orto = pick_latest(P["ORTO"], bb, lambda r: r.get("piksel") == "0.25" and r.get("kolor") == "RGB"
                       and r.get("uklad_xy") == "PL-1992")
    if orto:
        yr = orto[0]["akt_rok"]
        ingest_dataset(dl, {
            "id": f"gugik-orto-{yr}-rgb-0p25-{region.id}",
            "name": f"GUGiK orthophoto RGB 0.25 m, {orto[0]['akt_data']}, sheets covering {region.id}",
            "provider": "Główny Urząd Geodezji i Kartografii", "product": "ORTO", "region": region.id,
            "index_service": gi.INDEX_SERVICES["ORTO"][0], "format": "GeoTIFF", "crs": "EPSG:2180 (PL-1992)",
            "resolution_m": 0.25, "extent": f"sheets intersecting bbox {list(bb)}",
            "usage_restriction": "visual reference + alignment QA only; not a game texture (docs/05 §3)",
            **LIC_GUGIK, "used_by": [used_by],
        }, sheet_files(orto))

    # 4. BDOT10k (powiat, schema 2021, GeoPackage)
    t = region.teryt_powiat
    woj = t[:2]
    ingest_dataset(dl, {
        "id": f"gugik-bdot10k-{t}", "name": f"GUGiK BDOT10k powiat {t} (schemat 2021, GPKG)",
        "provider": "Główny Urząd Geodezji i Kartografii", "product": "BDOT10k", "region": f"powiat {t}",
        "index_service": "https://mapy.geoportal.gov.pl/wss/service/PZGIK/BDOT/WMS/PobieranieBDOT10k (GetFeatureInfo, layer Powiaty)",
        "format": "GeoPackage in ZIP", "crs": "EPSG:2180 (PL-1992)", "scale": "1:10 000",
        **LIC_GUGIK, "used_by": [used_by], "raw_subdir": f"gugik/bdot10k-{t}",
    }, [{"url": f"{OPENDATA}/bdot10k/schemat2021/GPKG/{woj}/{t}_GPKG.zip", "name": f"{t}_GPKG.zip"}])

    # 5. 3D buildings
    ingest_dataset(dl, {
        "id": f"gugik-lod2-2017-{t}", "name": f"GUGiK 3D building models LoD2 (state 2017), powiat {t}",
        "provider": "Główny Urząd Geodezji i Kartografii", "product": "Budynki3D LoD2", "region": f"powiat {t}",
        "index_service": "https://mapy.geoportal.gov.pl/wss/service/PZGIK/FOTO/WMS/ModeleBudynkow3D (layer Modele_3D_budynkow_LoD2_2017)",
        "format": "CityGML 2.0 in ZIP", "crs": "EPSG:2180 + PL-KRON86-NH heights (srsName urn:ogc:def:crs,crs:EPSG::2180,crs:PL-KRON86-NH in files)",
        **LIC_GUGIK_3D, "used_by": [used_by], "raw_subdir": f"gugik/lod2-2017-{t}",
    }, [{"url": f"{OPENDATA}/InneDane/Budynki3D/LOD2/{t}_gml.zip", "name": f"{t}_lod2_gml.zip"}])
    ingest_dataset(dl, {
        "id": f"gugik-lod1-2024-{t}", "name": f"GUGiK 3D building models LoD1 (2024), powiat {t}",
        "provider": "Główny Urząd Geodezji i Kartografii", "product": "Budynki3D LoD1", "region": f"powiat {t}",
        "index_service": "https://mapy.geoportal.gov.pl/wss/service/PZGIK/FOTO/WMS/ModeleBudynkow3D (layer Modele_3D_budynkow_LoD1_2024)",
        "format": "CityGML 2.0 in ZIP", "crs": "EPSG:2180 + EPSG:9651 EVRF2007 heights (srsName urn:ogc:def:crs,crs:EPSG::2180,crs:EPSG::9651 in files)",
        **LIC_GUGIK_3D, "used_by": [used_by], "raw_subdir": f"gugik/lod1-2024-{t}",
    }, [{"url": f"{OPENDATA}/InneDane/Budynki3D/LOD1/2024/{woj}/{t}.zip", "name": f"{t}_lod1_2024.zip"}])

    # 6. Opt-in heavy datasets
    if "nmpt" in a.extra:
        nmpt = pick_latest(P["NMPT"], bb, lambda r: r.get("uklad_h") == "PL-EVRF2007-NH")
        ingest_dataset(dl, {
            "id": f"gugik-nmpt-{nmpt[0]['akt_rok']}-{region.id}", "name": "GUGiK NMPT (DSM) 0.5 m",
            "provider": "Główny Urząd Geodezji i Kartografii", "product": "NMPT", "region": region.id,
            "index_service": gi.INDEX_SERVICES["NMPT"][0], "format": "ARC/INFO ASCII GRID",
            "crs": "EPSG:2180", "vertical_crs": "PL-EVRF2007-NH", **LIC_GUGIK, "used_by": [used_by],
        }, sheet_files(nmpt))
    if "trees" in a.extra:
        ingest_dataset(dl, {
            "id": f"gugik-trees3d-2023-{t}", "name": f"GUGiK 3D tree models LoD1 (2023), powiat {t}",
            "provider": "Główny Urząd Geodezji i Kartografii", "product": "Drzewa3D LoD1", "region": f"powiat {t}",
            "index_service": "https://mapy.geoportal.gov.pl/wss/service/PZGIK/FOTO/WMS/ModeleDrzew3D",
            "format": "CityGML 2.0 in ZIP", **LIC_GUGIK_3D, "used_by": [used_by], "raw_subdir": f"gugik/trees3d-2023-{t}",
        }, [{"url": f"{OPENDATA}/InneDane/Drzewa3D/LOD1/2023/{woj}/{t}.zip", "name": f"{t}_trees3d_2023.zip"}])
    if "lidar" in a.extra:
        las = pick_latest(P["LIDAR"], bb, lambda r: r.get("uklad_h") == "PL-EVRF2007-NH")
        ingest_dataset(dl, {
            "id": f"gugik-lidar-{las[0]['akt_rok']}-{region.id}", "name": "GUGiK LiDAR point cloud (LAZ)",
            "provider": "Główny Urząd Geodezji i Kartografii", "product": "LIDAR", "region": region.id,
            "index_service": gi.INDEX_SERVICES["LIDAR"][0], "format": "LAZ", "crs": "EPSG:2180",
            "vertical_crs": "PL-EVRF2007-NH", **LIC_GUGIK, "used_by": [used_by],
        }, sheet_files(las))

    print(f"[ingest] done: {dl.stats}")


if __name__ == "__main__":
    main()
