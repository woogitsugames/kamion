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
## 15.11 22:48 krok 6 — przejęcie po martwym agencie, ponowienie renderów
- Statusy `import=-1073741502` (0xC0000142, proces nie wystartował po zamknięciu sesji) przeniesione do `renders/<id>.status.dead-2242`; martwy slot zwolniony przez `unity-slot.ps1 -Release`.
- ODŁĄCZONY proces (Start-Process pwsh Hidden, pid 9568) renderuje 14 regionów: dk65-01,-02,-03,-04,-07,-08,-09,-10,-11, dk65-monki-01, dw671-tykocin-01, knyszyn-s, knyszyn, bialystok-dojlidy. Log: `artifacts/spawn-fix-0262/renders-rerun.log`.
- OK z poprzedniej tury (import=0 qa=0): dk65-05, dk65-06, knyszynska, maczka, kleeberga, knyszyn-w. NIE ufać `renders.done` — czytać `renders/<id>.status`.
NASTĘPNY KROK: `Get-ChildItem artifacts/spawn-fix-0262/renders/*.status | % { $_.BaseName + ' ' + (Get-Content $_ -Raw) }`; gdy 20/20 `import=0 qa=0` -> obejrzeć PNG, ADR „Wyniki”; brakujące: `Start-Process pwsh -WindowStyle Hidden -ArgumentList '-NoProfile','-Command',"& 'artifacts/spawn-fix-0262/run-renders.ps1' -Regions <id,...>"`
## 16.11 ~04:1x krok 7 — rendery 20/20, oględziny, ADR „Wyniki”, merge main
- 20/20 `import=0 qa=0` (sprawdzone per region); wszystkie 20 par PNG + 7 zrzutów exe obejrzane: bez regionu z problemem; uwagi: dk65-06 (start na wlocie ronda), kleeberga/knyszynska (nie skrajny prawy pas), maczka (własne zamknięcie zasłonięte).
- `git merge origin/main` (1311c25de) bez konfliktów; ADR 0262 „Wyniki” (tabela 21 regionów) — commit + push.
- ZNALEZISKO: log `[START] region=… route_s=12.0` przy starcie z zapieczonego spawnu wypisuje domyślne 12 m, nie pozycję (LogRegionStart) — poprawka 1 linii.
- W TOKU (odłączone, pid 68352): `run-post-merge.ps1` = EditMode StartClearance+RegionSelect, PlayMode RouteSpawnTests po scaleniu, z NIEZACOMMITOWANYMI zmianami: P2-1 (SpawnSafety: start nie za rzędem wyjazdowym) + test + poprawka logu.
NASTĘPNY KROK: `Get-Content artifacts/spawn-fix-0262/editmode-post-merge.done, artifacts/spawn-fix-0262/editmode-playmode-post-merge.done`; zielone -> `git add game/Assets/_Project/Gameplay/SpawnSafety.cs game/Assets/_Project/Gameplay/DrivingLabBootstrap.cs game/Assets/_Project/Tests/PlayMode/RouteSpawnTests.cs; git commit`; czerwone -> `git checkout -- game/Assets/_Project` i wpisać P2-1 + log jako otwarte.
## 16.11 ~04:2x krok 8 — KONIEC
- Po scaleniu main: EditMode StartClearance+RegionSelect 61/61 (skipped 0), PlayMode RouteSpawnTests 5/5, pytest 44 passed.
- Commit `8778bbe5a` (push): P2-1 wąsko w `SpawnSafety.ResolveStartS` + test, log `[START]` ze stacją zapieczonego spawnu, ADR 0262 „Wyniki” (21 regionów) i „Otwarte”.
- Efekty uboczne Unity: brak zmian w ProjectSettings/Packages/M_Sky/Resources (git status czysty).
NASTĘPNY KROK (lider): `git merge spawn-fix-0262` (4 pliki poza artifacts: ADR, SpawnSafety.cs, DrivingLabBootstrap.cs, RouteSpawnTests.cs); nowy build exe, żeby poprawki weszły.
