# STATUS trees-s24 (drzewa przydrożne i lasy, ADR 0308)

- 14:55 Worktree `trees-s24` (-CopyDerived, prywatna kopia `Data/raw/derived`). Generator: `tools/blender/world/make_trees.py`
  + `tools/worldgen/streetscape/leaf_textures.py`; rozmieszczenie `streetscape/{vegetation,tree_rows,forest_hlod}.py`.
  Podgląd Blender stanu „przed": `artifacts/trees-s24/preview/before_broadleaf.png` (korony = kilka kulistych kęp na gołych
  konarach; tekstury liści = okrągłe pompony). Render „przed" (import knyszyn + dk65-05, High clear) w tle.
  NASTĘPNY KROK: `cat artifacts/trees-s24/unity-before-knyszyn.status artifacts/trees-s24/unity-before-dk65.status`; obejrzeć `artifacts/trees-s24/vqa-before-*/`
- 15:45 „Przed" obejrzane (`artifacts/trees-s24/vqa-before-{knyszyn,dk65}/`, montaże `small/before*_m*.jpg`). Trzy źródła „brokułów":
  (1) drzewa biblioteki = kilka kulistych kęp na gołych konarach, karty liści = okrągłe pompony; (2) drzewa ogrodowe Knyszyna
  (3243 szt.) = skrzyżowane karty z ciemnym rdzeniem; (3) świerki = stos poziomych talerzy. Zrobione: `leaf_sprays.py` (atlasy
  gałązek 2×2), `make_trees.grow_crown` (lipa/klon/brzoza/olsza + topola), świerk z obrotem konarów, drzewa ogrodowe na High jako
  instancje biblioteki (`plantings.library_instance`), test `tests/gis/test_trees_0308.py` (10 passed), wpis LICENSES.
  LOD0 tris: lipa 3128–3272 → 3272–3354, klon 2450–2520 → 2916–2996, brzoza 3380–3534 → 2936–2976, olsza 4024–4130 → ~3100.
  Wypiek biblioteki + runda 1 (build_world knyszyn → import → render) w tle.
  NASTĘPNY KROK: `cat artifacts/trees-s24/bake-r1.status artifacts/trees-s24/round-r1.status`; obejrzeć `artifacts/trees-s24/vqa-r1-*/`
