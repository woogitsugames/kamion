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

## krok 4 — r2 dane zbudowane, czeka na PHONE_RUN (+ GPT_UNITY_HOLD) z importem/renderami
- r2 region: High 4038 submeshy (+13: opaska `buildings|sidewalk_paving` jako osobna siatka w 13 chunkach, nowy
  materiał tylko w 2), 14,03 mln tris; Low 3006 / 4,489 mln (bez zmian).
- pytest tests/gis (r2): 380 passed, 1 xfailed (`r2/pytest_gis.log`).
- r1 High clear: szczyt `r10_house_2` średnio 232/221/193 → 220/211/189, p99 R 255 → 253 (krem −8 %; reszta = ekspozycja).
- Rozbryzg cokołu `r10_block_3` (góra − dół pasa, luma): 8,4 → 11,7 poziomu (`plinth_profile.py`).
- ADR 0097 szkic: `docs/adr/0097-buildings-r5.md`.
- NASTĘPNY KROK: działa `run_round.ps1 -Round r2` + kamery `cams_r13.json` (po zdjęciu blokady), potem budżet
  `uv run --project tools/worldgen python artifacts/buildings-r13/budget.py artifacts/buildings-r13/base/Low-overcast artifacts/buildings-r13/r2/Low-overcast`

## krok 5 — r2 zrenderowany + kamery dodatkowe; opaska wyłączona → r3
- Budżet Low base → r2 (57 kamer): draws 16688 → 16697 (+0,1 %, maks. fire-station-ref7197 +0,8 %), tris +0,6 %
  (maks. r10_block_3 +2,8 %); kamer > 400 draws 10 → 10.
- Region r2: High 4038 submeshy (opaska), Low 3006. Rozbryzg cokołu `r10_block_3` 8,4 → 11,0 poziomu.
- Paleta domów (`palette_stats.py`): ciepłe 63 → 48 %, najbliższy sąsiad z tą samą ścianą 24 → 0 %, z tym samym
  dachem 39 → 1 %.
- Oglądane: zacieki pod parapetami czytelne (r13_block3_close, r10_block_5), kapinos = ciemna linia, konfetti znikło
  (r10_block_2/4), domy z podestem, kosze/skrzydła na kamerach r13_house2_*. Opaska zapadała się pod siatkę terenu
  (r10_block_5: jasne łaty) → `BLOCK_APRON = False` (otwarte).
- NASTĘPNY KROK: `pwsh artifacts/buildings-r13/chain.ps1 -Round r3`, potem `pwsh scripts/test.ps1 -Platform EditMode`

## krok 6 — KONIEC: r3 (stan końcowy) zmierzony, EditMode, ADR 0097
- r3 = r2 bez opaski. Region High 4025 / 14,02 mln tris, Low 3006 / 4,489 mln; budżet Low 57 kamer: draws 16688 →
  16683 (−0,0 %), tris +0,5 % (maks. r10_block_2 +2,2 %), kamer > 400 draws 10 → 10.
- EditMode 226: 223 passed, 3 failed (TruckDoorGlassTests × 3, znane, C# bez zmian). pytest gis (r2) 380 / 1 xfail.
- Pary przed/po: `pairs/*.jpg` (base vs r3), kamery dodatkowe `r2/extra/960/`.
- NASTĘPNY KROK (lider): visual-critic na `pairs/` + `r2/extra/960/`; scalenie `buildings-r5`, potem
  `uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py --only facade_atlas,facade_far` →
  `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c` →
  `pwsh scripts/import-region.ps1 -Region bialystok-industrial-c`
