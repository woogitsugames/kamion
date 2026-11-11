"""Derive a cloud opacity/luminance map from a verified CC0 photographic HDRI.

Run via run-heavy.ps1. The original HDRI stays in ignored Data/raw; only the
derived PNG and source/axis metadata ship. No generated bitmap replaces a photo.
"""
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
ART = Path(__file__).resolve().parent
ASSET = "kloofendal_48d_partly_cloudy_puresky"
RAW = ROOT / "Data/raw/cc0/sky" / ASSET
OUT = ROOT / "game/Assets/_Project/Rendering/Resources/Sky"
source = RAW / f"{ASSET}_4k.hdr"
files = json.loads((RAW / "files.json").read_text(encoding="utf-8-sig"))
expected = files["hdri"]["4k"]["hdr"]
if source.stat().st_size != expected["size"] or hashlib.md5(source.read_bytes()).hexdigest() != expected["md5"]:
    raise ValueError("HDRI does not match the public Poly Haven file metadata")
dimensions = subprocess.check_output(["magick", "identify", "-format", "%w %h", str(source)], text=True)
w, h = map(int, dimensions.split())
raw_float = RAW / "linear_rgb.f32"
if not raw_float.exists():
    subprocess.run(["magick", str(source), "-define", "quantum:format=floating-point",
                    "-depth", "32", "-endian", "LSB", "rgb:" + str(raw_float)], check=True)
rgb = np.fromfile(raw_float, dtype="<f4").reshape(h, w, 3)
if not np.isfinite(rgb).all() or rgb.max() <= 1:
    raise ValueError("Expected finite, unclipped linear HDR radiance")
rgb = np.maximum(rgb, 0)
y = rgb[..., 0]*0.2126 + rgb[..., 1]*0.7152 + rgb[..., 2]*0.0722
sun_row, sun_col = np.unravel_index(y[:h//2].argmax(), (h//2, w))
sun_lat = math.pi*(0.5-(sun_row+0.5)/h)
sun_lon = 2*math.pi*((sun_col+0.5)/w-0.5)
sun_direction = {"x": math.sin(sun_lon)*math.cos(sun_lat), "y": math.sin(sun_lat),
                 "z": math.cos(sun_lon)*math.cos(sun_lat)}
lat = np.pi*(0.5-(np.arange(h, dtype=np.float32)+0.5)/h)
lon = 2*np.pi*((np.arange(w, dtype=np.float32)+0.5)/w-0.5)
sun_dot = np.sin(lat)[:, None]*math.sin(sun_lat) + np.cos(lat)[:, None]*math.cos(sun_lat)*np.cos(lon[None, :]-sun_lon)

def smooth(a, b, x):
    t = np.clip((x-a)/(b-a), 0, 1)
    return t*t*(3-2*t)

# Blue gaps remain analytic. Neutral cloud scattering carries the real billow
# shape and self-shadowing, rather than the overcast deck's broad noise sheets.
blueness = (rgb[..., 2]-rgb[..., 0])/np.maximum(rgb.mean(axis=2), 1e-8)
alpha = 1-smooth(0.25, 0.85, blueness)
alpha *= 1-smooth(math.cos(math.radians(1.5)), math.cos(math.radians(0.45)), sun_dot)
alpha[lat < 0] = 0
cloud_pixels = (alpha > 0.95) & (lat[:, None] > math.radians(5)) & (sun_dot < math.cos(math.radians(2)))
if cloud_pixels.sum() < 100:
    raise ValueError("No usable photographic cloud pixels")
white = float(np.percentile(y[cloud_pixels], 95))
shade = np.clip(y/max(white, 1e-8), 0, 1)**0.7
pixels = np.stack([alpha, shade, np.zeros_like(alpha), np.ones_like(alpha)], axis=-1)
OUT.mkdir(parents=True, exist_ok=True)
texture = OUT / "T_ClearClouds.png"
Image.fromarray(np.uint8(np.round(np.clip(pixels, 0, 1)*255))).save(texture, optimize=True)
metadata = {
    "schema": "kamion.photographic-clouds/1", "asset": ASSET,
    "page": f"https://polyhaven.com/a/{ASSET}", "license": "CC0 1.0 Universal",
    "license_url": "https://polyhaven.com/license", "authors": {"Greg Zaal": "Original", "Jarod Guest": "Sky edits"},
    "url": expected["url"], "source_md5": expected["md5"],
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "texture_sha256": hashlib.sha256(texture.read_bytes()).hexdigest(), "width": w, "height": h,
    "sunDirection": sun_direction, "measured_sun_elevation_deg": math.degrees(sun_lat),
    "cloud_white_linear": white, "source_cloud_pixels": int(cloud_pixels.sum()),
    "processing": "Linear HDRI; chromatic blue-gap matte; sun removed within 1.5 degrees; R opacity, G relative luminance^0.7; lower hemisphere opacity zero",
    "checked_utc": datetime.now(timezone.utc).isoformat(),
}
(OUT / "ClearCloudsSource.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
preview = np.clip(rgb/(rgb+white*0.35), 0, 1)**(1/2.2)
mock = np.array([0.18, 0.32, 0.55])[None, None, :]*(1-alpha[..., None]) + (0.35+0.6*shade[..., None])*alpha[..., None]
sheet = Image.new("RGB", (960, 1000), "#202020")
draw = ImageDraw.Draw(sheet)
for i, (label, array) in enumerate((("CC0 HDRI / preview only", preview), ("Extracted photographic clouds / preview", mock))):
    im = Image.fromarray(np.uint8(np.round(np.clip(array, 0, 1)*255))))
    im.thumbnail((960, 480))
    sheet.paste(im, (0, i*500+20))
    draw.text((4, i*500+4), label, fill="white")
sheet.save(ART / "photographic-cloud-source.jpg", quality=94)
print(json.dumps(metadata, indent=2))
