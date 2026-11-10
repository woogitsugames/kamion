"""Map audit r9 helpers: 960 px copies, contact sheets, ortho crops and game|ortho|Mapillary montages.

    uv run --project tools/worldgen python scripts/map-audit-sheets.py sheets  [--render-dir D] [--prefix au_f_]
    uv run --project tools/worldgen python scripts/map-audit-sheets.py montage <cam_id> [<cam_id> ...] [--tag BUG-001]
    uv run --project tools/worldgen python scripts/map-audit-sheets.py ortho <cam_id>

Inputs: artifacts/map-audit-r9/cameras/audit_cameras.index.csv (scripts/map-audit-cameras.py), the renders,
Data/raw/derived/<region>/ortho_0p25m.tif (GUGiK ortho 0.25 m, EPSG:2180), Data/raw/mapillary/<region>/manifest.jsonl
(CC BY-SA 4.0, reference only). Data/raw is read from the main checkout when the worktree has none.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
MAIN = Path(r"C:\Users\matma\Documents\Claude\kamion")
REGION = "bialystok-industrial-c"
AUD = REPO / "artifacts/map-audit-r9"
OX, OY = 777995.0, 596223.0


def raw(rel):
    for b in (REPO, MAIN):
        p = b / rel
        if p.exists():
            return p
    return MAIN / rel


def index():
    with open(AUD / "cameras/audit_cameras.index.csv", encoding="utf-8") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def font(sz):
    try:
        return ImageFont.truetype("arial.ttf", sz)
    except OSError:
        return ImageFont.load_default()


def label(im, text, sz=20):
    d = ImageDraw.Draw(im)
    f = font(sz)
    w = d.textlength(text, font=f)
    d.rectangle([0, 0, w + 10, sz + 8], fill=(0, 0, 0))
    d.text((5, 3), text, fill=(255, 255, 0), font=f)
    return im


def sheets(render_dir: Path, prefix: str, cols=2, rows=3, tw=800):
    out = AUD / "sheets"; out.mkdir(parents=True, exist_ok=True)
    small = AUD / "renders_960"; small.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in render_dir.glob(f"{prefix}*.png") if not p.name.endswith("_mask.png"))
    for p in files:
        q = small / (p.stem + ".jpg")
        if not q.exists():
            im = Image.open(p).convert("RGB"); im.thumbnail((960, 960)); im.save(q, quality=88)
    per = cols * rows
    made = []
    for k in range(0, len(files), per):
        chunk = files[k:k + per]
        ims = []
        for p in chunk:
            im = Image.open(small / (p.stem + ".jpg")); im = im.resize((tw, round(im.height * tw / im.width)))
            ims.append(label(im, p.stem))
        th = ims[0].height
        sheet = Image.new("RGB", (cols * tw + (cols - 1) * 4, rows * th + (rows - 1) * 4), (40, 40, 40))
        for i, im in enumerate(ims):
            sheet.paste(im, ((i % cols) * (tw + 4), (i // cols) * (th + 4)))
        name = out / f"sheet_{chunk[0].stem}__{chunk[-1].stem}.jpg"
        sheet.save(name, quality=85); made.append(name)
    print(f"{len(files)} frames -> {len(made)} sheets in {out}")


_ORTHO = None


def ortho_crop(e, n, heading_deg, ahead=70.0, behind=15.0, half_w=35.0, px_per_m=4.0):
    """Ortho window rotated so the travel direction is up; camera = red dot. Returns PIL image."""
    global _ORTHO
    import rasterio
    from rasterio.windows import from_bounds
    if _ORTHO is None:
        _ORTHO = rasterio.open(raw(f"Data/raw/derived/{REGION}/ortho_0p25m.tif"))
    ds = _ORTHO
    r = math.hypot(max(ahead, behind), half_w) + 2
    x, y = e + OX, n + OY
    win = from_bounds(x - r, y - r, x + r, y + r, ds.transform)
    a = ds.read([1, 2, 3], window=win, boundless=True, fill_value=0)
    im = Image.fromarray(np.moveaxis(a, 0, -1).astype(np.uint8))
    s = im.width / (2 * r)
    im = im.rotate(heading_deg, resample=Image.BICUBIC, center=(im.width / 2, im.height / 2))  # CCW by heading -> heading up
    cx, cy = im.width / 2, im.height / 2
    im = im.crop((int(cx - half_w * s), int(cy - ahead * s), int(cx + half_w * s), int(cy + behind * s)))
    d = ImageDraw.Draw(im)
    px, py = half_w * s, ahead * s
    d.ellipse([px - 6, py - 6, px + 6, py + 6], outline=(255, 0, 0), width=3)
    d.line([px, py, px, py - 30 * s], fill=(255, 0, 0), width=2)
    for m in (20, 40, 60):
        if m < ahead:
            d.line([px - 8, py - m * s, px + 8, py - m * s], fill=(255, 255, 0), width=2)
    return im


def ortho_top(e, n, half=45.0):
    global _ORTHO
    import rasterio
    from rasterio.windows import from_bounds
    if _ORTHO is None:
        _ORTHO = rasterio.open(raw(f"Data/raw/derived/{REGION}/ortho_0p25m.tif"))
    x, y = e + OX, n + OY
    a = _ORTHO.read([1, 2, 3], window=from_bounds(x - half * 2.17, y - half, x + half * 2.17, y + half, _ORTHO.transform), boundless=True, fill_value=0)
    return Image.fromarray(np.moveaxis(a, 0, -1).astype(np.uint8))


def mapillary_near(lat, lon, heading, max_d=40.0, tol=50.0):
    best = None
    man = raw(f"Data/raw/mapillary/{REGION}/manifest.jsonl")
    seen = set()
    for line in man.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        m = json.loads(line)
        if m["id"] in seen or m.get("is_pano"):
            continue
        seen.add(m["id"])
        dy = (m["lat"] - lat) * 111320.0
        dx = (m["lon"] - lon) * 111320.0 * math.cos(math.radians(lat))
        d = math.hypot(dx, dy)
        dh = abs((m.get("compass_angle", 0) - heading + 180) % 360 - 180)
        if d <= max_d and dh <= tol:
            score = d + dh * 0.4
            if best is None or score < best[0]:
                best = (score, m, d, dh)
    return best


def montage(ids, tag=None, render_dir=None):
    idx = index()
    out = AUD / "montage"; out.mkdir(parents=True, exist_ok=True)
    rd = render_dir or (AUD / "renders/High-overcast")
    for cid in ids:
        r = idx[cid]
        e, n, hd = float(r["E"]), float(r["N"]), float(r["heading_deg"])
        game = Image.open(rd / f"{cid}.png").convert("RGB"); game.thumbnail((960, 960))
        H = game.height
        top = r["kind"] == "rondo_above"
        orth = ortho_top(e, n) if top else ortho_crop(e, n, hd)
        orth = orth.resize((round(orth.width * H / orth.height), H))
        parts = [label(game, f"GRA {cid}", 16), label(orth, "GUGiK orto 2024 (kierunek jazdy w gore)" if not top else "GUGiK orto 2024 (N w gore)", 14)]
        cap = ""
        if not top:
            b = mapillary_near(float(r["lat"]), float(r["lon"]), hd)
            if b:
                _, m, d, dh = b
                mi = Image.open(raw(f"Data/raw/mapillary/{REGION}/{m['file']}")).convert("RGB")
                mi = mi.resize((round(mi.width * H / mi.height), H))
                parts.append(label(mi, f"Mapillary {m['id']} {m['captured_at']} d={d:.0f}m dh={dh:.0f} CC BY-SA {m['author']}", 14))
                cap = f"mapillary={m['id']} ({m['file']}, d={d:.0f} m, dh={dh:.0f} deg)"
        W = sum(p.width for p in parts) + 4 * (len(parts) - 1)
        sheet = Image.new("RGB", (W, H), (30, 30, 30)); x = 0
        for p in parts:
            sheet.paste(p, (x, 0)); x += p.width + 4
        name = out / f"{(tag + '_') if tag else ''}{cid}.jpg"
        sheet.save(name, quality=85)
        print(name.relative_to(REPO), cap)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sheets", "montage", "ortho"])
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--render-dir")
    ap.add_argument("--prefix", default="au_")
    ap.add_argument("--tag")
    a = ap.parse_args()
    rd = Path(a.render_dir) if a.render_dir else AUD / "renders/High-overcast"
    if a.cmd == "sheets":
        sheets(rd, a.prefix)
    elif a.cmd == "montage":
        montage(a.ids, a.tag, rd)
    else:
        idx = index()
        for cid in a.ids:
            r = idx[cid]
            im = ortho_crop(float(r["E"]), float(r["N"]), float(r["heading_deg"]))
            p = AUD / "ortho" / f"{cid}.jpg"; p.parent.mkdir(parents=True, exist_ok=True); im.save(p, quality=88); print(p)


if __name__ == "__main__":
    main()
