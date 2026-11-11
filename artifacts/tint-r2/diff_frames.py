"""ADR0101: per-camera change between two rounds (only the recalibrated pigments differ), full-frame clip_250 and a
change mask (|dLevel| > 3) that localises the changed material when no renderer mask exists (instanced props/heroes)."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
def load(p): return np.asarray(Image.open(p).convert('RGB'), np.int16)
def main(a_dir, b_dir, out_json, cams=None):
    rows = []
    for cond in ['Low-overcast', 'Low-clear', 'High-overcast', 'High-clear']:
        for pb in sorted((Path(b_dir) / cond).glob('*.png')):
            if cams and pb.stem not in cams: continue
            pa = Path(a_dir) / cond / pb.name
            if not pa.exists() or pb.stem.endswith('_mask'): continue
            a, b = load(pa), load(pb)
            d = b.mean(2) - a.mean(2); ch = np.abs(d) > 3
            clip_a = float(np.all(a >= 250, axis=2).mean()); clip_b = float(np.all(b >= 250, axis=2).mean())
            rows.append({'condition': cond, 'camera': pb.stem, 'changed_frac': float(ch.mean()),
                         'mean_dlevel_changed': float(d[ch].mean()) if ch.any() else 0.0,
                         'clip250_all_before': clip_a, 'clip250_all_after': clip_b})
    Path(out_json).write_text(json.dumps(rows, indent=1) + '\n')
    for r in rows:
        if r['changed_frac'] > 0.001 or abs(r['clip250_all_after'] - r['clip250_all_before']) > 1e-4:
            print(f"{r['condition']:14s} {r['camera']:28s} changed {r['changed_frac']*100:6.2f} %  dL {r['mean_dlevel_changed']:+6.1f}  clip {r['clip250_all_before']*100:5.2f} -> {r['clip250_all_after']*100:5.2f} %")
if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
