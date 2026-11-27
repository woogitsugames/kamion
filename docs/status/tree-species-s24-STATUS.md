# tree-species-s24 — STATUS (ADR 0352)

Gałąź `worktree-agent-a492e5af856a32ed3`, worktree `.claude/worktrees/agent-a492e5af856a32ed3`.
`Data/raw/derived` = PRYWATNA kopia tylko `knyszyn-w`, `dw671-tykocin-03`, `cache` (nie junction; main nietknięty).

## Diagnoza (krytyk fala 11 pkt 10) — szczegóły w ADR 0352
- Biblioteka drzew ma już atlasy per gatunek (ADR 0308). Jeden stempel liścia miały drzewa ogrodowe zestawu działek
  (`plot_kit._crown_card`); „lizaki” przy ulicy = te drzewa o promieniu korony < 1,6 m (knyszyn-w: 213 + 156 owocowych).
- „Sztywny gradient” = `_CrownShade` (rampa po `normal.y`) + klin `occ_mid` w kartach zestawu; brak wariacji per drzewo.

## Zrobione (commity na gałęzi)
1. `plot_kit.py`: blaszki lipa / klon / brzoza w kartach koron, ciemne liście zamiast płaskiego wielokąta cienia.
2. `plantings.py`: `_crown_quad` (pełne drzewo 34 → 28 trójkątów, bez klina, karty niesymetryczne, spódnica < 6,5 m).
3. `Vegetation.shader` `_TreeVar` + `VegetationCanopyPolicy.TreeVariation` (tint per drzewo, kępy światła).
4. `InstanceImporter.TreeCrownWidth` (szerokość korony 0,84–1,0 per instancja).
5. Dąb: `leaves_oak.png`, `tree_oak_{0,1}` (3270 / 3332 tris LOD0, 766 / 748 LOD1) + impostory, `tree_crown_profile.json`,
   `vegetation.oak_share`, OSM Quercus. Reszta biblioteki bit w bit bez zmian (porównanie siatek GLB i meta).
6. Testy: `tests/gis/test_trees_0352.py` 6/6; `test_trees_0308/0347`, `test_vegetation_r2`, willow 0227: 42 passed, 26 skipped.
7. ADR 0352, `docs/LICENSES.md` (`world-foliage-species-0352`).
8. Render „przed”: `artifacts/tree-species-s24/before/knyszyn-w/High-{clear,overcast}/` (10 kamer; import 1757 s).
   `dw671-tykocin-03` „przed” NIE zrobiony w tym worktree (18 min czekania na slot Unity 2/2) — do porównania tylko
   `artifacts/regen-wave-11-s24/vqa/dw671-tykocin-03/High-clear/` (starszy derived, nie czyste A/B).

## W toku / otwarte
- [~] `pwsh artifacts/tree-species-s24/build.ps1` (build_world obu kafli, slot heavy) → `artifacts/tree-species-s24/build.status`.
- [ ] `pwsh artifacts/tree-species-s24/vqa.ps1 -Label after` (import Win64 + High clear / overcast) i porównanie liczb `stats.txt`.
- [ ] EditMode: `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64` (nowe `TreeCrownWidthTests.cs` — Unity dopisze `.meta`, zacommitować).
- [ ] visual-critic na parach przed / po; kopia `artifacts/tree-species-s24` do main.
- Nie zrobione: wierzba w bibliotece, osobna forma drzew owocowych (`PLT.fruit_tree` nadal ma `_core`), dąb w lasach liściastych.

NASTĘPNY KROK: po `build.status` = DONE → `pwsh artifacts/tree-species-s24/vqa.ps1 -Label after`.
