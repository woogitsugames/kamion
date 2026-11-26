"""road-patches-s24: before | after sheets (lower 60 % of each frame = the road), JPEG <= 1920 wide."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).parent
out = root / "sheets"
out.mkdir(exist_ok=True)
tag = sys.argv[1] if len(sys.argv) > 1 else "after"
for b in sorted((root / "before").glob("*/*/*.png")):
    a = root / tag / b.relative_to(root / "before")
    if not a.exists():
        continue
    ib, ia = Image.open(b).convert("RGB"), Image.open(a).convert("RGB")
    w, h = ib.size
    box = (0, int(h * 0.42), w, h)
    cb, ca = ib.crop(box).resize((960, int(960 * (box[3] - box[1]) / w))), ia.crop(box).resize((960, int(960 * (box[3] - box[1]) / w)))
    sh = Image.new("RGB", (1920, cb.size[1] + 24), "white")
    sh.paste(cb, (0, 24)); sh.paste(ca, (960, 24))
    d = ImageDraw.Draw(sh)
    d.text((6, 4), f"PRZED  {b.parent.parent.name}/{b.parent.name}/{b.stem}", fill="black")
    d.text((966, 4), f"PO ({tag})", fill="black")
    sh.save(out / f"{b.parent.parent.name}__{b.parent.name}__{b.stem}__{tag}.jpg", quality=88)
    print(out / f"{b.parent.parent.name}__{b.parent.name}__{b.stem}__{tag}.jpg")
