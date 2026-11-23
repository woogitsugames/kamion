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
