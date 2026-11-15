# STATUS gpu-ab-0241 (F8, ADR 0241, B-113)
- [krok 1] C#: `GpuAbOverrides.cs` (rq_depthtex, rq_opaquetex, rq_impostors, rq_hlodpart, rq_abtag) + 3 haki jednowierszowe
  (RenderOverrides.Any/Parse, QualityProfileApplier.ApplyPipelineOverrides) + `GpuAbOverridesTests.cs` (EditMode). NIESKOMPILOWANE w chmurze.
  NASTĘPNY KROK: katalog wariantów + parser + pytest: `uv run --project tools/worldgen --with pytest pytest tests/gpu_ab -q`
