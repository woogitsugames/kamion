# STATUS d3d11-default-s24 (ADR 0291 / D88: Direct3D 11 domyślne na Windows, D3D12 opcja)
- Kod: `ProjectSetup.WindowsGraphicsApis` = [Direct3D11, Direct3D12] + `ApplyWindowsGraphicsApis()` (z `ApplyPlayerSettings`); test `WindowsGraphicsApiTests` (3).
- Launchery: `Kamion-d3d12.cmd` / `Kamion-korytarz-d3d12.cmd` (-force-d3d12) zamiast *-d3d11; README paczki, JAK-GRAC-PC 1.6, docs/12; pytest tests/dist 49 passed.
- ADR 0291 + README ADR + docs/11 D88; DRAFT-d3d11-default usunięty.
- W toku: setup ApplyAll (Win64) + EditMode Win64 — `artifacts/d3d11-default-s24/run-setup-tests.ps1` (status `setup-tests.status`, wyniki `steps.log`).
- NASTĘPNY KROK: `Get-Content artifacts/d3d11-default-s24/steps.log`; potem build: `pwsh scripts/build-windows.ps1 -Slot -Regions knyszyn` i `pwsh scripts/build-windows.ps1 -SkipBuild -Run -Scene knyszyn -RunSeconds 60 -ShotSeconds 30`.
