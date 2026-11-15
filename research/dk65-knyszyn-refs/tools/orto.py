"""Fetch GUGiK ortho crops around points, rotate road-vertical, add metre scale, compute cross profile.
usage: orto.py points.json outdir [half_m=40] [ids...]"""
import json, sys, time, math, io, os, re
import requests, numpy as np
from PIL import Image, ImageDraw
UA = {"User-Agent": "research-client/1.0 (generic)"}
WMS = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution"
WFS = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WFS/Skorowidze"
RES = 0.1

def getmap(x, y, half, res=RES):
    n = int(round(2 * half / res))
    p = {"SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap", "LAYERS": "Raster", "STYLES": "", "SRS": "EPSG:2180",
         "BBOX": f"{x-half},{y-half},{x+half},{y+half}", "WIDTH": n, "HEIGHT": n, "FORMAT": "image/jpeg"}
    for a in range(4):
        try:
            r = requests.get(WMS, params=p, headers=UA, timeout=120)
            if r.ok and r.headers.get("content-type", "").startswith("image"):
                return Image.open(io.BytesIO(r.content)).convert("RGB"), r.url
        except Exception as e:
            print("retry", e, file=sys.stderr)
        time.sleep(3 * (a + 1))
    raise SystemExit("wms fail")

def sheets(x, y):
    out = []
    for yr in range(2021, 2027):
        p = {"SERVICE": "WFS", "VERSION": "1.0.0", "REQUEST": "GetFeature", "TYPENAME": f"gugik:SkorowidzOrtofomapy{yr}",
             "SRSNAME": "EPSG:2180", "BBOX": f"{x-2},{y-2},{x+2},{y+2}"}
        try:
            t = requests.get(WFS, params=p, headers=UA, timeout=60).text
        except Exception:
            continue
        for m in re.finditer(r"<gugik:akt_data>([^<]*)</gugik:akt_data>.*?<gugik:piksel>([^<]*)</gugik:piksel>", t, re.S):
            out.append((m.group(1), m.group(2), yr))
        time.sleep(0.5)
    return sorted(set(out))

def main():
    pts = json.load(open(sys.argv[1])); od = sys.argv[2]; half = float(sys.argv[3]) if len(sys.argv) > 3 else 40
    ids = set(sys.argv[4:])
    os.makedirs(od, exist_ok=True)
    meta = {}
    for p in pts:
        pid = p.get("id") or f"km{p['km']:05.2f}"
        if ids and pid not in ids: continue
        x, y = p["x"], p["y"]
        im, url = getmap(x, y, half)
        im.save(f"{od}/{pid}_north.jpg", quality=85)
        brg = p.get("bearing_grid", 0)
        rot = im.rotate(brg, resample=Image.BICUBIC)  # PIL rotates CCW; road bearing b clockwise from north -> rotate CCW by b = vertical
        n = rot.size[0]; c = n // 2; w = int(20 / RES)
        crop = rot.crop((c - w, c - w, c + w, c + w))
        a = np.asarray(crop.convert("L"), dtype=float)
        prof = np.median(a[int(5/RES):int(35/RES), :], axis=0)  # median along 30 m of road
        # draw scale
        d = ImageDraw.Draw(crop)
        W = crop.size[0]
        for m in range(-20, 21):
            px = int(W / 2 + m / RES)
            L = 30 if m % 5 == 0 else 14
            d.line([(px, 0), (px, L)], fill=(255, 0, 0), width=2)
            d.line([(px, W - L), (px, W)], fill=(255, 0, 0), width=2)
        crop.save(f"{od}/{pid}_rot.jpg", quality=85)
        # profile image (40 m wide at 10 px/m, height 200)
        pi = Image.new("RGB", (W, 220), (255, 255, 255)); dd = ImageDraw.Draw(pi)
        for i in range(1, W):
            dd.line([(i - 1, 210 - prof[i - 1] * 0.8), (i, 210 - prof[i] * 0.8)], fill=(0, 0, 0))
        for m in range(-20, 21):
            px = int(W / 2 + m / RES); dd.line([(px, 0), (px, 12 if m % 5 else 25)], fill=(255, 0, 0), width=2)
        pi.save(f"{od}/{pid}_prof.png")
        np.save(f"{od}/{pid}_prof.npy", prof)
        sh = sheets(x, y)
        meta[pid] = {"x": x, "y": y, "bearing_grid": brg, "wms_url": url, "half_m": half, "res_m": RES, "sheets": sh}
        print(pid, sh[-3:] if sh else None, flush=True)
    old = {}
    if os.path.exists(f"{od}/meta.json"): old = json.load(open(f"{od}/meta.json"))
    old.update(meta); json.dump(old, open(f"{od}/meta.json", "w"), indent=1)

if __name__ == "__main__":
    main()
