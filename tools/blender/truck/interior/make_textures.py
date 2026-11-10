"""Track A5 — self-made tileable PBR detail maps + display/label graphics for the cab interior.

    uv run --no-project --with pillow --with numpy python tools/blender/truck/interior/make_textures.py

Everything is synthesised here (numpy noise, Worley cells, hand-placed vector shapes);
no photos, no downloaded assets, no generator images. Output (PNG, small) goes to
art-source/truck/interior/textures/ and is consumed by build_interior.py.

Map conventions (match glTF so Blender/Unity import is straightforward):
  <set>_var.png    albedo VARIATION, linear, mean ~0.5; final albedo = tint * (0.7 + 0.6 * var)
                   -> one map serves every trim colour (trim colour is a material parameter)
  <set>_nrm.png    tangent-space normal, OpenGL (+Y up) convention (Blender + Unity)
  <set>_orm.png    R = micro AO (cavity), G = roughness, B = metallic
Display graphics are sRGB colour images used as emission behind cover glass.
Tileability: all noise is generated in the frequency domain or on a wrapped cell grid,
so every *_var/_nrm/_orm map tiles seamlessly.

Text on displays is rasterised with Inter (SIL OFL 1.1) taken from the Blender install (found via PATH);
fallback = Pillow's bundled Aileron (CC0, no Polish diacritics). No system fonts, no font file in the repo.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
OUT = os.path.join(REPO, "art-source", "truck", "interior", "textures")
RNG = np.random.default_rng(20261109)


# ---------------------------------------------------------------- tileable noise
def fnoise(n, f_lo, f_hi, power=1.0, aniso=(1.0, 1.0)):
    """Periodic band-limited noise, normalised to [0,1]. f in cycles per tile."""
    w = RNG.standard_normal((n, n))
    F = np.fft.fft2(w)
    fy = np.fft.fftfreq(n)[:, None] * n * aniso[1]
    fx = np.fft.fftfreq(n)[None, :] * n * aniso[0]
    r = np.sqrt(fx * fx + fy * fy) + 1e-6
    band = np.exp(-((np.log(r) - np.log(math.sqrt(f_lo * f_hi))) ** 2) / (2 * (math.log(f_hi / f_lo) / 2.5) ** 2))
    band /= r ** (power - 1.0)
    out = np.real(np.fft.ifft2(F * band))
    out -= out.min()
    return out / max(out.max(), 1e-9)


def worley(n, cells, jitter=0.85):
    """Wrapped Worley noise: returns F1, F2 distances (in cell units) on an n x n tile."""
    pts = RNG.random((cells, cells, 2)) * jitter + (1 - jitter) / 2
    ys, xs = np.mgrid[0:n, 0:n].astype(np.float32) * (cells / n)
    cy, cx = np.floor(ys).astype(int), np.floor(xs).astype(int)
    f1 = np.full((n, n), 9.0, np.float32)
    f2 = np.full((n, n), 9.0, np.float32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            gy, gx = cy + dy, cx + dx
            p = pts[gy % cells, gx % cells]
            d = np.sqrt((gx + p[..., 0] - xs) ** 2 + (gy + p[..., 1] - ys) ** 2)
            f2 = np.where(d < f1, f1, np.minimum(f2, d))
            f1 = np.minimum(f1, d)
    return f1, f2


def blur_wrap(a, k):
    """Gaussian blur with wrap-around (tile-safe), via FFT."""
    n = a.shape[0]
    f = np.fft.fftfreq(n)
    g = np.exp(-(f[:, None] ** 2 + f[None, :] ** 2) * (2 * math.pi * k) ** 2 / 2)
    return np.real(np.fft.ifft2(np.fft.fft2(a) * g))


def norm01(a):
    a = a - a.min()
    return a / max(a.max(), 1e-9)


def height_to_normal(h, strength):
    """Tile-safe normal map (OpenGL convention) from a height field in [0,1]."""
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    nx, ny, nz = -dx, dy, np.ones_like(h)  # image rows go down -> +dy flips for OpenGL green-up
    l = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / l, ny / l, nz / l], -1) * 0.5 + 0.5


def cavity(h, k=3.0, amt=1.0):
    c = h - blur_wrap(h, k)
    return np.clip(1.0 + c * 4.0 * amt, 0.0, 1.0)


def save_gray(a, name):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), "L").save(os.path.join(OUT, name), optimize=True)


def save_rgb(a, name):
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB").save(os.path.join(OUT, name), optimize=True)


def save_set(name, var, height, nstrength, rough, ao=None, metal=0.0):
    save_gray(var, f"{name}_var.png")
    save_rgb(height_to_normal(height, nstrength), f"{name}_nrm.png")
    ao = cavity(height) if ao is None else ao
    orm = np.stack([ao, np.clip(rough, 0, 1), np.full_like(ao, metal)], -1)
    save_rgb(orm, f"{name}_orm.png")
    print("set", name, var.shape)


# ---------------------------------------------------------------- material sets
def leather():
    """Pebble-grain automotive leather/vinyl. Tile = 0.12 m (see build_interior.TILE)."""
    n = 1024
    f1, f2 = worley(n, 96)
    pebble = norm01(blur_wrap(np.clip(f2 - f1, 0, 0.6), 1.2))       # raised pebbles, creases between
    fine = fnoise(n, 120, 400)
    crease = fnoise(n, 6, 20, aniso=(1.0, 3.0))                       # long soft creases (wear)
    h = 0.75 * pebble + 0.15 * fine + 0.10 * crease
    var = 0.5 + (pebble - 0.5) * 0.10 + (fnoise(n, 2, 8) - 0.5) * 0.12
    rough = 0.50 + (1 - pebble) * 0.14 + (fnoise(n, 3, 10) - 0.5) * 0.08
    save_set("leather", var, h, 2.2, rough)


def dashgrain():
    """Soft-touch moulded grain (fine stipple + low leathery cells). Tile = 0.10 m."""
    n = 1024
    f1, f2 = worley(n, 140, jitter=1.0)
    cells = norm01(blur_wrap(np.clip(f2 - f1, 0, 0.5), 0.8))
    stipple = fnoise(n, 250, 500)
    h = 0.55 * cells + 0.45 * stipple
    var = 0.5 + (fnoise(n, 2, 6) - 0.5) * 0.06 + (cells - 0.5) * 0.04
    rough = 0.66 + (1 - h) * 0.10 + (fnoise(n, 2, 8) - 0.5) * 0.06
    save_set("dashgrain", var, h, 1.4, rough)


def hardgrain():
    """Harder injection-moulded plastic: finer, flatter texture, slightly glossier. Tile = 0.08 m."""
    n = 512
    st = fnoise(n, 120, 250)
    h = st
    var = 0.5 + (fnoise(n, 2, 5) - 0.5) * 0.05
    rough = 0.52 + (1 - st) * 0.10
    save_set("hardgrain", var, h, 0.8, rough)


def fabric():
    """Knitted headliner / mattress fabric: fine 2x2 weave + fibre fuzz. Tile = 0.05 m."""
    n = 512
    y, x = np.mgrid[0:n, 0:n] / n
    k = 48  # yarns per tile
    wa = 0.5 + 0.5 * np.sin(2 * math.pi * k * x)
    wb = 0.5 + 0.5 * np.sin(2 * math.pi * k * y)
    over = (np.floor(x * k) + np.floor(y * k)) % 2
    weave = np.where(over > 0, wa * (0.6 + 0.4 * wb), wb * (0.6 + 0.4 * wa))
    fuzz = fnoise(n, 100, 256)
    h = 0.75 * weave + 0.25 * fuzz
    var = 0.5 + (weave - 0.5) * 0.12 + (fnoise(n, 2, 6) - 0.5) * 0.08
    rough = np.full_like(h, 0.88) + (fuzz - 0.5) * 0.06
    save_set("fabric", var, h, 1.0, rough)


def seatfabric():
    """Coarser seat-centre / bunk-cover cloth with a small woven pattern. Tile = 0.06 m."""
    n = 512
    y, x = np.mgrid[0:n, 0:n] / n
    k = 32
    rib = 0.5 + 0.5 * np.cos(2 * math.pi * k * (x + 0.5 * (np.floor(y * k * 2) % 2) / k))
    rib *= 0.6 + 0.4 * (0.5 + 0.5 * np.cos(2 * math.pi * k * 2 * y))
    fuzz = fnoise(n, 80, 256)
    h = 0.7 * rib + 0.3 * fuzz
    var = 0.5 + (rib - 0.5) * 0.16 + (fnoise(n, 2, 5) - 0.5) * 0.08
    rough = 0.9 + (fuzz - 0.5) * 0.05
    save_set("seatfabric", var, h, 1.2, rough)


def rubbermat():
    """Ribbed rubber floor mat with dust collected in the grooves. Tile = 0.40 m."""
    n = 1024
    y, x = np.mgrid[0:n, 0:n] / n
    ribs = 40  # ~10 mm pitch
    rib = np.clip(np.abs(((x * ribs) % 1.0) - 0.5) * 2.0, 0, 1)
    rib = 1.0 - np.clip((rib - 0.55) * 6.0, 0, 1)  # flat-topped ribs with sharp grooves
    rib = blur_wrap(rib, 1.0)
    wear = fnoise(n, 1, 4)
    scuff = fnoise(n, 20, 80, aniso=(1.0, 4.0))
    dust = np.clip((1 - rib) * 0.8 + (fnoise(n, 3, 12) - 0.5) * 0.6, 0, 1)
    h = rib * 0.9 + fnoise(n, 150, 400) * 0.1
    var = 0.45 + dust * 0.35 + (wear - 0.5) * 0.08 - (scuff > 0.7) * 0.04
    rough = 0.78 + dust * 0.12 - (wear - 0.5) * 0.10
    save_set("rubbermat", var, h, 3.0, rough)


def brushed():
    """Satin brushed aluminium / painted metal. Tile = 0.10 m, brushing along U."""
    n = 512
    streak = fnoise(n, 4, 200, aniso=(0.04, 1.0))
    h = streak * 0.6 + fnoise(n, 100, 256) * 0.4
    var = 0.5 + (streak - 0.5) * 0.10
    rough = 0.32 + (streak - 0.5) * 0.12
    save_set("brushed", var, h, 0.5, rough, metal=1.0)


def grime_mask():
    """Low-frequency smudge / dust mask for glass, dash top and floor (grayscale)."""
    n = 1024
    m = fnoise(n, 1.5, 6) * 0.6 + fnoise(n, 8, 40) * 0.3 + fnoise(n, 80, 300) * 0.1
    wipe = 0.5 + 0.5 * np.sin(np.linspace(0, 6 * math.pi, n))[None, :] * 0.0
    save_gray(norm01(m) * 0.9 + wipe * 0.0, "grime_mask.png")
    print("grime")


# ---------------------------------------------------------------- stitch / perforation / grille
def stitch():
    """RGBA strip: two parallel rows of lock stitches (tile along U every 4 stitches, 4 mm pitch)."""
    w, h = 256, 64
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pitch = w / 4
    for row_y in (18, 46):
        for i in range(4):
            x0 = i * pitch + pitch * 0.18
            x1 = i * pitch + pitch * 0.82
            for t in range(3):  # thread with a little shading: dark edge, light core
                c = (40 + t * 55, 40 + t * 55, 42 + t * 55, 255)
                d.line([(x0 + t, row_y), (x1 - t, row_y)], fill=c, width=7 - 2 * t)
            # needle holes pull the material in
            for xh in (x0 - 3, x1 + 3):
                d.ellipse([xh - 2, row_y - 2, xh + 2, row_y + 2], fill=(10, 10, 10, 200))
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    img.save(os.path.join(OUT, "stitch_rgba.png"), optimize=True)
    print("stitch")


def perforation():
    """Perforated-leather mask (seat centre panels): hex grid of 1.2 mm holes. Tile = 0.04 m."""
    n = 256
    img = Image.new("L", (n, n), 255)
    d = ImageDraw.Draw(img)
    k = 12
    for j in range(k + 1):
        for i in range(k + 1):
            x = (i + 0.5 * (j % 2)) * n / k
            y = j * n / k
            for ox in (-n, 0, n):
                for oy in (-n, 0, n):
                    d.ellipse([x + ox - 3.2, y + oy - 3.2, x + ox + 3.2, y + oy + 3.2], fill=30)
    img.filter(ImageFilter.GaussianBlur(0.7)).save(os.path.join(OUT, "perforation_mask.png"), optimize=True)
    print("perf")


def speaker_grille():
    """Speaker grille mask: punched round holes on a square grid (tile = 0.05 m)."""
    n = 256
    img = Image.new("L", (n, n), 255)
    d = ImageDraw.Draw(img)
    k = 16
    for j in range(k):
        for i in range(k):
            x, y = (i + 0.5) * n / k, (j + 0.5) * n / k
            d.ellipse([x - 4.5, y - 4.5, x + 4.5, y + 4.5], fill=0)
    img.filter(ImageFilter.GaussianBlur(0.6)).save(os.path.join(OUT, "grille_mask.png"), optimize=True)
    print("grille")


# ---------------------------------------------------------------- displays and labels
def ui_font_path():
    """Inter (SIL OFL 1.1) as shipped with Blender: has Polish glyphs (Pillow's bundled Aileron does not).
    The font is only used to rasterise text into textures; it is not copied into the repo or the build."""
    import glob
    import shutil
    exe = shutil.which("blender")
    if exe:
        hits = glob.glob(os.path.join(os.path.dirname(os.path.realpath(exe)), "*", "datafiles", "fonts", "Inter.woff2"))
        if hits:
            return hits[0]
    return None


_FONT_PATH = ui_font_path()


def font(size):
    if _FONT_PATH:
        return ImageFont.truetype(_FONT_PATH, size)
    return ImageFont.load_default(size)  # fallback: Aileron (CC0), no Polish diacritics


def arc_ticks(d, cx, cy, r, a0, a1, n_major, n_minor, col, col_minor, lw=3, ln=18):
    for i in range(n_major * n_minor + 1):
        a = math.radians(a0 + (a1 - a0) * i / (n_major * n_minor))
        major = i % n_minor == 0
        l = ln if major else ln * 0.5
        c = col if major else col_minor
        x0, y0 = cx + r * math.cos(a), cy - r * math.sin(a)
        x1, y1 = cx + (r - l) * math.cos(a), cy - (r - l) * math.sin(a)
        d.line([(x0, y0), (x1, y1)], fill=c, width=lw if major else max(1, lw - 1))


def telltale_row(d, W, y=12, s=44, pitch=72):
    """A6 r3 (REVIEW-2026-11-09-r2 A6 #6): full warning-lamp row along the top edge of the cluster, ISO 2575-style
    glyphs drawn here. Unlit lamps stay as faint grey symbols (as behind a real telltale lens); the vehicle state of
    the control frames (driving at 82 km/h, engine warm, dipped beam on, retarder in auto) lights only dipped beam and
    retarder-ready, both green. Order follows a typical EU truck: brakes/air first, then powertrain, then lamps."""
    off = (36, 37, 38)
    red, amber, green = (205, 52, 38), (226, 150, 28), (74, 168, 92)
    lit = {"retarder": green, "beam": green}
    names = ["park", "brake", "air", "abs", "trailer", "retarder", "mil", "preheat", "battery", "oil", "coolant",
             "belt", "beam"]
    x0 = (W - pitch * (len(names) - 1) - s) // 2
    lw = 4

    def arcs(x, c):  # brake-drum brackets either side of a circle
        d.arc([x - 4, y + 2, x + 14, y + s - 2], 110, 250, fill=c, width=lw)
        d.arc([x + s - 14, y + 2, x + s + 4, y + s - 2], -70, 70, fill=c, width=lw)

    def ring_text(x, c, t, fs=22):
        d.ellipse([x + 6, y + 4, x + s - 6, y + s - 4], outline=c, width=lw)
        f = font(fs)
        d.text((x + s / 2 - d.textlength(t, font=f) / 2, y + s / 2 - fs * 0.62), t, fill=c, font=f)

    for i, nm in enumerate(names):
        x = x0 + i * pitch
        c = lit.get(nm, off)
        if nm in ("park", "brake", "air", "abs", "retarder"):
            arcs(x, c)
            ring_text(x, c, {"park": "P", "brake": "!", "air": "I II", "abs": "ABS", "retarder": "R"}[nm],
                      fs={"air": 13, "abs": 12}.get(nm, 24))
            if nm == "air":  # low air: pressure waves under the symbol
                d.line([(x + 10, y + s + 1), (x + s - 10, y + s + 1)], fill=c, width=2)
        elif nm == "trailer":
            d.rectangle([x + 2, y + 8, x + s - 6, y + 28], outline=c, width=lw)
            d.line([(x + s - 6, y + 22), (x + s + 2, y + 22)], fill=c, width=lw)
            for wx in (x + 10, x + 22):
                d.ellipse([wx - 5, y + 28, wx + 5, y + 38], outline=c, width=3)
            d.text((x + 8, y + 10), "ABS", fill=c, font=font(11))
        elif nm == "mil":  # engine outline
            pts = [(x + 6, y + 16), (x + 14, y + 16), (x + 14, y + 10), (x + 30, y + 10), (x + 30, y + 16),
                   (x + 36, y + 16), (x + 40, y + 12), (x + 44, y + 12), (x + 44, y + 32), (x + 40, y + 32),
                   (x + 36, y + 28), (x + 32, y + 36), (x + 14, y + 36), (x + 6, y + 28)]
            d.line(pts + [pts[0]], fill=c, width=lw, joint="curve")
        elif nm == "preheat":  # glow-plug coil
            for k in range(4):
                d.arc([x + 6 + k * 8, y + 12, x + 18 + k * 8, y + 32], 180, 360, fill=c, width=lw)
            d.line([(x + 4, y + 36), (x + s - 4, y + 36)], fill=c, width=3)
        elif nm == "battery":
            d.rectangle([x + 4, y + 12, x + s - 4, y + 36], outline=c, width=lw)
            d.rectangle([x + 10, y + 7, x + 16, y + 12], fill=c)
            d.rectangle([x + s - 16, y + 7, x + s - 10, y + 12], fill=c)
            d.line([(x + 10, y + 23), (x + 17, y + 23)], fill=c, width=3)
            d.line([(x + s - 18, y + 23), (x + s - 10, y + 23)], fill=c, width=3)
            d.line([(x + s - 14, y + 19), (x + s - 14, y + 27)], fill=c, width=3)
        elif nm == "oil":  # oil can with a drop
            d.polygon([(x + 4, y + 22), (x + 16, y + 18), (x + 30, y + 18), (x + 42, y + 12), (x + 32, y + 32),
                       (x + 8, y + 32)], outline=c, width=lw)
            d.ellipse([x + 40, y + 26, x + 46, y + 34], fill=c)
        elif nm == "coolant":  # thermometer in waves
            d.line([(x + s / 2, y + 4), (x + s / 2, y + 28)], fill=c, width=5)
            d.ellipse([x + s / 2 - 6, y + 26, x + s / 2 + 6, y + 38], fill=c)
            for k, xx in enumerate((x + 4, x + s / 2 + 10)):
                d.line([(xx, y + 40), (xx + 6, y + 37), (xx + 12, y + 40)], fill=c, width=2)
        elif nm == "belt":
            d.ellipse([x + 16, y + 2, x + 28, y + 14], outline=c, width=3)
            d.line([(x + 22, y + 14), (x + 22, y + 34)], fill=c, width=lw)
            d.line([(x + 12, y + 16), (x + 32, y + 32)], fill=c, width=lw)
            d.line([(x + 12, y + 40), (x + 32, y + 40)], fill=c, width=3)
        elif nm == "beam":  # dipped beam
            d.pieslice([x, y + 4, x + 40, y + 40], 90, 270, fill=c)
            d.rectangle([x + 20, y + 4, x + 24, y + 40], fill=c)
            for k in range(3):
                d.line([(x + 30, y + 10 + 12 * k), (x + 52, y + 16 + 12 * k)], fill=c, width=4)


def cluster_display():
    """12.3-inch class instrument cluster screen (aspect ~ 2.6:1), daytime driving state (A6 layout).

    One primary speed readout (large digital, centre) as on 2020s EU truck clusters; rev counter as an arc with the
    green economy band (left); fuel + AdBlue (bottom left) and both air-brake circuit pressures (bottom right) are on
    the screen now, because the physical round dials were dropped (they sat behind the rim from the eye point).
    Telltale row along the top edge (only lit telltales are drawn). Region boxes match sightline_test.CLUSTER_REGIONS.
    Calm palette: near-black background, warm-white graphics, one green band, a red needle.
    """
    W, H = 1560, 600
    img = Image.new("RGB", (W, H), (6, 7, 8))
    d = ImageDraw.Draw(img)
    white, grey, dim = (225, 222, 214), (130, 130, 128), (58, 59, 60)
    red, green, blue = (205, 52, 38), (74, 150, 92), (110, 160, 210)
    # ---- rev counter (left): 0-2500 1/min, green band 1000-1500, needle at 1180
    cx, cy, r = 250, 300, 205
    a0, a1, vmax = 210, -30, 2500
    for t in np.linspace(1000, 1500, 80):
        a = math.radians(a0 + (a1 - a0) * t / vmax)
        d.ellipse([cx + (r - 8) * math.cos(a) - 5, cy - (r - 8) * math.sin(a) - 5,
                   cx + (r - 8) * math.cos(a) + 5, cy - (r - 8) * math.sin(a) + 5], fill=green)
    arc_ticks(d, cx, cy, r, a0, a1, 5, 5, white, grey, lw=4, ln=24)
    f = font(32)
    for i in range(6):
        a = math.radians(a0 + (a1 - a0) * i / 5)
        t = str(i * 5)
        tx, ty = cx + (r - 56) * math.cos(a), cy - (r - 56) * math.sin(a)
        d.text((tx - d.textlength(t, font=f) / 2, ty - 18), t, fill=white, font=f)
    a = math.radians(a0 + (a1 - a0) * 1180 / vmax)
    d.line([(cx - 26 * math.cos(a), cy + 26 * math.sin(a)), (cx + (r - 14) * math.cos(a), cy - (r - 14) * math.sin(a))],
           fill=red, width=7)
    d.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], fill=(28, 28, 30), outline=dim, width=2)
    fl = font(24)
    d.text((cx - d.textlength("1/min x100", font=fl) / 2, cy + 52), "1/min x100", fill=grey, font=fl)
    # ---- centre: one large digital speed, unit, CC / limiter, AMT gear + mode
    cx = W // 2
    fb = font(196)
    d.text((cx - d.textlength("82", font=fb) / 2, 40), "82", fill=white, font=fb)
    fm = font(36)
    d.text((cx - d.textlength("km/h", font=fm) / 2, 262), "km/h", fill=grey, font=fm)
    fs = font(30)
    d.text((cx - 175, 320), "CC 85", fill=green, font=fs)
    d.text((cx + 60, 320), "LIM 90", fill=grey, font=fs)
    d.rounded_rectangle([cx - 150, 400, cx + 150, 500], radius=12, fill=(20, 21, 23))
    fg = font(70)
    d.text((cx - 128, 410), "A", fill=grey, font=fg)
    d.text((cx - 22, 410), "12", fill=white, font=fg)
    d.text((cx + 88, 432), "E", fill=green, font=font(44))
    # ---- right top: trip computer
    x0 = 1150
    for i, (txt, col) in enumerate((("14:32", white), ("+7 °C", white), ("184 327 km", grey), ("T 412,6 km", grey))):
        d.text((x0 + (i % 2) * 200, 70 + (i // 2) * 60), txt, fill=col, font=fs)
    d.line([(x0, 205), (W - 40, 205)], fill=dim, width=2)
    d.text((x0, 228), "Ø 28,4 l/100 km", fill=grey, font=fs)
    # ---- bottom left: fuel + AdBlue level bars with pump / drop glyphs
    for i, (lab, frac, col) in enumerate((("D", 0.62, white), ("AdBlue", 0.80, blue))):
        y = 470 + i * 52
        d.text((40, y - 10), lab, fill=grey, font=font(26))
        d.rectangle([150, y, 350, y + 18], outline=dim, width=2)
        d.rectangle([153, y + 3, 153 + int(194 * frac), y + 15], fill=col)
        for k in range(1, 4):
            d.line([(150 + 50 * k, y + 18), (150 + 50 * k, y + 26)], fill=dim, width=2)
    # ---- bottom right: both air-brake circuits (bar), service range marked
    for i, (lab, v) in enumerate((("I", 10.4), ("II", 10.2))):
        y = 470 + i * 52
        d.text((1200, y - 10), lab, fill=grey, font=font(26))
        d.rectangle([1240, y, 1420, y + 18], outline=dim, width=2)
        d.rectangle([1243, y + 3, 1243 + int(174 * v / 12.5), y + 15], fill=white)
        d.line([(1240 + int(180 * 8.5 / 12.5), y - 4), (1240 + int(180 * 8.5 / 12.5), y + 22)], fill=grey, width=2)
        d.text((1432, y - 10), f"{v:.1f}".replace(".", ","), fill=white, font=font(28))
    d.text((1460, 412), "bar", fill=grey, font=font(24))
    telltale_row(d, W)
    img.save(os.path.join(OUT, "display_cluster.png"), optimize=True)
    print("cluster")


def infotainment_display():
    """10-inch centre screen: truck navigation, calm day palette (generic roads, fictional labels)."""
    W, H = 1280, 768
    img = Image.new("RGB", (W, H), (226, 226, 220))
    d = ImageDraw.Draw(img)
    rng = np.random.default_rng(7)
    # blocks of land use
    for _ in range(26):
        x, y = rng.integers(0, W), rng.integers(0, H - 120)
        w, h = rng.integers(60, 260), rng.integers(40, 180)
        col = [(214, 222, 204), (206, 214, 196), (220, 218, 210)][rng.integers(0, 3)]
        d.rectangle([x, y, x + w, y + h], fill=col)
    d.polygon([(0, 520), (300, 470), (520, 560), (700, 640), (0, 640)], fill=(188, 210, 226))  # river
    # roads
    roads = [[(-20, 300), (300, 330), (640, 360), (980, 300), (1300, 260)],
             [(420, -20), (460, 200), (640, 360), (700, 640)],
             [(900, -20), (880, 180), (980, 300), (1040, 640)],
             [(100, 640), (220, 420), (300, 330), (260, -20)]]
    for r in roads:
        d.line(r, fill=(250, 250, 248), width=22, joint="curve")
    for r in roads:
        d.line(r, fill=(255, 255, 255), width=14, joint="curve")
    d.line([(-20, 300), (300, 330), (640, 360), (980, 300), (1300, 260)], fill=(240, 200, 120), width=16, joint="curve")
    # route
    d.line([(640, 640), (640, 360), (980, 300), (1300, 260)], fill=(46, 110, 190), width=12, joint="curve")
    d.polygon([(640, 560), (622, 600), (640, 590), (658, 600)], fill=(30, 30, 30))
    # top manoeuvre box + bottom bar
    d.rectangle([0, 0, 360, 130], fill=(36, 70, 120))
    d.line([(60, 100), (60, 50), (110, 50)], fill=(255, 255, 255), width=12)
    d.polygon([(110, 34), (140, 50), (110, 66)], fill=(255, 255, 255))
    d.text((170, 30), "400 m", fill=(255, 255, 255), font=font(46))
    d.text((170, 85), "Trasa S8", fill=(210, 220, 235), font=font(26))
    d.rectangle([0, H - 110, W, H], fill=(40, 42, 46))
    d.text((40, H - 82), "14:58", fill=(255, 255, 255), font=font(44))
    d.text((240, H - 82), "126 km", fill=(255, 255, 255), font=font(44))
    d.text((520, H - 76), "Białystok  ·  Baza Zachód", fill=(190, 192, 196), font=font(32))
    d.rectangle([W - 120, H - 102, W - 20, H - 18], outline=(120, 122, 126), width=2)
    d.text((W - 100, H - 80), "MENU", fill=(200, 200, 200), font=font(26))
    img.save(os.path.join(OUT, "display_infotainment.png"), optimize=True)
    print("infotainment")


def din_displays():
    """Small LCD faces for the overhead DIN units: digital tachograph + radio (negative LCD)."""
    W, H = 512, 256
    img = Image.new("RGB", (W, H), (10, 12, 10))
    d = ImageDraw.Draw(img)
    lcd = (150, 200, 120)
    d.text((14, 10), "1 ▶ 00h47  ‖ 09h12", fill=lcd, font=font(34))
    d.text((14, 60), "2 ●  14:32   82km/h", fill=lcd, font=font(34))
    d.line([(0, 128), (W, 128)], fill=(0, 0, 0), width=4)
    d.text((14, 140), "FM  98,4", fill=(220, 150, 60), font=font(44))
    d.text((14, 196), "CH 19   AM", fill=(220, 150, 60), font=font(34))
    img.save(os.path.join(OUT, "display_din.png"), optimize=True)
    print("din")


# --- switch icon atlas: 8x4 cells, white symbols on black (ISO 2575-style, drawn here)
ICONS = ["low_beam", "fog_rear", "hazard", "diff_lock", "work_light", "beacon", "esp_off", "axle_lift",
         "ac", "fan", "defrost", "recirc", "seat_heat", "mirror_heat", "cab_light", "sun_blind",
         "lane_assist", "idle_up", "ptos", "horn_air", "tyre", "eco", "hill", "cruise",
         "plus", "minus", "res", "ok", "arrow_l", "arrow_r", "phone", "vol"]


def icon_atlas():
    C, N = 128, 8
    img = Image.new("L", (C * N, C * 4), 0)
    d = ImageDraw.Draw(img)
    w = 9

    def cell(i):
        return (i % N) * C, (i // N) * C

    for i, name in enumerate(ICONS):
        x, y = cell(i)
        cx, cy = x + C / 2, y + C / 2
        if name == "low_beam":
            d.chord([cx - 30, cy - 28, cx + 10, cy + 28], 90, 270, fill=255)
            for k in range(4):
                yy = cy - 22 + k * 15
                d.line([(cx + 6, yy), (cx + 40, yy + 10)], fill=255, width=w)
        elif name == "fog_rear":
            d.chord([cx - 10, cy - 28, cx + 30, cy + 28], 270, 90, fill=255)
            for k in range(3):
                d.line([(cx - 42, cy - 16 + k * 16), (cx - 14, cy - 16 + k * 16)], fill=255, width=w)
            d.line([(cx - 30, cy - 34), (cx - 30, cy + 34)], fill=255, width=5)
        elif name == "hazard":
            for s in (40, 22):
                d.polygon([(cx, cy - s), (cx + s * 0.87, cy + s * 0.5), (cx - s * 0.87, cy + s * 0.5)],
                          outline=255, width=w if s == 40 else 6)
        elif name == "diff_lock":
            d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], outline=255, width=w)
            d.line([(cx - 44, cy), (cx - 22, cy)], fill=255, width=w)
            d.line([(cx + 22, cy), (cx + 44, cy)], fill=255, width=w)
            d.line([(cx, cy - 22), (cx, cy + 22)], fill=255, width=6)
        elif name == "work_light":
            d.rectangle([cx - 30, cy - 18, cx, cy + 18], outline=255, width=w)
            for k in (-1, 0, 1):
                d.line([(cx + 8, cy + k * 16), (cx + 38, cy + k * 26)], fill=255, width=6)
        elif name == "beacon":
            d.chord([cx - 22, cy - 26, cx + 22, cy + 18], 180, 360, fill=255)
            d.rectangle([cx - 30, cy + 14, cx + 30, cy + 26], fill=255)
            for a in (200, 240, 300, 340):
                r = math.radians(a)
                d.line([(cx + 30 * math.cos(r), cy - 4 + 30 * math.sin(r)), (cx + 44 * math.cos(r), cy - 4 + 44 * math.sin(r))],
                       fill=255, width=5)
        elif name == "esp_off":
            d.rounded_rectangle([cx - 24, cy - 34, cx + 24, cy + 8], radius=8, outline=255, width=w)
            for k in (-1, 1):
                d.arc([cx - 40 + k * 14, cy + 4, cx + 40 + k * 14, cy + 34], 200, 340, fill=255, width=5)
            d.text((cx - 18, cy + 18), "OFF", fill=255, font=font(18))
        elif name == "axle_lift":
            d.line([(cx - 40, cy + 20), (cx + 40, cy + 20)], fill=255, width=w)
            for k in (-28, 0, 28):
                d.ellipse([cx + k - 9, cy + 26, cx + k + 9, cy + 44], fill=255)
            d.polygon([(cx, cy - 40), (cx - 16, cy - 16), (cx + 16, cy - 16)], fill=255)
            d.line([(cx, cy - 18), (cx, cy + 10)], fill=255, width=7)
        elif name == "ac":
            d.text((cx - 28, cy - 24), "A/C", fill=255, font=font(40))
        elif name == "fan":
            for a in range(0, 360, 90):
                r = math.radians(a)
                d.pieslice([cx - 36, cy - 36, cx + 36, cy + 36], a, a + 50, fill=255)
            d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=0)
        elif name == "defrost":
            d.arc([cx - 40, cy - 30, cx + 40, cy + 40], 200, 340, fill=255, width=w)
            d.line([(cx - 40, cy + 24), (cx + 40, cy + 24)], fill=255, width=w)
            for k in (-16, 0, 16):
                d.line([(cx + k, cy - 6), (cx + k + 6, cy - 32)], fill=255, width=5)
        elif name == "recirc":
            d.line([(cx - 40, cy + 26), (cx + 40, cy + 26)], fill=255, width=6)
            d.arc([cx - 30, cy - 34, cx + 30, cy + 26], 160, 380, fill=255, width=w)
            d.polygon([(cx - 36, cy + 8), (cx - 20, cy + 8), (cx - 28, cy + 22)], fill=255)
        elif name == "seat_heat":
            d.line([(cx - 20, cy + 30), (cx + 24, cy + 30), (cx + 24, cy + 14)], fill=255, width=w)
            d.line([(cx - 20, cy + 30), (cx - 26, cy - 30)], fill=255, width=w)
            for k in (-4, 10, 24):
                d.line([(cx + k - 10, cy - 30), (cx + k - 4, cy), (cx + k - 10, cy + 6)], fill=255, width=4)
        elif name == "mirror_heat":
            d.rectangle([cx - 34, cy - 24, cx + 26, cy + 24], outline=255, width=w)
            for k in (-12, 4):
                d.line([(cx + k, cy - 14), (cx + k + 6, cy), (cx + k, cy + 14)], fill=255, width=4)
        elif name == "cab_light":
            d.chord([cx - 30, cy - 30, cx + 30, cy + 20], 180, 360, fill=255)
            for k in (-1, 0, 1):
                d.line([(cx + k * 12, cy + 2), (cx + k * 26, cy + 34)], fill=255, width=5)
        elif name == "sun_blind":
            d.rectangle([cx - 38, cy - 34, cx + 38, cy - 22], fill=255)
            d.rectangle([cx - 34, cy - 22, cx + 34, cy + 10], outline=255, width=4)
            d.polygon([(cx, cy + 34), (cx - 12, cy + 18), (cx + 12, cy + 18)], fill=255)
        elif name == "lane_assist":
            for k in (-1, 1):
                d.line([(cx + k * 16, cy - 36), (cx + k * 34, cy + 36)], fill=255, width=w)
            d.rectangle([cx - 10, cy - 8, cx + 10, cy + 20], fill=255)
        elif name == "idle_up":
            d.text((cx - 30, cy - 26), "rpm", fill=255, font=font(30))
            d.polygon([(cx, cy + 6), (cx - 16, cy + 30), (cx + 16, cy + 30)], fill=255)
        elif name == "ptos":
            d.text((cx - 32, cy - 22), "PTO", fill=255, font=font(36))
        elif name == "horn_air":
            d.polygon([(cx - 36, cy - 10), (cx + 30, cy - 30), (cx + 30, cy + 30), (cx - 36, cy + 10)], outline=255, width=w)
        elif name == "tyre":
            d.ellipse([cx - 34, cy - 34, cx + 34, cy + 34], outline=255, width=w)
            d.text((cx - 6, cy - 22), "!", fill=255, font=font(40))
        elif name == "eco":
            d.text((cx - 32, cy - 22), "ECO", fill=255, font=font(36))
        elif name == "plus":
            d.line([(cx - 26, cy), (cx + 26, cy)], fill=255, width=w)
            d.line([(cx, cy - 26), (cx, cy + 26)], fill=255, width=w)
        elif name == "minus":
            d.line([(cx - 26, cy), (cx + 26, cy)], fill=255, width=w)
        elif name in ("res", "ok"):
            t = name.upper()
            f = font(44)
            d.text((cx - d.textlength(t, font=f) / 2, cy - 26), t, fill=255, font=f)
        elif name == "arrow_l":
            d.polygon([(cx - 24, cy), (cx + 16, cy - 26), (cx + 16, cy + 26)], fill=255)
        elif name == "arrow_r":
            d.polygon([(cx + 24, cy), (cx - 16, cy - 26), (cx - 16, cy + 26)], fill=255)
        elif name == "phone":
            d.arc([cx - 34, cy - 34, cx + 34, cy + 34], 120, 240, fill=255, width=14)
            d.ellipse([cx - 30, cy - 36, cx - 8, cy - 22], fill=255)
            d.ellipse([cx - 30, cy + 22, cx - 8, cy + 36], fill=255)
        elif name == "vol":
            d.polygon([(cx - 34, cy - 10), (cx - 18, cy - 10), (cx, cy - 28), (cx, cy + 28), (cx - 18, cy + 10),
                       (cx - 34, cy + 10)], fill=255)
            d.arc([cx - 10, cy - 22, cx + 22, cy + 22], 300, 60, fill=255, width=6)
            d.arc([cx - 10, cy - 36, cx + 36, cy + 36], 300, 60, fill=255, width=6)
        elif name == "cruise":   # r8: cruise control (ISO 2575-style: speedometer dial with a set-speed arrow)
            d.arc([cx - 34, cy - 26, cx + 34, cy + 42], 150, 390, fill=255, width=w)
            d.line([(cx, cy + 8), (cx + 16, cy - 10)], fill=255, width=7)
            d.ellipse([cx - 6, cy + 2, cx + 6, cy + 14], fill=255)
            d.polygon([(cx + 22, cy - 22), (cx + 42, cy - 40), (cx + 18, cy - 42)], fill=255)
            d.line([(cx + 30, cy - 32), (cx + 44, cy - 46)], fill=255, width=6)
        elif name == "hill":
            d.polygon([(cx - 40, cy + 30), (cx + 40, cy + 30), (cx + 40, cy - 20)], outline=255, width=w)
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    img.save(os.path.join(OUT, "icons_atlas.png"), optimize=True)
    print("icons", len(ICONS))


def gauge_faces():
    """Two small analogue-style gauges beside the screen: dual air pressure (0-12 bar, 2 needles) + fuel."""
    S = 512
    img = Image.new("RGB", (S * 2, S), (8, 8, 9))
    d = ImageDraw.Draw(img)
    white, grey, red = (220, 218, 210), (120, 120, 118), (200, 50, 36)
    for g in range(2):
        cx, cy, r = g * S + S / 2, S / 2 + 20, 200
        a0, a1 = 210, -30
        if g == 0:
            arc_ticks(d, cx, cy, r, a0, a1, 6, 4, white, grey, lw=6, ln=34)
            for i in range(7):
                a = math.radians(a0 + (a1 - a0) * i / 6)
                t = str(i * 2)
                d.text((cx + (r - 70) * math.cos(a) - 10, cy - (r - 70) * math.sin(a) - 18), t, fill=white, font=font(38))
            for v, col in ((10.4, red), (10.1, (230, 230, 230))):
                a = math.radians(a0 + (a1 - a0) * v / 12)
                d.line([(cx, cy), (cx + (r - 20) * math.cos(a), cy - (r - 20) * math.sin(a))], fill=col, width=9)
            d.text((cx - 30, cy + 70), "bar", fill=grey, font=font(36))
            d.text((cx - 36, cy + 112), "I   II", fill=grey, font=font(30))
        else:
            a0, a1 = 200, 340
            a0, a1 = 225, 135
            arc_ticks(d, cx, cy, r, 225, 135 - 180 + 180, 4, 2, white, grey, lw=6, ln=34)
            d.text((cx - r + 40, cy + 40), "0", fill=white, font=font(40))
            d.text((cx + r - 70, cy + 40), "1/1", fill=white, font=font(40))
            a = math.radians(225 + (-45 - 225) * 0.62)
            d.line([(cx, cy), (cx + (r - 20) * math.cos(a), cy - (r - 20) * math.sin(a))], fill=red, width=9)
            d.rectangle([cx - 20, cy + 70, cx + 18, cy + 120], outline=grey, width=6)
            d.line([(cx + 18, cy + 80), (cx + 34, cy + 96), (cx + 34, cy + 120)], fill=grey, width=6)
        d.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill=(30, 30, 32))
    img.save(os.path.join(OUT, "display_gauges.png"), optimize=True)
    print("gauges")


def tree_cards():
    """Render-backdrop only (not a game asset): 8 tree silhouettes for alpha cards, 256 x 512 each, RGBA.
    Podlasie mixed forest edge: Scots pine (bare upper trunk, flat irregular crown clumps), Norway spruce (dark
    cone), birch (white trunk, loose oval crown), alder (dense round crown). Drawn from many small leaf/needle blobs
    with value noise so the edges are ragged, never a smooth 'lollipop'."""
    CW, CH = 256, 512
    img = Image.new("RGBA", (CW * 8, CH), (0, 0, 0, 0))
    rng = np.random.default_rng(77)
    kinds = ["pine", "pine", "pine", "spruce", "spruce", "birch", "birch", "alder"]
    for k, kind in enumerate(kinds):
        tile = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        d = ImageDraw.Draw(tile)
        cx = CW // 2 + int(rng.integers(-10, 10))
        if kind == "pine":
            trunk_top = int(CH * rng.uniform(0.30, 0.42))
            d.polygon([(cx - 5, CH), (cx + 5, CH), (cx + 2, trunk_top), (cx - 2, trunk_top)], fill=(78, 54, 40, 255))
            for _ in range(int(rng.integers(5, 9))):  # crown clumps on short branches
                bx = cx + int(rng.normal(0, 34))
                by = int(rng.uniform(CH * 0.04, trunk_top + 40))
                d.line([(cx, min(by + 20, trunk_top + 60)), (bx, by)], fill=(60, 44, 34, 255), width=3)
                for _ in range(260):
                    x = bx + rng.normal(0, 26)
                    y = by + rng.normal(0, 11)
                    r = rng.uniform(2, 5)
                    g = int(rng.uniform(52, 82))
                    d.ellipse([x - r, y - r, x + r, y + r], fill=(int(g * 0.62), g, int(g * 0.55), 255))
        elif kind == "spruce":
            d.line([(cx, CH), (cx, int(CH * 0.02))], fill=(50, 38, 30, 255), width=6)
            for _ in range(3800):
                t = rng.uniform(0.0, 1.0) ** 0.8
                y = CH * 0.02 + t * CH * 0.93
                half = 6 + t * 70
                x = cx + rng.uniform(-half, half) * (0.75 + 0.25 * np.sin(y * 0.15))
                r = rng.uniform(2, 4)
                g = int(rng.uniform(36, 58))
                d.ellipse([x - r, y - r, x + r, y + r], fill=(int(g * 0.6), g, int(g * 0.62), 255))
        elif kind == "birch":
            top = int(CH * 0.10)
            d.polygon([(cx - 4, CH), (cx + 4, CH), (cx + 2, top), (cx - 2, top)], fill=(205, 200, 190, 255))
            for y in range(top, CH, 9):
                if rng.random() < 0.6:
                    d.line([(cx - 4, y), (cx + 4, y + 1)], fill=(40, 38, 36, 255), width=2)
            for _ in range(2600):
                a = rng.uniform(0, 2 * np.pi)
                rr = rng.uniform(0, 1) ** 0.6
                x = cx + np.cos(a) * rr * 70
                y = CH * 0.36 + np.sin(a) * rr * 150 * (0.8 if np.sin(a) > 0 else 1.0)
                r = rng.uniform(1.5, 3.5)
                g = int(rng.uniform(80, 118))
                d.ellipse([x - r, y - r, x + r, y + r], fill=(int(g * 0.72), g, int(g * 0.45), 255))
        else:
            d.polygon([(cx - 6, CH), (cx + 6, CH), (cx + 3, int(CH * 0.45)), (cx - 3, int(CH * 0.45))], fill=(58, 50, 44, 255))
            for _ in range(3200):
                a = rng.uniform(0, 2 * np.pi)
                rr = rng.uniform(0, 1) ** 0.5
                x = cx + np.cos(a) * rr * 95
                y = CH * 0.36 + np.sin(a) * rr * 140
                r = rng.uniform(2, 4.5)
                g = int(rng.uniform(52, 80))
                d.ellipse([x - r, y - r, x + r, y + r], fill=(int(g * 0.66), g, int(g * 0.46), 255))
        img.paste(tile, (k * CW, 0))
    img.save(os.path.join(OUT, "tree_cards.png"), optimize=True)
    print("tree cards")


def mirror_placeholders():
    """Render-only stand-ins for the mirror RenderTextures (REVIEW-2026-11-09-r2 A6 #4): a blurred 'probe' of what a
    class II/IV mirror sees on the yard, so the control frames show no white slabs. Not a game texture: in Unity every
    MIRROR_* quad gets its own camera RT. Linear values ~ scene radiance / sky (sky ~0.9), shader scales by light.

    mirror_rt_side.png (256 x 512, portrait): the cab flank runs up the INNER edge (u = 1; the shader flips u on the
    right-hand mirrors), sky above a ragged treeline and a low hall, asphalt with a lane line converging to the rear.
    mirror_rt_down.png (256 x 256): kerb/front mirror, mostly asphalt with a parking line and the dark tyre/step
    corner."""
    rng = np.random.default_rng(4242)
    w, h = 256, 512
    vv = np.linspace(0.0, 1.0, h)[:, None] * np.ones((1, w))     # 0 top .. 1 bottom
    uu = np.ones((h, 1)) * np.linspace(0.0, 1.0, w)[None, :]
    img = np.zeros((h, w, 3))
    sky = np.array([0.80, 0.83, 0.87]) * (1.0 - 0.18 * (1 - vv[..., None]))
    img[:] = sky
    hor = 0.36 + 0.004 * np.sin(uu * 5.0)                          # horizon (slightly bent by mirror curvature)
    hall = (uu > 0.08) & (uu < 0.52) & (vv > hor - 0.05) & (vv < hor)
    img[hall] = (0.55, 0.56, 0.57)
    tree_top = hor - 0.025 - 0.025 * norm01(np.cumsum(rng.normal(0, 1, w)))[None, :]
    trees = (vv > tree_top) & (vv < hor) & ~hall
    img[trees] = (0.085, 0.10, 0.075)
    ground = vv >= hor
    g = 0.20 + 0.03 * rng.normal(0, 1, (h, w))
    gd = np.clip((vv - hor) / (1 - hor + 1e-6), 0, 1)
    img[ground] = np.stack([g * (0.98 + 0.05 * gd), g * (0.98 + 0.05 * gd), g * 0.96], -1)[ground]
    lane = ground & (np.abs(uu - (0.30 - 0.22 * gd)) < 0.003 + 0.012 * gd)
    img[lane] = (0.55, 0.55, 0.53)
    # cab flank on the inner edge: perspective wedge (narrow at the horizon, wide near the mirror)
    edge = 1.0 - (0.05 + 0.20 * np.clip(vv - 0.05, 0, 1))
    cab = uu > edge
    paint = 0.50 - 0.14 * vv                                     # flank in its own shade
    img[cab] = np.stack([paint, paint, paint * 0.98], -1)[cab]
    win = cab & (vv < 0.26)                                       # side window band: dark glass
    img[win] = (0.10, 0.11, 0.115)
    gap = (np.abs(uu - (edge + 0.5 * (1 - edge))) < 0.004) & (vv > 0.26) & cab
    img[gap] = (0.05, 0.05, 0.05)
    step = cab & (vv > 0.86)                                       # steps / arch: dark
    img[step] = (0.04, 0.04, 0.04)
    im = Image.fromarray((np.clip(img, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8), "RGB")
    im = im.filter(ImageFilter.GaussianBlur(2.2))                  # probe blur
    arr = np.asarray(im).astype(np.float32) / 255.0
    vig = 1.0 - 0.25 * (np.abs(uu - 0.5) * 2) ** 4 - 0.25 * (np.abs(vv - 0.5) * 2) ** 4   # housing occlusion
    arr = arr * vig[..., None] ** (1 / 2.2)
    Image.fromarray((arr * 255).astype(np.uint8), "RGB").save(os.path.join(OUT, "mirror_rt_side.png"), optimize=True)
    # down-looking mirrors
    n = 256
    vv = np.linspace(0, 1, n)[:, None] * np.ones((1, n))
    uu = np.ones((n, 1)) * np.linspace(0, 1, n)[None, :]
    g = 0.19 + 0.035 * fnoise(n, 4, 60)
    img = np.stack([g, g, g * 0.97], -1)
    line = np.abs(uu * 0.8 + vv * 0.35 - 0.62) < 0.022
    img[line] = (0.50, 0.50, 0.48)
    tyre = (uu - 1.05) ** 2 + (vv - 1.05) ** 2 < 0.20
    img[tyre] = (0.035, 0.035, 0.035)
    im = Image.fromarray((np.clip(img, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8), "RGB").filter(ImageFilter.GaussianBlur(2.0))
    im.save(os.path.join(OUT, "mirror_rt_down.png"), optimize=True)
    print("mirror placeholders")


def main():
    os.makedirs(OUT, exist_ok=True)
    leather()
    dashgrain()
    hardgrain()
    fabric()
    seatfabric()
    rubbermat()
    brushed()
    grime_mask()
    stitch()
    perforation()
    speaker_grille()
    cluster_display()
    infotainment_display()
    din_displays()
    icon_atlas()
    gauge_faces()
    tree_cards()
    mirror_placeholders()
    tot = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
    print("TOTAL KB", tot // 1024)


if __name__ == "__main__":
    main()
