# STATUS far-forest-look-s24 (daleki plan lasu: smugi kurtyn, perspektywa powietrzna, widok z wysoka; dopiski ADR 0330/0354)

- Worktree `agent-a3176de6fa331c9d3`, galaz `worktree-agent-a3176de6fa331c9d3`. Nie scalac (lider).
- Srodowisko: Library + sceny kafli skopiowane z win-build; `Data/raw/*` = junction do main, `Data/raw/derived/*` junction
  poza prywatnymi kopiami `dw671-tykocin-03`, `knyszyn-w` (w nich nowy far_field.glb). NIE kasowac junctionow Remove-Item.
- [krok 0] UV kurtyn w glb main: shear iso-v <= 14,6 deg. d_extra (TEXCOORD_1.x) obecne.
- [krok 1] Probe (`Editor/VisualQA/FarFieldProbe.cs`, `artifacts/far-forest-look-s24/probe.ps1`): import win-build (z ktorego
  sa obrazy horizon-ring-s24) jest NIEAKTUALNY: atlas 1024x2048 (stary, 9 slotow) przy glb z UV 11 slotow, shear iso-v do 66 deg
  (geometria sprzed r2), las edge-north 144 m od kamery i 9,6 deg wysoki. Po RebuildEdgeBatch z aktualnego derived (bajt w bajt
  = kod HEAD): las 385+ m, 2,1 deg, atlas 1024x4096, shear <= 17 deg. Render PRZED = ten stan (`before/`), stary w `before-stale-winbuild/`.
- [krok 2] Poprawki: Vegetation.shader `_HLOD_EDGE` — v rzutowe (v*H, H; H = wysokosc kolumny w TEXCOORD1.y) we wszystkich
  przebiegach; far_field.py — TEXCOORD_1.y = wysokosc kolumny, pasmo zamglenia per pas kurtyny (mediana d_true) zamiast centroidu
  drzewostanu. Regeneracja far_field obu kafli (prywatnie, ffgen.ps1), RebuildEdge, render PO w toku (`vqa.ps1 -Phase after`).
  pytest far_field/forest: 147 pass, 1 fail PRE-EXISTING (sha glb bialystok-industrial-c w main != manifest; generator nie ruszany dla C).
- NASTEPNY KROK: porownanie before|after (sbs, crop 1:1, stats.txt), EditMode testy, dopiski ADR 0330/0354, raport.
