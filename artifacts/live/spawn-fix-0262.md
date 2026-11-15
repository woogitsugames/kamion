# spawn-fix-0262 (ADR 0262) — live
## 15.11 diagnoza (przyczyna wspólna, potwierdzona na danych 21 regionów)
- W 20/21 regionów trasa startowa zaczyna się NA krawędzi kafla (węzeł `boundary`), a zamknięcie krawędzi (WorldEdgeBuilder, ADR 0169:
  zapory betonowe + deski U-20, 60 m w głąb kafla) stoi na trasie w s≈60 m (dk65-05: 14 m, knyszynska: 20 m, dk65-06 i knyszyn-w: 54 m).
  Start s=12 m (ADR 0229 `startS`, `WorldSceneBuilder.spawnS`) wypada więc PO ZEWNĘTRZNEJ stronie zapory: z tyłu koniec drogi, z przodu bloki.
  dk65-05: zapora w s=14 m -> ciągnik w rzędzie zapór (zrzut 3.webp). Region C nie ma zamknięcia na trasie (start w bazie), więc nikt tego nie widział.
- To NIE odwrócony kierunek (drugie zamknięcie jest przy len-60) i NIE plac budowy D65 (construction_site = piasek/hałdy w terenie + siatka poza pasem 4 m od dróg).
- Plan: (1) test EditMode na prawdziwych zamknięciach + pytest katalogu (czerwone na main); (2) startS w katalogu = za zamknięciem wjazdowym;
  importer spawn z tej samej funkcji; (3) runtime: start za zamknięciem z WorldBoundary sceny + OverlapBox (naprawia APK bez reimportu scen).
NASTĘPNY KROK: implementacja `SpawnClearance` (Gameplay) + testy; `pwsh scripts/test.ps1 -Platform EditMode` pod slotem unity.
## 15.11 krok 2 — kod + testy (commit f95c31b44, push)
- `World/Runtime/StartClearance.cs` (geometria: przecięcia trasy z rzędami zapór, SafeStartS, FreeAround), `Gameplay/SpawnSafety.cs`
  (OverlapBoxNonAlloc + przesunięcie wzdłuż trasy), `DrivingLabBootstrap.ResolveRouteStart` (menu, route_s i zapieczony spawn),
  importer: spawn z katalogu + SafeStartS; `export-region-catalog.py`: trasa od krawędzi kafla -> startS 85 m (60 + 25).
- pytest `tests/gis/test_start_clear_0262.py` na katalogu z main: 21 failed / 23 passed (`artifacts/spawn-fix-0262/pytest-red-main-catalog.log`).
- W TLE: EditMode `StartClearanceTests` na starym katalogu (dowód czerwony + kompilacja) -> `artifacts/spawn-fix-0262/editmode-red.done|.log|.xml`.
NASTĘPNY KROK: po `editmode-red.done`: `python scripts/export-region-catalog.py` ; `pwsh artifacts/spawn-fix-0262/run-editmode.ps1 -Tag green`
## 15.11 krok 3 — czerwony dowód + katalog 90 m
- EditMode na starym katalogu: 45 testów, 41 failed (20 regionów × 2 + C: szlaban bazy na 244 m = wyjątek DepotBarrier) -> `artifacts/spawn-fix-0262/editmode-red.log|.xml`.
- Zmierzone stacje zamknięć wjazdowych (prawdziwe ResolveClosures): 60,0 m ×15, 61,2 (maczka), 54,6 (dk65-06), 53,9 (knyszyn-w), 20,8 (knyszynska), 14,5 (dk65-05).
- Katalog: startS 90 m (60 + 25 + 5 na skośny rząd) w 20 regionach, C 12 m; pytest 44 passed (`pytest-green.log`).
- W TLE: `run-green.ps1` (EditMode StartClearance+RegionSelect, PlayMode RouteSpawnTests) -> `artifacts/spawn-fix-0262/green-all.done`.
NASTĘPNY KROK: po `green-all.done` reimport + render startu regionów nieprzebudowywanych: `pwsh artifacts/spawn-fix-0262/run-renders.ps1`
## 15.11 krok 4 — zielono
- EditMode `StartClearanceTests`+`RegionSelectTests`: 61/61 (w tym 21 scen: pudło startu wolne, 300 m trasy bez colliderów); PlayMode `RouteSpawnTests` 4/4.
  Logi: `artifacts/spawn-fix-0262/editmode-green.*`, `editmode-playmode-green.*`.
- W TLE: `run-renders.ps1` (reimport Low + kamery truck-at-gate/cab-gate, 20 regionów) -> `artifacts/spawn-fix-0262/renders/<id>.status`, `renders.done`.
NASTĘPNY KROK: obejrzeć `artifacts/spawn-fix-0262/renders/<id>/*.png`; wznowienie: `pwsh artifacts/spawn-fix-0262/run-renders.ps1 -Regions <brakujące>`
## 15.11 krok 5 — rendery startu (w toku)
- Obejrzane po reimporcie (Low, clear): dk65-05, bialystok-knyszynska, bialystok-maczka — zestaw na jezdni, zapory z tyłu (dk65-05 ~75 m), droga przed kabiną wolna.
- UWAGA: pierwszy import w worktree uruchomił generator PBR `build_all.py` (521 s, poza slotem heavy) — brak tekstur PBR w kopii worktree.
- W TLE nadal: `run-renders.ps1` -> `artifacts/spawn-fix-0262/renders/<id>.status`, `renders.done`.
NASTĘPNY KROK: `ls artifacts/spawn-fix-0262/renders/*.status`; brakujące: `pwsh artifacts/spawn-fix-0262/run-renders.ps1 -Regions <id,...>`; potem obejrzeć PNG, uzupełnić ADR „Wyniki”, cofnąć efekty uboczne Unity, commit końcowy.
