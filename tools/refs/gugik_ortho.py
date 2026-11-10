r"""GUGiK orthophoto crops per route shot (D43, ADR 0066): top-down view of pavement, roofs, greenery.

Source: Geoportal WMS ORTO_HighResolution (https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution),
open data (Prawo geodezyjne i kartograficzne art. 40a; WMS terms: no access restrictions). Not Google. Reference and
alignment only (as in Data/SourceManifests/gugik-orto-*.json); the 4 full GeoTIFF sheets of the region stay in
Data/raw/gugik (not duplicated). Output: Data/raw/refs/gugik-ortho/shot_NN.png (+ manifest.jsonl),
annotated overview sheets artifacts/refs/gugik-ortho/.

  uv run --project tools/refs python tools/refs/gugik_ortho.py [--window 160] [--px 640]
"""
from __future__ import annotations

import argparse
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import refs_common as rc  # noqa: E402

WMS = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution"
LICENSE = "GUGiK open data (Prawo geodezyjne i kartograficzne art. 40a ust. 2 pkt 1); WMS: brak ograniczeń w publicznym dostępie"
ATTRIBUTION = "Źródło danych: Główny Urząd Geodezji i Kartografii (www.geoportal.gov.pl)"


def shot_bbox_2180(lon, lat, window_m):
    from pyproj import Transformer
    t = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
    x, y = t.transform(lon, lat)
    h = window_m / 2.0
    return (x - h, y - h, x + h, y + h), (x, y)


def wms_params(bbox, px):
    return {"SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap", "LAYERS": "Raster", "STYLES": "",
            "SRS": "EPSG:2180", "BBOX": ",".join(f"{v:.2f}" for v in bbox), "WIDTH": px, "HEIGHT": px,
            "FORMAT": "image/png"}


def is_blank(path: Path) -> bool:
    from PIL import Image
    lo, _ = Image.open(path).convert("L").getextrema()
    return lo >= 245


def fetch(points, http, outdir: Path, window=160.0, px=640, now=None, log=print):
    outdir = Path(outdir)
    entries = rc.load_manifest(outdir / "manifest.jsonl")
    n_new = 0
    for p in points:
        bb, xy = shot_bbox_2180(p["lon"], p["lat"], window)
        f = f"shot_{p['nr']:02d}.png"
        dest = outdir / f
        params = wms_params(bb, px)
        if dest.exists() and f"ortho{p['nr']}" in entries:
            continue
        for attempt in range(5):  # the WMS intermittently answers with a blank white tile: retry
            sha, size = http.download(WMS, dest, params=params)
            if not is_blank(dest):
                break
            http._sleep(3.0 * (attempt + 1))
        else:
            log(f"shot {p['nr']}: still blank after retries, skipped")
            dest.unlink(missing_ok=True)
            continue
        entries[f"ortho{p['nr']}"] = {
            "id": f"ortho{p['nr']}", "source": "gugik-ortho-wms", "title": f"Ortofotomapa, ujęcie {p['nr']}: {p['place']}",
            "page_url": "https://mapy.geoportal.gov.pl/",
            "file_url": WMS + "?" + "&".join(f"{k}={v}" for k, v in params.items()),
            "author": "GUGiK", "license": LICENSE, "license_key": "gugik-open-data",
            "license_url": "https://www.geoportal.gov.pl/dane/regulamin",
            "attribution": ATTRIBUTION, "usage": "reference_and_alignment_only", "crs": "EPSG:2180",
            "bbox_2180": [round(v, 2) for v in bb], "center_2180": [round(v, 2) for v in xy], "window_m": window,
            "px": px, "resolution_m_per_px": round(window / px, 4),
            "source_resolution_m": "0.25 (2024 sheets) or finer: UNVERIFIED for the WMS mosaic",
            "captured_at": "2024 (sheet date 2024-05-27 per Data/SourceManifests; UNVERIFIED for this WMS mosaic)",
            "lon": p["lon"], "lat": p["lat"], "file": f, "sha256": sha, "size_bytes": size, "shots": [p["nr"]],
            "fetched_at": (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        n_new += 1
    rc.write_manifest(outdir / "manifest.jsonl", entries)
    log(f"[gugik-ortho] new crops {n_new}, requests {http.requests_made}")
    return entries


def sheets(points, entries, raw_dir: Path, art_dir: Path, per_sheet=12, tile=360):
    """Annotated overview sheets: shot position (red cross), viewing direction (yellow), 100 m scale bar."""
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.load_default()
    art_dir = Path(art_dir)
    art_dir.mkdir(parents=True, exist_ok=True)
    have = [p for p in points if f"ortho{p['nr']}" in entries and (Path(raw_dir) / f"shot_{p['nr']:02d}.png").exists()]
    out = []
    for si in range(0, len(have), per_sheet):
        chunk = have[si:si + per_sheet]
        cols = 4
        rows = math.ceil(len(chunk) / cols)
        sh = Image.new("RGB", (cols * (tile + 4) + 4, rows * (tile + 22) + 4), (24, 24, 24))
        d = ImageDraw.Draw(sh)
        for i, p in enumerate(chunk):
            e = entries[f"ortho{p['nr']}"]
            im = Image.open(Path(raw_dir) / e["file"]).convert("RGB").resize((tile, tile))
            dd = ImageDraw.Draw(im)
            c = tile // 2
            dd.line([(c - 8, c), (c + 8, c)], fill=(255, 40, 40), width=2)
            dd.line([(c, c - 8), (c, c + 8)], fill=(255, 40, 40), width=2)
            if p.get("azimuth") is not None:
                a = math.radians(p["azimuth"])
                dd.line([(c, c), (c + 70 * math.sin(a), c - 70 * math.cos(a))], fill=(255, 230, 0), width=2)
            bar = 100.0 / e["window_m"] * tile
            dd.line([(8, tile - 10), (8 + bar, tile - 10)], fill=(255, 255, 255), width=3)
            dd.text((8, tile - 24), "100 m", fill=(255, 255, 255), font=font)
            x, y = 4 + (i % cols) * (tile + 4), 4 + (i // cols) * (tile + 22)
            sh.paste(im, (x, y))
            d.text((x + 2, y + tile + 4), f"#{p['nr']} {p['type']} (N up)", fill=(220, 220, 220), font=font)
        f = art_dir / f"overview_{si // per_sheet + 1:02d}.jpg"
        sh.save(f, "JPEG", quality=85)
        out.append(f)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--window", type=float, default=160.0, help="square window in metres (default 160)")
    ap.add_argument("--px", type=int, default=640)
    ap.add_argument("--interval", type=float, default=0.7)
    ap.add_argument("--out", help=argparse.SUPPRESS)
    ap.add_argument("--art", help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    out = Path(a.out) if a.out else rc.RAW_ROOT / "gugik-ortho"
    art = Path(a.art) if a.art else rc.ART_ROOT / "gugik-ortho"
    pts = rc.parse_photo_list()
    http = rc.Http(min_interval=a.interval)
    try:
        entries = fetch(pts, http, out, a.window, a.px)
    except rc.SourceError as e:
        sys.exit(f"error: {e}")
    print("sheets:", [str(x) for x in sheets(pts, entries, out, art)])


if __name__ == "__main__":
    main()
