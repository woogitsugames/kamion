# ADR DRAFT — Direct3D 11 jako domyślne API grafiki playera Windows (D3D12 jako drugie + furtka `-force-d3d12`)

Status: **Proposed** — 2026-11-16, szkic P24 (sesja P r8, gałąź `adr-d3d11-draft` z `origin/main` @ `eebb9813c`).
Numer nada lider przy scaleniu. **Bez zmian w kodzie i ustawieniach** — ten plik tylko proponuje; zmiana `ProjectSettings`
należy do lidera (CLAUDE.md, „Tylko lider zmienia `ProjectSettings/`”).
Podstawa: `docs/reports/RESEARCH-2026-11-16-d3d12-device-removed.md` (P20, dalej „research”). Powiązane: ADR 0051, 0260,
0261, 0266 (+ D76), 0269, 0270, 0271, 0276. Wszystkie źródła internetowe: **data dostępu 2026-11-16**. Liczby bez źródła
i bez pomiaru: `UNVERIFIED` albo `WORKING_VALUE`.

## 1. Kontekst

**Zdarzenie** (`HANDOVER.md:300`, wpis [16.11 15:2x]): exe `13104cf215`, region knyszyn, pełny ekran borderless, **D3D12**,
RTX 5070, sterownik **32.0.16.1088 = GeForce 610.88** (research §1.6: pakiet DCH 610.88 zawiera INF-y 32.0.16.1088), log
`d3d12: Device failed error (887a0001)` → device removed; dump `%LOCALAPPDATA%\CrashDumps\Kamion.exe.73136.dmp`. W tym czasie
na tej samej karcie pracowały inne procesy Unity (research §0). **Pełnego `Player.log` ani stosu nie ma w repo** — wszystko
niżej o przyczynie to ocena.

**Obejście doraźne:** lider uruchamia właścicielowi `-force-d3d11` (`HANDOVER.md:300`, `:311` — korytarz `-scene knyszyn
-stream 1 -force-d3d11`, jazda bez zgłoszonego crasha; jedna obserwacja, bez pomiaru). Instrukcja gracza opisuje to jako
awaryjne (`docs/owner/JAK-GRAC-PC.md:150-160`, sekcja 1.6). Dowód pośredni: obecny build (lista API automatyczna) **startuje
z `-force-d3d11`**, więc shadery D3D11 są w nim obecne.

**Wnioski z research (P20):**
- 0x887A0001 = `DXGI_ERROR_INVALID_CALL`, nie klasyczny TDR (0x887A0005/6/7); różni się od kodu sukcesu
  `DXGI_STATUS_OCCLUDED` (0x087A0001) tylko bitem błędu (Microsoft, research §1.1).
- Trzy najbardziej prawdopodobne przyczyny (research §2, ocena):
  1. **`Present` zwraca 0x887A0001 przy zmianie fokusu/stanu okna pełnoekranowego na D3D12** — **UUM-148214** (Closed, Third
     Party Issue; found in 6000.3.21f1; stos `D3D12SwapChain::Present` → `CheckDeviceStatus`; „Does not occur with DX11, only in
     fullscreen mode”) — prawdop. **wysokie**; u nas `runInBackground: 0` (`game/ProjectSettings/ProjectSettings.asset:89`).
  2. **Równoległe obciążenie GPU / brak VRAM** (kilka procesów Unity na 12 GB) — prawdop. średnie (ADR 0051:
     `CreateCommandQueue failed 8007000e`; Unity troubleshooting: GPU crash „often caused by … running out of dedicated video memory”).
  3. **Otwarty błąd backendu D3D12 Unity pod obciążeniem** — **UUM-147012** (Open; repro 6000.3.18f1, 6000.5.3f1, 6000.6.0b3;
     `CheckDeviceStatus` ← `D3D12CommandList::PrepareExecute`; DX12, nie DX11) — prawdop. średnie.
- **Release notes 6000.3.x** (research §1.3): 6000.3.11f1 „Fixed false-reporting of non-error return codes (i.e., 087a0001) in
  CheckDeviceStatus()” — Unity przyznaje problem z tą rodziną kodów; nasz kod ma bit błędu (8…), więc czy to ten sam problem —
  `UNVERIFIED`. 6000.3.28f1 (nasza wersja) jest najnowszym patchem 6000.3 — **nie ma nowszej poprawki do wzięcia** bez zmiany
  gałęzi Unity (zamrożone, decyzja właściciela). Release notes 6000.4/6000.5 nieprzejrzane w całości.
- Wszystkie publiczne pokrewne zgłoszenia 6000.3 (UUM-148214, UUM-134743, UUM-147012, wątek „DX12 Graphics Crash in Editor,
  Force DX11 Fixes It”) mówią: **DX11 nie dotyczy**.
