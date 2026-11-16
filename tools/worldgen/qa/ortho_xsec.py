"""Road cross-sections measured on the GUGiK orthophoto WMS (ADR 0272; open data, numbers only - no pixel is stored).

  measure:  uv run --project tools/worldgen python tools/worldgen/qa/ortho_xsec.py measure <region> <way,way,...> <step_m> <out_prefix>
            -> <out_prefix>.json (one row per station) and <out_prefix>.jpg (annotated strips, keep it outside git)
  summary:  uv run --project tools/worldgen python tools/worldgen/qa/ortho_xsec.py summary <file.json> [...]

Method. Stations every <step_m> along each graph edge of the given OSM ways (25 m in from the edge ends). Per station a
36 x 36 m GetMap crop at 0.05 m/px (WMS_URL, layer Raster, EPSG:2180; the server resamples its sheets - their native
resolution and date are not reported by the service at this scale: UNVERIFIED), a brightness / saturation profile
perpendicular to the graph axis (+-14 m, step 0.05 m), median over +-6 m along the axis. Asphalt = the run of grey
(low saturation, brightness within +-38 of the +-2 m core, not green) pixels through the axis, 0.3 m of noise tolerated;
line peaks = brightness maxima >= core + 18 inside it. Reading accuracy about +-0.2 m at a line, +-0.3 m at the asphalt
edge; tree shadows, junction mouths and lay-bys give wrong extents - `summary` keeps the stations with asphalt
CLEAN_W[0]-CLEAN_W[1] m ("clean") and, separately, those that also show both edge lines.
"""
import io, json, math, statistics, sys, time, urllib.request
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
WMS_URL = ("https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolution?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
           "&LAYERS=Raster&STYLES=&CRS=EPSG:2180&BBOX={y0},{x0},{y1},{x1}&WIDTH={px}&HEIGHT={px}&FORMAT=image/png")
URL = WMS_URL
HALF, PX = 18.0, 720
RES = 2 * HALF / PX
CLEAN_W = (6.0, 7.6)


def summarise(rows):
    """Median / range of the clean stations of one measurement file."""
    clean = [r for r in rows if CLEAN_W[0] <= r["asphalt_w"] <= CLEAN_W[1]]
    both = []
    for r in clean:
        left = [v for v in r["lines"] if v > 2.4]
        right = [v for v in r["lines"] if v < -2.4]
        if left and right:
            both.append(round(max(left) - min(right), 2))
    w = [r["asphalt_w"] for r in clean]
    return {"stations": len(rows), "clean": len(clean),
            "asphalt_median_m": round(statistics.median(w), 2) if w else None,
            "asphalt_range_m": [min(w), max(w)] if w else None,
            "edge_lines_both": len(both), "edge_line_spacing_median_m": round(statistics.median(both), 2) if both else None,
            "edge_line_spacing_range_m": [min(both), max(both)] if both else None}


