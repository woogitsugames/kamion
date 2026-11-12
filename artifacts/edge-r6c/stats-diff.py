"""ADR 0141: editor draw / triangle estimates per camera, before vs after (visual-qa stats*.txt).
Usage: stats-diff.py <before-name> <after-name> <Tier-Lighting>"""
import re, sys, glob, os
here = os.path.dirname(os.path.abspath(__file__))
def load(name, light):
    out = {}
    for f in glob.glob(os.path.join(here, name, light, 'stats-*.txt')):
        for line in open(f, encoding='utf-8', errors='replace'):
            m = re.match(r'(\S+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)', line)
            if m: out[m.group(1)] = {'draws': int(m.group(3)), 'shadow': int(m.group(4)), 'trisK': int(m.group(5))}
            m = re.match(r'\s+(\S+) instanced.*draws (\d+), instances (\d+), triangles (\d+)k', line)
            if m and m.group(1) in out: out[m.group(1)].update(idraws=int(m.group(2)), itrisK=int(m.group(4)))
    return out
a, b = load(sys.argv[1], sys.argv[3]), load(sys.argv[2], sys.argv[3])
rows = []
print(f"{'camera':36} draws b->a      shadow b->a    trisK b->a")
for cam in sorted(b):
    if cam not in a: continue
    x, y = a[cam], b[cam]
    rows.append((cam, y['draws'] - x['draws'], y['shadow'] - x['shadow'], y['trisK'] - x['trisK'], x['trisK']))
    print(f"{cam:36} {x['draws']:4}->{y['draws']:4} ({y['draws']-x['draws']:+4})  {x['shadow']:3}->{y['shadow']:3} ({y['shadow']-x['shadow']:+3})  {x['trisK']:4}->{y['trisK']:4} ({y['trisK']-x['trisK']:+3})"
          + ('' if x.get('idraws') == y.get('idraws') and x.get('itrisK') == y.get('itrisK') else f"  INSTANCED {x.get('idraws')}->{y.get('idraws')} / {x.get('itrisK')}k->{y.get('itrisK')}k"))
for label, flt in (('all', ''), ('sbs G3-A', 'sbs-g3-a'), ('sbs G3-B', 'sbs-g3-b'), ('g3a route', 'g3a-'), ('g3b route', 'g3b-'), ('edge', 'edge-')):
    r = [x for x in rows if flt in x[0]]
    if not r: continue
    d = sorted(x[1] for x in r); s = sorted(x[2] for x in r); t = sorted(x[3] for x in r)
    print(f"{label:10} n={len(r):3}  draws delta min/median/max {d[0]:+d}/{d[len(d)//2]:+d}/{d[-1]:+d}  sum {sum(d):+d} | shadow {s[0]:+d}/{s[len(s)//2]:+d}/{s[-1]:+d} sum {sum(s):+d} | trisK {t[0]:+d}/{t[len(t)//2]:+d}/{t[-1]:+d} sum {sum(t):+d} of {sum(x[4] for x in r)}")
