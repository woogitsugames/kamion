"""Arkusz 2×2 z podpisami: python3 -I sheet.py out.jpg img1 img2 [img3 img4]"""
import sys
from PIL import Image, ImageDraw
out = sys.argv[1]; fs = sys.argv[2:]
W = 640
tiles = []
for f in fs:
    im = Image.open(f).convert('RGB'); im.thumbnail((W, W)); tiles.append((f, im))
H = max(t[1].height for t in tiles)
sheet = Image.new('RGB', (W * 2, H * ((len(tiles) + 1) // 2)), 'white')
for i, (f, im) in enumerate(tiles):
    x, y = (i % 2) * W, (i // 2) * H
    sheet.paste(im, (x, y))
    ImageDraw.Draw(sheet).text((x + 5, y + 5), f.split('/')[-1][:10], fill=(255, 0, 0))
sheet.save(out, quality=88)
