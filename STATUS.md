# STATUS gpu-ab-0241 (F8, ADR 0241, B-113) — GOTOWE do weryfikacji lidera
- C#: `Rendering/Runtime/GpuAbOverrides.cs` (rq_depthtex, rq_opaquetex, rq_impostors, rq_hlodpart, rq_abtag) + haki jednowierszowe w
  `RenderOverrides.cs` / `QualityProfileApplier.cs`; `Tests/EditMode/GpuAbOverridesTests.cs` (19 przypadków). NIESKOMPILOWANE w chmurze.
- Dane/narzędzia: `tools/perf/gpu-ab-variants.json` (26 wariantów, 9 domyślnych), `tools/perf/src/perfgate/gpuab.py`,
  `tools/perf/tests/test_gpuab.py` (18) — `uv run --project tools/perf pytest tools/perf/tests -q` = 61 passed.
- `scripts/gpu-ab-a16.ps1` — NIE uruchomiony i NIE sparsowany (brak pwsh w chmurze). ADR `docs/adr/0241-gpu-ab-a16-low.md`.
- Ustawienia domyślne bez zmian (QualityProfile.cs/.asset, ProjectSetup.cs, URP, ProjectSettings nietknięte).
- NASTĘPNY KROK (lider): `pwsh scripts/test.ps1 -Platform EditMode` → `pwsh scripts/build-android.ps1` →
  `pwsh scripts/gpu-ab-a16.ps1 -DryRun` → `pwsh scripts/gpu-ab-a16.ps1 -Apk artifacts/apk/kamion-<ver>-<sha>.apk -Mode Camera -Uncapped`
