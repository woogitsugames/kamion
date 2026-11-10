"""Orthophoto access for fidelity checks (reference only, never a texture; docs/05 §3).

* sheet  - the 0.25 m 2024-05-27 GUGiK mosaic of the whole tile (Data/Regions/<id>/ortho.json, already ingested);
* hires  - GUGiK WMS ORTO HighResolution crops, 128 m cells at 0.08 m/px, only for cells along the start route
           and around the junctions under test. Polite: one request at a time, >= 1 s apart, cached on disk with a
           manifest (URL, time, sha256, CRS, bbox, licence). Not Google, not a tile server bulk scrape.

Cells: Data/raw/refs/gugik-ortho-hr/<region>/c_<ix>_<iy>.jpg (+ manifest.jsonl), EPSG:2180, north up.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
WMS = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution"
LICENSE = "GUGiK open data (Prawo geodezyjne i kartograficzne art. 40a ust. 2 pkt 1); WMS: no access restrictions"
ATTRIBUTION = "Źródło danych: Główny Urząd Geodezji i Kartografii (www.geoportal.gov.pl)"
CELL_M = 128.0
RES_HR = 0.08
UA = "kamion-worldgen-fidelity/0.1"


def cell_dir(region_id):
    return REPO / "Data/raw/refs/gugik-ortho-hr" / region_id


def _cell_bbox(region, ix, iy):
    x0 = region["bbox"]["xmin"] + ix * CELL_M
    y0 = region["bbox"]["ymin"] + iy * CELL_M
    return x0, y0, x0 + CELL_M, y0 + CELL_M


def cells_for(region, geoms_2180, pad=0.0):
    """Cells (ix, iy) intersecting shapely geometries (EPSG:2180) buffered by `pad`."""
    import shapely
    out = set()
    n = int(region["bbox"]["width_m"] // CELL_M)
    for g in geoms_2180:
        g = g.buffer(pad) if pad else g
        x0, y0, x1, y1 = g.bounds
        for ix in range(max(0, int((x0 - region["bbox"]["xmin"]) // CELL_M)),
                        min(n, int((x1 - region["bbox"]["xmin"]) // CELL_M) + 1)):
            for iy in range(max(0, int((y0 - region["bbox"]["ymin"]) // CELL_M)),
                            min(n, int((y1 - region["bbox"]["ymin"]) // CELL_M) + 1)):
                if g.intersects(shapely.box(*_cell_bbox(region, ix, iy))):
                    out.add((ix, iy))
    return sorted(out)


def _load_manifest(d: Path):
    f = d / "manifest.jsonl"
    if not f.exists():
        return {}
    return {e["file"]: e for e in (json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip())}


def fetch_cells(region, cells, log=print, interval=1.0):
    import requests
    from PIL import Image
    d = cell_dir(region["id"])
    d.mkdir(parents=True, exist_ok=True)
    man = _load_manifest(d)
    px = int(round(CELL_M / RES_HR))
    n_new, last = 0, 0.0
    for ix, iy in cells:
        f = f"c_{ix:02d}_{iy:02d}.jpg"
        if f in man and (d / f).exists():
            continue
        bb = _cell_bbox(region, ix, iy)
        params = {"SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap", "LAYERS": "Raster", "STYLES": "",
                  "SRS": "EPSG:2180", "BBOX": ",".join(f"{v:.2f}" for v in bb), "WIDTH": px, "HEIGHT": px,
                  "FORMAT": "image/jpeg"}
        ok = False
        for attempt in range(6):
            wait = interval - (time.time() - last)
            if wait > 0:
                time.sleep(wait)
            last = time.time()
            try:
                r = requests.get(WMS, params=params, headers={"User-Agent": UA}, timeout=120)
            except requests.RequestException as e:
                log(f"  {f}: {e}; retry")
                time.sleep(3 * (attempt + 1))
                continue
            if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image"):
                time.sleep(3 * (attempt + 1))
                continue
            (d / f).write_bytes(r.content)
            lo, _ = Image.open(d / f).convert("L").getextrema()
            if lo < 235:          # the WMS intermittently returns a blank white tile
                ok = True
                break
            time.sleep(3 * (attempt + 1))
        if not ok:
            log(f"  {f}: blank / failed after retries, skipped")
            (d / f).unlink(missing_ok=True)
            continue
        b = (d / f).read_bytes()
        man[f] = {"file": f, "source": "gugik-ortho-wms-highres", "url": WMS + "?" + "&".join(
                  f"{k}={v}" for k, v in params.items()), "crs": "EPSG:2180", "bbox_2180": list(bb),
                  "res_m": RES_HR, "px": px, "sha256": hashlib.sha256(b).hexdigest(), "size_bytes": len(b),
                  "license": LICENSE, "attribution": ATTRIBUTION, "usage": "reference_and_alignment_only",
                  "captured_at": "UNVERIFIED (WMS HighResolution mosaic; leaf-on, newest sheet per area)",
                  "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        n_new += 1
        with open(d / "manifest.jsonl", "w", encoding="utf-8") as fh:
            for k in sorted(man):
                fh.write(json.dumps(man[k], ensure_ascii=False, sort_keys=True) + "\n")
    log(f"[ortho-hr] cells requested {len(cells)}, new {n_new}, cached {len(man)}")
    return man


class Ortho:
    """Sample a north-up RGB window (EPSG:2180 bbox) at a given resolution: high-res cells where available
    (all cells covering the window must exist), otherwise the 0.25 m sheet."""

    def __init__(self, region):
        self.region = region
        self.d = cell_dir(region["id"])
        self.man = _load_manifest(self.d)
        self._cache = {}
        o = json.loads((REPO / "Data/Regions" / region["id"] / "ortho.json").read_text(encoding="utf-8"))
        self.sheet = REPO / o["file"]

    def _cell(self, ix, iy):
        k = (ix, iy)
        if k not in self._cache:
            from PIL import Image
            f = self.d / f"c_{ix:02d}_{iy:02d}.jpg"
            self._cache[k] = np.asarray(Image.open(f).convert("RGB")) if f.exists() else None
            if len(self._cache) > 80:
                self._cache.pop(next(iter(self._cache)))
        return self._cache[k]

    def has_hr(self, bbox):
        x0, y0, x1, y1 = bbox
        bx, by = self.region["bbox"]["xmin"], self.region["bbox"]["ymin"]
        for ix in range(int((x0 - bx) // CELL_M), int((x1 - 1e-6 - bx) // CELL_M) + 1):
            for iy in range(int((y0 - by) // CELL_M), int((y1 - 1e-6 - by) // CELL_M) + 1):
                if f"c_{ix:02d}_{iy:02d}.jpg" not in self.man:
                    return False
        return True

    def window(self, bbox, res, prefer_hr=True):
        """(rgb uint8 HxWx3, source) for EPSG:2180 bbox at `res` m/px (top-left = (x0, y1))."""
        x0, y0, x1, y1 = bbox
        w = int(round((x1 - x0) / res))
        h = int(round((y1 - y0) / res))
        if prefer_hr and self.has_hr(bbox):
            xs = x0 + (np.arange(w) + 0.5) * res
            ys = y1 - (np.arange(h) + 0.5) * res
            out = np.zeros((h, w, 3), np.uint8)
            bx, by = self.region["bbox"]["xmin"], self.region["bbox"]["ymin"]
            cx = ((xs - bx) // CELL_M).astype(int)
            cy = ((ys - by) // CELL_M).astype(int)
            n = int(round(CELL_M / RES_HR))
            for ix in np.unique(cx):
                for iy in np.unique(cy):
                    img = self._cell(ix, iy)
                    if img is None:
                        continue
                    mx = cx == ix
                    my = cy == iy
                    col = np.clip(((xs[mx] - (bx + ix * CELL_M)) / RES_HR).astype(int), 0, n - 1)
                    row = np.clip((((by + (iy + 1) * CELL_M) - ys[my]) / RES_HR).astype(int), 0, n - 1)
                    out[np.ix_(np.where(my)[0], np.where(mx)[0])] = img[np.ix_(row, col)]
            return out, "wms_hr_0.08"
        import rasterio
        from rasterio.enums import Resampling
        from rasterio.windows import from_bounds
        with rasterio.open(self.sheet) as o:
            a = o.read(window=from_bounds(x0, y0, x1, y1, o.transform), out_shape=(3, h, w),
                       resampling=Resampling.bilinear, boundless=True, fill_value=0)
        return np.moveaxis(a, 0, -1).copy(), "sheet_0.25_2024-05-27"


def register(ortho: Ortho, bbox, res=0.25, search=3.0):
    """Shift (dx, dy) in metres of the high-res mosaic relative to the 0.25 m sheet over bbox, by phase
    correlation of gradient magnitude. Positive dx = hi-res content lies east of the sheet content."""
    hr, src = ortho.window(bbox, res, prefer_hr=True)
    sh, _ = ortho.window(bbox, res, prefer_hr=False)
    if not src.startswith("wms"):
        return None

    def grad(a):
        g = a.astype(float).mean(2)
        gy, gx = np.gradient(g)
        m = np.hypot(gx, gy)
        return (m - m.mean()) / (m.std() + 1e-9)
    A, B = grad(hr), grad(sh)
    F = np.fft.fft2(A) * np.conj(np.fft.fft2(B))
    r = np.fft.ifft2(F / (np.abs(F) + 1e-9)).real
    r = np.fft.fftshift(r)
    cy, cx = np.array(r.shape) // 2
    k = int(math.ceil(search / res))
    sub = r[cy - k:cy + k + 1, cx - k:cx + k + 1]
    iy, ix = np.unravel_index(sub.argmax(), sub.shape)
    peak = float(sub.max())
    return {"dx_m": (ix - k) * res, "dy_m": -(iy - k) * res, "peak": round(peak, 4),
            "peak_ratio": round(peak / (np.sort(sub.ravel())[-20] + 1e-9), 2)}
