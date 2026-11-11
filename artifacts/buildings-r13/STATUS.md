# buildings-r13 (ADR 0097, zabudowa r5) — STATUS

Gałąź `buildings-r5`, worktree `.claude/worktrees/buildings-r5`, z main `0e73211a`.

## krok 1 — przygotowanie + kod r1 (część)
- Library skopiowana z main (robocopy), build_all (pełny) + build_world baza na kodzie main, PNG oznaczone jako świeże.
- Baza: `run_round.ps1 -Round base` (import + High/Low overcast + High clear) — w toku.
- Kod r1 (niezrenderowany): jeden typ balustrady na budynek (grupy `balcony_1/6/3` w row atlasie, typ z osiedla 250 m,
  12 % wyjątków na LOD0), balkony na obu długich stronach bloków, zacieki pod parapetami (TEXCOORD_1 +64, tryb sill
  shadera ADR 0092) na ścianach bloków / biur / domów, profil kapinosu nad cokołem, paleta domów przydzielana wg sąsiadów
  (ściana + dach), drzwi domu na cokole + podest/stopnie/próg, pranie stonowane (12 %).
- NASTĘPNY KROK: dach wielopołaciowy (`roofs.py` MultiRoof), potem
  `pwsh artifacts/buildings-r13/chain.ps1 -Round r1 -Only facade_atlas,facade_far`

## krok 2 — baza zrenderowana, kod r1 kompletny
- Baza (`base/`): import 145 s, QA High/Low overcast + High clear OK. Region GLB bazy niezmierzony (build r1 nadpisał
  generated przed chunk_mats) — porównanie regionu względem r12 r3b.
- Kod r1 + testy (`tests/gis/test_buildings_r5.py` 9 passed, r4 dostosowane): MultiRoof (obwiednia dwuspadowych
  części z rozkładu rzutu na prostokąty, kosze z obróbką), deska czołowa = soffit_boards, krem −8 %, cokół 0,24 /
  rozbryzg 0,8 m (blok addytywny na końcu materials.py).
- NASTĘPNY KROK: (build_world r1 w toku) → `pwsh artifacts/buildings-r13/run_round.ps1 -Round r1 -Configs 'High:overcast,Low:overcast,High:clear'`

## krok 3 — r1 zrenderowany (High/Low overcast; High clear czeka na PHONE_RUN lidera), kod r2
- r1: MultiRoof 98 / 270 domów (0 dziur pokrycia, `roof_scan.py`), balkony 2369 → 3413, region High 4025 submeshy /
  14,04 mln tris (r12 r3b: 4025 / 13,96), Low 3006 / 4,489 mln (r12: 3004 / 4,490).
- Budżet Low 57 kamer base → r1: draws 16688 → 16683 (−0,0 %), tris +0,6 % (maks. r10_block_2 +3,0 %).
- Obejrzane: balkony na obu długich stronach, jeden typ/budynek; wyjątek „brąz” czyta się pomarańczowo → usunięty;
  kapinos z jasnym wierzchem = przerywana biała linia → r2 ciemny, bez wierzchu; drzwi domu z podestem i progiem OK.
- P2-f (ząbki pod attyką `r10_fence_2`) = aliasing cienia mapy cieni od obróbki attyki (High clear wyraźny, maska
  zacieków gładka) → rendering, nie zabudowa (`base/crop_fence2_lc.png`, `base/runoff_top.png`).
- r2: opaska z kostki 0,5 m wokół bloków (sidewalk_paving), balkony > 2. kondygnacji bez bocznych poręczy (20 → 16 tris).
- NASTĘPNY KROK: po zdjęciu PHONE_RUN dokończy się `r1` High clear; potem
  `pwsh artifacts/buildings-r13/chain.ps1 -Round r2` i kamery `cams_r13.json`:
  `pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting overcast -Gate3 artifacts/buildings-r13/cams_r13.json -Cameras <ids> -OutputDir artifacts/buildings-r13/r2/extra`
