"""ADR 0159 after5: Low budget table against a compare TSV of a review (columns *_a = main with 0153 + 0154).
budget_tsv.py compare.tsv after_stats.txt [out.txt]"""
import csv, re, sys
def load_stats(p):
    d, cur = {}, None
    for ln in open(p, encoding='utf-8', errors='replace'):
        m = re.match(r'^(\S+): objects=\d+ drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)', ln)
        if m:
            cur = m.group(1); d[cur] = [int(m.group(2)), int(m.group(3)), int(m.group(4)), 0, 0]; continue
        m = re.match(r'^\s+\S+ instanced.*draws (\d+), instances \d+, triangles (\d+)k', ln)
        if m and cur:
            d[cur][3], d[cur][4] = int(m.group(1)), int(m.group(2))
    return d
b = {}
for r in csv.DictReader(open(sys.argv[1], encoding='utf-8'), delimiter='\t'):
    b[r['camera']] = [int(r['draws_a']), int(r['shadow_a']), int(r['trisK_a']), int(r['inst_draws_a']), int(r['itrisK_a'])]
a = load_stats(sys.argv[2])
rows = ['camera                               total draws b>a (d)   total trisK b>a (%)    renderer b>a  shadow b>a  inst.draws b>a  inst.trisK b>a']
worst = []
for k in sorted(a):
    if k not in b:
        continue
    B, A = b[k], a[k]
    tb, ta = B[0] + B[1] + B[3], A[0] + A[1] + A[3]
    qb, qa = B[2] + B[4], A[2] + A[4]
    pct = 100.0 * (qa - qb) / max(qb, 1)
    rows.append(f'{k:36s} {tb:5d}>{ta:5d} ({ta - tb:+4d})    {qb:4d}>{qa:4d} ({pct:+5.1f} %)   {B[0]:4d}>{A[0]:4d}   {B[1]:4d}>{A[1]:4d}    {B[3]:4d}>{A[3]:4d}      {B[4]:3d}>{A[4]:3d}')
    worst.append((ta - tb, pct, k))
rows.append('cameras compared: %d; max draws delta: %+d (%s); max tris delta: %+.1f %% (%s)' % (len(worst), max(worst)[0], max(worst)[2], max(worst, key=lambda x: x[1])[1], max(worst, key=lambda x: x[1])[2]))
out = '\n'.join(rows)
print(out)
if len(sys.argv) > 3:
    open(sys.argv[3], 'w', encoding='utf-8').write(out + '\n')
