# ARGON-S20 — ADR 0186 (`dojgreen-0186`)

- **Gałąź i SHA:** `dojgreen-0186` @ `da3640105` (po scaleniu `origin/main` z `e668a9588`)
- **Co zrobiono (rundy B-r1..B-r4):**
  - Szpaler 31 płatów `mickiewicza-kuronia-shrub-band` (`SPECIES["thicket"]`, `2.1–2.75 m`, skok `<= 0.25 m`, `ring_step=0.45`, `fill=(1.2, 0.75)`, `local_top=True`, `sprig=0.70`, `top_sprigs=0.40`, `side_share=0.18`) — usunięto namioty i poziome pasy cienia na High.
  - Narożnik `mickiewicza-kuronia-corner-trees`: 3 uziemione krzewy (`berberis_red` `2.8 m`, `shrub` `4.2 m`, `fruit` `5.2 m`) + 2 dojrzałe jesiony (`9.2 m`, `10.5 m`) z ażurowymi wielopłatowymi koronami bez szwu `"X"` na Low/High; 3 drzewa tła po północnej stronie Kuronia + `open_ground` usuwający goły pień z lewej krawędzi; kadr `photo_P11-063` skorygowany.
  - Budżet `photo_P11-063` (`B-r4`): Low `drawsEst=279`, `trisExact=339 096`, `WORLD_MEMORY=98.8 MB`; High `drawsEst=461`, `trisExact=753 627`, `WORLD_MEMORY=214.1 MB` (`+0.6 MB` vs `lead-s20`, `0` nowych tekstur).
- **Testy:**
  - `pytest tests/gis/test_dojgreen_0186.py tests/gis/test_dojlidy_0179.py` (po `B-r4`): `13 passed`.
  - Pełny `pytest tests/gis -q` (`B-r3`): `1155 passed, 2 xfailed, 3 failed` (nieaktualne raporty Regionu C w worktree: `test_p1_0161`, `test_world_v31`, `test_road_fidelity::test_report_not_stale`).
  - Pełny `EditMode` (`B-r3`, bez zmian C# w `B-r4`): `581 total, 580 passed, 0 failed, 1 skipped`.
- **Dowody i recenzja:**
  - `artifacts/dojgreen-0186/B-r4/`, `sbs-P11-063-{Low,High}.jpg`, `sbs-B-r4-{Low,High}.jpg`
  - ADR: `docs/adr/0186-dojlidy-zielen-kadru-063.md` (`PROPOSED`)
  - Recenzja niezależna: `docs/reports/REVIEW-ARGON-dojgreen-0186.md` — werdykt **SCAL** (0 P0, 0 P1).
- **Otwarte:** drobne P2 (ciemne cętki `thicket` na High 9.1%, żywszy odcień `berberis_red`, 2 konary u dołu `ash` na High); po scaleniu uruchomić pełny `EditMode` + `pytest tests/gis` i wykonać zrzut na Galaxy A16 przed bramką.
- **Komenda scalenia:** `git merge --no-ff origin/dojgreen-0186`
- **Gotowe do scalenia:** TAK
