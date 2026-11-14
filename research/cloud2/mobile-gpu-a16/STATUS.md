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

## 2026-11-14 krok 3 — manifest
- make_manifest.py → manifest.csv: 134 wiersze (SOURCED 117, UNVERIFIED 13, ESTIMATED 4); kategorie: technika 43, sprzęt 28, vulkan 18, stan 17, plan 16, narzędzie 6, problem 6.
- Następny krok: `cd /workspace/wt/mobile-gpu-a16/research/cloud2/mobile-gpu-a16` → fetch.py, sources.md, audit_20_percent.json, README.md.

## 2026-11-14 krok 4 — fetch.py + samokontrola
- fetch.py: 36 plików OK lokalnie (9,4 MB); test w izolowanej kopii: PDF Arm + pliki przypięte OK, 8 stron dynamicznych CHANGED (oczekiwane, ostrzeżenie).
- audit.py → audit_20_percent.json: seed 20261114, k=27/134, ponowne POBRANIE z sieci; 26 PASS / 1 FAIL (R8-029: cytat z dwóch raportów pod jednym URL — poprawiono, + ten sam błąd w wierszu maxBoundDescriptorSets). 3 wiersze datasheet sprawdzone przez ponowne obejrzenie stron PDF (audit_manual.json).
- Pełna kontrola wszystkich cytatów vs pliki lokalne: tylko wiersze z komórek tabel (datasheet, lista JSON) nie są dosłownym ciągiem — opisane w metodzie.
- Następny krok: `cd /workspace/wt/mobile-gpu-a16/research/cloud2/mobile-gpu-a16` → sources.md + README.md.

## 2026-11-14 krok 5 — README + sources (gotowe do recenzji)
- README.md (specyfikacje, tabela technik, problemy Unity, ranking P1–P12 + „nie robić”, co nowe/luki), sources.md (25 źródeł + repo).
- Wynik: 134 wiersze; audyt 26 PASS / 1 FAIL (poprawiony); fetch.py 27 plików / 9,4 MB.
- Następny krok (lider/rendering-perf, na telefonie): `pwsh scripts/build-android.ps1` ×2 (androidBlitType 0 vs 2, ten sam versionCode) → `pwsh scripts/device-metrics.ps1 -Launch -DurationSeconds 90` G3-A/G3-B (P1); RenderDoc for Arm GPUs: próbki MSAA przy msaa=2.
