# STATUS — pc-gates-0266 (H4, ADR 0266: bramki i budżety PC)

Agent chmurowy (bez Unity/dotnet/pwsh; Python przez uv). Gałąź `pc-gates-0266` od `origin/main` ae372b19c.

- [15.11] Start. Przeczytane: CLAUDE.md, AGENT-RULES, D56/D67–D73, ADR 0260, HANDOVER s22, docs/01/03/09/10, device-metrics.ps1, Telemetry/*. NASTĘPNY KROK: przepisać docs/03 pod PC.
- [15.11] docs/03 przepisany pod PC (klasy min/zalecany/wysoki, wszystko WORKING_VALUE, 🔒 mobilne zostają). NASTĘPNY KROK: tools/pcperf (budżety JSON + parser + pytest).
- [15.11] C#: Telemetry/PcMetricsMath.cs (percentyle, opcje CLI), Telemetry/PcFrameMetricsRecorder.cs (samostartujący przy -metrics, zero GC, zapis na końcu), Tests/EditMode/PcMetricsMathTests.cs (NIEuruchomiony — brak Unity). NASTĘPNY KROK: tools/pcperf parser + pytest.
- [15.11] tools/pcperf: pc_metrics.py (stdlib) + budgets/pc-budgets.json + README; pytest 27/27 (uv run --no-project --with pytest pytest tools/pcperf/tests -q). NASTĘPNY KROK: scripts/pc-metrics.ps1.
- [15.11] scripts/pc-metrics.ps1 (SZKIC, nieuruchomiony — brak pwsh/Windows): Start-Process playera z -metrics, próbki RAM/VRAM (CIM GPUProcessMemory) + nvidia-smi, parser. Recorder: zrzut screen.png + odroczone Quit. NASTĘPNY KROK: docs/01, docs/10, PERFORMANCE_BUDGETS, ADR 0266.
- [15.11] docs/01 + docs/10 (D73, §3a pytania DLC/dystrybucja), PERFORMANCE_BUDGETS (sekcja PC), ADR 0266. pytest 27/27. NASTĘPNY KROK: przegląd diffu + PR.
