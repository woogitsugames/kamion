"""Contact sheet: sheet.py out.jpg dir name1 name2 ... (2 columns, 800x450 cells)."""
import sys
from PIL import Image, ImageDraw
out, d0 = sys.argv[1], sys.argv[2]
names = sys.argv[3:]
W, H = 800, 450
s = Image.new('RGB', (W * 2, H * ((len(names) + 1) // 2)), 'white'); d = ImageDraw.Draw(s)
for i, n in enumerate(names):
    im = Image.open(f'{d0}/{n}.jpg').convert('RGB'); im.thumbnail((W, H - 16)); x = (i % 2) * W; y = (i // 2) * H
    s.paste(im, (x, y + 16)); d.text((x + 4, y + 2), n[:48], fill='red')
s.save(out, quality=88)
