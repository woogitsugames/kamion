# RESEARCH 2026-11-16 — crash D3D12 `Device failed error (887a0001)` w playerze Windows (P20)

Zadanie P20 (sesja P r7, `docs/owner/CLOUD-P7-PROMPT-S23.md`). Tylko research: **bez zmian w kodzie i ustawieniach**.
Wszystkie źródła internetowe: data dostępu **2026-11-16**. Twierdzenia bez źródła są oznaczone `UNVERIFIED` albo „ocena”.

## 0. Stan wyjściowy (z repo, `origin/main` `8a4de955a`)

**Zdarzenie** (`HANDOVER.md`, wpis [16.11 15:2x]): exe `13104cf215` (knyszyn), pełny ekran borderless, D3D12, RTX 5070,
sterownik 32.0.16.1088; log `d3d12: Device failed error (887a0001)` → device removed; dump
`%LOCALAPPDATA%\CrashDumps\Kamion.exe.73136.dmp`, raport Unity w `%LOCALAPPDATA%\Temp\woogitsugames\Kamion\Crashes`.
Kontekst z tego samego wpisu i sąsiednich: exe uruchomił **lider** (proces w tle) na pełnym ekranie; w tym czasie na tej samej
maszynie pracowały inne procesy Unity (world2: import/rendery VQA, int-h3: build + runy, int-stream: start) — wpisy
[16.11 15:0x]–[16.11 15:19]. Wcześniej (pc-shadows-s23, wpis [16.11 09:0x]): crash przy zamykaniu 1/5, dump w
`artifacts/pc-shadows-s23` (na maszynie właściciela; w tym środowisku niedostępny — **nie analizowany**).

**Pełnego `Player.log` i stosu z tego crasha nie ma w repo** — raport opiera się na jednej linii logu. To główne ograniczenie.

**Precedens w projekcie — ADR 0051** (2026-11-10, edytor, 6000.3.28f1, D3D12, RTX 5070): sporadyczny crash przy zamykaniu
`D3D12Core!D3D12GetInterface` ← `D3D12PipelineCacheLibrary::SaveCache` ← `~GfxDeviceD3D12` ← `Application::Exit`; 5 przebiegów na
bezczynnej maszynie bez powtórzenia → „wygląda na zależny od obciążenia (równoległe procesy Unity/GPU)”. Ten sam ADR notuje inny
crash `CreateCommandQueue failed 8007000e` (brak pamięci GPU przy kilku procesach Unity).

**Konfiguracja renderowania (odczyt, nic nie zmieniane):**

| Element | Wartość | Plik |
|---|---|---|
| Wersja Unity | 6000.3.28f1 (= najnowszy patch 6000.3 w dniu raportu, zob. §1.3) | `game/ProjectSettings/ProjectVersion.txt`, ADR 0261 |
| API Standalone | brak wpisu `Standalone` w `m_BuildTargetGraphicsAPIs` (są tylko iOS i Android) → lista automatyczna; player zgłasza `api='Direct3D 12'` (ADR 0261, log `[BOOT]`) | `ProjectSettings.asset:538-544` |
| `d3d12DeviceFilterListAsset` | `{fileID: 0}` → domyślne reguły filtra D3D12 | `ProjectSettings.asset:950` |
| Graphics jobs Standalone | `m_BuildTargetGraphicsJobs: []`, `m_BuildTargetGraphicsJobMode: []` → domyślne Unity (jaki to tryb na Win64: `UNVERIFIED`) | `ProjectSettings.asset:536-537` |
| `fullscreenMode` / `useFlipModelSwapchain` / `runInBackground` / `visibleInBackground` | 1 / 1 / **0** / 1 | `ProjectSettings.asset:89-114` |
| `gpuSkinning` / `enableFrameTimingStats` | 1 / 1 | `ProjectSettings.asset:105,160` |
| GPU Resident Drawer | `m_GPUResidentDrawerMode: 0` (wyłączony) we **wszystkich 9** assetach URP (mobilne + `URP_PC_*`) | `game/Assets/_Project/Rendering/**` |
| Render Graph | włączony (`RenderGraphSettings.m_EnableRenderCompatibilityMode: 0`) | `UniversalRenderPipelineGlobalSettings.asset:365-368` |
| Upscaler / STP / DLSS | brak (`m_UpscalingFilter: 0`; ADR 0269: TAA/STP wykluczone) | `URP_PC_*.asset` |
| Cienie High / Ultra | atlas głównego światła 4096 / 8192, 4 kaskady, MSAA 4× / 8×, soft shadows | `URP_PC_High.asset`, `URP_PC_Ultra.asset` |
| Renderer PC | Forward (`m_RenderingMode: 0`), Native Render Pass 1, brak featurów (SSAO tylko w `PC_Renderer_SSAO`) | `PC_Renderer*.asset` |
| Własny compute / async compute / własne passy Render Graph | **brak** (grep `ComputeShader|ComputeBuffer|GraphicsBuffer|AsyncGPUReadback|RecordRenderGraph|ExecuteCommandBufferAsync` w `Assets/_Project` = 0 trafień; brak plików `.compute`) | — |
| Limit klatek desktop | 60 fps domyślnie (ADR 0261 §5, WORKING_VALUE) | `GameBootstrap`, `PcSettingsRuntime` |

## 1. Co mówią źródła

