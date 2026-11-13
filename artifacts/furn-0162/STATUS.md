# furn-0162 STATUS (ADR 0162 meble uliczne + tablice G5/G3)

- 08:25 worktree z origin/main ff9777e2d, przygotowanie (Data/raw copies, junctions, Library).
- Krok 1 (kod): wiata BKM 5/7/9 m czerwona + czarna 7 m (atlas 1 materiał, szkło przezroczyste, dach PC dymiony, stelaż D-15 na dachu),
  latarnie GP 12 -> 11 m + drzwiczki 0.60x0.13 + szara podstawa 0.3 m (atlas galv), słup energetyczny 12 m jedno źródło (GROUND_PROP_H),
  U-12a / U-12 / U-5a prototypy (w danych regionu brak -> 0 sztuk), tablice: panele ze strzałkami, Centrum w białym polu, owale PL/BY,
  p40 wg 2024 (Centrum osobno ←) + kolumny z ortofoto, 3 nowe konstrukcje na al. Tysiąclecia (E-1 P009, VMS P010, portal P005-8).
- NASTĘPNY KROK: `uv run --project tools/worldgen python -m pytest tests/gis -q -k "furniture or props or signs or landmarks"` potem build_world.
- 09:10 build_world OK (8.9 min): wiaty 13x7 m / 7x5 m / 3 czarne (0x9 m w tej próbce), lamp_11m 164, 6 konstrukcji tablic (p40 przeniesiony na ortofoto: -475.2,-8.8), 0 stale. Testy jednostkowe 15/15 + 109 powiązanych.
- W tle: fidelity (heavy), unity_run.ps1 (czeka na PHONE_RUN lidera: baseline Low -> import -> after Low/High + sondy + sbs).
- NASTĘPNY KROK: `pwsh -File artifacts/furn-0162/tools/unity_run.ps1` (jeśli przerwane: -SkipBaseline), potem pary sbs i budżet.
- 09:45 1801374: latarnie są w danych (ortofoto: stopy E -539, N 114.7..297.9 co 32-40 m, dwuramienne na zdjęciu); reguła stawiała je 1.5 m dalej, na linii ekranu (zasłonięte). Dodany authored rząd `tysiaclecia-nb-east-double-lamps` (lamp_rows.json, lamp_double_10m), zastępuje 5 lamp reguły w197904074.
- W tle (bix6xpsch): build_world 3 + fidelity -> unity_run.ps1 (czeka na PHONE_RUN lidera; baseline Low -> import -> after).
- NASTĘPNY KROK: po renderach `python artifacts/furn-0162/tools/budget.py` i pary sbs.
