# ADR 0276 — PC: menu bez kolizji z nakładką diagnostyczną, identyfikacja buildu, skróty regionów, P2 z recenzji
Status: Proposed (chmura H r3, zadanie H10, gałąź `pc-polish-0276`), 2026-11-16. Do weryfikacji i scalenia przez lidera.
Powiązane: ADR 0261 (build Windows), ADR 0265 (HUD/menu PC, `HudScaleModel`), ADR 0266 (bramki PC), ADR 0269 (tiery PC),
ADR 0271 (dystrybucja PC), raport `docs/reports/INTEGRATION-2026-11-15-int-pc-s23.md` §6, §7, §8.

## Kontekst
Integracja s23 (exe `e28533ca31`) zostawiła trzy usterki P2 PC: (a) nakładka diagnostyczna (KAMION / Device / GPU / FPS…)
nachodzi na tytuł i pierwszy przycisk menu startowego (`artifacts/int-pc-s23/final2/menu.jpg`); (b) `Kamion.exe.sha256` jest
identyczny dla każdego buildu (`fbd073ca…17492b`) — `Kamion.exe` to launcher Unity, treść jest w `Kamion_Data`, więc nic nie
odróżnia dwóch buildów; (c) skróty `Kamion-knyszyn.cmd` / `Kamion-knyszyn-w.cmd` są zakodowane na sztywno, niezależnie od
`-Regions`. Do tego lista małych P2 z recenzji #129–#136 i FIX pc-fix-s23.

## Decyzja
### (a) Jeden układ menu + nakładki (`MenuOverlayLayout`)
1. Czysta funkcja `Game.Controls.MenuOverlayLayout.Solve` (obok `HudScaleModel`, bo testy EditMode nie widzą `Game.UI`):
   wejście = rozmiar treści w jednostkach płótna, prostokąt bloku menu (bez przesunięcia), czy nakładka istnieje, czy panel
   tekstowy jest chciany, zarezerwowany rozmiar panelu, rozmiar przycisków; wyjście = przesunięcie menu w pionie, miejsce
   panelu (lewy górny / lewy dolny / zwinięty), miejsce przycisków (kolumna lub wiersz w prawym rogu), końcowe prostokąty.
   Kandydaci w stałej kolejności preferencji; dla każdego menu może się przesunąć w pionie w obrębie treści; wygrywa
   pierwszy kandydat, w którym menu, panel i przyciski są parami odsunięte o `Gap` = 16 j. (WORKING_VALUE), z najmniejszym
   przesunięciem. Bez menu — historyczne miejsce (panel lewy górny, kolumna prawy górny, margines 24). Bez nakładki — menu
   się nie rusza. Zero alokacji (struktury, statyczne tablice kandydatów).
2. `UI/Layout/MenuOverlayBoard` (statyczne pola): menu publikuje swój blok, nakładka — stan panelu i rozmiar; obie strony
   co klatkę liczą ten sam `Solve` i stosują swoją część. `BootMenu`: wszystkie elementy w nowym `RectTransform` „Block”
   (rozciągniętym na safe area) przesuwanym w pionie; `DiagnosticsOverlay`: panel i trzy przyciski pozycjonowane z wyniku
   (bez `VerticalLayoutGroup` przycisków). Rozmiar panelu: największy zmierzony, zaokrąglony w górę do 20 j. — cyfry FPS
   nie poruszają menu. Panel zwinięty przez układ wraca po zamknięciu menu; przycisk „Ukryj/Diagnostyka” zmienia wybór gracza.
3. Wynik na ekranach z testu (jednostki z `HudScaleModel`): monitor 16:9 / 21:9 / 32:9 / 1440p / 4K / 4K 150 % → panel
   zostaje w lewym górnym rogu, menu schodzi tak, by jego górna krawędź była 16 j. pod panelem (przy domyślnej rezerwie
   1180×300 j.: 116 j. = 87 px na 1080p — liczba z modelu, nie z pomiaru zrzutu), przyciski w kolumnie obok menu; telefon
   (1080 j. wysokości) i monitor przy skali HUD 1,4 → panel zwinięty (brak miejsca nad i pod menu), przyciski obok menu albo
   wierszem w prawym dolnym rogu.

### (b) Identyfikacja buildu: git sha + skrót zawartości `Kamion_Data`
4. **Kolejność (skrót nie zawiera samego siebie):** git sha jest zapiekany przed buildem (`BuildInfoWriter` →
   `Resources/build_info.json`, czyli wewnątrz `Kamion_Data`); po buildzie `scripts/postbuild-windows.py` liczy manifest
   `Kamion_Data` i zapisuje **`build-id.json` obok exe** (poza haszowanym folderem); gra czyta go raz przy starcie
   (`BuildInfo.ReadContentHash(Application.dataPath)`, tylko player desktop; edytor/Android → pusto).
