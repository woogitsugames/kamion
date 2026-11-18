# ADR 0291 — Direct3D 11 domyślnym API grafiki playera Windows, Direct3D 12 jako opcja (`-force-d3d12`)

Status: **Accepted** — decyzja właściciela (klik) 2026-11-18 po pomiarze A/B na GTX 1070 (D88 w `docs/11`); wdrożenie agent
`d3d11-default-s24` (gałąź `d3d11-default-s24`). Zastępuje szkic P24 `docs/adr/DRAFT-d3d11-default.md` (usunięty w tym
zadaniu; pełny tekst w historii git, commit `9fa6a763d`) — analiza kosztów D3D11 (§3 szkicu), opcje A/B/C i warunki
wycofania pochodzą stamtąd i nadal obowiązują.
Powiązane: ADR 0051 (crash `SaveCache` D3D12 w edytorze), 0260 (Windows platformą główną), 0261 (build Windows), 0266 + D76
(pomiar PC), 0270 (ustawienia PC), 0271 (paczka), `docs/reports/CRASH-2026-11-16-d3d12.md` (crash-diag-s23),
`docs/reports/RESEARCH-2026-11-16-d3d12-device-removed.md`.

## Kontekst
- 16.11.2026 player u właściciela (RTX 5070, sterownik 610.88, Unity 6000.3.28f1) padł na **D3D12** w jeździe:
  `D3D12SwapChain::Present` → `CheckDeviceStatus`, `swapchain present failed (887a0001)`, tryb pełnoekranowy wyłączny
  (raport crash-diag-s23, crash A; zgodny z publicznymi UUM-148214 / UUM-134743 — „DX12 only”). Jedno wystąpienie,
  nieodtworzone. Mitygacja już w `main`: na D3D12 tryb wyłączny → bez ramki (`ExclusiveFullscreenPolicy`, furtka
  `-allow-exclusive-d3d12`).
- Do tej zmiany `ProjectSettings.asset` nie miał wpisu Windows w `m_BuildTargetGraphicsAPIs` (lista automatyczna → player
  wybierał Direct3D 12).
- Crash przy wyjściu (crash B, `win::NewInput::Activate` w `CleanupEngine`) występuje na **obu** API — ta decyzja go nie
  dotyczy.

## Pomiar (podstawa decyzji)
Maszyna: i5-10400F (12 wątków), 64 GB, **GTX 1070 8 GB**, Windows 11 10.0.26300; exe
`kamion-0.1.0-4f5e98a16f-regions` (worktree win-build, `-dirty`; lista API automatyczna, API wymuszane `-force-d3d11` /
`-force-d3d12`, potwierdzone w `run.json` → `graphicsApi` i w `Player.log`). Scena `knyszyn` (`World_knyszyn_High`),
`-stream 1 -autopilot route -speed 50`, tier High, 1920×1080 bez ramki, VSync 0, 90 s, rozgrzewka 5 s; kolejność
przeplatana D3D12/D3D11, 2 powtórzenia; bez innych procesów Unity (`unity_before=0 unity_after=0`). Dane:
`artifacts/d3d-ab/<api>-<tryb>-r<n>/pc-report.md` (poza gitem; kopia na maszynie właściciela w katalogu main).

| przebieg | śr. FPS | czas klatki p50 / p95 / p99 [ms] | max [ms] | klatki > 100 ms | prywatna szczyt [MB] | VRAM [MB] |
|---|---|---|---|---|---|---|
| d3d11 uncapped r1 | 171,4 | 5,70 / 7,36 / 8,36 | 14,03 | 0 | 2891 | 1763 |
| d3d11 uncapped r2 | 189,8 | 5,15 / 6,54 / 7,33 | 27,09 | 0 | 2890 | 1763 |
| d3d12 uncapped r1 | 157,5 | 6,36 / 8,12 / 8,90 | 18,45 | 0 | 3266 | 1872 |
| d3d12 uncapped r2 | 153,3 | 6,47 / 8,30 / 9,45 | 29,16 | 0 | 3211 | 1872 |
| d3d11 High60 r1 | 59,9 | 16,67 / 16,67 / 16,67 | 77,15 | 0 | 2685 | 1763 |
| d3d11 High60 r2 | 60,0 | 16,67 / 16,67 / 16,68 | 18,77 | 0 | 2638 | 1763 |
| d3d12 High60 r1 | 58,6 | 16,67 / 16,67 / 26,08 | 155,97 | **4** | 3063 | 1871 |
| d3d12 High60 r2 | 60,0 | 16,67 / 16,67 / 16,67 | 17,03 | 0 | 3040 | 1871 |

Wyjście z gry (`-quit_t`, `artifacts/d3d-ab/d3d-ab.log`): D3D12 3/3 i D3D11 3/3 bez znacznika crasha.
Werdykt `pc-report` High60 (klasa `zalecany`, `WORKING_VALUE`, pomiar **informacyjny** — maszyna nie jest w
`pc-machines.json`): D3D11 PASS/PASS, D3D12 FAIL (r1: p99 26,08 ms, 0,76 % > 33,3 ms, 4 klatki > 100 ms) / PASS.
Ograniczenia: 2 powtórzenia (nie 3 jak w szkicu §4.2), jedna scena, jedna maszyna, bez klasy `min` i bez DrivingLab;
czy klatki > 100 ms w D3D12 r1 to cecha API, czy jednorazowe zakłócenie — `UNVERIFIED` (r2 ich nie ma).

