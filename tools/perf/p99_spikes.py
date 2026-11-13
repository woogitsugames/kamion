"""ADR 0177: frame-spike breakdown of A16 drives (p50/p95/p99, frames > 40/45/50/60 ms, spike times).

Arguments: gate3 timestamps (artifacts/gate3/<ts>/RFGL34SJYDZ/drive/frametimes.csv), run directories that contain
frametimes.csv (tools/perf/phone-p99.ps1 output) or CSV paths. The window starts 25 s after the first frame (load),
as in device-metrics.ps1. `--summary` prints one line per run only. If logcat.txt sits next to the CSV, [SPIKE] lines
(spike_probe 1) are summarised: count, how many had a GC, positions.
"""
import csv, os, re, sys
import numpy as np

BASE = r'C:\Users\matma\Documents\Claude\kamion\artifacts\gate3'


def resolve(a):
    if os.path.isfile(a):
        return a
    if os.path.isdir(a):
        for p in (os.path.join(a, 'frametimes.csv'), os.path.join(a, 'drive', 'frametimes.csv')):
            if os.path.isfile(p):
                return p
    return os.path.join(BASE, a, 'RFGL34SJYDZ', 'drive', 'frametimes.csv')


def main(argv):
    summary = '--summary' in argv
    args = [a for a in argv if a != '--summary']
    for a in args:
        p = resolve(a)
        rows = list(csv.reader(open(p)))[1:]
        t = np.array([float(r[1]) for r in rows]); f = np.array([float(r[2]) for r in rows])
        c = np.array([float(r[3]) for r in rows]); g = np.array([float(r[4]) for r in rows])
        t0 = t[0]; m = t >= t0 + 25
        tw, fw, cw, gw = t[m], f[m], c[m], g[m]
        n = len(fw)
        line = (f"{a}: n={n} p50={np.percentile(fw,50):.2f} p95={np.percentile(fw,95):.2f} p99={np.percentile(fw,99):.2f} "
                f">40:{(fw>40).sum()} >45:{(fw>45).sum()} >50:{(fw>50).sum()} >60:{(fw>60).sum()} "
                f">40 in 25-40s:{((fw>40)&(tw-t0<40)).sum()} 1%rank={int(n*0.01)}")
        print(line)
        lc = os.path.join(os.path.dirname(p), 'logcat.txt')
        if os.path.isfile(lc):
            sp = [l for l in open(lc, encoding='utf-8', errors='replace') if '[SPIKE] t=' in l]
            gc = sum(1 for l in sp if ' gc=1 ' in l)
            print(f"  [SPIKE] lines={len(sp)} with_gc={gc}")
            if not summary:
                for l in sp:
                    mm = re.search(r'\[SPIKE\] (.*)', l)
                    print('   ', mm.group(1)[:200] if mm else l.strip()[:200])
        if summary:
            continue
        srt = np.sort(fw)[::-1]
        print(f"  top25={np.round(srt[:25],1).tolist()}")
        idx = np.where(fw > 40)[0]
        print("  spikes (t_rel, frame, cpu, gpu):")
        for i in idx:
            print(f"   {tw[i]-t0:7.2f} {fw[i]:6.1f} cpu {cw[i]:6.1f} gpu {gw[i]:6.1f}  prev {fw[i-1]:.1f} next {fw[min(i+1,n-1)]:.1f}")
        if len(idx) > 1:
            print("  intervals:", np.round(np.diff(tw[idx]), 2).tolist())


if __name__ == '__main__':
    main(sys.argv[1:])