5. **Definicja (`kamion/build-id/1`):** jedna linia `"<sha256>  <ścieżka>\n"` na plik z `Kamion_Data/` (ścieżka względem
   folderu buildu, separator `/`, sortowanie po bajtach UTF-8), bez `*.pdb` i folderów `*_DoNotShip` /
   `*_ButDontShipItWithYourGame`; `contentSha256` = SHA-256 tekstu manifestu, `contentHash` = pierwsze 12 hex. Pełny manifest:
   `Kamion_Data.sha256` (metadane, nie jedzie w zipie — zip ma `SHA256SUMS.txt`). Dwa buildy tego samego commitu mają
   zwykle różny skrót (`build_info.json` zawiera czas buildu) — skrót nazywa build, nie dowodzi powtarzalności.
6. **Gdzie widać:** `build.json` (`contentHash`, `contentSha256`, `contentFiles`, `contentBytes`), `[BOOT] Kamion <ver> (<sha>)
   content=<hash|none> …` (raz przy starcie), menu startowe (stopka) i „Informacje” (`Wersja: <ver> (<sha>) · dane <hash>`),
   nagłówek nakładki diagnostycznej, `system.txt` z `Zbierz-logi.cmd`, `run.json`-meta `pc-metrics.ps1` (`contentHash`,
   `buildGitSha`). `BuildInfo.ShortLabel` (telemetria, pcperf) bez zmian; nowe `IdentityLabel`.
7. **Paczka:** `kamion-<ver>-<sha>[-low][-regions][-dev][-dirty]-<contentHash>-win64.zip`. `package-windows.py` liczy skrót
   tą samą funkcją (import `postbuild-windows.py`) i porównuje z `build-id.json` — niezgodność = exit 2 („Kamion_Data
   zmienione po buildzie”); brak `build-id.json` (build sprzed ADR) → generowany i dokładany do zipu z ostrzeżeniem.
   `build-id.json` jedzie w paczce (gra testera pokazuje skrót).

### (c) Skróty startu
8. `Kamion-okno.cmd` (menu w oknie 1600×900) + `Kamion-<region>.cmd` (`-scene <region>`, okno 1600×900) **dla każdego
   regionu, którego scena Low jest w buildzie** — lista z linii `[BUILD] Windows x64 → … scenes=[…]` logu buildu, czyli po
   rozwinięciu zestawów / aliasów / zakresów przez `RegionBuildList` i po `-RegionsAllowMissing` (nie z katalogu: katalog nie
   wie, czego zabrakło). `GameBootstrap` przyjmuje `-scene <id|alias>` (→ scena regionu dla aktywnego tieru), co potwierdził
   przebieg int-pc-s23 (`-scene knyszyn`, `-scene knyszyn-w`). Id spoza `[a-z0-9-]` nie dostaje skrótu (ochrona linii cmd).
9. **Do paczki testera: tylko `Kamion-okno.cmd`** (README go opisuje). `Kamion-<region>.cmd` są wykluczane wzorcem
   (`Kamion-*.cmd` poza `Kamion-okno.cmd`): tester wybiera region w menu startowym; 21 plików w korzeniu paczki to szum;
   skróty mają sztywne okno 1600×900 i służą deweloperowi (ADR 0271 wykluczał już `Kamion-knyszyn.cmd`, ale nie
   `Kamion-knyszyn-w.cmd` — teraz reguła jest jedna).
10. `build-windows.ps1`: krok po buildzie przez Python (uv, w razie braku `python`/`python3`/`py -3`); błąd kroku = exit 5
    (player zbudowany, ale bez identyfikacji). Nowe `-Package [-PackageArgs …]` (propozycja ADR 0271) i przenoszenie
    `*_DoNotShip` do `artifacts/win/symbols/<build>/` zamiast kasowania (propozycja ADR 0271).

