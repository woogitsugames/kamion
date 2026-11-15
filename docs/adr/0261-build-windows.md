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
(uzupełniane po buildzie i przebiegu — patrz niżej „Wyniki”)

## Otwarte
- Kierownica z FFB (D56/D73) — nie w tym ADR.
- Dotykowy HUD (kierownica, pedały ekranowe) jest widoczny także na PC; ukrycie / układ PC — zadanie gameplay-ui.
- Mapowanie klawiszy i pada nie jest konfigurowalne w panelu ustawień (stałe w kodzie); brak podpowiedzi klawiszy w HUD.
- `fullscreenMode`, domyślna rozdzielczość okna, ikona, nazwa produktu w ProjectSettings — decyzja lidera.
- Referencyjny PC i docelowy FPS (ADR 0260); limit 60 fps i tier High to WORKING_VALUE.
- Scripting backend Standalone = Mono (domyślny w ProjectSettings); IL2CPP do rozważenia przy wydaniu.