- Dokumentacja Unity sama podaje D3D11 jako obejście: „**Use a fallback graphics API** — If the crash is specific to DX12, you
  can temporarily revert to DX11 while you investigate the root cause.” —
  https://docs.unity.com/en-us/engine/6000.3/manual/platform-specific/windows/develop/troubleshoot-gpu-crash (6000.3,
  last_updated 2026-10-30).

**Crash przy zamykaniu 1/5** (pc-shadows-s23, `HANDOVER.md:300`) — **osobny problem**, nie wpływa na tę decyzję wprost:
ścieżka `D3D12PipelineCacheLibrary::SaveCache` ← `~GfxDeviceD3D12` przy `Application::Exit` (ADR 0051, edytor; research §2
#8). Dump niezanalizowany. Na D3D11 tej ścieżki (cache PSO D3D12) nie ma, więc przejście **może** go usunąć jako efekt
uboczny — `UNVERIFIED`, mierzone osobno (§4.3).

**Stan konfiguracji (odczyt, nic nie zmieniane):**

| Element | Wartość | Plik:linia |
|---|---|---|
| API Standalone | brak wpisu Windows w `m_BuildTargetGraphicsAPIs` → **lista automatyczna**; player zgłasza `Direct3D 12` | `game/ProjectSettings/ProjectSettings.asset:538-544` |
| Graphics jobs Standalone | `m_BuildTargetGraphicsJobs: []`, `m_BuildTargetGraphicsJobMode: []` → domyślne Unity (tryb na Win64 `UNVERIFIED`) | `ProjectSettings.asset:536-537` |
| Filtr urządzeń D3D12 | `d3d12DeviceFilterListAsset: {fileID: 0}` → reguły domyślne | `ProjectSettings.asset:950` |
| Flip model / runInBackground / fullscreenMode | 1 / 0 / 1 | `ProjectSettings.asset:101`, `:89`, `:114` |
| Precedens „API jako kod” | `SetUseDefaultGraphicsAPIs(BuildTarget.Android, false)` + `SetGraphicsAPIs(Android, {Vulkan, OpenGLES3})` | `game/Assets/_Project/Editor/Setup/ProjectSetup.cs:248-249` |

## 2. Opcje

| | **A — D3D12 domyślnie (bez zmian) + diagnoza** | **B — D3D11 domyślnie, D3D12 drugie** | **C — B + przełącznik API w menu ustawień PC** |
|---|---|---|---|
| Co | lista automatyczna zostaje; gracze/testerzy dostają `-force-d3d11` w razie crasha; diagnoza wg research §6 (L1–L9) | `SetUseDefaultGraphicsAPIs(StandaloneWindows64, false)` + `SetGraphicsAPIs(…, {Direct3D11, Direct3D12})` w `ProjectSetup.ApplyAll`; D3D12 zostaje w buildzie → `-force-d3d12` działa jako furtka | jak B + pole `graphicsApi` (`auto`/`d3d11`/`d3d12`) w `settings_pc.json` (ADR 0270, `schemaVersion` 1→2) i w menu „Grafika”; **zmiana wymaga restartu** (API wybiera silnik przed pierwszym skryptem); argument `-force-d3d12`/`-force-d3d11` zawsze wygrywa |
| Ryzyko | **wysokie** dla graczy: znany, otwarty po stronie Unity crash (UUM-147012 Open, UUM-148214 Third Party) na naszej wersji; każdy, kto uruchomi sam exe/launcher bez flagi, ma D3D12 | **niskie–średnie**: inny backend = inne kadry (MSAA resolve, cienie, sRGB — do sprawdzenia VQA); wszystkie pomiary PC w repo są na D3D12 (ADR 0261, D76) → baseline do powtórzenia; możliwy wyższy koszt CPU wątku renderu (brak native/split graphics jobs na DX11 — §3) | jak B + ryzyko kodu: restart samego siebie (`Process.Start` exe z argumentem) nietestowany, pętla restartu przy błędnym zapisie, interakcja z `-single-instance`/launcherami `.cmd`; gracz może sam wybrać crashujące API |
| Koszt | 0 w kodzie; czas lidera na L1–L9 (i tak potrzebny) | 1 zmiana w `ProjectSetup.cs` + `pwsh scripts/setup-project.ps1` + pełny build Windows + pomiar §4 + VQA + aktualizacja docs (§5) ≈ jedna sesja lidera | B + UI (`PcSettingsRuntime`/menu), migracja `schemaVersion`, testy EditMode, restart-logika, ADR 0270 addendum ≈ +1–2 zadania agenta |
| Wpływ na graczy | crash możliwy przy Alt+Tab/fokusie na pełnym ekranie (hipoteza #1) — każdy tester musi znać flagę | domyślnie stabilniejsze API wg wszystkich zgłoszeń; nic do klikania; zaawansowani: `Kamion-*.cmd -force-d3d12` | jak B + wybór w menu bez wiersza poleceń |
| Wpływ na pomiary D76 / D83 | bez zmian (D3D12) — ale **klasa min na prawdziwym sprzęcie i tak dostanie D3D11** (filtr domyślny, niżej) → emulacja min na D3D12 mierzy inne API niż u gracza | **pomiary D76 (min/zalecany) i budżety per tier D83 trzeba zrobić/powtórzyć na D3D11**; zgodne z tym, co dostanie klasa min | jak B; dodatkowo `run.json` musi zapisywać API (już jest: `graphicsApi` = `SystemInfo.graphicsDeviceVersion`, `game/Assets/_Project/Telemetry/PcFrameMetricsRecorder.cs:354`), a parser powinien je raportować/porównywać (dziś tylko wypisuje, `tools/pcperf/pc_metrics.py:514`) |

**Ważna obserwacja dla D76/D83 (wszystkie opcje):** domyślny D3D12 Device Filtering Asset w 6000.3 „restricts devices” z
Feature level < 12.1, **≤ 4 rdzeniami CPU**, < 3600 MB VRAM, albo iGPU Intel/AMD; takie urządzenia „fall back to the default
graphics API configured in the Player settings” — https://docs.unity.com/en-us/engine/6000.3/manual/introduction-d3d12-device-filtering-asset.
Sprzęt klas D74: **GTX 660** (Kepler, max FL 11_0; 2 GB), **HD 630** (iGPU Intel), **RX 460** (FL 12_0), **RX 590** (FL 12_0)
— wszystkie poniżej progów (FL wg https://en.wikipedia.org/wiki/Feature_levels_in_Direct3D, źródło wtórne); i5-6400 / Ryzen 3
1200 mają 4 rdzenie (z wiedzy ogólnej, `UNVERIFIED` — nie sprawdzone u producentów; czy filtr liczy rdzenie fizyczne czy
logiczne: `UNVERIFIED`). Wniosek (ocena): **klasa min dostaje D3D11 niezależnie od tej decyzji**, a w klasie zalecany GTX 1660
(FL 12_1, 6 GB) dostałby D3D12, RX 590 — D3D11. Jakie API jest „default … in Player settings” przy liście automatycznej —
`UNVERIFIED` (prawdopodobnie D3D11). Opcja B ujednolica to: wszyscy na D3D11.

**Rozważone i odrzucone:**
- *Filtr urządzeń D3D12 z regułą deny* (np. NVIDIA + sterownik ≤ 610.88 — reguły mogą dopasować nazwę GPU regexem i wersję
  sterownika, ta sama strona Unity): precyzyjny, ale nie mamy dowodu, że winny jest sterownik (research §2 #4: nisko-średnie);
  przyczyny #1 i #3 nie zależą od sterownika. Do ponownego rozważenia przy powrocie do D3D12 (§5.2).
- *`boot.config` w `Kamion_Data` jako nośnik wyboru API dla opcji C*: czy istnieje klucz wymuszający API — `UNVERIFIED`;
  dodatkowo `Kamion_Data` jest objęty `contentHash` w `build-id.json` (ADR 0276) — zapis gracza zmieniałby tożsamość buildu.
- *Vulkan na Windows*: poza zakresem; brak pomiarów, nie rozwiązuje problemu D3D12 lepiej niż D3D11.

**Rekomendacja szkicu: B teraz, C odłożone.** Uzasadnienie: (a) jedyne publicznie znane obejście wszystkich trzech
przyczyn, potwierdzone dokumentacją Unity; (b) nie używamy żadnej funkcji wymagającej D3D12 (§3); (c) klasa min i tak
działa na D3D11 (filtr), więc B daje jedno API do mierzenia i wspierania; (d) B zachowuje D3D12 w buildzie, więc
`-force-d3d12` jest furtką bez kodu; (e) C kosztuje kod (restart, migracja ustawień) za korzyść, której dziś nie widać —
wraca, gdy pomiar §4 pokaże istotną przewagę D3D12 albo pojawi się funkcja tylko-DX12. Warunek: kryteria §4 spełnione.

## 3. Koszty D3D11 w Unity 6000.3 URP — co tracimy i czy tego używamy

Źródło główne: Unity Manual 6000.3 „DirectX” (tabele DX11 vs DX12) —
https://docs.unity.com/en-us/engine/6000.3/manual/platform-specific/cross-platform-features/graphics-apis/using-dx11gl3features
(dostęp 2026-11-16).

| Funkcja | DX11 wg dokumentacji 6000.3 | Używamy? (dowód) | Strata dla nas |
|---|---|---|---|
| Dynamic resolution | Unsupported (DX12: Supported) | **nie** — 0 trafień `allowDynamicResolution`/`ScalableBufferManager` w `game/Assets/_Project` | brak |
| Asynchronous compute | Unsupported | **nie** — 0 trafień `EnableAsyncCompute`, brak plików `.compute` (research §0) | brak |
| Native render pass (API) / URP „Native RenderPass”, „Raster pass merging”, „Framebuffer fetch” | Unsupported; w URP na DX12 tylko „Supported (**Windows on ARM**)” | ustawione `m_UseNativeRenderPass: 1` w `PC_Renderer.asset:31` i `PC_Renderer_SSAO.asset:56` (`game/Assets/_Project/Rendering/Resources/PcTiers/`) | **brak na x64** — na Windows x64 URP nie korzysta z tego także na DX12 wg tabeli |
| Ray tracing acceleration / ray tracing shader / inline RT | Unsupported | **nie** — 0 plików `.raytrace`, 0 `RaytracingAccelerationStructure`/`UNITY_DEVICE_SUPPORTS` | brak |
| Graphics state collection (PSO warm-up) | Unsupported | `PsoWarmup` (`game/Assets/_Project/Rendering/Runtime/PsoWarmup.cs:66-79`) ładuje kolekcje pasujące do API; **są tylko kolekcje Vulkan** (`Resources/Pso/pso_Vulkan_Low_g3a/g3b.graphicsstate`) → na PC dziś nic się nie rozgrzewa także na D3D12 | brak dziś; tracimy przyszłą opcję warm-upu PSO na PC (D3D11 nie ma PSO w tym sensie — kompilacja przy pierwszym użyciu, czy to daje zacięcia: `UNVERIFIED`, mierzy p99/„> 100 ms” w §4) |
| Render threading: **Native graphics jobs**, **Split graphics jobs** | Unsupported (Direct / single / main+render thread / **Legacy jobified**: Supported) | ustawienia puste (`ProjectSettings.asset:536-537`) → domyślny tryb na Win64 `UNVERIFIED` | **możliwa strata CPU** wątku renderu przy dużej liczbie draw calli (gęste kafle D83) — tylko pomiar §4; blog Unity nie podaje liczb DX12 vs DX11 |
| Native 16-bit, wave functions (shadery) | Unsupported | **nie** (0 trafień `UNITY_DEVICE_SUPPORTS_*`) | brak |
| XR foveated rendering | Unsupported | nie (brak XR) | brak |
| GPU Resident Drawer | strona 6000.3 nie wymienia DX11/DX12; wymaga „Forward+ rendering path” i API „that support compute shaders, except OpenGL ES” — https://docs.unity.com/en-us/engine/6000.3/manual/analysis/graphics-performance-profiling/in-urp/reduce-draw-calls-urp/reduce-rendering-work-on-cpu/gpu-resident-drawer | **nie** — `m_GPUResidentDrawerMode: 0` w `URP_PC_Low.asset:86`, `URP_PC_Medium.asset:86`, `URP_PC_High.asset:87`, `URP_PC_Ultra.asset:87`; renderery PC są **Forward** (`m_RenderingMode: 0`, `PC_Renderer.asset:48`, `PC_Renderer_SSAO.asset:77`), nie Forward+ | brak (i tak niespełniony warunek Forward+); czy GRD działa na DX11 — `UNVERIFIED` |
| Variable Rate Shading | strona 6000.3 niedostępna (404); strona 6.4 i notatki Core SRP 17: DX12/Vulkan/konsole — `UNVERIFIED` dla 6000.3 | **nie** (0 trafień `ShadingRate`) | brak |
| DirectStorage | wg wyników wyszukiwania dopiero od **6.4** (strony 6000.4+); w 6000.3 nie dotyczy — `UNVERIFIED` (strona 6000.3 nie znaleziona) | nie | brak |
| Bindless | brak w tabelach dokumentacji 6000.3 — nie dotyczy (ocena) | nie | brak |
| Render Graph (URP) | tabela nie wymienia ograniczeń DX11 | **tak** — `m_EnableRenderCompatibilityMode: 0` (`game/Assets/_Project/Rendering/Settings/UniversalRenderPipelineGlobalSettings.asset:368`) | działanie na DX11 potwierdza obecny build z `-force-d3d11` (jazda właściciela, `HANDOVER.md:311`); poprawność kadrów → VQA §4.4 |
| SSAO (High/Ultra, `PC_Renderer_SSAO`) | brak ograniczeń w tabeli | **tak** (`PC_Renderer_SSAO.asset:13-30`, `URP_PC_High/Ultra` lista rendererów) | → VQA §4.4 |
| Decale URP (`DecalRendererFeature`) | — | **nie** (0 trafień `DecalProjector`/`DecalRendererFeature`; „decal” w `FabDecalRetrofit.cs` to materiał, ADR 0131) | brak |
| Upscaler / STP / DLSS | — | **nie** (`m_UpscalingFilter: 0`; ADR 0269) | brak |
| MSAA 2×/4×/8×, cienie 2048–8192, 2–4 kaskady, soft shadows | standard DX11 | **tak** (`URP_PC_Low.asset:28,46,58,66`, `URP_PC_Ultra.asset:29,47,59,67`) | → VQA §4.4 (Ultra 8192/MSAA 8× — VRAM) |

**Pamięć:** blog Unity (Damian Nachman, 2025-04-16) o DX12: „can increase memory usage compared to the single-threaded
DX11” oraz „DirectX 12 may not be recommended on significantly old GPU models and outdated driver versions”; dla starszych
urządzeń radzi trzymać DX11 „or keep it as a fallback API” — https://unity.com/blog/directx-12-improvements-in-unity-6.
**Wydajność D3D11 vs D3D12:** ten sam blog **nie podaje liczb DX12 vs DX11** (twierdzenie o split jobs porównuje z „Native
Jobs”, nie z DX11). Dla naszego projektu: **`UNVERIFIED` — do pomiaru (§4)**. Kierunek nieznany: D3D12 może wygrywać na CPU
(graphics jobs) w gęstych kaflach, D3D11 może wygrywać na pamięci i stabilności klatek.

## 4. Kryteria pomiaru (rozstrzygające)

### 4.1 Warunki
- **Ten sam exe dla obu API** — obecny build (lista automatyczna, D3D11 dostępne — §1), wybór API wyłącznie argumentem:
  `-force-d3d11` / `-force-d3d12` (Unity Manual 6000.3 „Player command line arguments”: „-force-d3d11 (Windows only) Force the
  application to use Direct3D 11 for rendering.”, „-force-d3d12 (Windows only) Force the application to use Direct3D 12 for
  rendering.” — https://docs.unity.com/en-us/engine/6000.3/manual/unity-editor/command-line-arguments/player). Argumenty bez
  wartości. `-force-gfx-jobs` **nie istnieje** na tej stronie (jest `-force-gfx-direct` = „Force single threaded rendering”) —
  nie używać.
- Przekazanie przez `pc-metrics.ps1`: `-Extra force-d3d11` → skrypt dokleja `-force-d3d11` i pustą wartość
  (`scripts/pc-metrics.ps1:86`, `$k, $v = $kv -split '=', 2`); skrypt jest szkicem nieuruchomionym na Windows —
  **sprawdzić po każdym przebiegu** API w `run.json → system.graphicsApi` i w `Player.log` (`[BOOT] … api='Direct3D 11…'`,
  `game/Assets/_Project/Gameplay/GameBootstrap.cs:118`). Przebieg z niezgodnym API = odrzucony.
- Maszyna: RTX 5070 (emulacja D76), **bezczynna** — żadnego innego procesu Unity/renderu (research §5.3; inaczej nie da się
  oddzielić przyczyny #1 od #2), okno w fokusie, nakładki wyłączone, ten sam sterownik dla wszystkich przebiegów (zapisać wersję).
- Kolejność przeplatana (D3D12, D3D11, D3D12, …), żeby dryf temperatury/cache nie faworyzował jednego API.

### 4.2 Wydajność — komendy (lider, PowerShell 7, katalog repo)
`$exe = 'artifacts/win/kamion-<ver>-<sha>-regions/Kamion.exe'` (build z regionami korytarza; `Kamion-korytarz.cmd` wymaga
`knyszyn` i `knyszyn-s`, `scripts/postbuild-windows.py:49-53`). Dla każdego `$api` w `d3d12`, `d3d11`, 3 powtórzenia:

```powershell
# klasa min (D74/D76): Low, 1080p30, VSync 0 — korytarz ze streamingiem
pwsh scripts/pc-metrics.ps1 -Exe $exe -Scene knyszyn -Extra "force-$api","stream=1" -Tier Low  -Fps 30 -VSync 0 -Width 1920 -Height 1080 -DurationSeconds 90 -Class min      -Label "$api-min-korytarz"
# klasa zalecany: High, 1080p60, VSync 0
pwsh scripts/pc-metrics.ps1 -Exe $exe -Scene knyszyn -Extra "force-$api","stream=1" -Tier High -Fps 60 -VSync 0 -Width 1920 -Height 1080 -DurationSeconds 90 -Class zalecany -Label "$api-zal-korytarz"
# DrivingLab (powtarzalny autopilot) — obie klasy
pwsh scripts/pc-metrics.ps1 -Exe $exe -Scene DrivingLab -Extra "force-$api","autopilot=circle50","speed=40","trailer=40" -Tier Low  -Fps 30 -VSync 0 -Class min      -Label "$api-min-lab"
pwsh scripts/pc-metrics.ps1 -Exe $exe -Scene DrivingLab -Extra "force-$api","autopilot=circle50","speed=40","trailer=40" -Tier High -Fps 60 -VSync 0 -Class zalecany -Label "$api-zal-lab"
# zapas bez limitu (informacyjnie, pokazuje różnicę CPU/GPU, której limit FPS nie pokaże)
pwsh scripts/pc-metrics.ps1 -Exe $exe -Scene DrivingLab -Extra "force-$api","autopilot=circle50","speed=40","trailer=40" -Tier High -Fps 240 -VSync 0 -Label "$api-uncapped"
```
(`-Extra` przyjmuje tablicę; elementy z przecinkiem są też dzielone — `scripts/pc-metrics.ps1:43,86`. Czy w korytarzu przy
`-Scene knyszyn` okno pomiaru obejmuje przejazd przez szwy — zależy od trasy autopilota; korytarz bez autopilota = jazda
ręczna, mniej powtarzalna — `UNVERIFIED`, wtedy rozstrzyga DrivingLab, korytarz jest kontrolą.)

**Progi (D3D11 vs D3D12, mediana z 3 powtórzeń, każda para scena × klasa osobno) — wszystko `WORKING_VALUE`:**
- p95 i p99 czasu klatki D3D11 ≤ **1,05 ×** D3D12 (**X = 5 %**; uzasadnienie: rząd rozrzutu między powtórzeniami tej samej
  konfiguracji — do potwierdzenia rozrzutem z 3 powtórzeń; jeśli rozrzut > 5 %, próg = rozrzut);
- % klatek > 2× budżetu: D3D11 ≤ D3D12 + **0,5 pp** i w budżecie klasy (`tools/pcperf/budgets/pc-budgets.json`);
- klatki > 100 ms: D3D11 ≤ D3D12 (poza `loads[]`);
- pamięć prywatna i VRAM procesu: w budżecie klasy (różnicę raportować; oczekiwanie wg bloga Unity: D3D11 ≤ D3D12 — `UNVERIFIED`);
- werdykt `pc-report` dla D3D11: **PASS, `measurement_kind=emulation`** (ADR 0266 + D76) w obu klasach;
- przebieg uncapped: informacyjnie (bez progu); jeśli D3D11 ma > 15 % gorszy p50 (`WORKING_VALUE`), notatka do „Otwarte” —
  sygnał dla gęstych kafli D83.
- `gpu_ms` z `FrameTimingManager` na D3D11: czy dostępne — `UNVERIFIED` (kolumna może być 0 → wtedy tylko czas klatki).

### 4.3 Stabilność — komendy i progi
1. **Device removed w jeździe:** **N = 10** przebiegów na API, każdy 10 min w korytarzu, w tym 60 s przełączania fokusu
   (Alt+Tab / klik na drugim monitorze; repro UUM-148214):
   `& $exe -force-$api -scene knyszyn -stream 1 -screen-fullscreen 1 -window-mode borderless -logFile "artifacts/d3d-ab/$api-run$i.log"`.
   Po każdym: `Select-String -Path artifacts/d3d-ab/*.log -Pattern 'Device failed|Device removed|887a|DXGI error'` + folder
   `%LOCALAPPDATA%\Temp\woogitsugames\Kamion\Crashes` + `%LOCALAPPDATA%\CrashDumps`.
   **Próg: D3D11 = 0 / 10.** D3D12 notowane (≥ 1 crash = potwierdzenie obejścia; 0 / 10 = brak odtworzenia, decyzja nadal
   wg §2 — „0 z 10” daje górną granicę 95 % częstości ≈ 26 % na przebieg, czyli **nie dowodzi** braku rzadkiego crasha;
   obliczenie: 1 − 0,05^(1/10)).
2. **Crash przy zamykaniu (osobny, 1/5):** **N = 15** cykli start → 30 s → wyjście na API:
   `& $exe -force-$api -scene knyszyn -quit_t 30 -logFile "artifacts/d3d-ab/$api-quit$i.log"` (`-quit_t` = `DesktopAutoShot`,
   `game/Assets/_Project/Gameplay/DesktopAutoShot.cs:10-11`; nie łączyć z `-metrics`). Próg D3D11: 0 / 15 (przy prawdziwej
   częstości 1/5 szansa na 0 / 15 = 0,8^15 ≈ 3,5 %, więc 0 / 15 odróżnia „naprawione” od „1/5”).
   Czy `-quit_t` przechodzi przez tę samą ścieżkę `Application::Exit` co zamknięcie z menu — `UNVERIFIED`.

### 4.4 VQA — bez różnic wizualnych
- **Kamery kontrolne edytora** (Low i High): przed zmianą ProjectSettings (edytor na obecnym API) i po (wg dokumentacji
  „Configure graphics APIs” 6000.3 edytor przy wyłączonym Auto „uses the first API in the list” —
  https://docs.unity.com/en-us/engine/6000.3/manual/platform-specific/cross-platform-features/graphics-apis/configure; czy
  potrzebny restart edytora — `UNVERIFIED`; sprawdzić API w logu edytora):
  `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low  -Lighting clear -OutputDir artifacts/visual-qa/d3d-ab/<api>-low`
  `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting clear -OutputDir artifacts/visual-qa/d3d-ab/<api>-high`
  (+ `-Lighting overcast` dla High). Uwaga: to jednocześnie zmienia API **wszystkich renderów VQA agentów** — referencje
  sprzed zmiany są na starym API (konsekwencja §6).
- **Player** (to, co widzi gracz), ten sam exe, oba API:
  `& $exe -force-$api -scene knyszyn -tier High -fps 60 -screen-width 1920 -screen-height 1080 -screen-fullscreen 1 -window-mode borderless -shot "artifacts/d3d-ab/$api-high.png" -shot_t 20 -quit_t 25`
  i to samo z `-tier Low -fps 30`.
- **Kryterium:** przegląd pętlą `visual-qa` (visual-critic) par D3D11/D3D12 — brak różnic w cieniach (kaskady, soft), SSAO,
  MSAA, niebie, szkle, lampach, tonemappingu; dopuszczalny szum na poziomie pojedynczych pikseli (narzędzia do diffu
  liczbowego w repo nie ma — ocena wzrokowa + ewentualny jednorazowy skrypt PIL, `UNVERIFIED`). Każda widoczna różnica =
  stop i analiza przed wdrożeniem.

## 5. Plan wdrożenia i wycofania

### 5.1 Wdrożenie (po spełnieniu §4; wszystko **lider**)
1. **ProjectSettings jako kod:** w `ProjectSetup.ApplyAll` obok linii Androida (`ProjectSetup.cs:248-249`):
   `PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.StandaloneWindows64, false);`
   `PlayerSettings.SetGraphicsAPIs(BuildTarget.StandaloneWindows64, new[] { GraphicsDeviceType.Direct3D11, GraphicsDeviceType.Direct3D12 });`
   → `pwsh scripts/setup-project.ps1` → commit wynikowego `ProjectSettings.asset` (nowy wpis Windows w
   `m_BuildTargetGraphicsAPIs`; ręczna edycja YAML odradzana — nazwa build targetu i kodowanie `m_APIs` `UNVERIFIED`).
   Podpisy `SetGraphicsAPIs`/`SetUseDefaultGraphicsAPIs` dla 6000.3 — używane już w repo dla Androida; strona 6000.3 nie
   znaleziona (6.4/6.2: „The passed APIs will be tried in the order they are given, and first available one will be used”).
   Graphics jobs: **bez zmian** (na D3D11 i tak tylko Legacy/Direct/single/main+render).
2. **Build:** `pwsh scripts/build-windows.ps1 -Slot -Regions <korytarz> -Package` (ADR 0261/0271) → w `[BOOT]` `api='Direct3D 11…'`;
   porównać rozmiar `build.json` z poprzednim (shadery obu API — oczekiwanie: bez zmian, `UNVERIFIED`).
3. **Launchery** (`scripts/postbuild-windows.py`): bez zmian — przekazują `%*`, więc `Kamion-korytarz.cmd -force-d3d12` działa.
   Opcjonalnie (decyzja lidera) `Kamion-d3d12.cmd` dla testów porównawczych — **nie** w paczce dla graczy.
4. **Paczka** (`scripts/package-windows.py`, `dist/windows/README.txt.in`): sekcja „Grafika: domyślnie Direct3D 11; awaryjnie/
   do testów `-force-d3d12`”; przy okazji zaległość `JAK-GRAC-PC.md:395` (#14: README bez `-force-d3d11`/`CrashDumps`).
5. **`docs/owner/JAK-GRAC-PC.md`:** sekcja 1.6 odwrócona („domyślnie D3D11; `-force-d3d12` tylko na prośbę”), tabela
   argumentów (`:74`), pytania otwarte (`:410`).
6. **Pomiary:** raporty §4 do `docs/reports/`; ADR 0266 addendum „API pomiaru = D3D11”; D83 budżety per tier mierzone na
   D3D11. `HANDOVER.md` + licznik ADR.
7. (Opcja C, jeśli kiedyś) osobne zadanie: pole `graphicsApi` w `PcSettingsData` (`schemaVersion` 2, `PcSettingsJson.Migrate`),
   menu, restart — osobny ADR/addendum 0270.

### 5.2 Wycofanie (powrót do D3D12 domyślnie)
**Warunki (którykolwiek):** (a) Unity naprawi błąd w gałęzi, na którą przejdziemy (UUM-147012 → Fixed, albo release note
dotyczący 0x887A0001/`Present`/`CheckDeviceStatus`), **i** 10/10 przebiegów §4.3 na D3D12 bez crasha; (b) sterownik NVIDIA
z udokumentowaną poprawką + ten sam test; (c) potrzebujemy funkcji tylko-DX12 (split/native graphics jobs przy pomiarze
gęstych kafli pokazującym > 15 % zysku p95 na D3D12 — `WORKING_VALUE`; ray tracing; GPU Resident Drawer z Forward+, jeśli
okaże się wymagać DX12; VRS; DirectStorage po zmianie wersji Unity); (d) D3D11 okaże się mieć własny crash/regresję.
**Kroki:** zamiana kolejności w `ProjectSetup` (`{Direct3D12, Direct3D11}`) albo powrót do `SetUseDefaultGraphicsAPIs(…, true)`
→ `setup-project.ps1` → build → §4.2–4.4 odwrotnie → docs (JAK-GRAC-PC, README) → rozważyć filtr urządzeń D3D12 z regułą
deny dla wadliwych sterowników zamiast globalnego D3D11. D3D11 zostaje drugie na liście (klasa min).

## 6. Konsekwencje
- Gracze domyślnie na API, którego nie dotyczy żadne z trzech znanych zgłoszeń; klasa min i tak była na D3D11 (filtr).
- Wszystkie dotychczasowe liczby PC (ADR 0261, 0266/D76, pomiary s22–s23) są na D3D12 → dla bramek PC wymagany nowy baseline
  na D3D11; stare raporty zostają jako historia z adnotacją API.
- Edytor (VQA, rendery agentów) przełączy się na D3D11 wg dokumentacji — referencje VQA sprzed zmiany porównywać z
  ostrożnością; crash edytora z ADR 0051 (D3D12 `SaveCache`) może zniknąć jako skutek uboczny (`UNVERIFIED`).
- Tracimy możliwość native/split graphics jobs i przyszłego warm-upu PSO przez Graphics State Collection na PC.
- Diagnoza D3D12 (research §6, L1–L9) **nadal potrzebna** — zgłoszenie do Unity z repro, warunek powrotu §5.2.

## 7. Budżet
Brak zmian w danych/treści. Wpływ na czas klatki i pamięć — **nieznany do pomiaru §4** (`UNVERIFIED`); decyzja wdrożenia
jest warunkowa: D3D11 nie może pogorszyć p95/p99 o > 5 % ani wyjść z budżetu klasy (`WORKING_VALUE`).

## 8. Walidacja (tego szkicu)
- Odczyt plików repo (ścieżki:linie wyżej) na `origin/main` @ `eebb9813c`; grep funkcji (async compute, RT, VRS, GRD,
  decale, dynamic resolution, GSC) w `game/Assets/_Project`.
- Dokumentacja Unity 6000.3 pobrana 2026-11-16: „DirectX” (tabele DX11/DX12), „Player command line arguments”,
  „Configure graphics APIs”, „Troubleshoot D3D12 GPU crashes on Windows”, „Introduction to D3D12 Device Filtering Asset”,
  „GPU Resident Drawer”, „Configure graphics jobs mode on D3D12”, `GraphicsDeviceType`; blog Unity „DirectX 12 improvements in
  Unity 6” (2025-04-16).
- **Nieuruchomione:** żaden build, player, `pc-metrics.ps1`, VQA (agent chmurowy, Linux, bez Unity/pwsh/GPU).

## 9. Otwarte / UNVERIFIED
1. Pełny `Player.log`/stos crasha 16.11 — czy 0x887A0001 pochodzi z `Present` (hipoteza #1); research §6 L1–L3.
2. Domyślne API i lista „Auto Graphics API” na Windows w 6000.3; jakie API dostaje urządzenie odrzucone przez filtr D3D12 przy
   liście automatycznej (strona „Configure graphics APIs” 6000.3 tego nie podaje).
3. Domyślny tryb graphics jobs Win64 przy pustym `m_BuildTargetGraphicsJobMode` — od tego zależy, ile CPU tracimy na D3D11.
4. Wydajność D3D11 vs D3D12 w naszym projekcie (brak źródeł z liczbami; tylko pomiar §4).
5. `FrameTimingManager` `gpuFrameTime` na D3D11 w playerze release.
6. Czy `-Extra force-d3d11` w `pc-metrics.ps1` przekazuje flagę poprawnie (pusta wartość) — sprawdzić `graphicsApi` w `run.json`.
7. Czy edytor przełącza API po zmianie listy bez restartu; czy `-force-d3d11` działa w `Invoke-UnityBatch` dla VQA.
8. Czy `-force-d3d12` omija filtr urządzeń D3D12 na sprzęcie odrzuconym przez filtr.
9. Strony 6000.3 dla VRS, DirectStorage, `SetGraphicsAPIs`/`SetUseDefaultGraphicsAPIs` nieznalezione — użyto 6.2/6.4 lub
   wyników wyszukiwania; kodowanie `m_APIs` dla Windows w YAML.
10. Liczba rdzeni i5-6400 / Ryzen 3 1200 i czy filtr liczy rdzenie fizyczne; FL kart z Wikipedii (źródło wtórne).
11. Czy przejście usuwa crash przy zamykaniu 1/5 (dump pc-shadows niezanalizowany) — §4.3 pkt 2.
12. Progi X = 5 %, 0,5 pp, 15 %, N = 10 / 15 — `WORKING_VALUE` do akceptacji lidera/właściciela.
