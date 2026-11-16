# ADR 0266 — Bramki i budżety PC + narzędzie pomiaru playera Windows (H4)

## Kontekst
D73 / ADR 0260: Windows jest platformą główną; telefon później i lżej. Bramki w `docs/03` i budżety w
`docs/PERFORMANCE_BUDGETS.md` były pisane pod Samsunga A (APK, adb, PSS, temperatura baterii). Referencyjny PC nie jest
ustalony, maszyna deweloperska (RTX 5070) nie jest referencją. Brakowało też narzędzia, które w playerze Windows mierzy to
samo co `scripts/device-metrics.ps1` na telefonie.

## Decyzja
1. **`docs/03` przepisany pod PC:** dowodem bramki jest build Windows (player) + liczby z `pc-metrics`. Trzy klasy sprzętu
   **min / zalecany / wysoki** (1080p30 Low / 1080p60 High / 1440p60 Ultra; min i zalecany wg D74 — patrz „Scalenie”) z budżetami: p50/p95/p99, % klatek > 2× budżetu,
   klatki > 100 ms, pamięć prywatna procesu, VRAM dedykowany procesu, czas ładowania regionu, draw calls i trójkąty (p95), GC
   w oknie. **Każda liczba to `WORKING_VALUE`** do decyzji właściciela; bez wyników benchmarków. Sprzęt klas min/zalecany
   to modele z D74 (sekcja „Scalenie” niżej, zastąpiła pierwotne kategorie/generacje; ADR 0276, recenzja #130 P2-2). Wymagania mobilne oznaczone 🔒 „zabezpieczenie mobilne (odroczone, D73)” — zostają (np. tris
   High 1,5 M / Ultra 2 M, ADR 0221 < 2 M), dane wspólne nie mogą ich przekroczyć bez ADR.
2. **Jedno źródło budżetu:** `tools/pcperf/budgets/pc-budgets.json` (`kamion/pc-budgets/1`); tabela w `docs/03` musi się zgadzać
   (test pytest). `referenceMachines: []` → każdy raport jest „informacyjny” (`gate_eligible: false`) dopóki właściciel nie
   wskaże sprzętu.
3. **Nagrywanie w grze:** `Game.Telemetry.PcFrameMetricsRecorder` — samostartujący (`RuntimeInitializeOnLoadMethod`) tylko
   z argumentem `-metrics <dir>`, więc bez zmian w scenach, `GameBootstrap` i asmdef. Bufory prealokowane
   (`PcMetricsMath.FrameCapacity` = sekundy × `-metricsMaxFps`), zero alokacji w `Update`, zapis na końcu: `frames.csv`
   (czas klatki z `Time.unscaledDeltaTime`, CPU/GPU z `FrameTimingManager`, liczniki `ProfilerRecorder` Render: Draw Calls /
   Batches / SetPass / Triangles, GC count, numer sceny), `memory.csv` (co 0,5 s `Profiler.GetTotalAllocated/Reserved`,
   Mono, sterownik grafiki), `run.json` (`SystemInfo`, ekran, tier, VSync, opcje, utrata fokusu, ładowania scen, percentyle
   z gry do kontroli krzyżowej), `screen.png`. Okno startuje po Boot albo (z `-scene`) od pierwszej klatki regionu; klatka
   z synchronicznym `LoadScene` nie wchodzi do okna, tylko do `loads[]`.
   Czas ładowania = od klatki, która zleciła `LoadScene` (błąd ≤ 1 klatka), albo od `PcFrameMetricsRecorder.MarkRegionLoadStart()`
   (hak do wpięcia przez lidera), do końca pierwszej klatki nowej sceny. `MarkDrivingReady()` — opcjonalny hak „ciężarówka gotowa”.
4. **Czysta logika** `PcMetricsMath` (nearest rank jak `FrameTimeStats` i `device-metrics.ps1`, liczenie > progu, parsowanie
   argumentów niezależne od kultury) + test EditMode `PcMetricsMathTests`; te same przypadki w pytest.
