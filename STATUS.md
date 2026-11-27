# STATUS far-forest-look-s24 (daleki plan lasu: smugi kurtyn, perspektywa powietrzna, widok z wysoka; dopiski ADR 0330/0354)

- Worktree `agent-a3176de6fa331c9d3`, galaz `worktree-agent-a3176de6fa331c9d3`. Nie scalac (lider).
- Srodowisko: Library + sceny kafli skopiowane z win-build; `Data/raw/*` = junction do main, `Data/raw/derived/*` junction
  poza prywatnymi kopiami `dw671-tykocin-03`, `knyszyn-w` (w nich nowy far_field.glb). Junctiony odpinac `cmd /c rmdir`.
- [krok 0-1] Probe (`Editor/VisualQA/FarFieldProbe.cs`): import win-build (zrodlo obrazow horizon-ring-s24) NIEAKTUALNY —
  atlas 1024x2048, geometria sprzed r2 (shear v do 66 deg), las 03 edge-north 144 m / 9,6 deg. Aktualne derived: 385+ m, 2,1 deg.
- [krok 2] Poprawki: (a) Vegetation.shader `_HLOD_EDGE` v rzutowe (v*H, H w zw uv; H = TEXCOORD1.y); (b) far_field.py:
  TEXCOORD_1.y = wysokosc kolumny + pasmo zamglenia per pas; (c) RegionImporter.LoadForEdge odswieza material `*_far_atlas`
  (wczesniej stary atlas zostawal po przebudowie krawedzi).
- [krok 3] Render before|after (03 + knyszyn-w, High clear/overcast, -Neighbours auto, diag, zoom) — drawsEst/trisK identyczne
  na 42 kamerach; A/B mgly (hazeGroundFactor=10) potwierdza mgle na kurtynach. EditMode 1448/0/152. pytest far_field 147/1
  (fail istniejacy: sha glb C w main). Dopiski ADR 0330 (dopisek 3) i 0354. KONIEC zadania agenta.
- NASTEPNY KROK (lider): review + scalenie; potem `far_field.py --region <id>` dla wszystkich kafli i RebuildEdgeBatch
  (`Unity -batchmode -executeMethod Game.World.Import.WorldEdgeBuilder.RebuildEdgeBatch -region <id> -buildTarget Win64`)
  w win-build; ponowny render dowodow ADR 0354.
