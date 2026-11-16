"""contact sheet: python sheet.py <dir> <out.jpg> id1 id2 ... (2 columns, 960 px wide each tile 480)"""
import sys
from pathlib import Path
from PIL import Image
d, out, ids = Path(sys.argv[1]), sys.argv[2], sys.argv[3:]
W = 640
tiles = []
for i in ids:
    p = d / f"{i}.png"
    if not p.exists(): continue
    im = Image.open(p).convert("RGB"); im = im.resize((W, int(im.height * W / im.width)))
    tiles.append(im)
cols = 2; rows = (len(tiles) + 1) // 2; h = tiles[0].height
S = Image.new("RGB", (W * cols, h * rows))
for k, t in enumerate(tiles): S.paste(t, ((k % cols) * W, (k // cols) * h))
S.save(out, quality=85)