5. **Skrypt** `scripts/pc-metrics.ps1` przyjmuje ścieżkę do gotowego `.exe` (nie buduje — to ADR 0261), uruchamia z
   `-metrics`, `-logFile`, rozdzielczością, `-tier/-fps/-scene`, próbkuje co 1 s pamięć procesu, VRAM z klasy WMI
   `Win32_PerfFormattedData_GPUPerformanceCounters_GPUProcessMemory` (nazwy nielokalizowane — polski Windows) i opcjonalnie
   `nvidia-smi` (temperatura/obciążenie GPU), zapisuje SHA256 .exe, woła parser i zwraca jego kod wyjścia.
6. **Parser** `tools/pcperf/pc_metrics.py` (stdlib): raport JSON + MD po polsku, werdykt PASS / FAIL / INCOMPLETE (brak danych,
   np. liczniki niedostępne) / INVALID (edytor, < 600 klatek, utrata fokusu, przepełniony bufor, inny koniec niż `duration`,
   rozdzielczość/tier/limit FPS inne niż klasa). Exit 0/1/2.

## Konsekwencje
- Bramki etapów mówią „player Windows”; telefon wraca przy wersji mobilnej (Etap 9+). Gate 3 (D57) pozostaje zaliczona.
- `tools/perf` (perfgate, format telefonu) bez zmian; `tools/pcperf` jest osobnym narzędziem, bo formaty wejścia są inne.
- Propozycje dla lidera (poza moim zakresem — nie zmieniałem): (a) w `GameBootstrap` przed każdym `SceneManager.LoadScene`
  regionu wywołać `PcFrameMetricsRecorder.MarkRegionLoadStart()`, a w bootstrapie sceny jazdy po spawnie
  `MarkDrivingReady()` (Gameplay już referencjonuje Telemetry); (b) w `scripts/build-windows.ps1` (0261) po buildzie opcjonalny
  `-Measure` wołający `pc-metrics.ps1`; (c) `enableFrameTimingStats: 1` jest już w ProjectSettings — sprawdzić, czy D3D12 na
  Windows zwraca `gpuFrameTime` (inaczej kolumna `gpu_ms` = 0).
- `DiagnosticsSampler` (overlay, `persistentDataPath/diag`) działa dalej także na PC; pomiar bramki = `pc-metrics`.

## Budżet
Recorder poza `-metrics`: zero kosztu (nie tworzy obiektu). Z `-metrics`: ~49 B/klatkę prealokowane (91 s × 1000 FPS ≈ 4,5 MB),
per klatka 4 odczyty `ProfilerRecorder.LastValue` + `FrameTimingManager` + `GC.CollectionCount` — bez alokacji (UNVERIFIED
pomiarowo — nie uruchomione). Próbkowanie w skrypcie (CIM + nvidia-smi co 1 s) kosztuje trochę CPU na tej samej maszynie —
identyczne w przed/po.

## Walidacja
- Uruchomione: `uv run --no-project --with pytest pytest tools/pcperf/tests -q` → 27 passed (parser, budżet, zgodność z `docs/03`).
- **Nieuruchomione** (agent chmurowy bez Unity/pwsh/Windows): kompilacja C#, test EditMode `PcMetricsMathTests`,
  `scripts/pc-metrics.ps1`, pomiar na jakimkolwiek PC. `UNVERIFIED`: dostępność liczników Render w playerze release Unity
  6000.3 (kolumny -1 → INCOMPLETE, nie FAIL), `gpuFrameTime` na D3D12, licznik VRAM per proces przez CIM, margines 5 klatek
  na zapis `screen.png`.
- Pierwszy pomiar dla lidera (po buildzie 0261):
  `pwsh scripts/pc-metrics.ps1 -Exe <build>/<nazwa>.exe -Scene knyszyn -Tier High -Fps 60 -Width 1920 -Height 1080 -DurationSeconds 90 -Class zalecany`.

## Otwarte (pytania do właściciela)
Referencyjny PC dla każdej klasy (albo zgoda, że RTX 5070 + limit rozdzielczości/tieru emuluje klasę), docelowy FPS
(30/60/bez limitu), rozdzielczość i proporcje (16:9, ultrawide), budżet VRAM/RAM i minimalny SSD/HDD, wymóg kierownicy FFB na
premierę, kanał dystrybucji PC i model DLC (`docs/10` §3a), czy wersja telefonowa ma tę samą mapę.