def measure(region, ways, step, out):
    """Measure the stations of the OSM `ways` of a region every `step` m; writes <out>.json and <out>.jpg."""
    from PIL import Image, ImageDraw
    repo = str(REPO)
    def crop(cx, cy):
        u = URL.format(x0=cx - HALF, x1=cx + HALF, y0=cy - HALF, y1=cy + HALF, px=PX)
        for k in range(4):
            try:
                req = urllib.request.Request(u, headers={"User-Agent": "osm-research-client/1.0"})
                return Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=90).read())).convert("RGB")
            except Exception as ex:
                time.sleep(2 ** (k + 1))
        raise SystemExit("WMS failed")

    g = json.load(open(f"{repo}/Data/Regions/{region}/roads.graph.json"))
    rows, tiles = [], []
    for e in sorted(g["edges"], key=lambda e: e["id"]):
        if e["osm_way"] not in ways:
            continue
        P = np.array(e["geometry"], float)
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
        s = np.concatenate([[0], np.cumsum(seg)])
        if s[-1] < 2 * 25:
            continue
        for st in np.arange(25.0, s[-1] - 25.0 + 1e-6, step):
            i = min(np.searchsorted(s, st) - 1, len(seg) - 1)
            t = (P[i + 1] - P[i]) / seg[i]
            c = P[i] + t * (st - s[i])
            n = np.array([-t[1], t[0]])           # left of edge direction
            im = crop(*c)
            A = np.asarray(im, float)
            lat = np.arange(-14.0, 14.0 + 1e-9, 0.05)
            al = np.arange(-6.0, 6.0 + 1e-9, 0.25)
            X = c[0] + lat[None, :] * n[0] + al[:, None] * t[0]
            Y = c[1] + lat[None, :] * n[1] + al[:, None] * t[1]
            col = np.clip(((X - (c[0] - HALF)) / RES).astype(int), 0, PX - 1)
            row = np.clip((((c[1] + HALF) - Y) / RES).astype(int), 0, PX - 1)
            S = A[row, col]                        # (al, lat, 3)
            med = np.median(S, axis=0)
            v = med.mean(axis=1)
            sat = (med.max(axis=1) - med.min(axis=1)) / np.maximum(med.max(axis=1), 1)
            green = med[:, 1] - 0.5 * (med[:, 0] + med[:, 2])
            k0 = len(lat) // 2
            core = slice(k0 - 40, k0 + 41)        # +-2 m: always asphalt (may hold the centre line)
            a_v, a_sat = np.median(v[core]), np.median(sat[core])
            ok = (sat < a_sat + 0.07) & (np.abs(v - a_v) < 38) & (green < 6)
            okl = ok | (v > a_v + 25) & (sat < 0.12)          # paint counts as carriageway
            def run(sign):
                k, miss = k0, 0
                last = k0
                while 0 < k < len(lat) - 1 and miss < 6:    # tolerate 0.3 m of noise
                    k += sign
                    if okl[k]:
                        last, miss = k, 0
                    else:
                        miss += 1
                return lat[last]
            eL, eR = run(+1), run(-1)
            # line peaks: brightness maxima above asphalt + 18 within the asphalt
            pk = [round(float(lat[k]), 2) for k in range(2, len(lat) - 2)
                  if v[k] > a_v + 18 and v[k] >= v[k - 2:k + 3].max() and eR - 0.1 <= lat[k] <= eL + 0.1 and sat[k] < 0.15]
            merged = []
            for p in pk:
                if merged and p - merged[-1] < 0.4:
                    continue
                merged.append(p)
            rows.append({"edge": e["id"], "way": e["osm_way"], "s": round(float(st), 1), "x": round(float(c[0]), 1), "y": round(float(c[1]), 1),
                         "asphalt_L": round(float(eL), 2), "asphalt_R": round(float(eR), 2), "asphalt_w": round(float(eL - eR), 2),
                         "lines": merged, "bdot_w": (e["attrs"].get("width") or {}).get("v")})
            # annotated strip: 28 m across, 12 m along, rotated so the axis is vertical
            strip = Image.fromarray(np.uint8(np.clip(A[np.clip((((c[1] + HALF) - (c[1] + lat[None, ::1] * n[1] + np.arange(-9, 9, 0.05)[:, None] * t[1])) / RES).astype(int), 0, PX - 1),
                                                       np.clip(((c[0] + lat[None, :] * n[0] + np.arange(-9, 9, 0.05)[:, None] * t[0] - (c[0] - HALF)) / RES).astype(int), 0, PX - 1)], 0, 255)))
            d = ImageDraw.Draw(strip)
            for xv, colr in ((eL, (255, 0, 0)), (eR, (255, 0, 0))):
                xpix = int((xv + 14.0) / 0.05)
                d.line([(xpix, 0), (xpix, 40)], fill=colr, width=2)
            for m in range(-14, 15, 2):
                xpix = int((m + 14.0) / 0.05)
                d.line([(xpix, strip.height - 12), (xpix, strip.height)], fill=(255, 255, 0), width=1)
            d.text((4, 4), f"{e['osm_way']} s={st:.0f} w={eL - eR:.2f}", fill=(255, 255, 0))
            tiles.append(strip)
            print(json.dumps(rows[-1]), flush=True)
    json.dump(rows, open(out + ".json", "w"), indent=1)
    if tiles:
        W = tiles[0].width; H = tiles[0].height
        cols = 2
        sheet = Image.new("RGB", (W * cols, H * math.ceil(len(tiles) / cols)))
        for i, tl in enumerate(tiles):
            sheet.paste(tl, ((i % cols) * W, (i // cols) * H))
        sheet.save(out + ".jpg", quality=88)


def main(argv):
    if len(argv) >= 2 and argv[0] == "summary":
        for f in argv[1:]:
            print(Path(f).name, json.dumps(summarise(json.loads(Path(f).read_text(encoding="utf-8")))))
    elif len(argv) == 5 and argv[0] == "measure":
        measure(argv[1], {int(w) for w in argv[2].split(",")}, float(argv[3]), argv[4])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
