# truckdata-0201 (ADR 0201) — live
- 14.11: worktree + gałąź z main; baseline .NET testy 274/274; docs errata (docs/04 315/80, VRD S5 /115 40 km/h + S9, PV w.6 ≤ 52,4 m, scenariusz air_leak_rear_circuit max 52.4).
- NASTĘPNY KROK: baseline runner → `$env:DOTNET_ROOT='C:\Users\matma\AppData\Local\Microsoft\dotnet'; & $env:DOTNET_ROOT\dotnet.exe run -c Release --project tools/physics-runner/Runner -- --out artifacts/truckdata-0201/before`
