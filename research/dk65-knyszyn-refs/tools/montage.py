"""montage.py outprefix suffix files... -> 2x2 sheets with labels (each tile resized to 450 px)"""
import sys
from PIL import Image, ImageDraw
pre, files = sys.argv[1], sys.argv[2:]
S = 450
for k in range(0, len(files), 4):
    grp = files[k:k + 4]
    sheet = Image.new("RGB", (2 * S, 2 * S + 40), (255, 255, 255))
    for j, f in enumerate(grp):
        im = Image.open(f).convert("RGB"); im.thumbnail((S, S))
        x, y = (j % 2) * S, (j // 2) * (S + 20)
        sheet.paste(im, (x, y + 20))
        ImageDraw.Draw(sheet).text((x + 4, y + 4), f.split("/")[-1], fill=(0, 0, 0))
    sheet.save(f"{pre}_{k // 4:02d}.jpg", quality=88)
    print(f"{pre}_{k // 4:02d}.jpg", grp)
