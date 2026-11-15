"""M67-FIX: wysokość urządzeń nad dachem z chmury punktów GUGiK LIDAR (2025-04-18, 12 p/m², PL-1992, PL-EVRF2007-NH).

Uruchom:
  uv run --no-project --with "laspy[lazrs]" --with numpy --with pillow --with pyproj \
      python -I tools/lidar_roofs.py <katalog_z_laz> out/
Wynik: out/lidar_<dach>.png (mapa wysokości nad dachem, 0,25 m/komórkę, północ u góry),
       out/lidar_profile_<dach>.png (profil W–E i S–N przez punkt), out/lidar_roofs.json (liczby).

Metoda (każda liczba w JSON z wzorem):
- wycinek kwadratu S = 70 m wokół punktu dachu (EPSG:2180);
- poziom dachu Z_roof = mediana Z punktów w promieniu R_roof wokół punktu, ograniczona do pasma
  [Z_p90 − 3 m, Z_p90] — gdzie Z_p90 to 90. percentyl punktów klasy 6 (budynki) w promieniu 15 m
  (eliminuje grunt i drzewa, zostawia płaszczyznę dachu);
- urządzenie: maks. Z w promieniu r = 1,5 m wokół punktu masztu (OSM / wskazanego z mapy) − Z_roof;
- min / mediana / max po wszystkich wskazanych masztach dachu;
- niepewność: ± (σ_Z LIDAR ~0,1–0,15 m, ESTIMATED) + nierówność dachu (IQR pasma dachu) +
  niedoszacowanie szczytu cienkiego masztu (przy 12 p/m² ≈ 0,29 m odstępu punktów;
  rura Ø ~0,1 m może nie mieć trafienia w szczyt) — dlatego wynik = DOLNA granica wysokości.
"""
import sys, os, json, math, glob
import numpy as np
import laspy
from PIL import Image, ImageDraw
from pyproj import Transformer

T = Transformer.from_crs('EPSG:4326', 'EPSG:2180', always_xy=True)
LAZ_DIR, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

# godło arkusza LIDAR 2025 → dach; punkty masztów (lat, lon) uzupełniane po obejrzeniu map (masts_extra.json)
ROOFS = {
    'skorupska17': ('N-34-107-C-b-1-4-4-2', 53.133953, 23.180958),
    'dobra3': ('N-34-107-C-b-1-4-2-4', 53.138052, 23.180663),
    'zwierzyniecka4': ('N-34-107-C-b-3-1-2-4', 53.119647, 23.149357),
    'hallera19': ('N-34-107-C-b-1-1-3-1', 53.153529, 23.125354),
    'kopernika5a': ('N-34-107-C-b-3-1-2-1', 53.121630, 23.143090),
    # wieżowiec z M57 — tylko kontrola krzyżowa wysokości (środek z REVIEW-2026-11-14-s20-mistral-m57 §1)
    'wiezowiec_m57': ('N-34-107-C-b-1-2-3-2', 53.153231, 23.168022),
}
S = 70.0
CELL = 0.25
extra_path = os.path.join(os.path.dirname(OUT.rstrip('/')) or '.', 'masts_xy.json')
EXTRA = json.load(open(extra_path)) if os.path.exists(extra_path) else {}


def gps_to_utc(t):
    # LAS 1.4 adjusted standard GPS time: GPS sekundy − 1e9; GPS epoka 1980-01-06; GPS−UTC = 18 s (od 2017)
    import datetime
    return datetime.datetime(1980, 1, 6) + datetime.timedelta(seconds=float(t) + 1e9 - 18)


