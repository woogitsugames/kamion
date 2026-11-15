"""Wykaz UKE (xlsx): wiersze Białegostoku; dopasowanie adresów do wskazanych ulic/numerów; liczba operatorów (bez nazw w wyjściu: A, B, C…)."""
import sys, openpyxl, json, collections, re
files = sys.argv[1].split(',')
targets = json.loads(sys.argv[2])  # {"klucz": ["Zwierzyniecka 4", ...]}
rows = []
for f in files:
    ws = openpyxl.load_workbook(f, read_only=True).active
    for r in ws.iter_rows(values_only=True):
        if r and r[6] == 'Białystok':
            rows.append((f.split('uke_')[-1].split('.')[0],) + tuple(r))
ops = {}
letters = 'ABCDEFG'
print('wierszy Białystok', len(rows), 'stacji (IdStacji+operator)', len({(r[1], r[9]) for r in rows}))
out = {}
for k, pats in targets.items():
    hit = [r for r in rows if any(re.search(r'\b' + re.escape(p) + r'\b', str(r[8])) for p in pats)]
    oo = sorted({r[1] for r in hit})
    for o in oo:
        ops.setdefault(o, letters[len(ops)])
    out[k] = {'n_wierszy': len(hit), 'operatorzy': [ops[o] for o in oo], 'pasma': sorted({r[0] for r in hit}),
              'lokalizacje': sorted({str(r[8]) for r in hit}), 'wsp': sorted({(r[5], r[6]) for r in hit})[:3]}
    print(k, out[k])
json.dump(out, open(sys.argv[3], 'w'), ensure_ascii=False, indent=1, default=str)
