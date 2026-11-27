# STATUS agy-garden-var-s24 — małe drzewa ogrodowe: usunięcie „lizaka” i wariacja per egzemplarz (dopisek ADR 0352)

- Worktree `agy-garden-var-s24`, gałąź `agy-garden-var-s24`. Prywatna kopia `Data/raw/derived/knyszyn-w` (pozostałe kafle junction do main).
- [krok 1-3] Przebudowa `small_trees.py`, `plantings.py`, `plots.py`, `WorldPlotKit.shader`, `preview_kit.py`:
  - `young_tree`: 4 formy (`forked`, `lean`, `broad`, `tiered`), widoczne rozwidlenie i konary 3D (`_strip`) poniżej korony, asymetryczne płaty (`v_lo`, `twist` 0.65–0.95 rad), wyższe osadzenie pierwszych gałęzi zależnie od gatunku (`birch`/`ash` > `linden` > `maple`/`chestnut`).
  - `orchard_tree`: 4 formy (`open`, `flat`, `upright`, `leaning`), przesunięte wysokości konarów.
  - Zmienność per drzewo (+0 DC): obrót `0..2π`, przechył `±4°`, skala `0.7–1.3`, tint jasności/odcienia jak ADR 0352 przez `TEXCOORD_1` w `WorldPlotKit.shader`.
- [krok 4-5] Czyste A/B na `knyszyn-w` (High PC 1920×1080 `clear` + `overcast`, 11 kamer `garden-trees`) + pary SBS ≤960 px w `artifacts/agy-garden-var-s24/compare/knyszyn-w/` (skopiowane do `C:\Users\matma\Documents\Claude\kamion\artifacts\agy-garden-var-s24\`):
  - `garden_trees` (`streetscape_qa`): `trees` 808, `tris_high` 17 188 → 19 132 (+1 944), `tris_low` 15 428 (+0); `young` (164): 3 384 → 5 328, `orchard` (121): 5 600 (+0).
  - Visual-QA (11 kamer): `draws` +0, `shadowDraws` +0, `instDraws` +0 na każdej kamerze; `tris` sceny +0…+1 362 (`tykocka-dw671-out`: 490 762 → 491 081, +319).
- [krok 6] Dopisek `docs/adr/0352-drzewa-gatunki-tint-per-drzewo-dab.md`, testy zielone, commit końcowy.
- GOTOWE DO SCALENIA PRZEZ LIDERA.
- NASTĘPNY KROK (lider): `git merge --no-ff agy-garden-var-s24` + przebudowa kafli z małymi drzewami ogrodowymi (`build_world.py` + `import-region.ps1`).
