# STATUS — K67 dachowe GSM (gałąź research/rooftop-gsm-s21)

## 2026-11-15 ~13:30 UTC — PR
- manifest 35 wierszy (element 13, dach 6, kadr 11, przepis 5); katalog 13 typów (6 SOURCED z kart); 6 dachów (UKE+OSM+ortofoto); przepisy art. 29 PB, rozp. 2021/264; UKE bez wysokości.
- audyt 7/35 PASS.
- NIESPEŁNIONE: rozkład wysokości masztu dla ≥ 5 dachów (tylko M57), kadry naziemne 0 (Commons 429).

Następny krok: pobrać kadry z listy w `sources.md` (gdy Commons odblokuje), np. `python3 -I tools/commons_fetch960.py` z K69, i dopisać wysokości ESTIMATED (proporcja do kondygnacji 2,8–3,0 m bloku).
