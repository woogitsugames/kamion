# STATUS bridge-warn-s24 (ADR 0307, D91)

- 11:2x zdjęcia: Mapillary (bbox mostu, sekwencje 2019-07-03..2020-09-20) + Commons „Tykocin Most drogowy 01–09” (2025-09-20, CC BY-SA 4.0): B-16 „3,7 m” przy obu wjazdach (południowy razem z B-33 „40”); B-18 nie widać na żadnym zdjęciu (OSM maxweight:hgv=12 z 2026-08-22 jest nowsze od wszystkich zdjęć) → 12 t = WORKING_VALUE. Zdjęcia: `Data/raw/mapillary/tykocin-bridge`, `Data/raw/refs/tykocin-bridge-commons` (poza gitem), wycinki `artifacts/bridge-warn-s24/refs/`.
- 11:4x znaki: `tools/worldgen/streetscape/limit_signs.py` (B-16/B-18 15 m przed mostem/tunelem z limitem w grafie), twarz B-16 w `signs.py`, pytest `tests/gis/test_limit_signs_0307.py` 5/5; kafel `tykocin` przebudowany (470 s): 2 słupki (E 517,9 N −19,3 i E 494,5 N 203,9), B-16_3.7 ×2, B-18_12 ×2.
- 12:0x gra (nieskompilowane w Unity): `Core/Navigation/RouteRestriction.cs` (TruckLimits, RouteRestriction, RestrictionScout), `RoutePath.Restr`, planner, `NavTrip.Compose`, `NavigationService.Restriction`, pasek/znaczniki w `NavDraw` (minimapa, pełna mapa, ekran kabiny), kafle HUD (`HudWarning.RoadLimit*`), testy `NavRestriction0307Tests` (EditMode), `NavRestrictionWarning0307Tests` (PlayMode).
- NASTĘPNY KROK: Library (robocopy z main: `artifacts/bridge-warn-s24/logs/robocopy.status`), potem
  `pwsh scripts/unity-slot.ps1 -Acquire -Owner bridge-warn-s24; pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 -Filter NavRestriction0307Tests`
- 12:0x testy: EditMode Win64 63/63 (`artifacts/tests/editmode-20261119-115752.xml`: NavRestriction0307Tests 7 + NavTruckLimits/HudRedesign0283/NavRouting/Nav0168), PlayMode Win64 28/28 (`playmode-20261119-115912.xml`: NavRestrictionWarning0307Tests 4 + NavTrip/NavStreamFollow/CabScreens); .NET nav-runner 94/94, hud-runner 11/11; pytest znaków 58 pass / 1 skip. Most na trasie: S 1249..1443 m z 1610 m (start 300 m przed szwem).
- 12:02 łańcuch w tle `artifacts/bridge-warn-s24/logs/chain.ps1` (slot → import dw671-tykocin-09, tykocin Win64 → build-windows -Regions) — status `logs/chain.status`.
- NASTĘPNY KROK: po `build exit=0`: `pwsh artifacts/bridge-warn-s24/logs/run.ps1` (przejazd 300 s, zrzuty co 5 s od t=60), obejrzeć zrzuty z ostrzeżeniem (t ≈ 100–140 s), wpisać liczby do ADR 0307 (PLACEHOLDER_NUMBERS), skopiować `artifacts/bridge-warn-s24` do main.

## STAN przy STOP (limit tygodniowy), 2026-11-19 ~13:0x
- Gałąź wypchnięta. Zrobione i zmierzone: znaki B-16/B-18 w generatorze + kafel `tykocin` przebudowany (wspólny derived), ostrzeżenie GPS (minimapa, pełna mapa, ekran kabiny) + kafle HUD, EditMode 63/63, PlayMode 28/28, nav-runner 94/94, hud-runner 11/11, pytest znaków 58 pass/1 skip, przejazd playerem 300 s exit 0 (exe `b7374f8d68-dirty-regions`): ostrzeżenie 500 m przed mostem, „na tym odcinku” na moście, postój na Rynku. ADR 0307 z liczbami, LICENSES.
- NIEZWERYFIKOWANE: commit „kafel HUD WYS. 3,7 m” (po zrzucie: „WYSOKOŚĆ 3,7 m” łamało się na 2 linie) — zmieniony tekst + oczekiwanie w `NavRestriction0307Tests`; w tle biegnie `artifacts/bridge-warn-s24/logs/chain2.ps1` (EditMode → build → przejazd), wynik w `logs/chain2.status` (`edit exit=`, `build exit=`, `run exit=`), logi `test-edit2.log`, `build2.log`, `run2.log`.
- W ADR 0307 został znacznik `RUN2_NOTE` (sekcja Liczby) — zastąpić wynikiem przejazdu 2 albo zdaniem „nie sprawdzono w playerze”.
- Dowody nie są jeszcze skopiowane do main.
- NASTĘPNY KROK (komendy, z katalogu worktree):
  1. `Get-Content artifacts/bridge-warn-s24/logs/chain2.status` — oczekiwane `edit exit=0`, `build exit=0`, `run exit=0`.
  2. Obejrzeć zrzut t≈130 s z najnowszego `artifacts/win/runs/<ts>/shot_t0130.png` (kafel „WYS. 3,7 m” w jednej linii), zmniejszyć: `magick <png> -resize 960x artifacts/bridge-warn-s24/run/run2_t0130.jpg`.
  3. W `docs/adr/0307-*.md` zastąpić `RUN2_NOTE`; commit + `git push origin bridge-warn-s24`.
  4. `git checkout -- art-source game/Assets/_Project/Audio game/ProjectSettings` (efekty uboczne Unity), potem `robocopy artifacts\bridge-warn-s24 C:\Users\matma\Documents\Claude\kamion\artifacts\bridge-warn-s24 /E`.
- Uwaga dla lidera: przebudowa kafla `tykocin` z gałęzi bez `limit_signs.py` (kolejka regen-wave-2) usunie znaki do czasu scalenia; `Data/Regions/tykocin/generated/*` i `tykocin_route.bytes` w tej gałęzi pochodzą z przebudowy 11:4x.
