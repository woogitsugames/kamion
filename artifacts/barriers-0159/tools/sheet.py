"""Contact sheet: sheet.py out.jpg cols tile_w img[:x0,y0,x1,y1] ... (crop in 0..1)."""
import sys
from PIL import Image
out, cols, tw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
tiles = []
for a in sys.argv[4:]:
    f, _, c = a.partition('|')
    im = Image.open(f).convert('RGB')
    if c:
        x0, y0, x1, y1 = map(float, c.split(','))
        w, h = im.size
        im = im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))
    tiles.append(im.resize((tw, int(tw * im.height / im.width)), Image.LANCZOS))
H = max(t.height for t in tiles)
rows = (len(tiles) + cols - 1) // cols
sh = Image.new('RGB', (tw * cols, H * rows), (30, 30, 30))
for i, t in enumerate(tiles):
    sh.paste(t, ((i % cols) * tw, (i // cols) * H))
sh.save(out, quality=88)
print(sh.size)
