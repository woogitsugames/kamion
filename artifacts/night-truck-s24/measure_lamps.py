# uv run --no-project --with pillow --with numpy --with scipy python measure_lamps.py <tagdir> [<maskdir>]
# Lamp ROI = pixels where the stop render's R exceeds the tail-only render's R by > 40 (as lights-79-s24), measured in
# the tail-only and stop renders of the same tier/lighting; housing ring = 4..24 px around that mask (excluding any
# emitter); plate = bright low-saturation pixels (min channel > 90, max-min < 40) in the tail-only render.
# maskdir: render set used for the stop-vs-tail mask (default = tagdir, so before/after use their own lamps).
import sys, os, numpy as np
from PIL import Image
from scipy import ndimage

def load(p): return np.asarray(Image.open(p).convert('RGB')).astype(np.float32)
def lin(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

tag = sys.argv[1]
maskdir = sys.argv[2] if len(sys.argv) > 2 else tag
for tier, light in (('High', 'night'), ('Low', 'night'), ('High', 'dusk')):
    tail_d = os.path.join(tag, f'lamps-{tier}-{light}-low')
    stop_d = os.path.join(tag, f'lamps-{tier}-{light}-low+brake')
    for cam in ('lamp-truck', 'lamp-trailer', 'plate-trailer', 'plate-truck-bobtail'):
        pt = os.path.join(tail_d, cam + '.png')
        if not os.path.exists(pt): continue
        t = load(pt)
        ms = os.path.join(maskdir, f'lamps-{tier}-{light}-low+brake', cam + '.png')
        mt = os.path.join(maskdir, f'lamps-{tier}-{light}-low', cam + '.png')
        line = f'{tier:5s} {light:5s} {cam:20s}'
        if os.path.exists(ms) and os.path.exists(mt):
            mask = (load(ms)[..., 0] - load(mt)[..., 0]) > 40
            mask = ndimage.binary_opening(mask, iterations=1)
            if mask.sum() > 20:
                tm = t[mask].mean(0)
                line += f' | tail {tm[0]:5.1f},{tm[1]:4.1f},{tm[2]:4.1f} p95R {np.percentile(t[mask][:,0],95):5.1f}'
                ring = ndimage.binary_dilation(mask, iterations=24) & ~ndimage.binary_dilation(mask, iterations=4)
                ring &= ~(t[..., 0] - t[..., 1] > 60)  # exclude other lit emitters
                line += f' | ring(tail) {t[ring].mean(0)[0]:5.1f},{t[ring].mean(0)[1]:4.1f}'
                ps = os.path.join(stop_d, cam + '.png')
                if os.path.exists(ps):
                    s = load(ps)
                    sm = s[mask].mean(0)
                    ratio = lin(sm[0]) / max(lin(tm[0]), 1e-6)
                    line += f' | stop {sm[0]:5.1f},{sm[1]:4.1f},{sm[2]:4.1f} | ring(stop) {s[ring].mean(0)[0]:5.1f},{s[ring].mean(0)[1]:4.1f} | stop:tail lin R {ratio:5.2f}'
        refm = load(mt) if os.path.exists(mt) else t
        red = (refm[..., 0] - np.maximum(refm[..., 1], refm[..., 2])) > 25
        red = ndimage.binary_opening(red, iterations=1)
        if red.sum() > 20:
            rr = t[red].mean(0)
            ring2 = ndimage.binary_dilation(red, iterations=24) & ~ndimage.binary_dilation(red, iterations=4)
            line += f' | LIT-RED(tail) {rr[0]:5.1f},{rr[1]:4.1f},{rr[2]:4.1f} n={red.sum()} ring {t[ring2].mean(0)[0]:5.1f},{t[ring2].mean(0)[1]:4.1f}'
        mx = t.max(-1)
        ref = load(mt) if os.path.exists(mt) else t
        plate = (ref.min(-1) > 90) & ((ref.max(-1) - ref.min(-1)) < 40)
        plate = ndimage.binary_opening(plate, iterations=1)
        if plate.sum() > 30:
            line += f' | plate n={plate.sum()} mean {t[plate].mean():5.1f} p95 {np.percentile(t[plate].max(-1),95):5.1f} max {t[plate].max():5.1f}'
        line += f' | >250: {(mx > 250).mean()*100:.3f}%'
        print(line)
