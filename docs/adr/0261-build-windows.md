# ADR 0261 — build Windows x64 (pierwszy player PC, korytarz regionów)
Status: Proposed (agent `win-build-0261`, s22), 2026-11-15. Do weryfikacji i scalenia przez lidera.
Powiązane: ADR 0260 (D73: Windows platformą główną), ADR 0229 (`-regions`), ADR 0012 (tiery treści, `-worldHigh`),
ADR 0058 (kolumna kierownicy), ADR 0150 (trasy regionów).

## Kontekst
D73 przestawia platformę główną na Windows Standalone x64 (ten sam projekt Unity 6000.3.28f1 URP). Do tej pory istniało
tylko wejście `BuildCommands.BuildAndroidApk` i `scripts/build-android.ps1`. Właściciel ma móc uruchomić player i jechać
po Knyszynie. `ProjectSettings/`, `Packages/`, asmdef — poza zakresem agenta.

## Decyzja
1. **Wejście batchmode `Game.Editor.Build.BuildCommands.BuildWindowsPlayer`** (`BuildWindows(output, development)`),
   `-buildTarget Win64`. Lista scen z tej samej funkcji co APK (`ComposeBuildScenes`: `EditorBuildSettings` + scena
   High + `-regions` / `-regionsFile` / `-regionsAllowMissing` + `-noWorld`), ten sam import audio
   (`VehicleAudioImporter.ImportIfNeeded`), raport zawartości (`Kamion.content.json`, `.top.txt`, `.variants.txt`),
   `-development`, `-noShaderStrip`. Ścieżka Androida bez zmian zachowania (wydzielona tylko kompozycja scen).
2. **Treść PC = High.** Windows zawsze dokłada sceny `_High` regionów i zostawia zestawy materiałów High pojazdów
   (`HideHighTiers` nie jest wołane); `-worldLow` daje wariant jak domyślny APK. Sceny Low zostają w buildzie, bo menu
   startowe rozpoznaje region po scenie Low, a tiery Low/Medium ładują scenę Low.
3. **Nic nie jest zapisywane w ProjectSettings.** `versionCode` Androida (ustawiany przez `BuildInfoWriter`) jest
   przywracany jak w buildzie APK. Tryb okna: argumenty playera `-screen-fullscreen 0 -screen-width W -screen-height H`
   (skrypt tworzy obok exe `Kamion-okno.cmd` i `Kamion-knyszyn.cmd`); domyślny `fullscreenMode: 1` w ProjectSettings
   zostaje — ewentualna zmiana należy do lidera.
4. **`scripts/build-windows.ps1`**: dot-source `env.ps1`, `-Slot` (slot `unity`, czeka na `PHONE_RUN`), log
   `artifacts/logs/build-win-<ts>.log`, wyjście `artifacts/win/kamion-<ver>-<sha>[-low][-regions][-dev]/Kamion.exe`
   + `Kamion.exe.sha256` + `build.json` (liczba plików, rozmiar folderu). `-Run` uruchamia player w oknie z
   `-logFile`, `-shot`, `-quit_t`, kopiuje log, `summary.json`, `frametimes.csv` do `artifacts/win/runs/<ts>/`;
   exit 4 przy wyjątkach w logu, braku zrzutu albo niezerowym kodzie wyjścia. `scripts/test.ps1` dostał
   `-BuildTarget Android|Win64` (checkout przełączony na Win64 testuje się bez powrotnego reimportu).
5. **Domyślne ustawienia playera desktop** (`GameBootstrap`): bez argumentu `-tier` i bez zapisanego wyboru tier =
   **High** (reguły `QualityProfile.deviceRules` to lista GPU telefonów; fallback Medium), limit klatek **60**
   (`DesktopTargetFps`, WORKING_VALUE do czasu wskazania referencyjnego PC). `-tier`, `-fps` i wybór w menu wygrywają
   jak dotąd. Edytor i telefony bez zmian.
