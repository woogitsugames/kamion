"""sheet.py out.jpg cols img1 img2 ... — contact sheet with labels (selection only)."""
import sys, os
from PIL import Image, ImageDraw
out, cols = sys.argv[1], int(sys.argv[2])
files = sys.argv[3:]
tw, th = 320, 200
rows = (len(files) + cols - 1) // cols
S = Image.new('RGB', (cols * tw, rows * (th + 14)), 'white')
d = ImageDraw.Draw(S)
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB'); im.thumbnail((tw, th))
    x, y = (i % cols) * tw, (i // cols) * (th + 14)
    S.paste(im, (x, y + 14))
    d.text((x + 2, y + 1), os.path.basename(f)[:44], fill='black')
S.save(out, quality=85)
