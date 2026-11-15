"""Independent cross-section reading of ul. Elcka/Studzienna on K1's rotated GUGiK 0.1 m crops (road vertical, axis centre)."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
src = Path("research/dk65-knyszyn-refs/files/orto/km"); out = Path("artifacts/verify-cloud-c/pr80/ortho"); out.mkdir(parents=True, exist_ok=True)
KM = ["11.00", "11.50", "12.00", "12.50", "13.00", "13.50", "14.00", "14.50", "15.00", "15.50", "16.00"]
res = {}
for km in KM:
    im = Image.open(src / f"km{km}_rot.jpg").convert("RGB"); a = np.asarray(im).astype(float)
    h, w = a.shape[:2]; px = 0.1
    g = a.mean(axis=2); sat = a.max(axis=2) - a.min(axis=2)
    band = slice(h // 2 - int(15 / px), h // 2 + int(15 / px))
    prof = np.median(g[band], axis=0); psat = np.median(sat[band], axis=0)
    x = (np.arange(w) - w / 2 + 0.5) * px
    core = np.median(prof[np.abs(x) < 2.0][np.abs(x[np.abs(x) < 2.0]) > 0.6])   # asphalt gray off the centre line
    # line peaks: local maxima >= core+6 within |x| < 6 m
    pk = [i for i in range(2, w - 2) if abs(x[i]) < 6 and prof[i] >= core + 5 and prof[i] == prof[i - 3:i + 4].max()]
    cl = [i for i in pk if abs(x[i]) < 1.2]; C = max(cl, key=lambda i: prof[i]) if cl else w // 2
    def best(sign):   # edge line = strongest peak 2.4-3.9 m from the centre line
        c = [i for i in pk if 2.4 <= sign * (x[i] - x[C]) <= 3.9]
        return max(c, key=lambda i: prof[i]) if c else None
    L, R = best(-1), best(+1)
    # asphalt edge: walking outward from the edge line (or 2.5 m), first place where 0.5 m mean departs from core by > 18 gray or saturation > 28
    def edge(sign, start):
        i = start
        while 0 < i < w - 1 and abs(x[i]) < 9:
            j = slice(i, i + int(0.5 / px)) if sign > 0 else slice(i - int(0.5 / px), i)
            if abs(prof[j].mean() - core) > 14 or psat[j].mean() > 24: return i
            i += sign
        return None
    eL = edge(-1, (L - int(0.3 / px)) if L else int(w / 2 - 2.5 / px)); eR = edge(+1, (R + int(0.3 / px)) if R else int(w / 2 + 2.5 / px))
    r = {"px_m": px, "core_gray": round(float(core), 1), "centre_m": round(float(x[C]), 2), "line_L_m": None if L is None else round(float(x[L]), 2), "line_R_m": None if R is None else round(float(x[R]), 2),
         "line_to_line_m": None if None in (L, R) else round(float(x[R] - x[L]), 2),
         "asphalt_L_m": None if eL is None else round(float(x[eL]), 2), "asphalt_R_m": None if eR is None else round(float(x[eR]), 2),
         "asphalt_m": None if None in (eL, eR) else round(float(x[eR] - x[eL]), 2)}
    res[km] = r
    # evidence: 24 m wide x 30 m crop, 4x up, with marks + profile
    c0, c1 = int(w / 2 - 8 / px), int(w / 2 + 8 / px)
    crop = im.crop((c0, band.start, c1, band.stop)).resize(((c1 - c0) * 4, (band.stop - band.start) * 1), Image.LANCZOS)
    d = ImageDraw.Draw(crop)
    for i, col in ((L, (255, 0, 255)), (R, (255, 0, 255)), (eL, (0, 255, 255)), (eR, (0, 255, 255))):
        if i is not None: d.line([((i - c0) * 4, 0), ((i - c0) * 4, 40)], fill=col, width=2); d.line([((i - c0) * 4, crop.height - 40), ((i - c0) * 4, crop.height)], fill=col, width=2)
    for m in range(-8, 9):   # 1 m ticks
        d.line([((w / 2 + m / px - c0) * 4, crop.height // 2 - (8 if m % 5 else 16)), ((w / 2 + m / px - c0) * 4, crop.height // 2 + (8 if m % 5 else 16))], fill=(255, 255, 0), width=1)
    d.text((6, 6), f"km {km}  lines {r['line_to_line_m']} m  asphalt {r['asphalt_m']} m", fill=(255, 255, 0))
    for i in range(c0, c1 - 1):   # brightness profile
        d.line([((i - c0) * 4, crop.height - 45 - (prof[i] - core) * 1.2), ((i + 1 - c0) * 4, crop.height - 45 - (prof[i + 1] - core) * 1.2)], fill=(255, 60, 60), width=1)
    crop.save(out / f"xsec_km{km}.jpg", quality=88)
(out / "elcka_xsec.json").write_text(json.dumps(res, indent=1))
for k, r in res.items(): print(k, r)
