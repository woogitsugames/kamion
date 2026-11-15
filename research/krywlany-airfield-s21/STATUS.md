# STATUS — K64 (M64 lotnisko Krywlany z drogi)

- 2026-11-15 ~10:20 UTC — manifest gotowy (92 wiersze: 30 kadrów, 23 obiekty, 19 nawierzchni, 16 geometria, 4 kamery), README, sources, files/ (18 kadrów + 13 wycinków ortofoto, ~6 MB), tools/, data/. Audyt 20 % (seed 20261115, 19 wierszy): 17 PASS, 2 FIX — zapis `audit_20_percent.json` (sprawdzanie HTTP linków).
- Następny krok: `git add research/krywlany-airfield-s21 && git commit && git push -u origin research/krywlany-airfield-s21`, potem PR do main „research: M64 lotnisko Krywlany z drogi (K64)”.
- Odtworzenie obliczeń: `python3 -I tools/viewgeo.py <scratch> tools/points.json data/view_results.json` (wymaga mozaiki NMPT `dem/nmpt.npy` z `tools/asc_crop.py` i NMT z `tools/nmt_fetch.py`).
- 2026-11-15 ~11:20 UTC — audyt zapisany (`audit_20_percent.json`, 17 PASS / 2 FIX), manifest z LF i URL-ami bez parametrów utm. PR otwierany. Następny krok: brak (paczka gotowa do recenzji); lider: `gh pr view <nr>`.
