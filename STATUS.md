# STATUS gpu-ab-0241 (F8, ADR 0241, B-113)
- [krok 1] C#: `GpuAbOverrides.cs` (rq_depthtex, rq_opaquetex, rq_impostors, rq_hlodpart, rq_abtag) + 3 haki jednowierszowe
  (RenderOverrides.Any/Parse, QualityProfileApplier.ApplyPipelineOverrides) + `GpuAbOverridesTests.cs` (EditMode). NIESKOMPILOWANE w chmurze.
  NASTĘPNY KROK: katalog wariantów + parser + pytest: `uv run --project tools/worldgen --with pytest pytest tests/gpu_ab -q`
- [krok 2] katalog `tools/perf/gpu-ab-variants.json` (26 wariantów, 14 domyślnych, szacunki ESTIMATED/UNVERIFIED ze źródłem) + parser
  `tools/perf/src/perfgate/gpuab.py` + `tools/perf/tests/test_gpuab.py` (17 testów, dane syntetyczne) — perf 60/60 PASS.
  NASTĘPNY KROK: `scripts/gpu-ab-a16.ps1`, potem `pwsh scripts/gpu-ab-a16.ps1 -DryRun` u lidera.
- [krok 3] `scripts/gpu-ab-a16.ps1` (plan blokowy baza+warianty, temp. < 36 °C, keyguard, PHONE_RUN, tag `[GPUAB] abtag=`), parser paruje po `block`
  (18 testów gpuab). Skrypt PS NIE uruchomiony ani nie sparsowany w chmurze (brak pwsh).
  NASTĘPNY KROK: ADR 0241 + PR; lider: `pwsh scripts/gpu-ab-a16.ps1 -DryRun`.
