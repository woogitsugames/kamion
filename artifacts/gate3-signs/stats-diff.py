"""Editor draw / triangle estimates per SBS camera: baseline vs after (visual-qa stats-*.txt). Usage: stats-diff.py <after> [G3-B only]"""
import re, sys, glob, os
here = os.path.dirname(os.path.abspath(__file__))
def load(name):
    out = {}
    for f in glob.glob(os.path.join(here, name, 'renders', 'Low-overcast', 'stats-*x*.txt')):
        cam = None
        for line in open(f, encoding='utf-8', errors='replace'):
            m = re.match(r'(sbs-\S+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)', line)
            if m:
                cam = m.group(1); out[cam] = {'draws': int(m.group(3)), 'trisK': int(m.group(5))}
            m = re.match(r'\s+(sbs-\S+) instanced.*draws (\d+), instances (\d+), triangles (\d+)k', line)
            if m:
                out[m.group(1)].update(idraws=int(m.group(2)), inst=int(m.group(3)), itrisK=int(m.group(4)))
    return out
a, b = load('baseline'), load(sys.argv[1])
print(f"{'camera':34} draws b->a (d)   inst.draws b->a (d)   trisK b->a   inst.trisK b->a")
tot = []
for cam in sorted(b):
    if cam not in a or 'idraws' not in a[cam] or 'idraws' not in b[cam]: continue
    x, y = a[cam], b[cam]
    d = (y['draws'] + y['idraws']) - (x['draws'] + x['idraws'])
    tot.append((cam, d))
    print(f"{cam:34} {x['draws']:4}->{y['draws']:4} ({y['draws']-x['draws']:+4})   {x['idraws']:4}->{y['idraws']:4} ({y['idraws']-x['idraws']:+4})   {x['trisK']:4}->{y['trisK']:4}   {x['itrisK']:3}->{y['itrisK']:3}   total {d:+d}")
gb = [d for c, d in tot if '-g3-b-' in c]
print('G3-B cameras:', len(gb), 'total-draw delta min/median/max:', min(gb), sorted(gb)[len(gb)//2], max(gb))
