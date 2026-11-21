# water-tykocin-s24 — STATUS

Zadanie (lider s24, P1 przed buildem #3): most DW671 na Narwi (ul. Puchalskiego, kafel `tykocin`) stoi nad łąką —
włączyć etap wody ADR 0210 w `tykocin` (+ inne kafle korytarza z wodą w OSM/BDOT), przebudować, import Win64, render.

## Log
- 2026-11-21: worktree `.claude/worktrees/water-tykocin-s24` (`-CopyDerived`), gałąź `water-tykocin-s24`.
  Inwentaryzacja wody (WT.extract, bez zapisu): tykocin BDOT OT_PTWP_A 27 obiektów / 159 004 m², OT_SWRS_L 9,8 km;
  OSM 13 obszarów (Narew `water=river` 78 445 m², starorzecza `oxbow` 32 096 / 4 907 / 3 271 m²), osie Narew 4,1 km,
  Nereśl, Zajkowska Struga. `regions.py`: `tykocin` `water=True`.
  NASTĘPNY KROK: `uv run --project tools/worldgen tools/worldgen/build_region.py --region tykocin`
