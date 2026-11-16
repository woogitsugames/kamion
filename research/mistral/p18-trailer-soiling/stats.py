# -*- coding: utf-8 -*-
"""Zestawienie §4 README z stats_frames.csv (cechy odczytane ręcznie z kadrów; n/o = nieoceniane).
Uruchom: python stats.py"""
import csv, statistics
rows = list(csv.DictReader(open('stats_frames.csv', encoding='utf-8')))
def frac(rs, col, val='tak'):
    ok = [r for r in rs if r[col] != 'n/o']
    return f"{sum(r[col] == val for r in ok)}/{len(ok)}" + (f" (n/o: {len(rs) - len(ok)})" if len(ok) != len(rs) else "")
for name, rs in (("brud (bez poziomu ślad)", [r for r in rows if r['poziom'] == 'brud']), ("brud + ślad", rows)):
    z = [float(r['zacieki_na_skrzydlo']) for r in rs]
    print(f"== {name}: n = {len(rs)}")
    for col in ('prog_rama', 'belka', 'lampy', 'film_cala_wys', 'wycierki'):
        print(f"  {col}: {frac(rs, col)}")
    print(f"  zacieki/skrzydło: mediana {statistics.median(z):g}, zakres {min(z):g}–{max(z):g}, kadrów z ≥1 zaciekiem: {sum(v > 0 for v in z)}/{len(z)}")
    print(f"  zimowe (XII–II): {sum(r['zimowy'] == 'tak' for r in rs)}")
    eu = [r for r in rs if r['europa'].startswith('tak')]
    print(f"  Europa: {len(eu)} (pewne: {sum(r['europa'] == 'tak' for r in rs)}; + Rosja/PDM: {sum(r['europa'] == 'tak*' for r in rs)}; + kraj ESTIMATED/UNVERIFIED: {sum(r['europa'] == 'tak?' for r in rs)})")
