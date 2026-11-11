"""Summarise device runs: frametimes.csv per run dir (after 25 s warm-up). Usage: python summarize.py <dir> [<dir>...]"""
import csv, sys, os, re, glob
def pct(a, q):
    if not a: return float('nan')
    a = sorted(a); return a[max(0, min(len(a)-1, int(-(-q*len(a)//1))-1))]
def summ(d):
    f = os.path.join(d, 'frametimes.csv')
    if not os.path.exists(f): return None
    rows = [r for r in csv.DictReader(open(f)) if float(r['t_s']) > 25]
    ft = [float(r['frame_ms']) for r in rows]
    g = [float(r['gpu_ms']) for r in rows if float(r['gpu_ms']) > 0]
    c = [float(r['cpu_main_ms']) for r in rows if float(r['cpu_main_ms']) > 0]
    span = sum(ft)/1000
    out = dict(n=len(ft), fps=len(ft)/span if span else 0, p50=pct(ft,.5), p95=pct(ft,.95), p99=pct(ft,.99),
               gp50=pct(g,.5), gp95=pct(g,.95), gp99=pct(g,.99), cp50=pct(c,.5), cp95=pct(c,.95), over40=sum(x>40 for x in ft))
    # A/B rows
    ab = {}
    for r in rows:
        k = r.get('ab') or ''
        if k and float(r['gpu_ms']) > 0: ab.setdefault(k, []).append(float(r['gpu_ms']))
    out['ab'] = {k: (len(v), round(pct(v,.5),2), round(pct(v,.9),2)) for k, v in ab.items()}
    m = os.path.join(d, 'metrics.json')
    if os.path.exists(m):
        t = open(m).read(); p = re.search(r'"pssMb":\s*([\d.]+)', t); out['pss'] = float(p.group(1)) if p else None
        tt = re.search(r'"batteryTempC":\s*([\d.]+)', t); out['temp'] = float(tt.group(1)) if tt else None
    lc = os.path.join(d, 'logcat.txt')
    if os.path.exists(lc):
        out['passab'] = [l.split('[PASSAB]')[1].strip() for l in open(lc, encoding='utf-8', errors='ignore') if 'PASSAB] summary' in l][-1:]
    return out
dirs = []
for a in sys.argv[1:]: dirs += sorted(glob.glob(a))
print(f"{'run':28} {'n':>5} {'fps':>6} {'p50':>6} {'p95':>6} {'p99':>6} {'>40':>4} {'gp50':>6} {'gp95':>6} {'gp99':>6} {'cp50':>6} {'cp95':>6} {'pss':>5} {'T':>5}")
for d in dirs:
    s = summ(d)
    if not s: continue
    print(f"{os.path.basename(d):28} {s['n']:5d} {s['fps']:6.2f} {s['p50']:6.2f} {s['p95']:6.2f} {s['p99']:6.2f} {s['over40']:4d} {s['gp50']:6.2f} {s['gp95']:6.2f} {s['gp99']:6.2f} {s['cp50']:6.2f} {s['cp95']:6.2f} {s.get('pss') or 0:5.0f} {s.get('temp') or 0:5.1f}")
    if s['ab']: print('   ab', s['ab'])
    if s.get('passab'): print('   ', s['passab'])
