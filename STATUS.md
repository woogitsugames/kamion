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

## 23:1x after1 (pierwsza implementacja)
- TailNits 3800 (5,26:1), halo `Kamion/Truck Lamp Halo` (1 quad/emiter, 5 ciągnik + 10 naczepa), plate shoulder 0,55, cab soft shadows (PC), spill zegarów/nawigacji, lift nocą ×0,2, panelGlow 0,015.
- after1: pozycyjne 54,7 → 89,7 R; tablica 205 → 143; kabina noc: deska 12,4 → 5,7, słupek A 17,7 → 6,9 (niebo 12); cienie gładkie (crop). Halo miało ciemny pierścień (wycięcie rdzenia) → after2 bez wycięcia, K 0,25; spill słaby (powierzchnie współpłaszczyznowe z ekranami fizycznie ciemne).
- NASTĘPNY KROK: `pwsh -NoProfile -File artifacts/night-truck-s24/go.ps1 -Name after2 -Unity -Cmd 'pwsh artifacts/night-truck-s24/assets.ps1; ...lamps.ps1 -Tag after2; cab.ps1 -Tag after2; ab.ps1 -Tag after2'`
