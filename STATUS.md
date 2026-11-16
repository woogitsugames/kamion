# STATUS — D14 roundabout2-0274 (rondo Knyszyn, ADR 0274)

- [1] `tools/worldgen/qa/roundabout_ortho.py` + `docs/reports/roundabout-0274/`: ortofoto GUGiK w punkcie ronda = arkusz
  2025-05-27 (brak 2026), `roundabout_visible: false` (skrzyżowanie sprzed budowy) → wymiary ronda WORKING_VALUE / ESTIMATED.
- [2] `roads/compact_roundabout.py` tryb krawężnikowy (`lay_lanes`, promienie 6 / 8 m, nosek 4 m), `roads/carriageway_split.py`
  (DK65 S 27 m, N 17 m → wysepki 29,2 / 20,2 m), P-13 i P-10 przy pierścieniu, siatka wyspy z pierścieni, `plantings` clumps / stones
  (945 tris). Wloty 2 m za pierścieniem 13,1/11,8/12,9/13,4 → 10,9/11,0/11,5/11,4 m; asfalt 3 m za pierścieniem 165,5 → 141,3 m².
- [3] Recenzja D18: P1 + P2-2/3/4/5/6/7/8/11 zamknięte; P2-9, P2-10 nie ruszone. Trasa startowa knyszyn + region_catalog wyeksportowane.
- [4] Testy: `tests/gis/test_roundabout_0274.py` 62; ADR `docs/adr/0274-…md`.
- NASTĘPNY KROK (lider): `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region knyszyn` →
  `pwsh scripts/import-region.ps1 -Region knyszyn` → `pwsh scripts/visual-qa.ps1 -Scene World_knyszyn -Tier High -Lighting clear -Cameras rondo_dk65_top,rondo_dk65_above,rondo_dk65_from_south -OutputDir artifacts/roundabout-0274/vqa/High`
