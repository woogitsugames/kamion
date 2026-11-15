"""zoom.py dir ids... -> strip 16 m across x 40 m along, 2x upscaled, side by side (each 320x800)"""
import sys
from PIL import Image, ImageDraw
d = sys.argv[1]; ids = sys.argv[2:]
tiles = []
for i in ids:
    im = Image.open(f"{d}/{i}_rot.jpg")
    W = im.size[0]; c = W // 2
    cr = im.crop((c - 80, 0, c + 80, W)).resize((320, 2 * W), Image.LANCZOS)
    dr = ImageDraw.Draw(cr); dr.rectangle([0, 0, 120, 14], fill=(255, 255, 255)); dr.text((2, 2), i, fill=(0, 0, 0))
    tiles.append(cr)
sheet = Image.new("RGB", (330 * len(tiles), tiles[0].size[1]), (255, 255, 255))
for k, t in enumerate(tiles): sheet.paste(t, (k * 330, 0))
out = f"{d}/zoom_{'_'.join(ids)}.jpg"; sheet.save(out, quality=88); print(out)
