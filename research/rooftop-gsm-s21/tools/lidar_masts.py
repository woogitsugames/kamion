"""M67-FIX: wysokość wybranych urządzeń dachowych nad lokalnym poziomem dachu z chmury LIDAR GUGiK 2025-04-18
+ profile boczne (widok z S i z W) do kontroli wzrokowej.

Uruchom:
  uv run --no-project --with "laspy[lazrs]" --with numpy --with pillow --with pyproj \
      python -I tools/lidar_masts.py <katalog_z_laz> out/
Punkty urządzeń (dx, dy w m względem punktu dachu, EPSG:2180) wybrane z out/lidar_<dach>.png / klastrów
z lidar_roofs.py. Wynik: out/lidar_masts.json, out/prof_<dach>_<id>.png.

Wzory:
  Z_top   = maks. Z punktów w walcu r (domyślnie 1,0 m) wokół (dx, dy)
  Z_top2  = 2. najwyższy punkt w walcu (odporność na pojedynczy szum)
  Z_base  = dominanta histogramu Z (koszyki 0,1 m) punktów w pierścieniu 2–6 m, w paśmie Z_top−20 m..Z_top−0,5 m
            (= płaszczyzna dachu, na której stoi urządzenie)
  h       = Z_top − Z_base;  h2 = Z_top2 − Z_base
  niepewność: σ ≈ ±0,15 m (pomiar, ESTIMATED) + dolna granica dla cienkich elementów (odstęp punktów
  ≈ 1/√12 ≈ 0,29 m; szczyt rury Ø ≤ 0,1 m może nie mieć trafienia) → podajemy h jako ≥.
"""
import sys, os, json, glob, datetime
import numpy as np
import laspy
from PIL import Image, ImageDraw
from pyproj import Transformer

T = Transformer.from_crs('EPSG:4326', 'EPSG:2180', always_xy=True)
LAZ_DIR, OUT = sys.argv[1], sys.argv[2]
ROOFS = {
    'skorupska17': ('N-34-107-C-b-1-4-4-2', 53.133953, 23.180958),
    'dobra3': ('N-34-107-C-b-1-4-2-4', 53.138052, 23.180663),
    'zwierzyniecka4': ('N-34-107-C-b-3-1-2-4', 53.119647, 23.149357),
    'hallera19': ('N-34-107-C-b-1-1-3-1', 53.153529, 23.125354),
    'kopernika5a': ('N-34-107-C-b-3-1-2-1', 53.121630, 23.143090),
    # wieżowiec z M57 — tylko kontrola krzyżowa wysokości (środek z REVIEW-2026-11-14-s20-mistral-m57 §1)
    'wiezowiec_m57': ('N-34-107-C-b-1-2-3-2', 53.153231, 23.168022),
}
MASTS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'masts_xy.json')))


def gps_to_utc(t):
    return datetime.datetime(1980, 1, 6) + datetime.timedelta(seconds=float(t) + 1e9 - 18)


def profile(px, pz, top, base, path, title):
    W, H, sc = 15.0, 22.0, 30  # m, m, px/m
    im = Image.new('RGB', (int(W * sc), int(H * sc)), (15, 15, 25))
    d = ImageDraw.Draw(im)
    z0 = base - 4
    for zz in range(0, int(H) + 1):
        yy = int((H - zz) * sc)
        d.line((0, yy, 6 if zz % 5 else 14, yy), fill=(0, 200, 200))
    yb = int((H - (base - z0)) * sc)
    d.line((0, yb, im.width, yb), fill=(80, 80, 255))
    yt = int((H - (top - z0)) * sc)
    d.line((0, yt, im.width, yt), fill=(255, 80, 80))
    for a, b in zip(px, pz):
        u, v = int((a + W / 2) * sc), int((H - (b - z0)) * sc)
        if 0 <= u < im.width and 0 <= v < im.height:
            d.rectangle((u - 1, v - 1, u + 1, v + 1), fill=(255, 255, 255))
    d.text((18, 4), title, fill=(255, 255, 0))
    d.text((18, 18), 'skala: kreska co 1 m (dluga co 5 m); niebieska = dach, czerwona = szczyt', fill=(0, 200, 200))
    im.save(path)


res = {}
cache = {}
for name, items in MASTS.items():
    godlo, lat, lon = ROOFS[name]
    if godlo not in cache:
        fn = glob.glob(os.path.join(LAZ_DIR, '*%s.laz' % godlo))[0]
        las = laspy.read(fn)
        cx, cy = T.transform(lon, lat)
        m = (abs(las.x - cx) < 60) & (abs(las.y - cy) < 60)
        cache[godlo] = (np.asarray(las.x)[m], np.asarray(las.y)[m], np.asarray(las.z)[m],
                        np.asarray(las.classification)[m], np.asarray(las.gps_time)[m], os.path.basename(fn))
    x, y, z, cls, gt, fn = cache[godlo]
    cx, cy = T.transform(lon, lat)
    out = []
    for it in items:
        mx, my = cx + it['dx'], cy + it['dy']
        r = np.hypot(x - mx, y - my)
        sel = r < it.get('r', 1.0)
        zs = np.sort(z[sel])[::-1]
        top, top2 = float(zs[0]), float(zs[1]) if len(zs) > 1 else float('nan')
        ann = (r > 2.0) & (r < 6.0) & (z < top - 0.5) & (z > top - 20)
        hist, edges = np.histogram(z[ann], bins=np.arange(top - 20, top - 0.4, 0.1))
        base = float(edges[np.argmax(hist)] + 0.05)
        t_top = gps_to_utc(gt[sel][np.argmax(z[sel])])
        rec = dict(it, Z_top=round(top, 2), Z_top2=round(top2, 2), Z_base=round(base, 2),
                   h=round(top - base, 2), h2=round(top2 - base, 2), n_pts_walec=int(sel.sum()),
                   n_pts_powyzej_base_1m=int((z[sel] > base + 1).sum()), utc_szczytu=str(t_top)[:19])
        out.append(rec)
        # profile: widok z S (oś X) i z W (oś Y), pas ±3 m
        strip = (abs(y - my) < 3) & (abs(x - mx) < 7.5)
        profile(x[strip] - mx, z[strip], top, base, os.path.join(OUT, 'prof_%s_%s_zS.png' % (name, it['id'])),
                '%s %s widok z S  h=%.2f m (h2=%.2f)' % (name, it['id'], top - base, top2 - base))
        strip = (abs(x - mx) < 3) & (abs(y - my) < 7.5)
        profile(y[strip] - my, z[strip], top, base, os.path.join(OUT, 'prof_%s_%s_zW.png' % (name, it['id'])),
                '%s %s widok z W (N w prawo)  h=%.2f m' % (name, it['id'], top - base))
        print(name, rec)
    hs = [o['h'] for o in out if o.get('telecom', True)]
    res[name] = {'laz': fn, 'urzadzenia': out,
                 'h_min_med_max_telecom': [round(min(hs), 1), round(float(np.median(hs)), 1), round(max(hs), 1)] if hs else None}
json.dump(res, open(os.path.join(OUT, 'lidar_masts.json'), 'w'), ensure_ascii=False, indent=1)