6. **Sterowanie.** Klawiatura (Input System, `KeyboardDriverInput`) działała już w playerze: W/S lub ↑/↓ gaz / hamulec
   (narastanie), A/D lub ←/→ kierownica (narastanie, powrót), spacja hamulec postojowy, 1/2/3 = D/N/R, E/Q biegi,
   M automat/ręczny, X/Z retarder, G nogi, B tempomat zjazdu, V kamera cofania, `,` `.` kierunkowskazy, H awaryjne,
   K klakson, Esc menu. Zmiany: **C = następna kamera** (kabina → pościg → orbita), a sprzęganie / rozprzęganie naczepy
   przeniesione z C na **T**. Nowe źródło **`GamepadDriverInput`** (za `IDriverInput`, w mikserze po klawiaturze):
   lewa gałka = kierownica (martwa strefa 0,12, krzywa 1,8 — WORKING_VALUE; prędkość rąk nadal ogranicza kolumna),
   RT gaz, LT hamulec, A hamulec postojowy, RB/LB biegi, X = D, B = N, Back = R, d-pad ←/→ kierunkowskazy, ↑ awaryjne,
   ↓ / klik lewej gałki retarder +/−; Y kamera, Start menu, prawa gałka rozglądanie, klik prawej gałki klakson.
   Fizyka bez zmian (moment na koła, żadnego `transform.position`). Menu i HUD obsługuje mysz (`InputSystemUIInputModule`).
7. **Przebieg dowodowy bez człowieka:** `DesktopAutoShot` — argumenty `-shot <png> [-shot_t s] [-quit_t s]` (zrzut
   bufora ekranu z HUD-em i wyjście po czasie); razem z istniejącymi `-scene <region>`, `-autopilot route`, `-speed`.

## Budżet
Draws/tris: bez zmian treści (te same sceny High co `-worldHigh` w APK). Rozmiar i czas buildu — sekcja Walidacja.
Budżety PC (docs/03) nie są jeszcze zdefiniowane (ADR 0260): pomiary poniżej to maszyna deweloperska, NIE referencja.

## Walidacja
Maszyna deweloperska (Ultra 7 270K Plus, 64 GB, RTX 5070, D3D12) — **NIE referencja** (ADR 0260).
- **Build** `pwsh scripts/build-windows.ps1 -Slot -Regions 'd67,knyszyn-w,dk65-monki-01,dw671-tykocin-01,bialystok-dojlidy'`
  (kod z 4ee3e0262): `BUILD_RESULT: Succeeded errors=0 warnings=7`, 628 s BuildPlayer / 813 s razem z reimportem Library
  pod Win64; `artifacts/win/kamion-0.1.0-4ee3e02626-regions/Kamion.exe`, sha256 `fbd073ca…17492b`, folder 4 923 MB
  (188 plików). Zawartość świata przed kompresją 8 372 MB (siatki High 3 231 MB, tekstury PBR 2 085 MB, siatki Low
  1 059 MB); 5 052 warianty shaderów. Log `artifacts/logs/build-win-20261115-211152.log`.
- **Start w Knyszynie** (`-scene knyszyn-w -autopilot route -speed 50 -fps 1000`, okno 1600×900): log
  `[BOOT] … api='Direct3D 12' tier=High`, `[START] region=knyszyn-w route_s=12.0 road='Obozowa'`, scena
  `World_knyszyn-w_High`, wyjście 0, brak wyjątków. Bez `-tier` log `[BOOT] desktop default tier High`, menu `fps=60`,
  a [DIAG] pokazuje równe 60,0 fps (p99 16,7 ms).
- **FPS bez limitu, tier High, 1600×900:** 360–445 fps w oknach 5 s (średnia sesji 423–430, p95 3,1–3,9 ms, p99
  3,4–6,0 ms; `artifacts/win/runs/20261115-212548` i `…-213342`). **Uwaga: to pomiar w większości na postoju** —
  autopilot po ok. 40 m staje na zaporze (niżej), więc nie jest to FPS z jazdy przez region.
- **Zrzuty obejrzane** (`artifacts/win/runs/*/shot.png`): widok z kabiny, zegary, lusterka-wstawki, zabudowa Knyszyna,
  niebo; dotykowy HUD (kierownica, pedały, selektor) jest widoczny na PC. **Zapora na starcie:** start bez autopilota
  (`…-213125-keys/shot.png`) pokazuje betonową zaporę w poprzek jezdni ok. 60–80 m przed ciężarówką; w przebiegach z
  autopilotem ciężarówka dojeżdża do niej i stoi (0 km/h, bieg D3, szary blok przy lewym narożniku kabiny — odległości
  i identyfikacja bloku to ocena ze zrzutu, nie pomiar). Próba startu dalej (`-route_s 300`) nie zadziałała: log
  nadal `[START] … route_s=12.0` (przyczyna niezbadana), więc nie ma pomiaru z jazdy. To ten sam problem, który właściciel zgłosił na A16 (naprawia `spawn-fix-0262`); tu tylko opisany.
