# STATUS — K67 dachowe GSM (gałąź research/rooftop-gsm-s21)

## 2026-11-15 FIX r2 — krok 1: LIDAR
- Skorowidze WFS (ORTO + LIDAR) dla 5 dachów → `out/skorowidz.json`: nalot ortofoto i LIDAR 2025-04-18 (12 p/m²).
- Wysokości urządzeń nad dachem z chmur LAZ GUGiK (`tools/lidar_masts.py`, `masts_xy.json`) → `out/lidar_masts.json` + profile boczne PNG.
Następny krok: metoda cieni jako kontrola krzyżowa — `uv run --no-project --with pillow python -I tools/sun.py`

## 2026-11-15 ~13:30 UTC — PR
- manifest 35 wierszy; audyt 7/35 PASS. NIESPEŁNIONE wtedy: rozkład wysokości (≥ 5 dachów), kadry naziemne 0.
