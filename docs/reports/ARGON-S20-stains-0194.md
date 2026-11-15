# ARGON-S20 — ADR 0194 (`stains-0194`)

- **Gałąź i SHA:** `stains-0194` @ `5b87ea429` (build `after4` @ `2d5e2ef33`, po scaleniu `origin/main`)
- **Co zrobiono (rundy after1..after4):**
  - Plamy oleju (`_OilStains`): ciemne, matowe, ostre (`P11-129b` ~62 vs asfalt 66–70).
  - Łaty asfaltu (`roads/decals.py`): szew 25 mm, gęstość ważona klasą drogi (`A/S 0.35` … `D 1.3`), strefą wlotów (`30 m`, `×1.8`) i osią kolein; D `285→416`, C `317→443` łat.
  - Brud placów (`_GrimeTraffic` z UV1 paved) oraz naprawa 3 artefaktów płyt/poboczy: `_patch_uv1` + spawanie `(qp, UV1)` w `assemble()` (usunięty żółty pas `route-s1370`), `UV1=(-1, 5)` dla `road_asphalt*` w `_emit_strip` (usunięte pręgi `route-s0457`, `P11-056`), wygładzenie `lane` za `hw` (usunięte zygzaki zjazdów `g3-a-2818555625124739`).
  - Budżet `after4`: `drawsEst` Low `+0..+4` (Dojlidy) / `+0..+1` (C), `trisExact` ok. `+0.1%` na C; `WORLD_MEMORY` Dojlidy Low `103.8→98.3 MB` / High `213.6 MB`, C Low `123.2 MB` / High `266.1 MB`.
- **Testy (po `after4`):**
  - `pytest tests/gis/test_stains_0194.py tests/gis/test_unit_meshing_chunks.py -q`: `14 passed`.
  - Pełny `pytest tests/gis -q`: `1157 passed, 2 failed, 2 xfailed` (znane upstream niezwiązane: `test_dojbld_0185.py::test_fence_mesh_mips_do_not_preserve_coverage`, `test_road_fidelity.py::test_report_not_stale`).
  - Pełny `EditMode`: `584 total, 583 passed, 0 failed, 1 skipped`.
- **Dowody i recenzja:**
  - `artifacts/stains-0194/{after4,view4,sbs4}/`
  - ADR: `docs/adr/0194-plamy-i-brud-asfaltu.md` (`PROPOSED`)
  - Recenzja niezależna: `docs/reports/REVIEW-ARGON-stains-0194.md` — werdykt **SCAL** (0 P0, 0 P1).
- **Otwarte:** koleiny na nowych drogach (`wheel_darkening=0.45`, P2); pomiar ALU shaderów na Galaxy A16 przy najbliższym APK.
- **Komenda scalenia:** `git merge --no-ff origin/stains-0194`
- **Gotowe do scalenia:** TAK