### 1.1 Kody błędów (Microsoft)
- **0x887A0001 = `DXGI_ERROR_INVALID_CALL`**: „The application provided invalid parameter data; this must be debugged and fixed
  before the application is released.” Dla porównania 0x887A0005 `DEVICE_REMOVED` (karta usunięta / aktualizacja sterownika;
  diagnoza przez `GetDeviceRemovedReason`), 0x887A0006 `DEVICE_HUNG` („badly formed commands sent by the application”),
  0x887A0007 `DEVICE_RESET` („badly formed command … run-time issue”), 0x887A0020 `DRIVER_INTERNAL_ERROR`.
  — https://learn.microsoft.com/en-us/windows/win32/direct3ddxgi/dxgi-error
- **0x087A0001 = `DXGI_STATUS_OCCLUDED`** (kod sukcesu, okno niewidoczne; „You will not receive DXGI_STATUS_OCCLUDED if you're
  using a flip model swap chain”). Różni się od naszego kodu tylko bitem błędu (8 vs 0).
  — https://learn.microsoft.com/en-us/windows/win32/direct3ddxgi/dxgi-status
- `IDXGISwapChain::Present` dokumentuje jako możliwe zwroty S_OK, `DEVICE_RESET`, `DEVICE_REMOVED`, `STATUS_OCCLUDED`,
  `D3DDDIERR_DEVICEREMOVED` — **`INVALID_CALL` nie jest na tej liście**.
  — https://learn.microsoft.com/en-us/windows/win32/api/dxgi/nf-dxgi-idxgiswapchain-present
- **Wniosek (ocena):** 887a0001 to formalnie „nieprawidłowe wywołanie API”, a nie klasyczne usunięcie urządzenia (TDR daje zwykle
  887a0005/0006). Sama linia `Device failed error (887a0001)` nie dowodzi, że GPU „padło”; mówi, że Unity potraktowało ten HRESULT
  jako błąd krytyczny. Czy w logu była też linia `Device removed reason (…)` — nieznane (brak logu).

### 1.2 Unity — dokumentacja
- **„Troubleshoot D3D12 GPU crashes on Windows” (6000.3):** typy: GPU timeout (TDR), GPU page fault (np. bufor zwolniony przed
  końcem pracy GPU), crash sterownika (UMD, dla NVIDIA `nvwgf2umx.dll`), crash GPU („often caused by the GPU running out of
  dedicated video memory”). Znaczniki w logu: `GfxDeviceWorker::RunGfxDeviceWorker`, `D3D12Fence::Wait`,
  `Device failed error (887a0006)`, `Device removal`, `d3d12: GfxDevice was not out of Local memory`. Szczegółowe logi:
  **Windows 11 + „Graphics diagnostics tools”** + argumenty `-force-d3d12-debug` (i dla edytora `-force-d3d12-editor-pix-events`);
  `-force-d3d12-debug-gbv` dopiero jako drugi krok (GPU-based validation, duże logi). „These arguments enable Microsoft's Device
  Removed Extended Data (DRED) API”. Format: `d3d12 validation error: …`, `d3d12 DXGI error: …`. Wykluczenia systemowe:
  nakładki (Discord, Steam, MSI Afterburner), podkręcanie, aktualizacja OS/sterownika, czyste instalacje sterownika, czyszczenie
  cache shaderów (`%LOCALAPPDATA%\NVIDIA\DXCache`, `%LOCALAPPDATA%\D3DSCache`), fallback DX11 przez D3D12 Device Filtering Asset.
  — https://docs.unity.com/en-us/engine/6000.3/manual/platform-specific/windows/develop/troubleshoot-gpu-crash.md
- **„Player command line arguments” (6000.3):** udokumentowane `-force-d3d11`, `-force-d3d12`, `-force-d3d11-flip-model`,
  `-force-d3d11-bitblt-model`, `-force-d3d11-(no-)singlethreaded`, `-force-device-index`, `-logFile <path>`,
  `-window-mode exclusive|borderless`, `-screen-fullscreen 0|1`, `-single-instance`. **`-force-d3d12-debug`, `-force-d3d12-debug-gbv`
  i `-force-gfx-jobs` NIE są na tej stronie** (dwa pierwsze są tylko na stronie troubleshootingu wyżej; `-force-gfx-jobs`:
  `UNVERIFIED` — nie znaleziono w dokumentacji 6000.3, nie używać w planie).
  — https://docs.unity.com/en-us/engine/6000.3/manual/unity-editor/command-line-arguments/player
- **D3D12 Device Filtering Asset:** domyślnie Unity odmawia D3D12 przy FL < 12.1, ≤ 4 rdzeniach, < 3600 MB VRAM, iGPU Intel/AMD;
  zezwala przy FL 12.2+. Odrzucone urządzenia biorą domyślne API z Player Settings. Reguły mogą dotyczyć m.in. wersji sterownika
  i nazwy GPU (regex). — https://docs.unity.com/en-us/engine/current/manual/introduction-d3d12-device-filtering-asset
