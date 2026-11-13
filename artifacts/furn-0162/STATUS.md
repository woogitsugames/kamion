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
- 10:00 Pierwszy przebieg Unity OK, ale baseline z kopii _Generated main był nieczysty (brak portalu Andersa, inna roślinność) -> run1/ zarchiwizowany. Dach wiaty przeniesiony do atlasu (2 sloty). Teraz czysty A/B (ab_run.ps1): origin/main build+import+render, potem HEAD build+import+render. NIE commitować w trakcie (drzewo ma pliki main).
- NASTĘPNY KROK: po `ab_run.log` "== done": `python artifacts/furn-0162/tools/budget.py artifacts/furn-0162/base-Low-clear artifacts/furn-0162/after-Low-clear artifacts/furn-0162/budget-low.txt`; `pwsh -File artifacts/furn-0162/tools/pairs.ps1`.

## STOP (limit 5 h), 2026-11-13 — stan do wznowienia
- Cały kod ADR 0162 jest na gałęzi `furn-0162` (HEAD na origin). Zrobione: wiata BKM 5/7/9 m + czarna (2 sloty), latarnie 11 m + drzwiczki + szara podstawa, słup energetyczny 12 m jedno źródło, U-12a/U-12/U-5a prototypy (0 w danych), tablice G3 (p40 wg 2024 + kolumny z ortofoto, strzałki portalu Andersa, E-1 P009, VMS P010, portal P005-8), rząd latarni dwuramiennych Tysiąclecia NB (1801374), D-15 bez „BUS”, LICENSES, szkic ADR 0162, testy 15/15.
- W TLE działa `artifacts/furn-0162/tools/ab_run.ps1` (log `artifacts/furn-0162/logs/ab_run.log`). UWAGA: w fazie A drzewo robocze ma pliki origin/main w `tools`, `Data/Regions`, `art-source`, `game/Assets/_Project/World/Import`, `.../UI/Resources/CabDisplay` (także w indeksie). NIE commitować całości, dopóki log nie pokaże "== B" (skrypt sam przywraca `git checkout HEAD -- <ścieżki>`).
- Jeśli zadanie zostało przerwane przed "== B": `git checkout HEAD -- tools Data/Regions art-source game/Assets/_Project/World/Import game/Assets/_Project/UI/Resources/CabDisplay` i zwolnij sloty `pwsh scripts/unity-slot.ps1 -Release -Owner furn-0162; pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner furn-0162`, potem `git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings`.
- NASTĘPNY KROK (wznowienie): jeśli brak "== done" w logu -> `pwsh -File artifacts/furn-0162/tools/ab_run.ps1`; potem `uv run --project tools/worldgen python artifacts/furn-0162/tools/budget.py artifacts/furn-0162/base-Low-clear artifacts/furn-0162/after-Low-clear artifacts/furn-0162/budget-low.txt` i `pwsh -File artifacts/furn-0162/tools/pairs.ps1`, obejrzeć pary, uzupełnić sekcję „Dowody” ADR 0162, `pytest tests/gis` (heavy slot) + EditMode, skopiować pary do `C:\Users\matma\Documents\Claude\kamion\artifacts\furn-0162\pairs\`.
- Run1 (nieczysty baseline z kopii _Generated main): Low draws +36 max (Putry), tris +2.2 % max — liczby niewiarygodne, do zastąpienia czystym A/B. Wizualnie run1: wiaty czerwone BKM OK, p40 na właściwej stacji, tablice czytelne.
- Zgłoszenia: krawężnik przystankowy 16 cm -> 0161; drzewa 297817 -> 0163; zmiana poza zakresem: `InstanceImporter.cs` + `build_world.instance_ends` StartsWith("bus_shelter") — do akceptacji lidera.

## WZNOWIENIE (nowy agent) 2026-11-13 10:20
- ab_run przerwany po build_furn (exit 0) w fazie B. Bazowe rendery A kompletne (base-Low-clear 49, base-probes-Low, base-sbs-Low-clear). Drzewo = HEAD + świeże wyjście build B (dach w atlasie -> 2 sloty; commit regen).
- W TLE: `artifacts/furn-0162/tools/ab_resume_b.ps1` (tylko import + rendery B), log `artifacts/furn-0162/logs/ab_run.log`.
- NASTĘPNY KROK: po "== done" w logu: `uv run --project tools/worldgen python artifacts/furn-0162/tools/budget.py artifacts/furn-0162/base-Low-clear artifacts/furn-0162/after-Low-clear artifacts/furn-0162/budget-low.txt`; `pwsh -File artifacts/furn-0162/tools/pairs.ps1`. Jeśli przerwane przed "== done": zwolnij slot i `pwsh -File artifacts/furn-0162/tools/ab_resume_b.ps1`.
- 10:55 A/B czysty (after1, Low): max draws +24 g3b-rondo-putry-approach, +11 putry-above, +11 route-putry-entry-signs, +9 route-putry-approach, +10 g3b-eye-s1482; tris max +1.0 %. Przyczyna: 5 nowych tablic OB x 3 submesze + 3 konstrukcje. pytest gis: 1 fail (test_photo_matched_overrides_applied: 3 nowe bramownice) -> test poprawiony. Dodany test EditMode InstancePolicyShelterTests.
- Redukcja: tablica OB = 1 materiał (lico + szary pas tyłu w teksturze tablicy; tył i szyny próbkują pas) -> 1 draw zamiast 3.
- W TLE: `pwsh -File artifacts/furn-0162/tools/ab_b2.ps1` (build + import + rendery after*), log ab_run.log.
- NASTĘPNY KROK: po "== done": `python artifacts/furn-0162/tools/budget.py artifacts/furn-0162/base-Low-clear artifacts/furn-0162/after-Low-clear artifacts/furn-0162/budget-low.txt`; pairs.ps1; EditMode testy.
- 11:45 B2 (tablica OB = 1 materiał) Low: max draws +10 g3b-rondo-putry-approach (3 nowe konstrukcje + 5 tablic G3 2024), g3a-rondo-bie-approach +3, reszta trasy -10..+1; tris max +1,0 %. pytest gis 1016/1 fail (lamp_12m -> lamp_11m, poprawione; streetscape 59/59), EditMode 498/498. Pary w C:\Users\matma\Documents\Claude\kamion\artifacts\furn-0162\pairs\ (18). ADR 0162 Dowody uzupełnione.
- DECYZJA WŁAŚCICIELA: +10 draws Low na g3b-rondo-putry-approach (421 -> 431) za 3 prawdziwe konstrukcje 2024 al. Tysiąclecia; para: pairs\probe-f162-tys-portal-g3p005.jpg. Dalsza redukcja = scalić tablice z bramownicą w jeden mesh (zmiana QA/walidatora tablic) — nie robione.
- Gotowe do scalenia: TAK (z decyzją właściciela o +10 draws na jednej kamerze gate3 i akceptacją InstanceImporter.cs).
- NASTĘPNY KROK (lider): `git merge furn-0162` (bez konfliktów z main w tools/tests), potem `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c` i kamery WorldC.
