# REVIEW s22 (kod) — chmura H: SUMMARY (#129–#136)
Recenzent: D13 (chmura, bez Unity/GPU/Windows/kierownicy). Data: 2026-11-15. Main w chwili recenzji `13477802a`.
Recenzje są przypięte do sha, bo w trakcie pracy H6 scalał main w gałęzie PR. Raporty: `REVIEW-2026-11-15-s22-code-<nr>.md`.

## Werdykty
| PR | gałąź @ sha | Werdykt | P1 | P2 | Uwagi |
|---|---|---|---|---|---|
| #129 | `region-select-fix-0267` @ `541ca8b95` | **SCAL** | 0 | 3 | `d67-full` (21), pusta lista = błąd, spacje/NBSP, `ParseOrNull`. pytest 3/3, `--check` 0 |
| #130 | `pc-gates-0266` @ `ae5bd7544` | **SCAL** | 0 (było 1) | 5 | D74 wpięte przez H6 (min = Low, 8 GB, VRAM ≤ 1,75 GB). Recorder bez GC. pytest 27/27. P2: iGPU (HD 630) bez VRAM dedykowanego |
| #131 | `pc-ui-0265` @ `5410e71a4` | **FIX** | 1 | 5 | Pad/strzałki obsługują menu i jednocześnie jadą ciężarówką |
| #132 | `wheel-0263` @ `82bcf40ee` | **SCAL po #133** | 0 (było 1) | 5 | FFB z `AligningTorqueTotal` + Fz kół skrętnych ✓. Stos na #133. physics-runner 277/277. Sink = Null |
| #133 | `gamepad-0264` @ `734fef660` | **SCAL** | 0 (było 3) | 5 | H6: jedno źródło pada, układ 0261, GUID `.meta` z main, `WindowsBuildTests` przepisane |
| #134 | `pc-dist-0271` @ `6d2d3a997` | **SCAL** | 0 | 4 | zip powtarzalny, bramka `--release` R-P0-2. pytest 14/14. P2: `-regions` znika z nazwy zipu |
| #135 | `pc-tiers-0269` @ `9342b94bc` | **SCAL po weryfikacji** | 0 | 6 | URP_PC_* w Resources + hak w `QualityTiers.Apply`, bez ProjectSettings. Autodetekcja D74. Wymaga visual-qa/zrzutów tierów PC |
| #136 | `pc-settings-0270` @ `0047b38ef` | **FIX** | 1 | 5 | „auto” zapisuje High i omija autodetekcję #135 |

#135 (H7) i #136 (H8) pojawiły się w trakcie pracy i są ujęte. H6 to rebase/merge main w gałęziach (`59c777865`, `29a0145b6`, `ae5bd7544`).

