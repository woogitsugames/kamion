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

## Wynik (27.11)
- build_world: knyszyn-w 441 s (78 dębów), dw671-tykocin-03 683 s (112 dębów); skrajnia `violations_after` 0. Smart App Control nie zablokował.
- Import Win64 + VQA High clear / overcast: `artifacts/tree-species-s24/after/`, pary `compare/<kafel>/*.jpg`, liczby `compare/<kafel>/stats-*.txt` (kopia w main).
- knyszyn-w (czyste A/B): draw calle instancji −7…+2 / kamerę, trójkąty instancji −2964…+84, sceny −346…−5753.
- EditMode Win64: 1603 total, 1488 passed, 0 failed (`artifacts/tests/editmode-20261127-083602.xml`). pytest drzew: 42 passed + 6 nowych.
- Manifesty `Data/Regions/*/generated` z prywatnej przebudowy COFNIĘTE (derived main nieprzebudowany).

## Otwarte
- Małe drzewa ogrodowe zestawu działek (promień < 1,6 m) nadal „lizaki” z ciemnym klinem w słońcu — ADR 0352 „Nie rozwiązane”.
- dw671-tykocin-03: brak czystego „przed” (porównanie z renderami fali 11, tylko clear).
- visual-critic nie uruchomiony (subagent nie tworzy subagentów) — do zlecenia przez lidera na `compare/`.
- Wierzba, forma drzew owocowych (`PLT.fruit_tree` nadal ma `_core`), dąb w lasach liściastych; pamięć tekstur wyliczona, nie zmierzona.

NASTĘPNY KROK (lider, po scaleniu): przebudowa wszystkich kafli (`oak_share`, karty `plot_kit`):
`uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region <id>` + `pwsh scripts/import-region.ps1 -Region <id> -BuildTarget Win64`.
