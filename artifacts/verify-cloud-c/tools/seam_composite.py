"""Stitch the two top_site_seam renders (dk65-06 above the seam, dk65-05 below) into one image; the seam is marked at the
image edges only. Both cameras: same E centre, 140 m N-S footprint, seam 10 m inside the frame.
uv run --project tools/worldgen python artifacts/verify-cloud-c/tools/seam_composite.py <out.jpg> [low-dir-05] [low-dir-06]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
A = Path("artifacts/verify-cloud-c/pr80")
out = sys.argv[1]
d5 = Path(sys.argv[2]) if len(sys.argv) > 2 else A / "dk65-05/Low-clear"
d6 = Path(sys.argv[3]) if len(sys.argv) > 3 else A / "dk65-06/Low-clear"
a = Image.open(d5 / "top-site-seam.png").convert("RGB"); b = Image.open(d6 / "top-site-seam.png").convert("RGB")
k = round(a.height * 10.0 / 140.0)                      # px from the frame edge to the seam
top = b.crop((0, 0, b.width, b.height - k)); bot = a.crop((0, k, a.width, a.height))
M = Image.new("RGB", (a.width, top.height + bot.height)); M.paste(top, (0, 0)); M.paste(bot, (0, top.height))
d = ImageDraw.Draw(M)
for x0, x1 in ((0, 40), (M.width - 40, M.width)):
    d.line([(x0, top.height), (x1, top.height)], fill=(255, 255, 0), width=3)
d.text((50, top.height - 28), "dk65-06  (seam y = 603391)", fill=(255, 255, 0)); d.text((50, top.height + 10), "dk65-05", fill=(255, 255, 0))
M.resize((960, round(M.height * 960 / M.width)), Image.LANCZOS).save(out, quality=90)
# 3x detail of the seam strip: 100 m wide (E 767690..767790), 30 m N-S
ppm = a.width / (a.height * 16 / 9 / a.height * 140.0) if False else a.width / (140.0 * a.width / a.height)
cx = M.width / 2 + (767740 - 767735) * ppm
det = M.crop((int(cx - 50 * ppm), int(top.height - 15 * ppm), int(cx + 50 * ppm), int(top.height + 15 * ppm)))
det.resize((960, round(det.height * 960 / det.width)), Image.LANCZOS).save(out.replace(".jpg", "-detail.jpg"), quality=92)
# Ełcka at the seam: E 767640..767680
cx = M.width / 2 + (767660 - 767735) * ppm
det = M.crop((int(cx - 20 * ppm), int(top.height - 12 * ppm), int(cx + 20 * ppm), int(top.height + 12 * ppm)))
det.resize((960, round(det.height * 960 / det.width)), Image.LANCZOS).save(out.replace(".jpg", "-elcka.jpg"), quality=92)
print("ok")