## Decyzja
1. Lista API Standalone Windows x64 ustawiana kodem, nieautomatyczna: **[Direct3D11, Direct3D12]**
   (`Game.Editor.Setup.ProjectSetup.WindowsGraphicsApis` + `ApplyWindowsGraphicsApis()`, wołane z `ApplyPlayerSettings()`,
   czyli z `ApplyAll` / `scripts/setup-project.ps1`; idempotentne; test EditMode `WindowsGraphicsApiTests`).
2. Direct3D 12 zostaje w buildzie jako drugie API: `-force-d3d12` działa bez osobnego buildu.
3. Launchery postbuild (`scripts/postbuild-windows.py`): zamiast `Kamion-d3d11.cmd` / `Kamion-korytarz-d3d11.cmd` są
   `Kamion-d3d12.cmd` / `Kamion-korytarz-d3d12.cmd` (`-force-d3d12`, bez `-screen-*`), w paczce testera tak jak dotąd.
4. Mitygacja D3D12 zostaje bez zmian: `ExclusiveFullscreenPolicy` sprawdza `SystemInfo.graphicsDeviceType` w czasie
   działania, więc przy wymuszonym D3D12 tryb wyłączny nadal staje się „bez ramki”; `-allow-exclusive-d3d12` nadal go
   przywraca (test `ForcedD3D12_StillGetsExclusiveToBorderlessMitigation`).
5. Graphics jobs, filtr urządzeń D3D12, Vulkan — bez zmian. Opcja C szkicu (przełącznik API w menu) — odłożona.

## Konsekwencje i ryzyka
- **Baseline PC:** wcześniejsze liczby PC (ADR 0261, 0266/D76, pomiary s22–s24 bez `-force-d3d11`) są na D3D12. Nowe
  pomiary bramek PC i budżety D83 — na D3D11; stare raporty zostają jako historia z adnotacją API.
- **Kadry:** inny backend może różnić się w cieniach / SSAO / MSAA / sRGB. Zrzuty `screen.png` z A/B istnieją
  (`artifacts/d3d-ab/*/screen.png`), ale przegląd pętlą `visual-qa` par D3D11/D3D12 **nie był zrobiony** — `UNVERIFIED`,
  zadanie dla visual-critic.
- **Edytor:** wg dokumentacji Unity przy wyłączonym „Auto” edytor używa pierwszego API z listy → rendery VQA agentów
  przejdą na D3D11 (czy wymaga restartu edytora — `UNVERIFIED`); może to zmienić porównania z referencjami sprzed zmiany i
  przy okazji ominąć crash edytora z ADR 0051 (`UNVERIFIED`).
- **CPU wątku renderu:** D3D11 nie ma native/split graphics jobs. Na GTX 1070 przy ~1800–2100 draw calls D3D11 był
  szybszy, ale gęste kafle miejskie (D83) i słabsze CPU klasy `min` nie były mierzone — `UNVERIFIED`.
- **Crash `887a0001`:** na D3D11 dotąd nie widziany; crash D3D12 był jednorazowy, więc brak wystąpień nie jest dowodem.
- **Crash przy wyjściu (B):** bez zmian, oba API.
- Tracimy przyszły warm-up PSO przez Graphics State Collection na PC (dziś i tak tylko kolekcje Vulkan).

## Wycofanie
Warunki i kroki jak w szkicu §5.2: poprawka Unity/sterownika + 10/10 przebiegów bez crasha na D3D12, potrzeba funkcji
tylko-DX12 albo regresja D3D11. Technicznie: zamiana kolejności w `ProjectSetup.WindowsGraphicsApis` (albo powrót do listy
automatycznej) → `setup-project.ps1` → build → pomiar A/B → zamiana launcherów i docs (README paczki, `JAK-GRAC-PC.md` 1.6).

## Walidacja
- pytest `tests/dist` (launchery, paczka, README): wynik w STATUS gałęzi.
- EditMode Win64 (`pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64`): wynik w STATUS gałęzi.
- Build Windows z nowymi ustawieniami + start playera bez `-force-*`: w `Player.log` `Version:  Direct3D 11.0 …` — STATUS.
- Zmiana `game/ProjectSettings/ProjectSettings.asset` (nowy wpis Windows w `m_BuildTargetGraphicsAPIs`) — **commit lidera**
  (agent zapisuje diff w `artifacts/d3d11-default-s24/projectsettings.diff`).

## Otwarte
1. VQA par D3D11/D3D12 (player High/Low) — visual-critic.
2. Pomiar klasy `min` (Low, 30 fps) i DrivingLab na D3D11; 3. powtórzenie A/B.
3. Pomiar gęstego kafla miejskiego (draw calls > 4000) D3D11 vs D3D12 — ryzyko CPU wątku renderu.
