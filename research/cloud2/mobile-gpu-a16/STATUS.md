# STATUS — R8 mobile-gpu-a16

## 2026-11-14 krok 0
- Worktree + gałąź research/cloud2-mobile-gpu-a16 z origin/main 81c9bae.
- Przeczytano stan repo: PERFORMANCE_BUDGETS, DEVICE_MATRIX, ADR 0013/0046/0106/0113/0136/0153/0177, GATE12 A16, URP_Low + QualityProfile Low.
- Następny krok: `cd /workspace/wt/mobile-gpu-a16 && ls research/cloud2/mobile-gpu-a16` → zbieranie źródeł (spec Mali-G57, gpuinfo, Arm BPG).

## 2026-11-14 krok 1 — źródła sprzętowe
- Pobrane (files/, poza gitem): MediaTek G99 (strona), Arm GPU Datasheet 2024 (PDF, 3 s., obejrzane s.1–2), Arm GPU Best Practices 101897 Issue 10 (PDF 135 s.; przeczytane s.21–23, 48, 56–62, 66–67, 75–77, 94–95, 104), gpuinfo: raporty 53265/53260 (SM-A165F), 52490 (SM-S926B), listy raportów; Samsung Exynos 2400 (strona).
- Ustalenie: S24+ właściciela = SM-S926B, Exynos 2400 (s5e9945, repo DEVICE_MATRIX), gpuinfo: 7/8 raportów SM-S926B = Xclipse 940.
- Ustalenie kluczowe: datasheet Arm — 2xMSAA na Mali-G57 „Automatically promoted to 4xMSAA”.
- Następny krok: `cd /workspace/wt/mobile-gpu-a16` → źródła Unity (URP docs, Issue Tracker), Vulkan-Samples, Adreno/AMD, narzędzia (Streamline, AGI).

## 2026-11-14 krok 2 — źródła technik i problemów
- Pobrane: Unity URP docs (configure-for-better-performance, anti-aliasing, URP asset), Unity Android Player settings + ScriptReference AndroidBlitType, UnityCsReference (enum AndroidBlitType Always=0), Unity Issue Tracker JSON (UUM-147578, -137912, -28518, -107530), Khronos Vulkan-Samples (msaa, render_passes, subpasses; commit b4fb432), Qualcomm Adreno mobile best practices (md), AGI supported devices, Arm learn (Performance Studio free, Development Build), libGPUCounters README, gsmmaniak (S24+ PL = Exynos 2400).
- NOWE w repo: ProjectSettings `androidBlitType: 0` = Always (dodatkowy blit pełnoekranowy w natywnej rozdzielczości) — kandydat nr 1.
- Następny krok: `cd /workspace/wt/mobile-gpu-a16/research/cloud2/mobile-gpu-a16 && python3 make_manifest.py` (pisanie manifestu).