- **Klawiatura w playerze: UNVERIFIED.** Kod klawiatury jest wspólny z edytorem i Input System jest aktywny, ale próba
  wstrzyknięcia klawisza (`scripts/win-key-drive.ps1`, SendInput) nie powiodła się: Windows nie oddał fokusu oknu
  uruchomionemu z procesu w tle. Pad: UNVERIFIED (brak pada przy maszynie w tej sesji). Do sprawdzenia przez właściciela.
- **Efekty uboczne Unity po buildzie** (cofnięte `git checkout`): `M_Sky.mat`, `URP_Ultra.asset`,
  `UniversalRenderPipelineGlobalSettings.asset` oraz `ProjectSettings.asset` — Unity dopisał wpis batchingu dla
  `m_BuildTarget: Standalone` (static 1 / dynamic 0). Jeśli lider chce mieć to jawnie w gicie — jego decyzja.
- `build_info` w playerze ma etykietę `ab4e89799e-dirty` (HEAD w chwili preprocessu + efekty uboczne Unity), a nazwa
  folderu `4ee3e02626` (HEAD przy starcie skryptu); kod identyczny (ab4e89799 dodaje tylko ten ADR).
- **Testy EditMode** (`scripts/test.ps1 -Platform EditMode -BuildTarget Win64`, worktree): przebieg pełny 633 razem,
  630 zaliczonych, 1 pominięty, 2 niezaliczone (`CarPaintMaterialTests.DepositionChannel_…`). Przyczyna środowiskowa,
  potwierdzona: `WorldPbrMaterials.Has` wymaga plików PNG zestawu `car_grime_clean` z `art-source/world/materials`
  (poza gitem; main 534 pliki, świeży worktree 27 — `new-agent-worktree.ps1` ich nie kopiuje). Po skopiowaniu katalogu
  z main: `-Filter CarPaintMaterialTests` 11/11. Nie było jednego pełnego zielonego przebiegu po kopii (630 + te 2).
  `WindowsBuildTests` 5/5, `RegionSelectTests` 16/16. Wyniki: `artifacts/win-build-0261/tests/editmode-20261115-213516.xml`
  i `…-214026.xml`.
- Ścieżka Androida po wydzieleniu `ComposeBuildScenes` jest skompilowana i objęta testami `RegionSelectTests`; build
  APK po tej zmianie nie był wykonywany (UNVERIFIED).

**Zmiana (ADR 0276):** skróty `Kamion-<region>.cmd` powstają dla każdego regionu w buildzie (z logu buildu, po rozwinięciu
zestawów), obok `Kamion-okno.cmd`; build dostaje `build-id.json` ze skrótem zawartości `Kamion_Data` (suma `Kamion.exe` jest
w każdym buildzie taka sama — to launcher Unity).

## Otwarte
- **Jazda po Knyszynie tym exe nie jest możliwa dalej niż do zapory** — po `spawn-fix-0262` potrzebny reimport regionów
  i ponowny build (regiony w worktree to kopia `_Generated` z main z 15.11 ~20:50).
- Player ma etykietę `-dirty` przy każdym buildzie Windows, dopóki wpis batchingu Standalone nie trafi do
  `ProjectSettings.asset` (decyzja lidera).
- Kierownica z FFB (D56/D73) — nie w tym ADR.
- Dotykowy HUD (kierownica, pedały ekranowe) jest widoczny także na PC; ukrycie / układ PC — zadanie gameplay-ui.
- Mapowanie klawiszy i pada nie jest konfigurowalne w panelu ustawień (stałe w kodzie); brak podpowiedzi klawiszy w HUD.
- `fullscreenMode`, domyślna rozdzielczość okna, ikona, nazwa produktu w ProjectSettings — decyzja lidera.
- Referencyjny PC i docelowy FPS (ADR 0260); limit 60 fps i tier High to WORKING_VALUE.
- Scripting backend Standalone = Mono (domyślny w ProjectSettings); IL2CPP do rozważenia przy wydaniu.
