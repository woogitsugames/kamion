# INTEGRATION 2026-11-15/16 — int-pc-s23 (PR-y PC chmury H + spawn-fix + pc-fix)

Agent: build-qa `int-pc-s23`, worktree `.claude/worktrees/win-build-0261` (Library Win64). Gałąź `int-pc-s23`.
Maszyna: Ultra 7 270K Plus, 64 GB, RTX 5070, D3D12 — **maszyna deweloperska, NIE referencja** (ADR 0260).
Dowody: `artifacts/int-pc-s23/` (main), testy `artifacts/tests/`, logi `artifacts/logs/`.

## 1. Co jest na gałęzi (kolejność merge commitów)
| # | Co | Merge | Head = sha z recenzji |
|---|---|---|---|
| 1 | #129 region-select-fix-0267 | `a83ecb3da` | tak (`541ca8b95`) |
| 2 | #134 pc-dist-0271 | `d122512e0` | tak (`6d2d3a997`) |
| 3 | #130 pc-gates-0266 | `308641263` | tak (`ae5bd7544`) |
| 4 | #135 pc-tiers-0269 | `4d8881784` | tak (`9342b94bc`) |
| 5 | #133 gamepad-0264 | `80219c391` | tak (`734fef660`) |
| 6 | #132 wheel-0263 | `d92699bd9` | tak (`82bcf40ee`) |
| 7 | origin/main `5f51007ee` (spawn-fix-0262) | `cc3e1ee90` | konflikt tylko w docstringu `export-region-catalog.py`; katalog wygenerowany skryptem |
| 8 | origin/main `c6160684a` (chain_bollard.png, docs) | `8701306fd` | — |
| 9 | pc-fix-s23 `c2ba3d5bb` (#131 + #136 z poprawkami P1) | `a73ffe6f3` | czysto |
| 10 | origin/main `6e6fe972f` (spawn-fix r2, rail_bed.png w gicie) | `d8ec3751c` | czysto; `--check` katalogu 0 |

Żaden PR nie zmienia `ProjectSettings/`, `Packages/`, asmdef. Bez konfliktów poza pozycją 7.
Commity własne (skrypty): `ced70db9d` + `5db51c343` (`import-region.ps1 -BuildTarget Android|Win64`), `e28533ca3`
(`build-windows.ps1`: `Kamion-knyszyn.cmd` → region `knyszyn`, nowy `Kamion-knyszyn-w.cmd`).

## 2. PR → testy → decyzja
| PR | Testy (ten worktree, Win64) | Decyzja |
|---|---|---|
| #129 | EditMode `RegionSelectTests` 20/20; pytest 0267 3/3; `export-region-catalog.py --check` 0; build `-Regions d67-full` = 21 regionów | **do main** |
| #134 | pytest `tests/dist` (razem z pcperf 41/41) | **do main** (job CI `dist-tests` w `ci.yml` — świadoma akceptacja lidera) |
| #130 | EditMode `PcMetricsMathTests` 10/10; pytest `tools/pcperf/tests` | **do main** |
| #135 | EditMode `PcGraphicsTierAssetTests` 6/6, `PcGraphicsTierTableTests` 8/8; build + zrzuty 4 tierów + autodetekcja (§4) | **do main**, z P2 o cieniach Low/Medium (§4) |
| #133 | EditMode `PadKeyboardInputTests` 21/21, `WindowsBuildTests` 5/5; pad fizyczny UNVERIFIED | **do main** |
| #132 | EditMode `ForceFeedbackModelTests` 12/12, `PcWheelDataTests` 7/7, `PcWheelInputTests` 30/30; `dotnet test tools/physics-runner` 277/277; kierownica fizyczna UNVERIFIED | **do main** |
| #131 + #136 (pc-fix-s23) | EditMode `MenuInputGateTests` + `PcAutoTierTests` 19/19; PlayMode `PcHudSolverTests` 3/3 | **do main** (build i zrzuty: §6) |
| spawn-fix-0262 (z main) | EditMode `StartClearanceTests` + `RegionSelectTests` 65/65 po reimporcie 21 regionów; PlayMode `RouteSpawnTests` 4/4; zrzuty startu 7 regionów (§3) | zweryfikowane w playerze |

Przebiegi pełne EditMode:
- po 6 PR-ach H (`d92699bd9`, przed main): **731 razem / 730 zaliczonych / 0 niezaliczonych / 1 pominięty** (`GardenCanopyWidthTests`, Ignore)
  — `artifacts/int-pc-s23/editmode-20261115-225152.xml`. `CarPaintMaterialTests` 11/11 (w tym worktree jest
  `art-source/world/materials`).
- po main + pc-fix (`e28533ca3`): **847 / 845 / 1 niezaliczony / 1 pominięty** — `artifacts/tests/editmode-20261116-034915.xml`.
  Niezaliczony: `StreetLampOpticsTests.SodiumTint_HasTheLedLuminance` (oczekiwane 0,93694, jest 0,94206). **Nie pochodzi
  z PR-ów H ani pc-fix** (nie dotykają lamp ani `lighting_profiles.json`); przed scaleniem main test przechodził, a main
  wniósł `346654291` (lighting-0216b: `lighting_profiles.json`, `RegionLightingProfiles.cs`). Do naprawy u autora
  lighting-0216b; nie naprawiane tutaj. Klasa uruchomiona osobno przechodzi 10/10 (`editmode-20261116-035729.xml`) — błąd zależy od kolejności testów
  (stan statyczny). **Otwarte, nie z PR-ów H ani pc-fix — zmierzone:** pełny EditMode na `8701306fd` (6 PR-ów H + main,
  bez pc-fix) = 777 / 775 / 1 niezaliczony (ten sam test) — `artifacts/tests/editmode-20261116-041822.xml`; na `d92699bd9`
  (6 PR-ów H bez main) było 0 niezaliczonych. Fail wniosło więc scalenie main (`5f51007ee`..`c6160684a`).
- PlayMode: PR-y H nie dodają testów PlayMode; pc-fix dodaje `PcHudSolverTests` (3/3).

`dotnet` z PATH nie ma SDK — potrzebne `DOTNET_ROOT=%LOCALAPPDATA%\Microsoft\dotnet` (jak w `docs/PHYSICS_VALIDATION.md`).

## 3. Błąd główny: start przed zaporą (spawn-fix-0262) — zweryfikowany w playerze
- Reimport 21 regionów w tym worktree z `-BuildTarget Win64` (log: `Targeting platform: Win64`, Library nie przełączone).
- Build `d67-full` `cc3e1ee900`, potem `8701306fd1` (Tykocin z nową sceną).
- Zrzuty startu `-scene <id>` bez `-route_s`, obejrzane: **knyszyn, knyszyn-s, dk65-11, dk65-05, bialystok-dojlidy,
  bialystok-industrial-c, dw671-tykocin-01 — jezdnia przed kabiną wolna we wszystkich**; zapory widać w lusterkach
  (knyszyn, dk65-11, tykocin). `artifacts/int-pc-s23/starts/`, `starts2/`.
- Bezpiecznik runtime działa na starej scenie (Tykocin przed reimportem): `[START] start moved along the route:
  route_s 12.0 -> 85.0`.
- Dla porównania exe sprzed poprawki (`4ee3e02626`, knyszyn-s): zapora w poprzek jezdni przed kabiną
  (`artifacts/int-pc-s23/tiers-shadow/preH-Medium.jpg`).
- Naczepa: z kabiny widoczna tylko we wstawkach lusterek; położenie zestawu pokrywa test `StartClearanceTests`
  (kategoria WorldScenes, 21 regionów).
- `-route_s` działa: `-scene knyszyn-w -route_s 300` → `[START] … route_s=300.0`. W ADR 0261 argument nie dotarł do exe
  (sposób przekazania), kod był poprawny.

## 4. #135 — tiery PC w playerze (exe `8701306fd1`, knyszyn, autopilot 46 km/h na zrzucie, 1920×1080, `-fps 1000`)
| Tier | Asset (log `[PC_TIER]`) | Scena | średni FPS | p95 [ms] (ostatnie okno) |
|---|---|---|---|---|
| Low | `URP_PC_Low` msaa 2, mipLimit 1 | `World_knyszyn` | 535 | 2,3 |
| Medium | `URP_PC_Medium` msaa 4 | `World_knyszyn` | 379 | 3,3 |
| High | `URP_PC_High` msaa 4, ssao | `World_knyszyn_High` | 334 | 3,7 |
| Ultra | `URP_PC_Ultra` msaa 8, cienie 8192 | `World_knyszyn_High` | 194 | 6,4 |
| bez `-tier` | High (`desktop default tier High: VRAM 11943 MB`) | `World_knyszyn_High` | 322 | 3,7 |

**To pomiar na maszynie dev (RTX 5070), NIE referencja**; jeden przebieg 55 s na tier, bez powtórzeń; okno gry w tle
innych zadań (Unity w innych worktree). Źródło: `artifacts/int-pc-s23/tiers/<tier>.summary.json`, `.log`, `.frametimes.csv`.
Obraz: brak magenty i czerni; Low ma treść Low i rozmyte tekstury (mip limit), High/Ultra cienie i gładsze krawędzie;
różnica Medium ↔ High ↔ Ultra w tym kadrze jest mała (`tiers/crop-*.jpg`).

**P2 (nowe): Low i Medium nie rysują cieni drzew na jezdni**, choć `[PC_TIER]` deklaruje 60 m/2 kaskady i 100 m/3 kaskady.
A/B w `knyszyn-s`: Low i Medium bez cieni; High na scenie Low (`-scene World_knyszyn-s -tier High`) cienie ma, więc to
nie treść sceny. Exe sprzed PR-ów H zachowuje się tak samo, więc **to nie regresja #135**, ale tabela tierów deklaruje
coś, czego obraz nie pokazuje. Przyczyna niezbadana (UNVERIFIED: ustawienie tieru dla roślinności albo wycięte
warianty shaderów assetów ładowanych z Resources). Dowody: `artifacts/int-pc-s23/tiers-shadow/`.

## 5. Wejście w playerze
- **Klawiatura: ZWERYFIKOWANA w playerze** (exe `e28533ca31`, `scripts/win-key-drive.ps1 -Scene knyszyn -Keys W -TapFirst Space
  -HoldSeconds 12`, okno z fokusem): `[CONTROLS] cmd t=16.48 parking=toggle`, `thr=1.00`, po 12 s `v=35.3` km/h; zrzut
  z 34 km/h na biegu D7. Dowód: `artifacts/int-pc-s23/keys/` (`player.log`, `shot.jpg`). Sprawdzone tylko W i spacja;
  pozostałe klawisze — testy EditMode.
- **Pad i kierownica fizycznie: UNVERIFIED** (brak urządzeń). Ścieżka kodu: log `[CONTROLS] pc-input installed schema=1
  overrides=no` (PcInputBridge, #133) w każdym przebiegu jazdy + testy EditMode z §2.

## 6. Build końcowy (z pc-fix: #131 + #136)
- **Exe: `C:\Users\matma\Documents\Claude\kamion\artifacts\win\kamion-0.1.0-e28533ca31-regions\Kamion.exe`**
  (kod `e28533ca3`; `BUILD_RESULT: Succeeded errors=0 warnings=7`, 507 s, folder 4 941 MB, 189 plików, 42 sceny regionów w logu buildu = 21 regionów × Low/High,
  `d67-full`, treść High). Log `artifacts/logs/build-win-20261116-035803.log`. Etykieta w playerze `e28533ca31-dirty`.
- **Start w Knyszynie dla właściciela: `…\kamion-0.1.0-e28533ca31-regions\Kamion-knyszyn.cmd`** (okno 1600×900,
  `-scene knyszyn`). Obok: `Kamion-okno.cmd` (menu w oknie), `Kamion-knyszyn-w.cmd` (region knyszyn-w).
  Jazda: spacja zwalnia hamulec postojowy, W/S gaz/hamulec, A/D kierownica (reszta: ADR 0261/0264).
- Zrzuty obejrzane (`artifacts/int-pc-s23/final2/`):
  - `knyszyn.jpg` — start: jezdnia wolna, zapora w lusterkach; **HUD PC (#131): tylko lusterka, pasek prędkości/biegu
    i przycisk „Panel”; dotykowa kierownica, pedały i selektor zniknęły, nic nie zasłania widoku z kabiny.**
  - `knyszyn-drive.jpg` — autopilot 46 km/h, D9, obraz poprawny.
  - `menu.jpg` — menu startowe z nowymi przyciskami („Ustawienia sterowania”, „Informacje”, „Ekran, grafika, dźwięk”),
    lista regionów 1/21. **Usterka wizualna (P2): nakładka diagnostyczna (KAMION / Device / GPU / FPS…) nachodzi na tytuł
    i pierwszy przycisk menu** — tekst na tekście.
- Logi: `[SETTINGS] pc load source=Defaults … pc apply startup … tier=auto` oraz `[BOOT] desktop default tier High: VRAM
  11943 MB` — na tej maszynie błąd P1 #136 i poprawna autodetekcja dają ten sam High, więc log tego nie rozróżnia (w playerze UNVERIFIED; pokrywa to `PcAutoTierTests`); `-tier Low` → `URP_PC_Low`. Brak wyjątków.
- Menu klikane myszą/padem w playerze: nie sprawdzane ręcznie (UNVERIFIED); bramka wejścia — test `MenuInputGateTests`.
- **Ten exe nie zawiera spawn-fix r2** (main `6e6fe972f`, scalony do gałęzi po buildzie jako `d8ec3751c`; zmienia
  `SpawnSafety`, `DrivingLabBootstrap`, `RouteSpawnTests`). Testy po tym merge: §6a.

## 6a. Po merge spawn-fix r2 (`d8ec3751c`)
- EditMode dotknięte klasy (`StartClearanceTests`, `RegionSelectTests`, `MenuInputGateTests`, `PcAutoTierTests`,
  `PadKeyboardInputTests`, `PcWheelInputTests`): **135/135** — `artifacts/tests/editmode-20261116-041031.xml`.
- PlayMode `RouteSpawnTests` + `PcHudSolverTests`: **8/8** — `artifacts/tests/playmode-20261116-041142.xml`.
- Pełny EditMode: **847 / 845 / 1 niezaliczony / 1 pominięty** — ten sam `StreetLampOpticsTests.SodiumTint_HasTheLedLuminance`
  (kolejnościowy, z main) — `artifacts/tests/editmode-20261116-041223.xml`.
- Buildu Windows z `d8ec3751c` nie było (UNVERIFIED w playerze dla r2); komenda:
  `pwsh scripts/build-windows.ps1 -Slot -Regions d67-full` (ok. 9 min w tym worktree).

## 6b. Werdykt
**Gałąź `int-pc-s23` gotowa do scalenia do main: TAK, z jednym zastrzeżeniem** — pełny EditMode ma 1 niezaliczony test
(`StreetLampOpticsTests.SodiumTint_HasTheLedLuminance`), który nie pochodzi z integrowanych PR-ów (kolejnościowy, pojawił się
po scaleniu main z lighting-0216b; na samym main nie był tu uruchamiany — UNVERIFIED). Zawiera: #129, #130, #132, #133,
#134, #135, #131 + #136 (pc-fix-s23), main do `6e6fe972f`, poprawki skryptów (`import-region.ps1 -BuildTarget`,
`build-windows.ps1` launchery). Bez zmian `ProjectSettings/`, `Packages/`, asmdef.
Scalenie: `git merge --no-ff origin/int-pc-s23`. Po scaleniu PR-y #129–#136 można zamknąć jako scalone przez tę gałąź.
## 7. P2 z recenzji, które warto zrobić (kolejność wg wpływu)
1. **#135** cienie Low/Medium na PC (wyżej) + P2-2 `globalTextureMipmapLimit = 1` na Low rozmywa też znaki i tablice.
2. **#133 P2-1** `PcInputBridge` instaluje się także na Androidzie — sprawdzić na telefonie przed następnym APK.
3. **#132 P2-3** nazwy producentów w `Resources/Controls/wheel_profiles.json` (`note`) jadą w buildzie — przenieść do `docs/compat`.
4. **#132 P2-1/P2-2** FFB nie dociera do urządzenia (`NullForceFeedbackSink`), brak panelu kierownicy.
5. **#130 P2-1/P2-3** bramka VRAM dla iGPU, `tris.p95 ≤ 2 M` dla Low bez źródła; **P2-4** haki `MarkRegionLoadStart/MarkDrivingReady`.
6. **#134 P2-1** `-regions` znika z nazwy paczki zip; **P2-2** zrzuty awarii nieanonimizowane.
7. **#129 P2-1** `build-windows.ps1` bez normalizacji listy regionów (spacje/NBSP) jak w `build-android.ps1`.
8. **#133 P2-2** test zera GC dla `Sample` z wirtualnym padem (wymaga `Unity.InputSystem` w asmdef testów — lider).

## 8. Uwagi z tej integracji (nowe)
- **`[START] … route_s=12.0` przy `-scene`**: log podaje wartość domyślną i punkt 12 m, a scena ma zapieczony spawn 90 m
  (ciężarówka stoi poprawnie). Mylące przy diagnozie — `LogRegionStart` powinien logować faktyczny punkt.
- **`Kamion.exe.sha256` jest identyczny dla wszystkich buildów** (`fbd073ca…17492b`): `Kamion.exe` to ten sam launcher,
  treść jest w `Kamion_Data` / `GameAssembly`/`Managed`. Suma nie identyfikuje buildu — potrzebna suma zawartości
  (np. manifest sum plików folderu) w `build.json`.
- **Pliki generowane poza gitem blokują import na świeżym checkoucie**: `art-source/world/textures/chain_bollard.png`
  i `rail_bed.png` (dw671-tykocin-01) — oba dodane do main w trakcie tej integracji. Warto dodać do `doctor.ps1`/importu
  kontrolę, że każda tekstura z `world_manifest.json` istnieje.
- **`import-region.ps1` uruchamia `build_all.py` po każdej kopii worktree**: robocopy zachowuje daty PNG, a `_src/*.py`
  dostają datę checkoutu → „171 older than _src”. Przy obciążonej maszynie proces (BelowNormal) stał 6 min z 14 s CPU,
  trzymając slot Unity. Obejście: przywrócić daty `_src` z main. Trwale: porównywać sumy, nie daty.
- **Etykieta `-dirty` w `build_info`** przy każdym buildzie Windows (Unity dopisuje wpis batchingu Standalone do
  `ProjectSettings.asset`) — decyzja lidera z ADR 0261 nadal otwarta.
- knyszyn-s raz zakończył się kodem −1 mimo poprawnego zrzutu i `[AUTOSHOT] quit` (jednorazowo, niepowtórzone).
- `-Regions d67-full` rozwija się poprawnie do 21 regionów (build 498–541 s, folder 4 941 MB, 188 plików).