## Kluczowe P1 (do wklejenia autorom)
**#131 P1-1 — wejście jazdy przy otwartym panelu.** `ControlSettingsPanel.cs:396` (`UiFocus.Decorate`: A/Enter = klik,
B/Esc = zamknij) i `UiFocus.cs:153-170` (krzyżak/gałka/strzałki) obsługują menu. `DrivingLabBootstrap.Update` nadal próbkuje
mikser: pad (0261/0264) A = postojowy, B = N, krzyżak = kierunkowskazy/awaryjne/retarder, a klawiatura: strzałki = gaz,
hamulec, skręt. Zamknięcie panelu przyciskiem B wrzuca luz w trakcie jazdy. Poprawka: przy `m_SettingsPanel != null`
(albo `UiFocus.HasModal`) źródła Pad/Keys (#133 `PcInputBridge`) i `HidWheelDriverInput` (#132) dają pusty zamiar.
Do tego test EditMode. Jedna poprawka zamyka też #133 P2-3 i uwagę w #132.

**#136 P1-1 — „auto” na desktopie zapisuje High i omija autodetekcję.** `PcSettingsRuntime.cs:81` → `ApplyTier("auto")` →
`AutoTier` = "High" (`:42`) → `QualityTiers.Apply(name, persist: true)` (`:27`). Pierwszy start zapisuje `diag.qualityTier = High`
wbrew ADR 0261 („not saved”). Po #135 wybór sprzętowy (GTX 660 → Low) jest w tej samej klatce nadpisany i zapisany, więc
autodetekcja nigdy więcej nie działa. Poprawka: „auto” bez zapisu i bez ruszania tieru z `GameBootstrap`, a po #135
`AutoTier = () => PcTierTable.NameOf(PcGraphicsTiers.DefaultFor(PcGraphicsTiers.DetectHardware()))`. Do tego test EditMode.

Rozwiązane w trakcie recenzji (H6), dla historii: #130 klasy niezgodne z D74. #132 konflikt `m_Mixer.Add(Pad)`. #133 add/add
`GamepadDriverInput.cs/.meta` (błąd kompilacji), podwójne Y/prawa gałka/C oraz inny układ przycisków niż 0261.

## Zgodność z CLAUDE.md (przekrojowo)
- **GC w pętli jazdy:** zero alokacji w `Update`/`FixedUpdate`, odczytach wejścia i FFB we wszystkich PR (przeczytane).
  Testy `GcAllocCounter` są w #132 (ścieżka kroku) i #133 (kształtowanie). Brak testu GC dla `Sample` z prawdziwym Input
  System — potrzebne `Unity.InputSystem` w `Game.Tests.EditMode` (asmdef = lider).
- **Fizyka w FixedUpdate:** FFB (#132) w `FixedUpdate`, kolumna `SnapTo`/`Step` w `FixedUpdate`. Wejście próbkowane w `Update`
  (jak dotąd) ✓.
- **FFB z fizyki opon:** ✓ (szczegóły w raporcie #132). Brak efektów z animacji i szumu, SPRING urządzenia odrzucony.
- **Marki:** w tekstach UI brak (pad: „przycisk dolny”, kierownica: „kierownica”). P2: `note` z nazwami producentów
  w `Resources/Controls/wheel_profiles.json` (#132) — przenieść do `docs/compat`.
- **ProjectSettings/Packages/asmdef:** brak zmian we wszystkich 8 PR (#135 celowo nadpisuje URP asset w runtime zamiast w QualitySettings; #136 P2-3: `Commit` w edytorze brudzi `vSyncCount`). #134 zmienia `.github/workflows/ci.yml` (nowy job
  `dist-tests`) — do świadomej akceptacji lidera.
- **ADR 0261:** `GamepadDriverInput` — jedna implementacja po #133 ✓. `DesktopAutoShot` — #130 nie łączy `-shot`/`-quit_t`
  z `-metrics` (opisane) ✓. Tier High na desktopie = klasa „zalecany” (#130); klasa min wymaga `-Tier Low -Fps 30` ✓.
- **Liczby PC (D74):** min/zalecany = D74. Progi FPS/RAM/VRAM/tris = propozycja lidera `WORKING_VALUE` (D74 tak mówi), klasa
  „wysoki” oznaczona jako spoza D74 ✓. P2: `tris.p95 ≤ 2 M` dla min/Low bez źródła; VRAM iGPU.

## Konflikty (`git merge-tree`, head jak w tabeli)
- Z main: **brak** dla wszystkich 8.
- Parami (28 par): **jeden konflikt — #131 × #136 `UI/BootMenu.cs`** (oba zmieniają blok przycisków ustawień/„Informacje”).
  #135 × #136 `GameBootstrap.cs` scala się czysto, ale jest konflikt logiczny (#136 P1). Na sha sprzed H6 były: #132×main (`DrivingLabBootstrap`), #133×main (add/add
  `GamepadDriverInput.cs/.meta`), #131×#133 (`ControlSettingsPanel`) — usunięte.
- Zależność: **#132 zawiera #133** (merge `82bcf40ee`).

## Kolejność scalania
1. **#129** — niezależne, małe (EditMode `RegionSelectTests`).
2. **#134** — same skrypty/dokumenty.
3. **#130** — dokumenty + recorder (autostart tylko z `-metrics`).
4. **#135** — tiery PC (po EditMode, buildzie i zrzutach Low/High). Potem pierwszy pomiar `pc-metrics` klas min/zalecany.
5. **#133** — pad/klawiatura. EditMode (`PadKeyboardInputTests`, `WindowsBuildTests`) + jazda z padem.
6. **#132** — kierownica (po #133, bo jest na nim zbudowana). EditMode + `dotnet test tools/physics-runner`.
7. **#131** — po P1-1 (blokada wejścia jazdy obejmuje `PcInputBridge.Pad/Keys` i `PcWheel.Input`) + `UiFocus` w `InputBindingsPanel`.
   Pętla wizualna 16:9/21:9/32:9/4K + regresja HUD na A16.
8. **#136** — po P1-1, na końcu: rozwiązać `BootMenu.cs` z #131 (przycisk w `UiFocus.ApplyGrid`, `PcFocusOutline` → `UiFocus`),
   `ApplyHudScale` → `UiPreferences.HudScale`, `AutoTier` z #135.

## Testy uruchomione przeze mnie
- `pytest tests/gis/test_region_catalog_0267.py` 3/3 + `export-region-catalog.py --check` (#129).
- `pytest tools/pcperf/tests` 27/27 na obu sha (#130).
- `dotnet test tools/physics-runner -c Release` 277/277 (#132, SDK 8.0.428 user-local).
- `pytest tests/dist` 14/14 (#134).
- #135/#136: tylko czytanie kodu (testy autorów na dotnet ze stubami spoza repo).
- **Nieuruchomione:** wszystkie EditMode/PlayMode (brak Unity), pwsh, build Windows, pomiary PC, pad/kierownica, pętla
  wizualna #131/#135/#136.

## Komendy dla lidera (zbiorczo)
```powershell
pwsh scripts/test.ps1 -Platform EditMode
pwsh scripts/test.ps1 -Platform PlayMode                     # PcHudSolverTests (#131)
dotnet test tools/physics-runner -c Release
uv run --no-project --with pytest pytest tools/pcperf/tests tests/dist -q
pwsh scripts/build-windows.ps1 -Regions d67-full
pwsh scripts/pc-metrics.ps1 -Exe artifacts/win/kamion-<ver>-<sha>-regions/Kamion.exe -Scene knyszyn-w -Tier High -Fps 60 -Width 1920 -Height 1080 -DurationSeconds 90 -Class zalecany
uv run --no-project python scripts/package-windows.py artifacts/win/kamion-<ver>-<sha>-regions --dry-run
pwsh scripts/build-android.ps1 -Install -Run -Serial RFGL34SJYDZ -Tier Low -LogcatSeconds 60   # regresja HUD dotykowego po #131
```
