"""ADR 0183 evidence: P11-063 next to the renders of camera photo_P11-063 (+ zoomed crops of the row) and the
close-up cameras of r1 vs r2. Writes artifacts/bollards-0183/compare/*.jpg (960 px wide max per panel row)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

wt = Path(__file__).resolve().parents[3]
A = wt / "artifacts/bollards-0183"
PHOTO = Path(r"C:/Users/matma/Documents/Claude/kamion/research/_incoming/mistral-p11-dojlidy-photos-v2/files/P11-063.jpg")
tag = sys.argv[1] if len(sys.argv) > 1 else "r2"
out = A / "compare"
out.mkdir(exist_ok=True)


def lab(im, t):
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 8 * len(t) + 10, 18], fill=(0, 0, 0))
    d.text((5, 3), t, fill=(255, 255, 255))
    return im


def fit(im, w):
    return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)


def grid(rows, w, path):
    rows = [[fit(i, w) for i in r] for r in rows]
    W = max(sum(i.width for i in r) for r in rows)
    H = sum(max(i.height for i in r) for r in rows)
    can = Image.new("RGB", (W, H), (20, 20, 20))
    y = 0
    for r in rows:
        x = 0
        for i in r:
            can.paste(i, (x, y))
            x += i.width
        y += max(i.height for i in r)
    can.save(path, quality=90)
    print(path, can.size)


photo = Image.open(PHOTO).convert("RGB")
ren = {t: Image.open(A / f"renders/{tag}-{t}/photo-P11-063.png").convert("RGB") for t in ("low", "high")}
grid([[lab(photo.copy(), "P11-063 (owner photo)"), lab(ren["low"], f"{tag} Low photo_P11-063")],
      [lab(Image.new("RGB", photo.size, (20, 20, 20)), ""), lab(ren["high"], f"{tag} High photo_P11-063")]],
     800, out / f"{tag}-photo-P11-063-side-by-side.jpg")
# crop of the row in the photo vs the same relative band of the renders (the camera pose is off by metres: ADR text)
pc = photo.crop((560, 560, 1360, 740))
rows = [[lab(fit(pc, 960), "P11-063 crop (posts 1-8)")]]
for t in ("low", "high"):
    r = ren[t]
    sx, sy = r.width / photo.width, r.height / photo.height
    rows.append([lab(fit(r.crop((int(380 * sx), int(520 * sy), int(1500 * sx), int(760 * sy))), 960), f"{tag} {t} same band")])
grid(rows, 960, out / f"{tag}-photo-P11-063-row-crops.jpg")
for cam in ("bollards-detail-2m", "bollards-close-5m", "bollards-cab-20m", "bollards-along-8m"):
    rr = []
    for t in ("low", "high"):
        r1 = A / f"renders/r1-{t}/{cam}.png"
        r2 = A / f"renders/{tag}-{t}/{cam}.png"
        if r1.exists() and r2.exists():
            rr.append([lab(Image.open(r1).convert("RGB"), f"r1 {t} {cam}"), lab(Image.open(r2).convert("RGB"), f"{tag} {t} {cam}")])
    if rr:
        grid(rr, 480, out / f"r1-vs-{tag}-{cam}.jpg")
