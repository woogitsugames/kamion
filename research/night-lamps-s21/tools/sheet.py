"""Arkusz 2x2 (każdy kafel 480 px szer.) z podpisami — do oglądania kilku kadrów naraz. Użycie: sheet.py out.jpg img1 img2 [img3 img4]"""
import sys
from PIL import Image, ImageDraw
out, ims = sys.argv[1], sys.argv[2:6]
tiles = []
for p in ims:
    im = Image.open(p).convert('RGB')
    s = 480 / im.width
    im = im.resize((480, int(im.height * s)))
    if im.height > 640:
        im = im.resize((int(480 * 640 / im.height), 640))
    tiles.append((p, im))
H = max(t[1].height for t in tiles)
W = 960
rows = (len(tiles) + 1) // 2
sh = Image.new('RGB', (W, rows * (H + 18)), (0, 0, 0))
d = ImageDraw.Draw(sh)
for k, (p, im) in enumerate(tiles):
    x, y = (k % 2) * 480, (k // 2) * (H + 18)
    sh.paste(im, (x, y + 18))
    d.text((x + 4, y + 3), p.split('/')[-1][:60], fill=(255, 255, 0))
sh.save(out, quality=88)
