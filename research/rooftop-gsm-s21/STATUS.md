# STATUS — K67 dachowe GSM (gałąź research/rooftop-gsm-s21)

## 2026-11-15 ~15:40 UTC — uzupełnienie s21b (gotowe do recenzji)
- Manifest 148 wierszy (nowe K67-083…148 = 66). Obejrzane kadry naziemne: 60 (KartaView 11, Commons 48, Panoramax 1); przypisane z widoczną instalacją: 4 (wszystkie wieżowiec M57, KartaView 2019/2021).
- Wysokości: statusy LIDAR → ESTIMATED (LIDAR, dolna granica); 6 dachów z rozkładem (5 z urządzeniami + Hallera negatyw); wieżowiec dodatkowo metodą proporcji do kondygnacji (K67-094…096): środkowy 9,7–11,0 m, W 8,4–9,5 m, krótkie NE 4,4–5,1 m nad attyką. Konflikt środkowego masztu z LIDAR 2025 (5,25 m) — zgłoszony, nierozstrzygnięty.
- Nowe: maszt na Zwierzynieckiej 4 wg OSM jest radiowy (communication:radio), nie GSM (K67-148).
- Audyt r3: 14/66, seed 2026111521 — 13 PASS, 1 FIX (K67-137).
- KRYTERIA: 5/5 spełnione; kadry naziemne — CZĘŚCIOWO (tylko wieżowiec; 5 dachów bez pokrycia/zasłonięte).
Następny krok (opcjonalny, gdy Commons przestanie zwracać 429): `cd research/rooftop-gsm-s21 && python3 -I tools/s21b/cbatch.py <cb_dir> <tytuły.json>` z geosearch dla zwierzyniecka4/hallera19/kopernika5a (usunąć SKIPGEO), potem `python3 -I tools/s21b/commons_export.py <cb_dir> . && python3 -I build_manifest.py`

## 2026-11-15 ~14:00 UTC — FIX r2 (gotowe do recenzji)
- Wysokości urządzeń nad dachem z LIDAR GUGiK 2025-04-18 (12 p/m²): Skorupska 17 4,3/4,5/11,6; Dobra 3 7,7/8,6/9,6; Zwierzyniecka 4 8,6 (n=1); Kopernika 2,5/2,7/3,4; wieżowiec (kontrola) 4,5/5,1/10,9; Hallera 19 — brak > 1,3 m. Metoda cieni: kontrola na Zwierzynieckiej (h > 5,6 m, zgodne).
- Ortofoto przecentrowane (ortho_dobra_c + 6 nowych), art. 29 Pb potwierdzony w t.j. Dz.U. 2026 poz. 524 (ELI), wieżowiec 9–12 m (M57-FIX #88), Commons: 9 kadrów (4 tytuły nadal 429, log w out/commons_log.json).
- KRYTERIA M67: spełnione 5/5, kadry naziemne dachów z masztami — CZĘŚCIOWO (luka 1 w README).
Następny krok (opcjonalny, gdy Commons przestanie zwracać 429): `python3 -I tools/commons_fetch.py tools files/ out/commons_log.json && python3 -I build_manifest.py`

## 2026-11-15 FIX r2 — krok 1: LIDAR
- Skorowidze WFS (ORTO + LIDAR) → out/skorowidz.json; out/lidar_masts.json + profile boczne PNG.

## 2026-11-15 ~13:30 UTC — PR
- manifest 35 wierszy; audyt 7/35 PASS. NIESPEŁNIONE wtedy: rozkład wysokości (≥ 5 dachów), kadry naziemne 0.
