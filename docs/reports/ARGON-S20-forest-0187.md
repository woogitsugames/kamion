# ARGON-S20 — ADR 0187 (`forest-0187`)

- **Gałąź i SHA:** `forest-0187` @ `11e965a88` (po scaleniu `origin/main` i wdrożeniu M68 §6)
- **Co zrobiono (rundy after1..after2):**
  - Wdrożono parametry BDL/NMPT 2023 w `bialystok-dojlidy/overrides.yaml`: 3× `forest_stand` (`20–29 m` + `emergent` `0.03` do `32 m`, bez mnożnika `0.7` na `1ac1a146` przy `young_edge` `8 m`), `tree_stand` (`allotment-gardens` `4–10 m` + `emergent` `14–17 m`, `wood-NW` `8–19 m`, `wood-skatepark` `6.5–11.5 m`).
  - `vegetation.py` + `forest_hlod.py`: `UNDERSTOREY` (`shrub 0.55, birchyoung 0.20, spruce 0.15, maple 0.10, pineyoung 0`); zewnętrzny pas krzewów i spódnica HLOD na `18%` krawędzi (widoczne pnie sosen z podszytem), młody pas na `58%`; atrybucja BDL w `docs/LICENSES.md`.
  - Horyzont `photo-P11-056` domknięty w 100% na Low.
  - Budżet `compare2-*.tsv`: C `draws` `0 Δ` na 129 kamerach (`tris +0.12%/+0.19%`), Dojlidy `draws +89/+149` (47 kamer, `tris +1.48%/+1.08%`).
- **Testy (po `after2`):**
  - `pytest tests/gis/test_forest_0187.py tests/gis/test_world_v34.py -q`: `33 passed`.
  - Pełny `pytest tests/gis -q`: `1162 passed, 2 xfailed, 1 failed` (`test_dojbld_0185.py::test_fence_mesh_mips_do_not_preserve_coverage` — niezwiązany upstream).
  - Pełny `EditMode`: `581 total, 580 passed, 0 failed, 1 skipped`.
- **Dowody i recenzja:**
  - `artifacts/forest-0187/{after2,pairs2,compare2-*.tsv}`
  - ADR: `docs/adr/0187-sciana-lasu-swierk-mlodnik-plaszcz-horyzont.md` (`PROPOSED`)
  - Recenzja niezależna: `docs/reports/REVIEW-ARGON-forest-0187.md` — werdykt **SCAL warunkowo**.
- **Otwarte:** P1/P2 z recenzji (ostre narożniki HLOD `krywlany-runway` / `forest_wall_meadow`, oderwane plamy koron na High `P11-056`/`krywlany-runway`) dopisać do backlogu; zrzuty na Galaxy A16 przed bramką.
- **Komenda scalenia:** `git merge --no-ff origin/forest-0187`
- **Gotowe do scalenia:** TAK (warunkowo — wg `REVIEW-ARGON-forest-0187.md`)
