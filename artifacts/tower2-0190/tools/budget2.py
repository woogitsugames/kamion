"""Low budget: stats.txt of a baseline run vs stats.txt of this run (all cameras; renderer, shadow and instanced draws apart)."""
import re, sys
def load(fn):
    cur = {}
    for line in open(fn, encoding='utf-8'):
        m = re.match(r'(\S+): objects=\d+ drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+) trisExact=(\d+)', line)
        if m: cur[m.group(1)] = dict(r=int(m.group(2)), s=int(m.group(3)), rt=int(m.group(5)), i=0, it=0)
        m = re.match(r'\s+(\S+) instanced.*draws (\d+), instances \d+, triangles (\d+)k.*trianglesExact (\d+)', line)
        if m: cur[m.group(1)].update(i=int(m.group(2)), it=int(m.group(4)))
    for a in cur.values(): a['draws'] = a['r'] + a['s'] + a['i']; a['tris'] = a['rt'] + a['it']
    return cur
base, cur = load(sys.argv[1]), load(sys.argv[2])
lines = [f"{'camera':36} draws base>now (d)   tris base>now (%)            renderer   shadow    inst.draws"]
dd, dp = [], []
for c in sorted(cur):
    a = cur[c]
    if c not in base: lines.append(f"{c:36} (no baseline) draws {a['draws']} tris {a['tris']}"); continue
    b = base[c]; d = a['draws'] - b['draws']; p = 100.0 * (a['tris'] - b['tris']) / b['tris']
    dd.append((d, c)); dp.append((p, c))
    lines.append(f"{c:36} {b['draws']:5}>{a['draws']:5} ({d:+3})   {b['tris']:8}>{a['tris']:8} ({p:+5.2f} %)   {b['r']:4}>{a['r']:4} {b['s']:4}>{a['s']:4} {b['i']:4}>{a['i']:4}")
lines.append(f"cameras {len(dd)}; draws delta min {min(dd)} max {max(dd)}; tris % min {min(dp)[0]:+.2f} ({min(dp)[1]}) max {max(dp)[0]:+.2f} ({max(dp)[1]})")
open(sys.argv[3], 'w', encoding='utf-8').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
