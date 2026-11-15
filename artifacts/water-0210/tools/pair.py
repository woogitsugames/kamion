"""ADR 0210: render (top_bridge) | orthophoto pairs + downsized water frames -> artifacts/water-0210/<region>/<tag>/view.
uv run --project tools/worldgen python artifacts/water-0210/tools/pair.py <region> <tag>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[3]
MAIN = Path(r"C:\Users\matma\Documents\Claude\kamion")
reg, tag = sys.argv[1], sys.argv[2]
base = ROOT / "artifacts/water-0210" / reg / tag
vd = base / "view"
vd.mkdir(parents=True, exist_ok=True)
odir = MAIN / "artifacts/dk65-tiles-0207" / reg / "ortho"
for tier in ("Low", "High"):
    rd = base / f"{tier}-clear"
    if not rd.exists():
        continue
    for o in sorted(odir.glob("top_*.jpg")):
        cid = o.stem.replace("_", "-")
        rp = rd / f"{cid}.png"
        if not rp.exists():
            continue
        a = Image.open(rp).convert("RGB").resize((960, 540)); b = Image.open(o).convert("RGB").resize((960, 540))
        M = Image.new("RGB", (1920, 540)); M.paste(a, (0, 0)); M.paste(b, (960, 0))
        d = ImageDraw.Draw(M); d.text((8, 8), f"{reg} {tag} {tier}: {cid}", fill=(255, 255, 0))
        d.text((968, 8), "GUGiK orto 2024-05-27 (QA only)", fill=(255, 255, 0))
        M.save(vd / f"pair-{tier.lower()}-{cid}.jpg", quality=85)
    for p in rd.glob("*.png"):
        if p.stem.startswith(("water", "drive-bridge")):
            Image.open(p).convert("RGB").resize((960, 540)).save(vd / f"{tier.lower()}-{p.stem}.jpg", quality=85)
print("ok", vd)
