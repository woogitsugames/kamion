"""ADR 0207: stack strip_*.jpg of a tile into mosaics (2 columns, 8 chunks per image) for reading edge lines."""
import sys
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[3]
reg = sys.argv[1]; sc = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
od = ROOT / "artifacts/dk65-tiles-0207" / reg / "ortho"
fs = sorted(od.glob("strip_*.jpg"))
for p in range(0, len(fs), 8):
    ims = [Image.open(f) for f in fs[p:p + 8]]
    ims = [i.resize((int(i.size[0] * sc), int(i.size[1] * sc)), Image.LANCZOS) for i in ims]
    w, h = ims[0].size
    M = Image.new("RGB", (w * 2 + 10, h * 4), (255, 255, 255))
    for k, i in enumerate(ims):
        M.paste(i, ((k // 4) * (w + 10), (k % 4) * h))
    M.save(od / f"mosaic_{p // 8}.jpg", quality=88)
