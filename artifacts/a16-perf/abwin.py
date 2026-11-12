"""Per-window A/B GPU p50 pairs from [PASSAB] logcat lines. Usage: python abwin.py <rundir>..."""
import re, sys
for d in sys.argv[1:]:
    rows = []
    for l in open(d + '/logcat.txt', encoding='utf-8', errors='ignore'):
        m = re.search(r'state=([AB]) n=\d+ gpu_p50=([\d.]+)', l)
        if m: rows.append((m.group(1), float(m.group(2))))
    pairs = []
    for i in range(len(rows) - 1):
        if rows[i][0] == 'A' and rows[i + 1][0] == 'B': pairs.append(round(rows[i][1] - rows[i + 1][1], 1))
    print(d.split('/')[-1], 'A-B per pair:', pairs)
