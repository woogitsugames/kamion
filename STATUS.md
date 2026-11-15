# STATUS — G2 perf-loop-0244 (chmura G, s21)
- Krok 1: audyt 47 plików z metodami co klatkę/krok → `docs/adr/0244-audyt-petli-jazdy-zero-gc-koszt-cpu.md` (5 poprawek, 14 znalezisk z priorytetem, plan pomiaru A16).
- Krok 2: poprawki: `FrameCsvFormat` (frametimes.csv bez alokacji + brakujące kolumny mirror_n/ab), `KamionHeadlamps.Resolve` bez FindObjectsOfTypeAll+LINQ, `CabInteriorLighting` throttling wyszukiwania środowiska (DrivingLab), cache id shaderów, `TryGetComponent`.
- Testy w chmurze: `dotnet test tools/loop-runner/Tests/LoopTests.csproj -c Release` 30/30, `dotnet test tools/physics-runner -c Release` 277/277; Roslyn: 0 błędów składni w 9 plikach C#. Unity EditMode/PlayMode NIEuruchomione (brak Unity).
- NASTĘPNY KROK (lider): `pwsh scripts/test.ps1 -Platform EditMode; pwsh scripts/test.ps1 -Platform PlayMode` → APK `-Development` A (main) / B (ta gałąź) → Profiler GC Alloc wg ADR 0244 §Plan.