## Scalenie z main (ADR 0261) i dopasowanie do D74 — agent H6, s22
- **D74** (właściciel: wymagania jak ETS2/ATS) zastąpił kategorie sprzętu z pkt 1: klasa **min** = i5-6400 / Ryzen 3 1200,
  GTX 660 / RX 460 / HD 630 (2 GB VRAM), 8 GB RAM → **tier Low** (było Medium), 1080p, 30 fps; klasa **zalecany** =
  i5-9600 / Ryzen 5 3600, GTX 1660 / RX 590, 12 GB RAM → High, 1080p, 60 fps; dysk ≤ 25 GB (`diskGB` w JSON). Progi pamięci
  przeliczone pod RAM/VRAM z D74 (min: prywatna ≤ 4 GB, VRAM ≤ 1,75 GB, draw calls ≤ 2 000, trójkąty ≤ 2 M; zalecany:
  prywatna ≤ 7 GB, VRAM ≤ 5 GB). Klasa **wysoki** zostaje jako propozycja spoza D74. Wszystko `WORKING_VALUE`.
  **Trójkąty ≤ 2 M dla min/Low to sufit bezpieczeństwa, nie cel** (ten sam rząd co cały budżet kamer C na High; wartość
  bez źródła) — pierwszy pomiar Low na buildzie Windows ustawi właściwą wartość (ADR 0276, recenzja #130 P2-3).
- **`pc-metrics.ps1` vs `build-windows.ps1`:** przyjmuje exe z `artifacts/win/kamion-<ver>-<sha>[-low][-regions][-dev]/Kamion.exe`
  (przykłady poprawione; region `knyszyn-w` z korytarza 0261). Argumenty `-metrics*` nie kolidują z `DesktopAutoShot`
  (`-shot`, `-shot_t`, `-quit_t`) — nie łączyć ich w jednym przebiegu (oba kończą player). Desktop bez `-tier`/`-fps` startuje
  High/60 (0261), więc pomiar klasy min wymaga `-Tier Low -Fps 30`.
- Propozycja (b) z „Konsekwencji” (`-Measure` w `build-windows.ps1`) nadal otwarta — `build-windows.ps1` nie zmieniany.
- Weryfikacja po scaleniu: `uv run --with pytest pytest tools/pcperf -q` → 27 passed (Linux, chmura). C# i pwsh nieuruchomione.

## Uzupełnienie s23 (D76) — emulacja klas min / zalecany na maszynie deweloperskiej
**Decyzja właściciela D76** (`docs/11`): klasy „min” i „zalecany” z D74 mierzymy teraz emulacją na RTX 5070 (ograniczenie
rozdzielczości, tieru i limitu FPS); raporty mogą zaliczać bramki z adnotacją „emulacja”; przed publiczną obietnicą wymagań
— pomiar na prawdziwym słabszym sprzęcie (HD 630 / GTX 660, GTX 1660). Zmienia skutek pkt 2 („`referenceMachines: []` → każdy
raport informacyjny”) i odpowiada na pierwsze pytanie z „Otwarte” (rozbieżność R1 w `docs/reports/GATES-STATUS-2026-11-16.md`).

- **Osobny plik maszyn** `tools/pcperf/budgets/pc-machines.json` (format `kamion/pc-machines/1`) — nie w `pc-budgets.json`,
  bo budżety per tier zmienia równolegle pomiar D83. Schemat:
  `{format, adr, decision, note, reference: [wpis], emulation: [wpis]}`; wpis = `{id, label, decision, match, classes, method}`.
  `match` dopasowuje pola `run.json → system` (to, co zapisuje `PcFrameMetricsRecorder` z `SystemInfo`): `gpuContains` /
  `gpuExcludes` (`graphicsDeviceName`), `gpuVendorContains`, `cpuContains` / `cpuExcludes` (`processorType`),
  `deviceModelContains` — podciągi bez wielkości liter; nieznany klucz = błąd formatu (exit 2). `classes` dla `reference` =
  lista nazw klas; dla `emulation` = obiekt klasa → `{resolution, tier, targetFps, vSyncCount, fullScreenModes, realHardware}`.
- **Wpis `dev-rtx5070`** (emulation, D76): `gpuContains ["RTX 5070"]`, `gpuExcludes ["Ti"]`, `gpuVendorContains ["NVIDIA"]`
  (nazwa w logach Unity: „NVIDIA GeForce RTX 5070”; dokładny ciąg `SystemInfo.graphicsDeviceName` w playerze `UNVERIFIED` —
  dlatego podciąg); klasy **min** = 1920×1080, Low, 30 FPS, VSync 0; **zalecany** = 1920×1080, High, 60 FPS, VSync 0; obie
  w trybie `FullScreenWindow` (domyślne `-WindowMode borderless` skryptu) albo `ExclusiveFullScreen`; okno = niezgodne.
  Klasa „wysoki” bez emulacji (poza D76) → informacyjna. `reference: []` — gotowe na prawdziwy sprzęt.
- **Reguła parsera:** `measurement_kind` = `reference` (wpis `reference` z tą klasą pasuje do `system`, albo stary
  `referenceMachines` z budżetu — zgodność wstecz) → `emulation` (wpis `emulation` pasuje i ma tę klasę, a `display` w
  `run.json` spełnia jego konfigurację: rozdzielczość, `qualityName`, `targetFrameRate`, `vSyncCount`, `fullScreenMode`;
  brak pola = niepotwierdzone = niezgodne) → w przeciwnym razie `informational` z powodami w `measurement.reasons`.
  **`gate_eligible` = werdykt `PASS` i `measurement_kind` ∈ {reference, emulation}.** `--allow-context-mismatch` nadal
  daje tylko wynik informacyjny. Raport JSON: `measurement_kind`, `measurement {kind, machine, decision, reasons, annotation}`;
  MD i JSON emulacji: „EMULACJA (D76) — nie zastępuje pomiaru na sprzęcie klasy X (…) przed obietnicą wymagań sprzętowych”.
  Werdykt i kody wyjścia 0/1/2 bez zmian (rodzaj pomiaru nie zmienia exit code); CLI: nowy opcjonalny `--machines <plik>`
  (domyślnie `budgets/pc-machines.json`), linia stdout dopisuje na końcu `kind=… gate_eligible=…`. `scripts/pc-metrics.ps1`
  bez zmian w parametrach (parser bierze plik domyślny); poprawiony tylko opis.
- **Komendy (lider, Windows, RTX 5070):**
  `pwsh scripts/pc-metrics.ps1 -Exe artifacts/win/kamion-<ver>-<sha>-regions/Kamion.exe -Scene knyszyn-w -Tier Low -Fps 30 -VSync 0 -Width 1920 -Height 1080 -DurationSeconds 90 -Class min`
  i `… -Tier High -Fps 60 -VSync 0 -Width 1920 -Height 1080 -DurationSeconds 90 -Class zalecany`. `-VSync 0` jest wymagane
  (domyślne `-1` zostawia ustawienie gry, które może mieć VSync włączony → `informational`).
- **Ograniczenie metody:** emulacja ogranicza rozdzielczość, tier i limit FPS, ale RTX 5070 / Ultra 7 270K Plus / 64 GB nie
  odtwarzają przepustowości GTX 660 / HD 630 / GTX 1660 ani 8–12 GB RAM; progi pamięci procesu i VRAM są mierzone, ale
  słabsza karta może zachowywać się inaczej (sterownik, kompresja tekstur, streaming). Dlatego adnotacja w każdym raporcie.
- Walidacja: `uv run --no-project --with pytest pytest tools/pcperf -q` → 51 passed (było 27; nowe: emulacja zgodna/niezgodna
  — rozdzielczość, tier, FPS, VSync, tryb ekranu; GPU niepasujące, w tym „RTX 5070 Ti”; wpis `reference`; stary
  `referenceMachines`; niepełny `run.json`; CLI z `--machines`; schemat i spójność `pc-machines.json` z `pc-budgets.json`).
  `pc-budgets.json` niezmieniony. pwsh / player nieuruchomione (chmura, Linux).
