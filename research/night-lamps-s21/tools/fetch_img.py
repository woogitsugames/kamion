"""Pobiera obraz z URL, zapisuje: oryginał-pobrany (raw), wersję ≤1600 px JPG q82 (do gita) i podgląd ≤960 px (do oglądania).
Użycie: fetch_img.py <tools> <url> <out_basename_bez_rozszerzenia> ; drukuje sha256 pobranego pliku i pliku 1600."""
import sys, hashlib, io, os
sys.path.insert(0, sys.argv[1])
from httpc import get  # noqa
from PIL import Image, ImageOps
url, base = sys.argv[2], sys.argv[3]
b = get(url, timeout=180, tries=5)
raw_sha = hashlib.sha256(b).hexdigest()
im = Image.open(io.BytesIO(b))
im = ImageOps.exif_transpose(im).convert('RGB')
w, h = im.size
for lim, suf, q in ((1600, '', 82), (960, '_v', 85)):
    s = min(1.0, lim / max(w, h))
    im2 = im.resize((round(w * s), round(h * s)), Image.LANCZOS) if s < 1 else im
    im2.save(base + suf + '.jpg', quality=q)
sha = hashlib.sha256(open(base + '.jpg', 'rb').read()).hexdigest()
print(os.path.basename(base), w, h, 'raw_sha256', raw_sha, 'jpg1600_sha256', sha)
