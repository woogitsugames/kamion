# water-tykocin-s24 — STATUS

Zadanie (lider s24, P1 przed buildem #3): most DW671 na Narwi (ul. Puchalskiego, kafel `tykocin`) stoi nad łąką —
włączyć etap wody ADR 0210 w `tykocin` (+ inne kafle korytarza z wodą w OSM/BDOT), przebudować, import Win64, render.

## Log
- 2026-11-21: worktree `.claude/worktrees/water-tykocin-s24` (`-CopyDerived`), gałąź `water-tykocin-s24`.
  Inwentaryzacja wody (WT.extract, bez zapisu): tykocin BDOT OT_PTWP_A 27 obiektów / 159 004 m², OT_SWRS_L 9,8 km;
  OSM 13 obszarów (Narew `water=river` 78 445 m², starorzecza `oxbow` 32 096 / 4 907 / 3 271 m²), osie Narew 4,1 km,
  Nereśl, Zajkowska Struga. `regions.py`: `tykocin` `water=True`.
  NASTĘPNY KROK: `uv run --project tools/worldgen tools/worldgen/build_region.py --region tykocin`
- build_region tykocin → `generated/water_sources.json`; build_world r2 (6,7 min): 36 ciał wody, 176 724 węzłów,
  tafla 182 627 m² / 32 175 tris, pas trzciny (water_banks: brzeg 13,0 km, pas 9,1 km = 70 %, 1055 koron;
  4193 wstęg / 139 168 tris High, 400 / 8 416 Low), 654 krzewy + 140 olch; ściany terenu 0; spójność dróg jak main
  (6 × lane_blind_end, 1 na trasie). Narew pod mostem N 15..70 m przy E 506 (BDOT), poziom 104,5 → 103,5 m (2,3 km).
- Włączono też `water=True`: dw671-tykocin-09 (Nereśl, szew z tykocin), -08 (Stara Narew), -02, -01 (stawy
  0,83 km²), knyszyn (Jaskrzanka, Zalew), knyszyn-s (Jaskrzanka + stawy 87 500 m²). -03/-04/-05/-06/-07, knyszyn-w:
  tylko drobne stawy (≤ 9 000 m²) — pominięte. buildings.geojson/rail_sources tych kafli zostawione jak na main
  (build_region dawał dryf niezwiązany z wodą).
- Library Win64 skopiowana z win-build (robocopy /MIR). Import tykocin Win64 w toku.
  NASTĘPNY KROK: `pwsh scripts/visual-qa.ps1 -Scene World_tykocin_High -Tier High -Lighting clear -BuildTarget Win64 -Gate3 artifacts/water-tykocin-s24/bridges-tykocin.json -OutputDir artifacts/water-tykocin-s24/after-bridges`
