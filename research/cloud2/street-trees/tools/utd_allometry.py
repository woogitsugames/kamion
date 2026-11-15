"""Wymiary drzew ulicznych wg wieku z surowych pomiarów USDA Urban Tree Database (RDS-2016-0005, TS3_Raw_tree_data.csv).
Regiony chłodne/kontynentalne: MidWst (Minneapolis), NoEast (Queens NY), LoMidW (Indianapolis), NMtnPr (Fort Collins),
TpIntW (Boise), PacfNW (Longview) — tylko jako uzupełnienie gdy gatunku brak w czterech pierwszych.
python3 -I tools/utd_allometry.py files/docs/utd/Data/TS3_Raw_tree_data.csv > data/utd_allometry.json
"""
import csv, sys, json, statistics as st
rows = list(csv.DictReader(open(sys.argv[1], encoding='latin-1')))
COLD = ['MidWst', 'NoEast', 'LoMidW', 'NMtnPr']
EXTRA = ['TpIntW', 'PacfNW', 'InlVal']
SP = ['Tilia cordata', 'Acer platanoides', 'Fraxinus pennsylvanica', 'Fraxinus excelsior', 'Aesculus hippocastanum',
      'Betula pendula', 'Robinia pseudoacacia', 'Acer negundo', 'Pyrus calleryana', 'Tilia tomentosa', 'Carpinus betulus',
      'Platanus x acerifolia']
AGE = [(1, 10), (11, 20), (21, 40), (41, 60), (61, 200)]
def f(r, k):
    try:
        v = float(r[k]); return v if v >= 0 else None
    except ValueError: return None
def q(v, p):
    v = sorted(v); i = (len(v) - 1) * p; lo = int(i); hi = min(lo + 1, len(v) - 1); return round(v[lo] + (v[hi] - v[lo]) * (i - lo), 1)
out = {}
for sp in SP:
    R = [r for r in rows if r['ScientificName'].strip().lower() == sp.lower()]
    regs = [g for g in COLD if any(r['Region'] == g for r in R)] or [g for g in EXTRA if any(r['Region'] == g for r in R)]
    R = [r for r in R if r['Region'] in regs]
    o = {'regions': regs, 'n': len(R), 'age_classes': []}
    for lo, hi in AGE:
        S = [r for r in R if f(r, 'Age') is not None and lo <= f(r, 'Age') <= hi and f(r, 'TreeHt (m)') and f(r, 'AvgCdia (m)')]
        if len(S) < 5:
            o['age_classes'].append({'age': f'{lo}-{hi}', 'n': len(S)}); continue
        H = [f(r, 'TreeHt (m)') for r in S]; C = [f(r, 'AvgCdia (m)') for r in S]; D = [f(r, 'DBH (cm)') for r in S]
        B = [f(r, 'CrnBase') for r in S if f(r, 'CrnBase') is not None]
        o['age_classes'].append({'age': f'{lo}-{hi}', 'n': len(S), 'H_p25': q(H, .25), 'H_med': q(H, .5), 'H_p75': q(H, .75),
                                 'crown_p25': q(C, .25), 'crown_med': q(C, .5), 'crown_p75': q(C, .75),
                                 'dbh_med_cm': q(D, .5), 'girth_med_cm': round(q(D, .5) * 3.1416), 'crown_base_med': q(B, .5) if B else None,
                                 'crown_over_H_med': round(st.median(c / h for c, h in zip(C, H)), 2)})
    # klasy obwodu jak u Łaski 2015 (obwód na 1,2 m; tu DBH na 1,37 m)
    o['girth_classes'] = []
    for lo, hi in [(0, 50), (51, 100), (101, 150), (151, 200), (201, 300)]:
        S = [r for r in R if f(r, 'DBH (cm)') and lo < f(r, 'DBH (cm)') * 3.1416 <= hi + 0.999 and f(r, 'TreeHt (m)') and f(r, 'AvgCdia (m)')]
        if len(S) < 5: o['girth_classes'].append({'girth_cm': f'{lo}-{hi}', 'n': len(S)}); continue
        H = [f(r, 'TreeHt (m)') for r in S]; C = [f(r, 'AvgCdia (m)') for r in S]
        o['girth_classes'].append({'girth_cm': f'{lo}-{hi}', 'n': len(S), 'H_p25': q(H, .25), 'H_med': q(H, .5), 'H_p75': q(H, .75),
                                   'crown_p25': q(C, .25), 'crown_med': q(C, .5), 'crown_p75': q(C, .75)})
    out[sp] = o
json.dump(out, sys.stdout, indent=1)
