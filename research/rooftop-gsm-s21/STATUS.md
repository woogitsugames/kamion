# STATUS — K67 dachowe GSM (gałąź research/rooftop-gsm-s21)

## 2026-11-15 ~14:00 UTC — FIX r2 (gotowe do recenzji)
- Wysokości urządzeń nad dachem z LIDAR GUGiK 2025-04-18 (12 p/m²): Skorupska 17 4,3/4,5/11,6; Dobra 3 7,7/8,6/9,6; Zwierzyniecka 4 8,6 (n=1); Kopernika 2,5/2,7/3,4; wieżowiec (kontrola) 4,5/5,1/10,9; Hallera 19 — brak > 1,3 m. Metoda cieni: kontrola na Zwierzynieckiej (h > 5,6 m, zgodne).
- Ortofoto przecentrowane (ortho_dobra_c + 6 nowych), art. 29 Pb potwierdzony w t.j. Dz.U. 2026 poz. 524 (ELI), wieżowiec 9–12 m (M57-FIX #88), Commons: 9 kadrów (4 tytuły nadal 429, log w out/commons_log.json).
- KRYTERIA M67: spełnione 5/5, kadry naziemne dachów z masztami — CZĘŚCIOWO (luka 1 w README).
Następny krok (opcjonalny, gdy Commons przestanie zwracać 429): `python3 -I tools/commons_fetch.py tools files/ out/commons_log.json && python3 -I build_manifest.py`

## 2026-11-15 FIX r2 — krok 1: LIDAR
- Skorowidze WFS (ORTO + LIDAR) → out/skorowidz.json; out/lidar_masts.json + profile boczne PNG.

## 2026-11-15 ~13:30 UTC — PR
- manifest 35 wierszy; audyt 7/35 PASS. NIESPEŁNIONE wtedy: rozkład wysokości (≥ 5 dachów), kadry naziemne 0.
