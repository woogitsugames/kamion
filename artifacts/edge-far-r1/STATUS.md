# ARGON-TASK-01-WORLD-EDGE Status
- Branch: `argon-edge`
- Worktree: `.claude/worktrees/argon-edge`
- Last completed step: DONE — All Definition of Done criteria verified: `r0-before`, `r1`, `r2` visual QA rounds completed and inspected (`<= 960 px`), `pytest tests/gis/test_far_field.py` (5/5 passed) + `tests/gis/test_route_corridor.py` (3/3 passed), Unity `EditMode` (`188/188 passed`), Unity `PlayMode -Filter WorldEdgeRecoveryTests` (`3/3 passed`), ADR [`0085-far-field-backdrop.md`](../../docs/adr/0085-far-field-backdrop.md), [`LICENSES.md`](../../docs/LICENSES.md), and [`REPORT.md`](./REPORT.md) finalized.

## `r0-before` Baseline Summary
- `r0-before` stats (`Low-clear`, without `WorldFarField`):
  - `edge-north`: `objects=10 drawsEst=43 shadowDrawsEst=21 trisK=59`
  - `edge-east`: `objects=9 drawsEst=46 shadowDrawsEst=18 trisK=63`
  - `edge-south`: `objects=14 drawsEst=114 shadowDrawsEst=69 trisK=124`
  - `edge-west`: `objects=13 drawsEst=46 shadowDrawsEst=15 trisK=70`
  - `dk8-dk19-exit`: `objects=23 drawsEst=77 shadowDrawsEst=2 trisK=106`

## Round 1 (`r1`) Stats & Visual Critique (`docs/06_GRAFIKA_ANTI_AI_SLOP.md`)
- `r1` stats (`Low-clear` / `Low-overcast`):
  - `edge-north`: `objects=12 (+2) drawsEst=47 (+4) shadowDrawsEst=21 (+0) trisK=75 (+16k)`
  - `edge-east`: `objects=10 (+1) drawsEst=48 (+2) shadowDrawsEst=18 (+0) trisK=74 (+11k)`
  - `edge-south`: `objects=16 (+2) drawsEst=118 (+4) shadowDrawsEst=69 (+0) trisK=144 (+20k)`
  - `edge-west`: `objects=14 (+1) drawsEst=48 (+2) shadowDrawsEst=15 (+0) trisK=80 (+10k)`
  - `dk8-dk19-exit`: `objects=25 (+2) drawsEst=81 (+4) shadowDrawsEst=2 (+0) trisK=122 (+16k)`
  - Total Low far-field mesh budget across all 4 sectors combined: `27,118` tris (`far_north`: 5,974, `far_east`: 6,093, `far_south`: 9,492, `far_west`: 5,559).