### (d) Małe P2 z recenzji #129–#136 i FIX pc-fix-s23
| P2 | Stan | Uzasadnienie |
|---|---|---|
| #129 P2-1 `build-windows.ps1` bez normalizacji `-Regions` / `-RegionsFile` | **zrobione** | to samo wyrażenie co `build-android.ps1` (+ NBSP), `throw` przy pustej liście, `-RegionsFile` względem cwd → korzeń repo → ścieżka absolutna |
| #129 P2-2 FIX 6/7 z #104 w HANDOVER | pominięte | HANDOVER prowadzi lider; dotyczy startu (H13) |
| #129 P2-3 stała nazwa pliku tymczasowego w `RegionSelectTests` | **zrobione** | `Path.GetRandomFileName()` |
| #130 P2-1 bramka VRAM dla iGPU | pominięte | nowy próg bez źródła; wymaga pomiaru na iGPU (decyzja, nie poprawka) |
| #130 P2-2 ADR 0266 pkt 1 przeczy sekcji D74 | **zrobione** | zdanie w pkt 1 odsyła do „Scalenie” |
| #130 P2-3 `tris ≤ 2 M` min/Low bez źródła | **zrobione** | dopisek w ADR 0266: sufit, nie cel; pierwszy pomiar Low ustawi wartość |
| #130 P2-4 haki `MarkRegionLoadStart/MarkDrivingReady` | pominięte | dotyka startu regionu (H13) |
| #130 P2-5 `over33Ms` na sztywno | pominięte | zmiana formatu `run.json` i parsera pcperf; nie bezsporne |
| #131 P2-2 ukrycie sekcji dotyk/gyro na PC | pominięte | wymaga zmiany testu PlayMode i przebiegu w Unity (FIX pc-fix-s23) |
| #131 P2-4 wskaźnik kierunkowskazów w HUD | pominięte | pytanie do właściciela |
| #131 P2-5 rozdzielczość lusterek na 4K | pominięte | lusterka = H12 |
| #132 P2-1/2/4/5 FFB, panel kierownicy, override, H-shifter | pominięte | kierownica = H12 |
| #132 P2-3 nazwy producentów w `wheel_profiles.json` | pominięte | ten sam plik co H12 (konflikt); **do zrobienia w H12** (przenieść `note` do `docs/compat`) |
| #133 P2-1 `PcInputBridge` na Androidzie | pominięte | decyzja (pad BT na telefonie jako cel albo warunek platformy) + wejście = H12 |
| #133 P2-2 test GC `Sample` z wirtualnym padem | pominięte | wymaga `Unity.InputSystem` w asmdef testów (lider) |
| #133 P2-5 `ToggleMirrorInsets` w `OnDestroy` | pominięte | `DrivingLabBootstrap` (H13) + lusterka (H12) — konflikt |
| #134 P2-1 `-regions` znika z nazwy zipu | **zrobione** | flaga z `build.json` (`regions`/`regionsFile`/`regionIds`) albo nazwy folderu |
| #134 P2-2 zrzuty awarii nieanonimizowane | **zrobione** | README, `Zbierz-logi.cmd` i `collect-logs.ps1` ostrzegają; nowe `-NoCrashes` |
| #134 P2-3 job CI `dist-tests` | bez zmian | już zaakceptowany przez lidera; nowe testy wchodzą do tego samego joba |
| #134 P2-4 `-Package`, symbole Burst | **zrobione** | pkt 10 |
| #135 P2-1 visual-qa tierów PC | pominięte | właściciel visual-qa |
| #135 P2-2 `globalTextureMipmapLimit` na Low | pominięte | wymaga zrzutu czytelności znaków (GPU) |
| #135 P2-3 lusterka przez SSAO | pominięte | lusterka = H12 |
| #135 P2-4 `AutoTier` po #136 | już w main | pc-fix-s23 |
| #135 P2-5 zamknięta lista iGPU | **zrobione** | dopisek w ADR 0269 „Otwarte” |
| #135 P2-6 dwa źródła budżetów PC w docs | **zrobione** | `PERFORMANCE_BUDGETS.md`: bramka = `pc-budgets.json`, tabela tierów to cel projektowy |
| #136 P2-1/P2-2(część)/P2-3 | już w main | pc-fix-s23 |
| #136 P2-2 reszta (`PcFocusOutline` → `UiFocus`) | pominięte | do zrobienia z padem w ręku (FIX pc-fix-s23) |
| #136 P2-4 podpis „Silnik” / P2-5 WORKING_VALUE + zrzut | pominięte | decyzja właściciela / build Windows |
| (dodatkowo) `collect-logs.ps1` bez BOM | **zrobione** | Windows PowerShell 5.1 czyta UTF-8 bez BOM jako ANSI — polskie komunikaty były zniekształcone |
| cienie drzew (#135 / int §4) | pominięte | poza zakresem (pc-shadows-s23) |

## Budżet
Pętla jazdy: bez nowego kodu. `DiagnosticsOverlay.Update` i `BootMenu.Update` wołają `MenuOverlayLayout.Solve` (kilkanaście
porównań prostokątów, bez alokacji — test `Solve_DoesNotAllocate`); pozycje `RectTransform` ustawiane tylko przy zmianie
wyniku. Odczyt `build-id.json` raz na proces (`BuildInfo.Current` w cache). Draws/tris bez zmian.

## Walidacja
- **Uruchomione (Linux, chmura):** `uv run --no-project --with pytest pytest tests/dist -q` → **27 passed** (14 starych
  dostosowanych do nowej nazwy + 13 nowych: manifest/skrót, `build-id.json`, `--check`, regiony z prawdziwej linii logu,
  skróty, `-regions` w nazwie, dwa buildy jednego commitu → różne nazwy, niezgodny `build-id.json` → błąd, ostrzeżenie o
  zrzutach, zgodność stałych C# ↔ Python). `pytest tools/pcperf -q` → 27 passed (regresja).
- **dotnet 8 z atrapą UnityEngine:** `MenuOverlayLayoutTests` + `BuildInfoTests` (te same pliki co w Unity) → **38/38**
  (14 ekranów × 2 bloki menu × panel pokazany/ukryty × 3 rozmiary panelu; brak alokacji przez
  `GC.GetAllocatedBytesForCurrentThread`).
- **pwsh 7.4.6 (Linux):** parsowanie `build-windows.ps1`, `collect-logs.ps1`, `pc-metrics.ps1` bez błędów; normalizacja
  `-Regions` (5 przypadków, w tym NBSP i `','`) zgodna; funkcja `Invoke-RepoPython` wyjęta z `build-windows.ps1` + krok
  postbuild na sztucznym buildzie → `build-id.json`, `Kamion-okno.cmd`, `Kamion-knyszyn.cmd`, `Kamion-dk65-11.cmd`; po
  zmianie pliku w `Kamion_Data` inny `contentHash`.
- Składnia C# (Roslyn, bez referencji Unity) zmienionych plików: OK. **Kompilacja w Unity, EditMode/PlayMode w Unity, build
  Windows, zrzut menu: NIEURUCHOMIONE** (brak Unity/Windows/GPU w chmurze). PlayMode `MenuOverlayUiTests` (prawdziwe obiekty
  uGUI, 5 ekranów) — napisany, nieuruchomiony.

## Komendy dla lidera
```powershell
pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 -Filter "Game.Tests.MenuOverlayLayoutTests;Game.Tests.BuildInfoTests;Game.Tests.RegionSelectTests;Game.Tests.PcHudLayoutTests"
pwsh scripts/test.ps1 -Platform PlayMode -BuildTarget Win64 -Filter "Game.Tests.MenuOverlayUiTests;Game.Tests.HudLayoutTests;Game.Tests.HudTextAllocTests;Game.Tests.BootSceneTests"
uv run --no-project --with pytest pytest tests/dist -q
pwsh scripts/build-windows.ps1 -Slot -Regions d67-full            # log: CONTENT <12 hex>, RUN Kamion-okno.cmd, Kamion-<21 regionów>.cmd
pwsh scripts/build-windows.ps1 -Slot -Regions 'knyszyn knyszyn-w'  # drugi build: inny contentHash w build.json / build-id.json
python scripts/postbuild-windows.py artifacts/win/kamion-0.1.0-<sha>-regions --check   # exit 0
artifacts\win\kamion-0.1.0-<sha>-regions\Kamion-knyszyn.cmd       # start w Knyszynie w oknie; Player.log: [BOOT] … content=<hash>
uv run --no-project python scripts/package-windows.py artifacts/win/kamion-0.1.0-<sha>-regions --dry-run   # nazwa …-regions-<hash>-win64.zip
```
Pętla wizualna: `Kamion-okno.cmd` → zrzut menu 1920×1080 i 2560×1080 (panel diagnostyki nad menu, nic nie zachodzi), ekran
„Informacje” (stopka `· dane <hash>`).

## Otwarte
- Zrzut menu z buildu Windows (16:9, 21:9, 4K) i telefonu (APK) — pętla wizualna do zrobienia przez lidera.
- Na telefonie i przy skali HUD 1,4 panel diagnostyki jest w menu zwinięty (brak miejsca bez zasłaniania menu); dane
  diagnostyczne nadal w logu i `diag/summary.json`, panel wraca w jeździe.
- Unity build nie jest bajtowo powtarzalny (czas w `build_info.json`; inne źródła niezbadane — UNVERIFIED), więc skrót
  identyfikuje build, nie commit.
- Propozycja dla lidera: CLAUDE.md „Komendy” — dopisać `-Package` i `postbuild-windows.py --check`; mapa dokumentów — „12
  dystrybucja PC” (ADR 0271).
