# STATUS pacing-s24 (rendering-perf, frame pacing P0 bramki 3)

## Krok 1 — analiza danych #5 (24.11 00:15)
- Powtórka „pusty PC” (runs/20261123-223724, start 22:37:24): 597 kl. > 40 ms, ale 579 z nich w dwóch oknach czasu:
  t 2160–2308 s (= 23:13:24–23:15:52) i t 2820–3660 s (= 23:24–23:38). W tych oknach lider startował 5 agentów:
  Library worktree banks2-s24 powstał 23:13:35, monument2-s24 23:15:27, haze-s24 23:36:19 (kopia artifacts od ~23:24,
  tysiące plików), MsMpEng (Defender) skanuje kopie. Pomiar NIE był na pustym PC.
- Dowód „zewnętrzne”: pojazd stoi przy celu (ten sam widok) — t 3540–3600: 54–59 kl. > 40 ms/min, GPU śr. 10,7 ms;
  t 3720+: 0 kl. > 40 ms, GPU 4,9 ms. Ten sam kadr, inne obciążenie maszyny → GPU i CPU gry spowolnione przez inne procesy.
- Skoki NIE są wielokrotnościami 16,67 ms ani 15,625 ms (rozkład ciągły 18–70 ms; VSync off, cap 60) → nie present/vsync
  ani rozdzielczość timera; serie (klatka przed/po skoku średnio 23–31 ms), nie pojedyncze hitche.
- Czysta część (t 10–2150 s, 57 % trasy, 13 kafli): 18 kl. > 40 ms, prawie wszystkie = zdarzenie streamingu (load/unload
  kafla, 40–87 ms, 1 na kafel). To jest realny koszt gry: ekstrapolacja ~30 na 28 kafli → bramka 3 nadal FAIL bez obciążenia.
- Dane: artifacts/pacing-s24/analysis/ (main).

## Krok 2 — narzędzia (WIP)
- scripts/sysload-sampler.ps1 (CPU gry/reszty, top procesy, okno na pierwszym planie, GPU util/zegar/P-state co 1 s ->
  sysload.csv; koszt ~21 ms CPU + 1 nvidia-smi na próbkę), wpięty w build-windows.ps1 -Run i pc-metrics.ps1 (-NoSysload).
- tools/pcperf/pacing_attribution.py (+ test 2/2 zielone): kl. > 40 ms -> clean / contended / unsampled, pacing.json.

NASTĘPNY KROK: gdy PC wolny (brak Unity/Kamion, slot heavy) —
  pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner pacing-s24
  pwsh scripts/pc-metrics.ps1 -Exe <win-build>/artifacts/win/kamion-0.1.0-770ea8d900-regions/Kamion.exe -Scene dw671-tykocin-06 -Tier High -Fps 60 -DurationSeconds 90 -Extra autopilot=route,speed=50,stream=1

## Krok 3 — build #6 + start pomiarów (24.11 ~00:35)
- #6 (artifacts/full-build-6-s24/run): ten sam wzór — pojedyncze skoki ~1/kafel (40–80 ms) + skupiska t 1020–1080
  (20 kl. > 40) i 2340–2520 (100 kl.) przy CPU tła 36–47 % (dane lidera) → zgodne z hipotezą rywalizacji o CPU/GPU.
- PC wolny (0 slotów, 0 Unity) → slot heavy pacing-s24 zajęty; w tle artifacts/pacing-s24/run-experiments.ps1
  (E1 D3D11 bez ramki czysto, E2 + syntetyczne obciążenie robocopy Library + 4 pętle CPU, E3 D3D12, E4 okno 1600x900,
  E5 VSync 1), log artifacts/pacing-s24/experiments.log, wyniki artifacts/pacing-s24/runs/*/ (pc-report.md, pacing.json).
NASTĘPNY KROK: Get-Content artifacts/pacing-s24/experiments.log -Tail 30 ; po końcu slot zwalnia się sam.

## Krok 4 — pomiary A/B (24.11 09:24–, build #5, dw671-tykocin-06, High60, 1920x1080 bez ramki, autopilot 50, 80 s)
- E1 D3D11 czysto: 0 kl. > 33,3 ms, p99 16,67, max ≤ 33 (inne procesy śr. 6,6 % CPU).
- E2 D3D11 + robocopy Library + 4 pętle CPU (inne procesy 44 % CPU maszyny, jak tło #6): 0 kl. > 33,3 ms, max 23,3 ms.
  → samo obciążenie CPU/dysku 44 % NIE wywołuje skoków. Gra nie była na pierwszym planie w E1/E2 (fg=claude) — też bez skutku.
- E3 D3D12: 4 kl. > 40 ms (zgodne z ADR 0291: D3D12 gorszy).
- W toku: E4 okno 1600x900, E5 VSync 1; dodany E6 = drugi player na GPU (zastępstwo renderu innego agenta).
NASTĘPNY KROK: pwsh artifacts/pacing-s24/run-experiments.ps1 -Only E6  (po końcu E5, slot heavy)