- **Log/crash playera:** `Player.log` w `%USERPROFILE%\AppData\LocalLow\<Company>\<Product>\` (u nas `woogitsugames\Kamion`),
  folder crashy — `CrashReporting.crashReportFolder`.
  — https://docs.unity.com/en-us/engine/6000.3/manual/get-started/project-configuration/log-files.md
- DX12 domyślnym API nowych projektów od Unity 6.1 (blog Unity, kwiecień 2025):
  https://unity.com/blog/directx-12-improvements-in-unity-6 (treść z wyników wyszukiwania; strona nie pobrana w całości).

### 1.3 Unity — release notes 6000.3.x (pełne listy z mirrora `sator-imaging/Unity-ReleaseNotes`, przefiltrowane `dx12|d3d12|dxgi|device|swapchain|pipeline cache`)
Źródło: `https://raw.githubusercontent.com/sator-imaging/Unity-ReleaseNotes/main/Unity6.3/6000.3.<n>/Unity_6000.3.<n>f1_LTS.md`
(n = 0…28; 6000.3.28f1 opublikowany 2026-11-03; `whats-new/6000.3.29f1` i `.30f1` na unity.com zwracają 404 → **6000.3.28f1 jest
najnowszym patchem LTS**). Oryginały: `https://unity.com/releases/editor/whats-new/6000.3.<n>f1`.

| Wersja | Wpis (cytat skrócony) | Znaczenie dla nas |
|---|---|---|
| 6000.3.1f1 | „DX12: … Now we shut down the app as early as possible after a DX12 crash, so that log messages, callstacks and DRED outputs are only relevant to the original GPU error.” | log powinien zawierać właściwą przyczynę + DRED |
| 6000.3.9f1 | „DX12: Fixed crashes related to scratch memory allocation” (UUM-131707, UUM-131824 *Crash on CheckDeviceStatus when moving in the scene view*); async compute fence waits w render passach (UUM-105302) | już mamy |
| **6000.3.11f1** | „DX12: Added Direct3D Graphics Infrastructure (DXGI) errors to the user logs that were not covered by validation errors. **Fixed false-reporting of non-error return codes (i.e., 087a0001) in CheckDeviceStatus()**.” + „Fixed a player hang after switching window focus.” | Unity przyznaje, że `CheckDeviceStatus` traktował kod 0x087A0001 (OCCLUDED) jak błąd. Nasz kod to **8**87a0001 — czy to ten sam problem w innej postaci, czy inny: `UNVERIFIED` |
| 6000.3.13–14f1 | UUM-138597 *Crash on CheckDeviceStatus when selecting GameObjects… DX12* → „Performed periodic full flushes when too many command buffers were pending”; „Reduced critical crashes when minimizing (via Alt-Tab) "Exclusive Fullscreen" … consider using "FullScreenWindow" (borderless)” | my już jesteśmy w borderless |
| 6000.3.15–18f1 | wyciek fence’ów D3D12 w dużych scenach; „Fixed crash on DX12, when performing memory-heavy operations” (17); async compute w Render Graph `AddComputePass … EnableAsyncCompute(true)` → crash `D3D12SwapChain::Present` naprawiony (18, UUM-140183) | już mamy; my nie używamy własnego async compute |
| 6000.3.23f1 | VRAM małych tekstur nie był zwracany sterownikowi (parametr boot config `d3d12-small-texture-tiles-per-heap`) | już mamy |
| 6000.3.27f1 | „Fixed a random crash on Windows when using the Direct3D12 graphics API, caused by a use-after-free when releasing GPU buffers.” | już mamy |
| 6000.3.28f1 | crash przy wielokrotnej aktualizacji dużej tekstury w klatce; „The Editor no longer crashes with an out-of-memory failure or a GPU device reset when a single repaint renders a scene with extreme per-frame draw volume … `d3d12-scratch-flush-threshold`” | to nasza wersja |

**Wniosek:** w gałęzi 6000.3 nie ma nowszego patcha z poprawkami D3D12. Release notes 6000.4/6000.5 nie zostały przejrzane
w całości (mirror ma inną strukturę nazw, nie pobrałem) — **czy 6000.4.x ma coś nowego dla `887a0001`/Present: nieustalone**.

### 1.4 Unity Issue Tracker / Discussions (tylko realnie otwarte strony)
- **UUM-148214** „Player crash on "UnityMain" when rapidly switching app focus in Fullscreen window mode while using DirectX12” —
  **status: Closed, Third Party Issue**. Found in 6000.0.73f1, 6000.0.80f1, **6000.3.21f1**, 6000.5.6f1, 6000.6.0b6, 6000.7.0a3.
  Stos: **`D3D12SwapChain::Present` zwraca HRESULT 0x887A0001** → `CheckDeviceStatus` → błąd krytyczny; wątek
  `GfxTaskExecutorD3D12::DoPresent`. „Does not occur with DX11, only in fullscreen mode”, Windows 11; repro przez szybkie
  przełączanie fokusu (klik na drugim ekranie / Alt+Tab), crash po 15–45 s. Notatka Unity: „the issue originates from a third-party
  asset, plugin, or service, rather than Unity itself” (bez wskazania, jaki).
  — https://issuetracker.unity.com/issues/23712/player-crash-on-unitymain-when-rapidly-switching-app-focus-in-fullscreen-window-mode-while-using-directx12
- **UUM-134743** „Player crash when switching focus in Exclusive Fullscreen mode with DirectX 12” — Fixed in 6000.3.14f1 (też
  6000.0.73f1, 6000.4.3f1, 6000.5.0b4, 6000.6.0a2); tylko DX12 + exclusive; DX11/Vulkan bez problemu.
  — https://issuetracker.unity.com/issues/21431/player-crash-when-switching-focus-in-exclusive-fullscreen-mode-with-directx-12