- `r1` visual critique against `docs/06_GRAFIKA_ANTI_AI_SLOP.md` and real Białystok geography:
  1. **What improved in `r1`:**
     - `dk8-dk19-exit`: The bare horizon gap at the end of al. Tysiąclecia N is filled by layered pine crowns of Las Pietrasze.
     - `edge-east`: Real multi-storey residential blocks (with `_FAR_FACADE` window grids), brick offices, industrial halls, and two red/white-banded chimneys appear on the eastern horizon in atmospheric haze.
     - `edge-west`: Deduplicating parallel slip-road stubs eliminated the overlapping 4.5 m green embankment wall that blocked the road in `r0-before`.
  2. **Defects identified in `r1` and fixed in Round 2 (`r2`):**
     - **D1 — BDOT10k GeoPackage filename & uppercase column names:** `bdot10k-2061/gpkg` files are named `PL.PZGiK.335.BDOT10k.2061__OT_*.gpkg` (not `330`) with uppercase columns (`LOKALNYID`, `KATEGORIA`, `FUNKCJAOGOLNABUDYNKU`, `PRZEWAZAJACAFUNKCJABUDYNKU`, `LICZBAKONDYGNACJI`, `RODZAJ`, `WYSOKOSC`), and `lod1_zip` is `2061_lod1_2024.zip`. Fixed in `far_field.py`: now extracts **472** forests, **8,470** buildings, **16** chimneys, **302** HV pylons/towers, and **107** power lines.
     - **D2 — Synthetic `_corridor_treelines` & true exit coordinates:** Aligned `_road_exit_corridors`, `_corridor_taper`, and `_corridor_treelines` with the true border road exit coordinates (`edge-north` at `E = -856.6, N = +1024`, `edge-east` at `E = +1024, N = -980.1`, `edge-south` at `E = -237.6, N = -1024`, `edge-west` at `E = -1024, N = +44.1`), opening clear urban/industrial vistas at `edge-south`, `edge-east`, and `edge-west` and closing the `edge-north` pine horizon at `d >= 165 m`.
     - **D3 — Radial grazing-angle forest curtains & concave mound spanning:** Skipped exterior forest curtain segments that run radially (`facing_tile < 0.44`), replaced interior curtain cuts with frontal transverse ribs perpendicular to the radial view direction, and subdivided large forest polygons into `<= 320 m` cells before building under-canopy mounds so triangle fans never bridge across concave road corridors.
     - **D4 — Synchronized local perimeter elevation smoothing (`w = 6`, `±96 m`):** Both `WorldEdgeBuilder.BuildApron` and `BorderElevation.z_at_eff` now use the exact same circular moving average (`w = 6`, `±96 m`) and ease curve (`260 m`), eliminating the `+2.8 m` vertical gap in the `edge-east` valley (`N = -980.1 m`).

## Round 2 (`r2`) Final Stats & Verification
- `r2` stats (`Low-clear` / `Low-overcast`):
  - `edge-north`: `objects=12 (+2) drawsEst=47 (+4) shadowDrawsEst=21 (+0) trisK=71 (+12k)`
  - `edge-east`: `objects=11 (+2) drawsEst=50 (+4) shadowDrawsEst=18 (+0) trisK=85 (+22k)`
  - `edge-south`: `objects=15 (+1) drawsEst=116 (+2) shadowDrawsEst=69 (+0) trisK=140 (+16k)`
  - `edge-west`: `objects=14 (+1) drawsEst=48 (+2) shadowDrawsEst=15 (+0) trisK=78 (+8k)`
  - `dk8-dk19-exit`: `objects=25 (+2) drawsEst=81 (+4) shadowDrawsEst=2 (+0) trisK=118 (+12k)`
  - Total Low far-field mesh budget across all 4 sectors combined: **`24,826` tris** (`<= 30,000` budget; `far_north`: 4,003, `far_east`: 6,204, `far_south`: 11,211, `far_west`: 3,408).
- `r2` stats (`High-clear` / `High-overcast`):
  - `edge-north`: `objects=12 drawsEst=47 shadowDrawsEst=81 trisK=71`
  - `edge-east`: `objects=11 drawsEst=50 shadowDrawsEst=102 trisK=85`
  - `edge-south`: `objects=16 drawsEst=118 shadowDrawsEst=270 trisK=169`
  - `edge-west`: `objects=14 drawsEst=48 shadowDrawsEst=102 trisK=80`
  - `dk8-dk19-exit`: `objects=30 drawsEst=96 shadowDrawsEst=51 trisK=153`
  - Total High far-field mesh: **`118,902` tris** across 4 sectors (`far_north`: 19,350, `far_east`: 35,030, `far_south`: 47,581, `far_west`: 16,941).
- **Test Suite Verification:**
  - `uv run --project tools/worldgen pytest tests/gis/test_far_field.py -q`: `5 passed`
  - `pwsh scripts/test.ps1 -Platform EditMode`: `188 total, 188 passed, 0 failed` (`artifacts/tests/editmode-20261111-104802.xml`)
  - `pwsh scripts/test.ps1 -Platform PlayMode -Filter WorldEdgeRecoveryTests`: `3 total, 3 passed, 0 failed` (`artifacts/tests/playmode-20261111-115415.xml`)
- Next step (ready command):
  Task complete — branch `argon-edge` ready for owner review/merge.
