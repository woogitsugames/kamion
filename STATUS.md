# STATUS agy-garden-var-s24 — małe drzewa ogrodowe: usunięcie „lizaka” i wariacja per egzemplarz (dopisek ADR 0352)

- Worktree `agy-garden-var-s24`, gałąź `agy-garden-var-s24`.
- [krok 1-3] Przebudowa generatora `tools/worldgen/streetscape/small_trees.py`, `plantings.py`, `plots.py`, `WorldPlotKit.shader`:
  - `young_tree`: 4 formy (`forked`, `lean`, `broad`, `tiered`), widoczne rozwidlenie i konary 3D (`_strip`) poniżej korony, asymetryczne płaty liści (`v_lo` przycinające płaską stopę pnia, `twist` 0.65–0.95 rad), wyższe osadzenie pierwszych gałęzi zależne od gatunku (`birch`/`ash` wyżej niż `linden`/`maple`/`chestnut`).
  - `orchard_tree`: 4 formy (`open`, `flat`, `upright`, `leaning`), przesunięte wysokości konarów i gęstsze pędy w `upright`/małych średnicach.
  - Zmienność per drzewo (+0 DC): pełny obrót `0..2pi`, przechył całej bryły `±4°`, skala `0.7–1.3` w `garden_trees` / `plots`, tint jasności/odcienia per drzewo jak ADR 0352 przez `TEXCOORD_1` w `WorldPlotKit.shader` (+ subtelne kępy światła).
- [krok 4] Testy jednostkowe i budżetowe: `test_small_trees_0352.py` (5/5), `test_trees_0352.py`, `test_trees_0347.py`, `test_trees_0308.py`, `test_house_greenery_0163.py`, `test_horizon_0170.py`, `test_buildings_r9.py`, `test_budget_0221.py`, `test_typology_0238.py`, `test_world_v31.py`, `test_hero_bridge.py` — zielone.
- NASTĘPNY KROK: prywatna kopia `Data/raw/derived/knyszyn-w`, `build_world.py --region knyszyn-w` (przed/po), `import-region.ps1` + `visual-qa.ps1` High clear+overcast → `artifacts/agy-garden-var-s24/`.
