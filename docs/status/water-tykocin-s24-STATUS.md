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
- Import Win64 tykocin OK (Library z win-build, FBX kabiny skopiowany z main — import #1 padł na braku FBX).
  WORLD_MEMORY Low 80,8 → 81,8 MB, High 173,9 → 180,3 MB. Rendery High 1920×1080 (`r2-bridges-1920`, `r2-place-1920`)
  + Low (`r2-bridges-low`): Narew pod mostem, starorzecza, widok z łodzi pod przęsłem — otwarte, prześwit spód przęsła
  107,5 m − tafla 104,46 m ≈ 3,0 m. Budżet A/B `artifacts/water-tykocin-s24/budget-ab.md` (most +4…+34 draws).
- pytest (11 plików gis: water 0210/0213, ring 0231, regiony, szwy) 148 passed po aktualizacji 3 asercji listy opt-in.
  EditMode Win64: 1519 / 1405 passed / 1 failed (`RegionSelectTests.ShippedCatalog_D67Full` 39 vs 54 — katalog
  regionów na main, plik nietknięty tutaj) / 113 skipped.
- build_world tykocin r3 (po zmianie kamer) zmienił 27 chunków vs r2 — sprawdzam determinizm (r4).

- Determinizm: build_world tykocin r3 == r4 (world_manifest identyczny). r2→r3 różniło 27 chunków (prawdopodobnie
  nieśledzone art-source odświeżone przez import #1 — UNVERIFIED); rendery r2 vs r3 RMSE ≤ 1,2 %. Import #3 + rendery
  r3 = stan końcowy. Dowody skopiowane do `C:\Users\matma\Documents\Claude\kamion\artifacts\water-tykocin-s24\`.
- GOTOWE do przeglądu (nie scalone). ADR: `docs/adr/DRAFT-water-tykocin-s24-woda-narew-korytarz-dw671.md`.
  NASTĘPNY KROK (lider): przed usunięciem worktree skopiować derived 7 kafli do main:
  `foreach ($r in 'tykocin','dw671-tykocin-01','dw671-tykocin-02','dw671-tykocin-08','dw671-tykocin-09','knyszyn','knyszyn-s') { robocopy .claude\worktrees\water-tykocin-s24\Data\raw\derived\$r Data\raw\derived\$r /E /MT:16 }`
  potem `pwsh scripts/import-region.ps1 -Region <id> -BuildTarget Win64` dla każdego kafla w worktree buildu.
