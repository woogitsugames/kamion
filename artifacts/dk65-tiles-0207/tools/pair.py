"""ADR 0207: side-by-side pair render top view | orthophoto crop (same footprint) -> <dir>/view/pair-<id>.jpg (1920x540).
uv run --project tools/worldgen python artifacts/dk65-tiles-0207/tools/pair.py <region> <tag> [<tier>]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[3]
reg, tag = sys.argv[1], sys.argv[2]; tier = sys.argv[3] if len(sys.argv) > 3 else "Low"
base = ROOT / "artifacts/dk65-tiles-0207" / reg
vd = base / tag / "view"; vd.mkdir(parents=True, exist_ok=True)
for o in sorted((base / "ortho").glob("top_*.jpg")):
    cid = o.stem.replace("_", "-")
    rp = base / tag / f"{tier}-clear" / f"{cid}.png"
    if not rp.exists():
        continue
    a = Image.open(rp).convert("RGB").resize((960, 540)); b = Image.open(o).convert("RGB").resize((960, 540))
    M = Image.new("RGB", (1920, 540)); M.paste(a, (0, 0)); M.paste(b, (960, 0))
    d = ImageDraw.Draw(M); d.text((8, 8), f"{reg} {tag} {tier}: {cid}", fill=(255, 255, 0)); d.text((968, 8), "GUGiK orto 2024-05-27 (QA only)", fill=(255, 255, 0))
    M.save(vd / f"pair-{cid}.jpg", quality=85)
for p in (base / tag / f"{tier}-clear").glob("*.png"):
    if p.stem.startswith(("drive", "rev", "route", "edge")):
        Image.open(p).convert("RGB").resize((960, 540)).save(vd / f"{tier.lower()}-{p.stem}.jpg", quality=85)
print("ok")
