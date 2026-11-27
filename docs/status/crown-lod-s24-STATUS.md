# STATUS crown-lod-s24 (korony drzew: stipple na krawędziach + rozmyta plama LOD; krytyk build #10 TOP 3)

- Worktree `agent-a380c075164a3cedd`, gałąź `worktree-agent-a380c075164a3cedd`. Nie scalane, nie pushowane.
- Środowisko: Win64 `game/Library` + `game/Assets/_Generated` (tylko `knyszyn-w`) skopiowane z worktree tree-species-s24
  (a492e5af); derived main nietknięte (bez importu). Kamery: `artifacts/crown-lod-s24/cams.json` (widok spawnu build #10).
- [krok 0] Analiza: Vegetation.shader NIE ma LOD crossfade (zero `LOD_FADE_CROSSFADE`); WorldInstances przełącza LOD
  twardo (High: LOD0 < 20 m, LOD1 < 60 m, impostor dalej; treeCardLodScale 1.0). Liście High PC = MSAA 4 + alpha-to-coverage
  (`CoverageAlpha` = alfa wyostrzona przez fwidth). Impostor: 6 widoków 256 × 384 px, blend dwóch sąsiednich widoków (60°).
- NASTĘPNY KROK: `pwsh -NoProfile -File artifacts/crown-lod-s24/vqa.ps1 -Label before` (trwa), potem A/B `-Rq rq_a2c=0`.
