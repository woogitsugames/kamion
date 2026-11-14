# STATUS — R7 sky-weather-bialystok

## Krok 1 (2026-11-14) — IMGW pobrane i przeliczone
- `tools_imgw.py download` → 40 plików, 5,41 MB (`imgw_files.csv` z sha256); `compute` → `out/imgw_monthly_raw.csv`,
  `out/imgw_monthly_normals.csv` (1991–2020 i 2014–2023), `out/imgw_hourly_visibility_cloud.csv` (87 613 terminów 2014–2023).
- Uwaga: usłonecznienie ma braki od 2016 (status 8); liczniki dni ze zjawiskami IV 2022–XII 2023 = status 9 (brak pomiaru zjawisk).
- NASTĘPNY KROK: `python3 -I tools_sun.py` (słońce NOAA) → `out/sun_table.csv`

## Krok 2 — słońce (NOAA) policzone
- `tools_sun.py` → `out/sun_table.csv` (12 dat × wysokość/azymut 8/12/16/20, wschód/zachód, zmierzchy, azymuty). Kontrola krzyżowa
  z pakietem astral 3.2 (niezależna implementacja): różnice ≤ 1 min i ≤ 0,1°.
- NASTĘPNY KROK: zdjęcia nieba — Panoramax API (bbox Białystok) + Commons API; pobranie do files/, miniatury 960 px, oglądanie.
