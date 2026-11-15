# ARGON-S20 — ADR 0193 (`sigplate-0193`)

- **Gałąź i SHA:** `sigplate-0193` @ `5b77931d4` (kod/build @ `51b9976da`, po scaleniu `origin/main` @ `b0d9769fc`)
- **Co zrobiono (runda 3 wg M66 §5):**
  - Tarcze kontrastowe `0,85 × 1,40 m` (`R70`, biała obwódka `40 mm` z czarnym marginesem `20 mm`, kolor `marking_white`) wyłącznie na głowicach wysięgnikowych (`signal_head_*`, pochylenie `7°`), umieszczone **za** czarną obudową `280 mm`; daszki wydłużono do `0,22 m`.
  - Głowice boczne na słupach (`signal_head_side_*`, `plate=False`) i sygnalizatory piesze (`signal_ped_*`) bez tarczy kontrastowej.
  - Kamera `photo_P11-094` odsunięta o ~10 m na `(784.3, 394.0)` — znak D-6 i narożnik hali Rosti zgodne z `P11-094.jpg`.
  - Budżet: `drawsEst` Low bez zmian (`104/474/487/496`), `trisExact` `+0,14..+0,33%`, `WORLD_MEMORY` `123,1 MB` (C Low) / `265,9 MB` (C High) / `98,2 MB` (D Low) / `213,5 MB` (D High); prototyp oszczędza `-1 144 tris LOD1` w C i `-592 tris LOD1` w D względem sprzed 0193.
- **Testy:**
  - `pytest tests/gis/test_signal_head_0193.py ...` (po przebudowie C3/D3): `62 passed, 1 xfailed` (`test_signal_head_0193.py`: `26 passed`).
  - Pełny `pytest tests/gis -q` (`pytest-gis.log`): `1168 passed, 1 failed, 2 xfailed` (jedyny fail: `test_dojbld_0185.py::test_fence_mesh_mips_do_not_preserve_coverage`, niezwiązany).
  - Pełny `EditMode` (`editmode.log`): `581 total, 580 passed, 0 failed, 1 skipped`.
- **Dowody i recenzja:**
  - `artifacts/sigplate-0193/sbs3/` (`after-heads.jpg`, `after-C-sheet-{Low,High}.jpg`, `gate3-signal-{Low,High}.jpg`, `sbs-P11-{063,094}-{Low,High}.jpg`)
  - ADR: `docs/adr/0193-sygnalizator-tarcza-i-kamera-d6.md` (`PROPOSED`)
  - Recenzja niezależna: `docs/reports/REVIEW-ARGON-sigplate-0193.md` — werdykt **SCAL** (0 P0, 0 P1).
- **Otwarte:** brak piktogramów na soczewkach `signal_ped`/`signal_bike` (P2, 0 instancji), brak obejmy między wysięgnikiem a tarczą (P2), zrzut z telefonu przed bramką.
- **Komenda scalenia:** `git merge --no-ff origin/sigplate-0193`
- **Gotowe do scalenia:** TAK