res = {}
for name, (godlo, lat, lon) in ROOFS.items():
    fn = glob.glob(os.path.join(LAZ_DIR, '*%s.laz' % godlo))[0]
    las = laspy.read(fn)
    x, y, z = np.asarray(las.x), np.asarray(las.y), np.asarray(las.z)
    cls = np.asarray(las.classification)
    cx, cy = T.transform(lon, lat)
    m = (abs(x - cx) < S / 2) & (abs(y - cy) < S / 2)
    x, y, z, cls = x[m], y[m], z[m], cls[m]
    gt = np.asarray(las.gps_time)[m]
    gsf = int(las.header.global_encoding.gps_time_type) if hasattr(las.header.global_encoding, 'gps_time_type') else None
    r = np.hypot(x - cx, y - cy)
    b = (cls == 6) & (r < 15)
    zp90 = float(np.percentile(z[b], 90)) if b.sum() else float(np.percentile(z[r < 15], 90))
    band = (r < 15) & (z > zp90 - 3) & (z <= zp90)
    zroof = float(np.median(z[band]))
    iqr = float(np.percentile(z[band], 75) - np.percentile(z[band], 25))
    ground = float(np.median(z[cls == 2])) if (cls == 2).sum() else float('nan')
    # mapa wysokości nad dachem
    n = int(S / CELL)
    ix = ((x - (cx - S / 2)) / CELL).astype(int).clip(0, n - 1)
    iy = ((cy + S / 2 - y) / CELL).astype(int).clip(0, n - 1)
    hmax = np.full((n, n), -99.0)
    np.maximum.at(hmax, (iy, ix), z - zroof)
    img = np.zeros((n, n, 3), np.uint8)
    hv = hmax.copy()
    # skala: <−1 m szary ciemny (grunt/niżej), −1..0.5 m szary jasny (dach), 0.5..15 m żółty→czerwony→biały
    img[:] = (30, 30, 30)
    img[(hv > -1) & (hv <= 0.5)] = (120, 120, 120)
    k = (hv > 0.5)
    t = np.clip((hv - 0.5) / 12.0, 0, 1)
    img[k, 0] = 255
    img[k, 1] = (255 * (1 - t[k])).astype(np.uint8)
    img[k, 2] = (255 * np.clip(t[k] * 2 - 1, 0, 1)).astype(np.uint8)
    img[hv == -99] = (0, 0, 60)
    im = Image.fromarray(img).resize((n * 3, n * 3), Image.NEAREST)
    d = ImageDraw.Draw(im)
    sc = 3 / CELL
    for g in range(0, int(S) + 1, 10):
        d.line((g * sc, 0, g * sc, 8), fill=(0, 255, 255)); d.line((0, g * sc, 8, g * sc), fill=(0, 255, 255))
    d.ellipse((S / 2 * sc - 4, S / 2 * sc - 4, S / 2 * sc + 4, S / 2 * sc + 4), outline=(0, 255, 0))
    d.text((10, n * 3 - 30), '%s  Zroof=%.2f  10 m siatka  N^  zolty 0.5 m -> czerwony 6.5 m -> bialy 12.5 m nad dachem' % (name, zroof), fill=(0, 255, 255))
    masts = []
    for mm_ in EXTRA.get(name, []):
        mx, my = mm_['dx'] + cx, mm_['dy'] + cy
        rr = np.hypot(x - mx, y - my)
        sel = rr < mm_.get('r', 1.5)
        if sel.sum() == 0:
            masts.append({**mm_, 'n_pts': 0}); continue
        top = float(z[sel].max())
        npts_above = int(((z[sel] - zroof) > 1.0).sum())
        masts.append({**mm_, 'z_top': round(top, 2), 'h_nad_dachem': round(top - zroof, 2), 'n_pts_r': int(sel.sum()),
                      'n_pts_powyzej_1m': npts_above})
        px, py = (mx - (cx - S / 2)) * sc, ((cy + S / 2) - my) * sc
        d.ellipse((px - 6, py - 6, px + 6, py + 6), outline=(0, 255, 0), width=2)
        d.text((px + 8, py - 8), '%s %.1f' % (mm_['id'], top - zroof), fill=(0, 255, 0))
    # automatyczne skupiska: komórki > 1,0 m nad dachem, w promieniu 35 m, sąsiedztwo 8
    from scipy import ndimage
    yy, xx = np.mgrid[0:n, 0:n]
    near = np.hypot((xx + 0.5) * CELL - S / 2, (yy + 0.5) * CELL - S / 2) < 35
    above = (hmax > 1.0) & (hmax < 60) & near
    lab, nl = ndimage.label(above, structure=np.ones((3, 3)))
    clusters = []
    for li in range(1, nl + 1):
        cm = lab == li
        area = float(cm.sum() * CELL * CELL)
        iy_, ix_ = np.unravel_index(np.argmax(np.where(cm, hmax, -99)), hmax.shape)
        dx_, dy_ = (ix_ + 0.5) * CELL - S / 2, S / 2 - (iy_ + 0.5) * CELL
        mx, my = cx + dx_, cy + dy_
        rr = np.hypot(x - mx, y - my)
        ann = (rr > 2.0) & (rr < 6.0) & (abs(z - zroof) < 4)
        zloc = float(np.median(z[ann])) if ann.sum() > 10 else zroof
        top = float(hmax[iy_, ix_] + zroof)
        if top - zloc < 1.5 and area < 4:
            continue
        clusters.append({'id': 'c%d' % li, 'dx': round(dx_, 2), 'dy': round(dy_, 2), 'area_m2': round(area, 2),
                         'h_glob': round(top - zroof, 2), 'Z_base_lok': round(zloc, 2), 'h_lok': round(top - zloc, 2),
                         'n_cells': int(cm.sum())})
    clusters.sort(key=lambda c: -c['h_lok'])
    for c in clusters[:12]:
        px, py = (c['dx'] + S / 2) * sc, (S / 2 - c['dy']) * sc
        d.rectangle((px - 5, py - 5, px + 5, py + 5), outline=(0, 255, 255))
        d.text((px + 7, py + 2), '%s %.1f' % (c['id'], c['h_lok']), fill=(0, 255, 255))
    im.save(os.path.join(OUT, 'lidar_%s.png' % name))
    hs = [m_['h_nad_dachem'] for m_ in masts if 'h_nad_dachem' in m_]
    t0, t1 = float(gt.min()), float(gt.max())
    res[name] = {
        'laz': os.path.basename(fn), 'n_pts_wycinek': int(m.sum()), 'x2180': round(cx, 2), 'y2180': round(cy, 2),
        'Z_roof_m_EVRF2007': round(zroof, 2), 'roof_band_IQR_m': round(iqr, 2), 'Z_ground_median': round(ground, 2),
        'roof_above_ground_m': round(zroof - ground, 1),
        'gps_time_min': t0, 'gps_time_max': t1, 'utc_min': str(gps_to_utc(t0)), 'utc_max': str(gps_to_utc(t1)),
        'classes': {int(c): int((cls == c).sum()) for c in np.unique(cls)},
        'masts': masts, 'clusters': clusters[:15],
        'h_min_med_max': [round(min(hs), 1), round(float(np.median(hs)), 1), round(max(hs), 1)] if hs else None,
    }
    print(name, json.dumps({k: v for k, v in res[name].items() if k != 'masts'}, ensure_ascii=False))
    for m_ in masts:
        print('   ', m_)
    for c in clusters[:15]:
        print('    C', c)
json.dump(res, open(os.path.join(OUT, 'lidar_roofs.json'), 'w'), ensure_ascii=False, indent=1)