- **UUM-147012** „Editor device-removal Crash on CheckDeviceStatus when Editor is under heavy load” — **Open**; reproducible m.in.
  6000.3.18f1, 6000.5.3f1, 6000.6.0b3, 6000.7.0a2; DX12 (nie DX11), Windows 11, RTX 3080, sterownik 610.74 / 596.21;
  stos `CheckDeviceStatus` ← `D3D12CommandList::PrepareExecute` ← `GfxTaskExecutorD3D12`. Brak obejścia poza DX11.
  — https://issuetracker.unity.com/issues/23402/editor-device-removal-crash-on-checkdevicestatus-when-editor-is-under-heavy-load
- **UUM-107390** „Crash on D3D12SwapChain::Present when performing various Unity operations” — Closed, Won't Fix (6.1–6.4),
  stosy w `nvwgf2umx`/`amdxc64` (UMD).
  — https://issuetracker.unity.com/issues/19304/crash-on-d3d12swapchainpresent-when-performing-various-unity-operations
- **UUM-92417** „D3D12 PSO disk cache feature crashes if paths contain non-ASCII characters” — Fixed w 6.1.X/6.2.X (Won't Fix 6.0);
  stos przy zamykaniu `PipelineUtilities::WriteData` ← `D3D12PipelineCacheLibrary::SaveCache` ← `~GfxDeviceD3D12`. Ta sama
  ścieżka co ADR 0051, ale inna przyczyna (wyjątek `create_directories`, my mamy access violation w `D3D12Core`) — poprawka jest
  przed naszą wersją, więc to **inny** błąd tej samej ścieżki (ocena).
  — https://issuetracker.unity.com/issues/2500/d3d12-pso-disk-cache-feature-crashes-if-paths-contain-non-ascii-characters
- Wątek „Unity 6.3+ Windows Player crashes on Alt+Tab when Discord is running (D3D12) — CASE IN-129682” (sty–mar 2026): staff
  (Tautvydas-Zilys, 4.02.2026) — dumpy pokazują „D3D12 device removal crash”; **obejście dla debug layer w buildzie release:
  skopiować `d3d12SDKLayers.dll` z folderu D3D12 edytora do folderu `D3D12` obok exe** („normally only ships with development
  builds”); błąd `d3d12: could not get the debug interface (0x887a002d)` = brak „Graphics Tools” w Windows; staff (eafanas,
  13.03.2026) poleca NVIDIA Nsight Aftermath, czystą instalację sterownika, test `-window-mode borderless`; reporter: włączenie
  **„Run In Background” usuwa crash** (przyczyna w tym przypadku: `UIAutomationCore.dll` na głównym wątku, błąd Windows).
  — https://discussions.unity.com/t/unity-6-3-windows-player-crashes-on-alt-tab-when-discord-is-running-d3d12-case-in-129682/1702606
  i `?page=2`
- Wątek „DX12 Graphics Crash in Editor, Force DX11 Fixes It” (6000.3.1–6000.3.9, URP, RTX 2060 S, sterowniki 591.74/581.57):
  `DXGI_ERROR_DEVICE_HUNG`, `Device removed reason (887a0006)`, ~900 błędów walidacji „deleted ScratchBufferInternal resource”;
  obejścia: `-force-d3d11` (najskuteczniejsze), wyłączenie HAGS (anegdota), reinstalacja sterownika z „force firmware reset”
  (anegdota); kilka osób: problem dalej na 6000.3.9f1. — https://discussions.unity.com/t/dx12-graphics-crash-in-editor-force-dx11-fixes-it/1703990

### 1.5 Microsoft — TDR, DRED, zrzuty
- **TDR:** domyślny limit **2 s**; po resecie Windows loguje „Display driver stopped responding and has recovered” w Event Viewer;
  ≥ 5 hangów w 60 s → bugcheck 0x117. — https://learn.microsoft.com/en-us/windows-hardware/drivers/display/timeout-detection-and-recovery
- **Klucze TDR** (`HKLM\System\CurrentControlSet\Control\GraphicsDrivers`: `TdrDelay` dom. 2, `TdrDdiDelay` dom. 5, `TdrLevel` dom. 3,
  `TdrLimitTime` 60, `TdrLimitCount` 5): „End users shouldn't manipulate these registry keys. Applications shouldn't manipulate these
  registry keys outside of targeted testing or debugging” — **tylko diagnostycznie, nigdy w instrukcji dla gracza**.
  — https://learn.microsoft.com/en-us/windows-hardware/drivers/display/tdr-registry-keys
- **DRED:** auto-breadcrumbs (2–5 % kosztu, domyślnie wyłączone) + raport page fault (obiekty istniejące/niedawno zwolnione pod
  adresem błędu); włączane przez `ID3D12DeviceRemovedExtendedDataSettings` **przed** utworzeniem urządzenia; odczyt
  `ID3D12DeviceRemovedExtendedData`; w debuggerze eksport `d3d12!D3D12DeviceRemovedExtendedData` + rozszerzenie WinDbg z
  `github.com/microsoft/DirectX-Debugging-Tools`; od Windows 10 1903 zdarzenia device-removed idą do WER, a DRED bywa
  automatycznie włączany dla konfiguracji z wieloma zdarzeniami. — https://learn.microsoft.com/en-us/windows/win32/direct3d12/use-dred
  Unity: `-force-d3d12-debug` włącza DRED (§1.2). Czy Unity w buildzie release bez argumentu włącza DRED: `UNVERIFIED`.
- **WER LocalDumps:** domyślnie wyłączone; `HKLM\SOFTWARE\Microsoft\Windows\Windows Error Reporting\LocalDumps`, `DumpFolder`
  dom. `%LOCALAPPDATA%\CrashDumps`, `DumpType` 1 = mini (dom.), 2 = full; klucz per-exe `LocalDumps\Kamion.exe`. Skoro dump
  właściciela leży w `%LOCALAPPDATA%\CrashDumps`, LocalDumps jest u niego włączone (ocena). Czy minidump zawiera dane DRED
  (pamięć sterty procesu): `UNVERIFIED` — do odczytu DRED pewniejszy jest full dump.
  — https://learn.microsoft.com/en-us/windows/win32/wer/collecting-user-mode-dumps

### 1.6 NVIDIA
- **32.0.16.1088 = GeForce 610.88**: DriverCloud — pakiet `610.88-…-dch-international.exe` zawiera 20 INF-ów display w wersji
  **32.0.16.1088** (data INF 2026-07-22). — https://www.driverscloud.com/en/services/GetInformationDriver/77107-0/nvidia-61088-data-center-tesla-desktop-win10-win11-64bit-dch-internationalexe
  Microsoft Update Catalog: „NVIDIA Display Driver Update (32.0.16.1088)” z 2026-07-21 (wg wyników wyszukiwania, strona katalogu nie
  pobrana). Reguła ogólna (ostatnie 5 cyfr wersji WDDM = numer NVIDIA): przykład 21.21.13.7892 ↔ 378.92 —
  https://forums.tomshardware.com/threads/every-nvidia-driver-has-two-version-numbers-which-is-the-real-one.3106663 (forum).
- **610.88 WHQL Game Ready, 2026-07-28**: poprawki m.in. crashy RTX 50 w jednym tytule (Release 610), długich pauz w DX12 w jednym
  tytule, crashy przy wyjściu w dwóch tytułach; znany problem „Prefer Maximum Performance” może nie być stosowane. **Nic o Unity,
  ogólnym device removed ani TDR na RTX 50.** — https://www.thefpsreview.com/2026/07/31/nvidias-610-88-whql-driver-adds-dlss-rtx-support-for-halo-campaign-evolved-and-the-gears-of-war-e-day-beta-plus-fixes-rtx-50-crashes/
  (oficjalny PDF release notes nie pobrany — guru3d 403).
- **Nowsze sterowniki istnieją**: wątek elevenforum podaje 621.01 (2026-10-21), 621.14 (2026-11-04) — wg wyników wyszukiwania,
  strona zwróciła 403; **niezweryfikowane z NVIDIA**.
- **Nsight Aftermath**: SDK (D3D12/Vulkan) do zrzutów GPU przy wyjątku/TDR + Aftermath Monitor w Nsight Graphics; Windows 2026.3.0.
  — https://developer.nvidia.com/nsight-aftermath. Czy Monitor łapie zrzuty z aplikacji bez integracji SDK: `UNVERIFIED` (strona nie mówi).
- Event Viewer: **nvlddmkm 153** = reset sterownika przez TDR (strony pomocy/Q&A, nie dokumentacja NVIDIA:
  https://learn.microsoft.com/en-us/answers/questions/2282086/how-to-fix-event-id-153-nvlddmkm); **Display 4101** = „Display
  driver … stopped responding and has successfully recovered” (tylko źródła forumowe, np.
  https://forums.evga.com/GTX-680-Event-ID-4101-14-m2283817.aspx). Numer **nvlddmkm 14**: brak źródła — `UNVERIFIED`.
- Specyfikacja RTX 5070: 12 GB GDDR7 (listingi sklepowe/bazy, nie nvidia.com — wg wyników wyszukiwania, np. https://www.pugetsystems.com/parts/Video-Card/NVIDIA-GeForce-RTX-5070-12GB-Founders-Edition-16032/).

## 2. Znane przyczyny — tabela

Prawdopodobieństwo = **ocena** na podstawie jednej linii logu i kontekstu z HANDOVER; zmieni się po odczycie pełnego logu/dumpa.

| # | Przyczyna | Objaw wg źródła | Źródło | Prawdop. u nas | Uzasadnienie |
|---|---|---|---|---|---|
| 1 | **`Present` zwraca 0x887A0001 przy zmianie fokusu / stanu okna pełnoekranowego na D3D12** (Unity kwalifikuje jako błąd krytyczny) | dokładnie nasz kod; stos `D3D12SwapChain::Present` → `CheckDeviceStatus`; tylko DX12; tylko pełny ekran | UUM-148214 (Closed, Third Party, found in 6000.3.21f1); 6000.3.11f1 release note o fałszywym raportowaniu 087a0001; UUM-134743 | **wysokie** | jedyne publiczne źródło z identycznym HRESULT; u nas pełny ekran borderless, exe startowany przez lidera z procesu w tle (ADR 0261: Windows nie oddaje fokusu takim oknom), więc właściciel musiał przełączać fokus; `runInBackground: 0` → player pauzuje/wznawia przy każdej utracie fokusu. Nie wiadomo, czy był Alt+Tab tuż przed crashem |
| 2 | **Równoległe obciążenie GPU / brak VRAM** (kilka procesów Unity + player na jednej karcie 12 GB) → page fault / TDR / błąd sterownika | `Device removed reason (887a0005/0006/0020)`, `CreateCommandQueue failed 8007000e`, linia o „Local memory” | Unity troubleshooting (GPU crash „often caused by … running out of dedicated video memory”); ADR 0051 (8007000e przy kilku procesach Unity; crash zależny od obciążenia); HANDOVER 15:0x–15:19 (world2, int-h3, int-stream w tym czasie) | **średnie** | warunki pasują („pod obciążeniem GPU”), ale kod 887a0001 nie jest typowym kodem TDR/OOM; rozstrzyga Event Viewer (4101/153 o tej godzinie) i linie `Device removed reason`/`Local memory` w logu |
| 3 | **Błąd backendu D3D12 Unity pod dużym obciążeniem** (otwarty) | `CheckDeviceStatus` ← `PrepareExecute`; tylko DX12 | UUM-147012 (Open, repro 6000.3.18f1); wątek 1703990 (problemy dalej na 6000.3.9f1) | **średnie** | jesteśmy na najnowszym 6000.3.28f1, więc poprawki 6000.3.9–28 już mamy; otwarte zgłoszenie pod obciążeniem nadal dotyczy 6.3 |
| 4 | **Sterownik NVIDIA 610.88 / RTX 50** | crashy DX12 w konkretnych grach | release notes 610.88 (poprawki crashy RTX 50 w jednym tytule); anegdota forum Unity o RTX 50 + DX12 (bez ID) | **nisko-średnie** | brak publicznego znanego błędu 610.88 + Unity; sterownik ma ~4 mies., są nowsze (621.x, niezweryfikowane) — tani test |
| 5 | Nakładki (Discord/Steam/Afterburner/GeForce overlay) przechwytujące Present | crash przy Alt+Tab / Present | Unity troubleshooting; wątek IN-129682; UUM-148214 „third-party … service” | **nisko-średnie** | nie wiemy, co działało u właściciela; wspólny mianownik z #1 |
| 6 | TDR przy długiej klatce (> 2 s pracy GPU) | Display 4101 / nvlddmkm 153, `DEVICE_HUNG` | MS TDR | **niskie** | limit 60 fps, RTX 5070 ~425 fps na postoju (ADR 0261); długa klatka możliwa tylko przy ładowaniu/aktywacji sceny (świat 8 GB treści) — Event Viewer rozstrzygnie |
| 7 | Przełączanie trybu ekranu (exclusive) | crash przy Alt+Tab/zmianie trybu | UUM-134743 (naprawione 6000.3.14f1), release note 6000.3.14 | **niskie** | używamy borderless (wg HANDOVER); zmiana trybu tylko z menu ustawień (`PcSettingsRuntime.ApplyDisplay`) |
| 8 | Crash przy zamykaniu (`D3D12PipelineCacheLibrary::SaveCache`) | access violation w `D3D12Core` przy `Application::Exit` | ADR 0051 (u nas, edytor); UUM-92417 (ta sama ścieżka, inna przyczyna, naprawione przed 6000.3) | **wysokie dla „crash przy zamykaniu 1/5”**, **niezwiązane** z crashem w trakcie jazdy | dump pc-shadows niezanalizowany — trzeba sprawdzić, czy stos ten sam co ADR 0051; jeśli tak, to znany sporadyczny błąd silnika przy teardown |
| 9 | GPU Resident Drawer | — | — | **wykluczone** | `m_GPUResidentDrawerMode: 0` we wszystkich assetach URP |
| 10 | Async compute w Render Graph | crash `D3D12SwapChain::Present` | UUM-140183 (naprawione 6000.3.18f1) | **bardzo niskie** | brak własnych passów/compute; poprawka już w naszej wersji |
| 11 | Wysokie rozdzielczości cieni (4096/8192) | — (brak źródła łączącego z device removed) | — | **niskie** | wkład tylko przez VRAM (#2): atlas 8192² × 4 B ≈ 256 MiB tylko na Ultra (obliczenie, format głębi 32 bit — założenie) |

## 3. Diagnoza — jak zebrać dowody

1. **Najpierw to, co już jest** (maszyna właściciela, zero ryzyka):
   - `Player.log` z crasha: `%USERPROFILE%\AppData\LocalLow\woogitsugames\Kamion\Player.log` (albo `Player-prev.log`, jeśli player był
     uruchomiony ponownie — nazwa `-prev`: `UNVERIFIED`) lub plik z `-logFile`, jeśli lider go podał. Szukać: stosu
     (`D3D12SwapChain::Present` / `DoPresent` → hipoteza #1; `PrepareExecute` / `ExecuteCommandLists` → #3), linii
     `Device removed reason (…)`, `GfxDevice was not out of Local memory`, `d3d12 DXGI error:`.
   - Folder Unity `%LOCALAPPDATA%\Temp\woogitsugames\Kamion\Crashes\Crash_*` (`error.log`, `crash.dmp`, `Player.log`).
   - Dump WER `Kamion.exe.73136.dmp` → WinDbg: `!analyze -v`, `~*k` (stos wątku `GfxDeviceWorker`/`UnityGfxDeviceWorker`); DRED:
     rozszerzenie `d3dred` z https://github.com/microsoft/DirectX-Debugging-Tools (`!d3ddred` — nazwa komendy wg tego repo, nie
     sprawdzona tutaj: `UNVERIFIED`). Bez `-force-d3d12-debug` DRED mógł być wyłączony.
   - Event Viewer z godziny crasha (16.11 ok. 15:2x):
     ```powershell
     Get-WinEvent -FilterHashtable @{LogName='System'; StartTime='2026-11-16 15:00'; EndTime='2026-11-16 16:00'} |
       Where-Object { $_.ProviderName -in 'nvlddmkm','Display' -or $_.Id -in 4101,153 } |
       Format-List TimeCreated, ProviderName, Id, Message
     Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='Application Error','Windows Error Reporting'; StartTime='2026-11-16 15:00'} |
       Where-Object Message -match 'Kamion' | Format-List TimeCreated, Id, Message
     ```
   - Dumpy jądra TDR: `C:\Windows\LiveKernelReports\WATCHDOG\` (lokalizacja z wiedzy ogólnej — `UNVERIFIED`).
   - Dump „crash przy zamykaniu 1/5” z `artifacts/pc-shadows-s23`: porównać stos z ADR 0051.
2. **Uruchomienia diagnostyczne** (exe `artifacts/win/<build>/Kamion.exe`):
   - Warunek wstępny dla debug layer: Windows 11 + funkcja opcjonalna **„Graphics Tools”**; build release potrzebuje
     `D3D12\d3d12SDKLayers.dll` obok exe (staff Unity, IN-129682) — prościej zbudować **development**:
     `pwsh scripts/build-windows.ps1 -Slot -Development -Regions 'knyszyn'` (parametr `-Development` istnieje w skrypcie).
     Bez tego w logu: `could not get the debug interface (0x887a002d)` / „Couldn't activate D3D12 debug layer!”.
   - `Kamion.exe -force-d3d12 -force-d3d12-debug -screen-fullscreen 1 -window-mode borderless -scene knyszyn -logFile C:\kamion-dbg\d3d12-debug.log`
     (debug layer + DRED; spadek FPS oczekiwany). Drugi krok, tylko jeśli pierwszy nic nie da: `-force-d3d12-debug-gbv`.
   - Porównanie API: to samo z `-force-d3d11` zamiast `-force-d3d12 -force-d3d12-debug`. W logu sprawdzić `[BOOT] … api='Direct3D 11'`.
   - Prowokacja hipotezy #1 (wg repro UUM-148214): pełny ekran, przez ~60 s przełączać fokus (Alt+Tab / klik na drugim monitorze);
     osobno D3D12 i D3D11; potem D3D12 z wyłączonymi nakładkami.
   - `nvidia-smi` w tle (pc-metrics już próbkuje VRAM co 1 s; ręcznie np. `nvidia-smi --query-gpu=timestamp,memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv -l 1 > vram.csv` — `UNVERIFIED` składnia pól w tej wersji sterownika).
   - Aftermath (opcjonalnie): Nsight Graphics → Aftermath Monitor; przydatność bez integracji SDK `UNVERIFIED`.
3. **TDR — tylko diagnostycznie, na maszynie dev, z przywróceniem:** `TdrDelay` np. 10 s jako test, czy crash znika, gdy GPU dostaje
   więcej czasu (jeśli znika → praca GPU > 2 s, czyli #6). Wymaga restartu i uprawnień admina; **nigdy dla graczy** (MS).

## 4. Obejścia i ich koszt

| Obejście | Koszt / ryzyko | Uwagi |
|---|---|---|
| **D3D11 jako pierwsze API Windows** (lista Standalone: Direct3D11, Direct3D12 lub sam D3D11) — zmiana `ProjectSettings` → **tylko lider** | nie używamy funkcji wymagających D3D12: GRD wyłączony, brak STP/DLSS, brak własnego compute/async compute, Render Graph i SSAO URP działają też na DX11 (ocena — nie mierzone). Tracimy ewentualny zysk CPU z D3D12/split graphics jobs — **niezmierzony** (wszystkie pomiary PC w repo są na D3D12, ADR 0261). Wymaga pełnego buildu + porównania kadrów VQA (zmiana backendu = inny dowód, ADR 0051) | wątki Unity: `-force-d3d11` to najskuteczniejsze zgłaszane obejście; UUM-148214/134743/147012 — wszystkie „DX11 not affected” |
| D3D12 Device Filtering Asset z regułą deny (np. NVIDIA + wersja sterownika) | precyzyjne, ale bez dowodu, że winny jest sterownik — przedwczesne | wymagałby ADR |
| `-force-d3d11` w skrótach `Kamion-*.cmd` (bez zmiany ProjectSettings) | najtańsze doraźnie; gracz uruchamiający sam exe dalej ma D3D12 | lider już tak uruchamia (HANDOVER 15:2x, 16:5x) |
| `runInBackground: 1` | player renderuje także bez fokusu (koszt GPU w tle, dźwięk) | jedyne udokumentowane obejście crasha przy zmianie fokusu w IN-129682 (inna przyczyna root) — **test, nie decyzja** |
| Wyłączenie nakładek, czysta instalacja sterownika / nowszy niż 610.88 | po stronie użytkownika | Unity troubleshooting; 621.x niezweryfikowane |
| Limit FPS / VSync | już 60 fps; dalsze ograniczanie nie dotyczy #1 | pomocne tylko przy #2/#6 |
| Wyłączenie podejrzanych funkcji URP | GRD już wyłączony; brak innych kandydatów z dowodem | nie zalecane bez pomiaru |
| Aktualizacja Unity | 6000.3.28f1 to najnowszy patch 6000.3; skok na 6000.4 = poza zakresem (decyzja właściciela, `ProjectVersion.txt` zamrożony) | — |
| Nie uruchamiać playera równolegle z buildami/renderami Unity | koszt organizacyjny (kolejka slotu) | zgodne z CLAUDE.md „jeden proces Unity”, ale player też konkuruje o GPU |

## 5. Rekomendacja (Windows)

1. **Do czasu rozstrzygnięcia:** uruchamiać właścicielowi i testerom z `-force-d3d11` (jak dziś). Decyzja o **D3D11 jako
   domyślnym API Standalone w ProjectSettings należy do lidera** — rekomenduję ją, jeśli kroki 1–3 niżej nie wskażą przyczyny po
   naszej stronie, bo (a) wszystkie publiczne pokrewne zgłoszenia 6000.3 mówią „DX11 not affected”, (b) nie używamy żadnej funkcji
   wymagającej D3D12, (c) jesteśmy już na najnowszym patchu 6000.3. Warunek: pomiar `pc-metrics` D3D11 vs D3D12 bez pogorszenia
   budżetu i VQA bez różnic wizualnych. To wymaga ADR (zmiana backendu buildu).
2. Nie zmieniać `TdrDelay` poza testem diagnostycznym; nie włączać filtra urządzeń bez dowodu na sterownik.
3. Pomiarów/odtworzeń nie robić przy równolegle działających procesach Unity (wtedy nie da się oddzielić #1 od #2).

## 6. Kroki lokalne (Windows, właściciel/lider) i co rozstrzyga

| Krok | Komenda | Co rozstrzyga |
|---|---|---|
| L1 | odczyt `Player.log` + `Crashes\Crash_*\error.log` z 16.11 15:2x | stos z `Present`/`DoPresent` → **#1**; `Device removed reason (887a0005/6/20)` lub `Local memory` → **#2/#3** |
| L2 | `Get-WinEvent` z §3 (System, 15:00–16:00) | zdarzenie Display 4101 / nvlddmkm 153 w minucie crasha → TDR/reset sterownika (**#2/#6**); brak → GPU się nie zawiesiło, wzmacnia **#1** |
| L3 | WinDbg na `Kamion.exe.73136.dmp` i dumpie pc-shadows | stos crasha w jeździe; czy crash przy zamykaniu = ADR 0051 (**#8**) |
| L4 | build dev: `pwsh scripts/build-windows.ps1 -Slot -Development -Regions 'knyszyn'` (bez innych procesów Unity), potem `Kamion.exe -force-d3d12 -force-d3d12-debug -screen-fullscreen 1 -window-mode borderless -scene knyszyn -logFile C:\kamion-dbg\d3d12-debug.log`, 10 min jazdy + 60 s przełączania fokusu | błędy walidacji `d3d12 validation error:` wskazujące nasz zasób/pass → **nasz błąd**; crash bez błędów walidacji, ze stosem w `Present` przy zmianie fokusu → **#1** (zgłosić do Unity z repro) |
| L5 | to samo z `-force-d3d11` | brak crasha na D3D11 przy tym samym scenariuszu, a crash na D3D12 → potwierdza wybór D3D11 jako obejścia |
| L6 | L4 na **bezczynnej** maszynie vs L4 z równoległym renderem VQA (`pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High …`) | crash tylko pod równoległym obciążeniem → **#2**; VRAM z `nvidia-smi`/`memory.csv` blisko 12 GB → OOM |
| L7 | `pwsh scripts/pc-metrics.ps1 -Exe <exe> -Scene knyszyn-w -Tier High -Fps 60 -Width 1920 -Height 1080 -Class zalecany -Label d3d12` oraz to samo z `-Extra force-d3d11 -Label d3d11` (w `Player.log` sprawdzić `api=`; przekazanie flagi bez wartości przez `-Extra`: `UNVERIFIED`, skrypt to szkic) | koszt przejścia na D3D11 (p50/p95/p99, VRAM) — warunek rekomendacji §5.1 |
| L8 | `runInBackground` test (tylko jeśli L1/L4 wskażą #1): uruchomienie zbudowane z `runInBackground: 1` w gałęzi testowej lidera | crash znika → przyczyna w ścieżce pauza/wznowienie przy utracie fokusu |
| L9 | (opcjonalnie) sterownik nowszy niż 610.88, czysta instalacja, nakładki wyłączone; powtórzyć L4 | crash znika → **#4/#5** |

## 7. Czego nie ustalono
- Pełnej treści logu i stosu crasha 16.11 (nie ma w repo) — wszystkie prawdopodobieństwa są oceną.
- Czy `887a0001` z naszego logu pochodzi z `Present` (jak w UUM-148214) czy z innego wywołania.
- Domyślnego trybu graphics jobs dla Win64 w 6000.3 przy pustym `m_BuildTargetGraphicsJobMode`; czy Unity w buildzie release
  włącza DRED bez argumentu; istnienia/nazwy `-force-gfx-jobs` w 6000.3.
- Release notes 6000.4.x/6000.5.x pod kątem `887a0001`/`Present` (nie przejrzane w całości).
- Oficjalnych release notes NVIDIA 610.88 (PDF niedostępny) i treści sterowników 621.x; znaczenia zdarzenia nvlddmkm **14**.
- Jaki „third-party” element Unity wskazało w UUM-148214.
- Kosztu wydajności D3D11 vs D3D12 w naszym projekcie (brak pomiaru).
