# STATUS night-truck-s24 (ADR 0297)

## 2026-11-18 22:5x baseline
- Worktree + Library (robocopy z win-build) + LOD0 kabiny; Truck/Trailer BuildBatch OK; build-lab Win64.
- Baseline (artifacts/night-truck-s24/base, base-lamps.txt, base-cab.txt): pozycyjne ciągnik High noc 54.7 R (stop 192.9, 14:1 lin),
  tablica naczepy 205 (max 254), pierścień obudowy 9.2 bez zmiany przy stopie; kabina noc High: niebo 12.0, deska 12.4, słupek A 17.7, droga 8.2.
- Przyczyny: tablica nie jest ograniczona wobec lamp (limiter tylko na lampach); brak poświaty (bloom wyłączony, lampy display-limited);
  noc kabiny = mnożnik lokalnego podbicia cieni (_CabShadowLift k=8) + jednolity panelGlow × albedo (jasna tapicerka słupka A);
  schodkowe cienie = CabInterior.shader bez wariantów _SHADOWS_SOFT (twarde 1 próbka niezależnie od tieru).
- NASTĘPNY KROK: implementacja (halo shader, plate shoulder, TailNits, spill zegarów, soft shadows w CabInterior), potem
  `pwsh -NoProfile -File artifacts/night-truck-s24/go.ps1 -Name after1 -Unity -Cmd '...assets.ps1; lamps.ps1 -Tag after1; cab.ps1 -Tag after1'`
