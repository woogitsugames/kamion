# ARGON-TASK-01-WORLD-EDGE Status
- Branch: `argon-edge`
- Worktree: `.claude/worktrees/argon-edge`
- Last completed step: Step 2 (Round 1 `r1`) — Implemented `tools/worldgen/streetscape/far_field.py`, hooked into `tools/worldgen/roads/build_world.py`, extended `WorldSurface.shader` (`_FAR_FACADE` vertex color + window modes) and `WorldEdgeBuilder.cs` / `RegionImporter.cs`, built `WorldEdge` on `WorldC` and `WorldC_High`, rendered 20 `r1` frames (`Low-clear`, `Low-overcast`, `High-clear`, `High-overcast`), and inspected all resized PNGs (`<= 960 px`).

## `r0-before` Baseline Summary
- `r0-before` stats (`Low-clear`):
  - `edge-north`: `objects=11 drawsEst=45 shadowDrawsEst=21 trisK=69`
  - `edge-east`: `objects=9 drawsEst=46 shadowDrawsEst=18 trisK=67`
  - `edge-south`: `objects=15 drawsEst=116 shadowDrawsEst=69 trisK=135`
  - `edge-west`: `objects=13 drawsEst=46 shadowDrawsEst=15 trisK=75`
  - `dk8-dk19-exit`: `objects=24 drawsEst=79 shadowDrawsEst=2 trisK=116`

## Round 1 (`r1`) Stats & Visual Critique (`docs/06_GRAFIKA_ANTI_AI_SLOP.md`)
- `r1` stats (`Low-clear` / `Low-overcast`):
  - `edge-north`: `objects=12 (+1) drawsEst=47 (+2) shadowDrawsEst=21 (+0) trisK=75 (+6k)`
  - `edge-east`: `objects=10 (+1) drawsEst=48 (+2) shadowDrawsEst=18 (+0) trisK=74 (+7k)`
  - `edge-south`: `objects=16 (+1) drawsEst=118 (+2) shadowDrawsEst=69 (+0) trisK=144 (+9k)`
  - `edge-west`: `objects=14 (+1) drawsEst=48 (+2) shadowDrawsEst=15 (+0) trisK=80 (+5k)`
  - `dk8-dk19-exit`: `objects=25 (+1) drawsEst=81 (+2) shadowDrawsEst=2 (+0) trisK=122 (+6k)`
  - Total Low far-field mesh budget across all 4 sectors combined: `27,118` tris (`far_north`: 5,974, `far_east`: 6,093, `far_south`: 9,492, `far_west`: 5,559), `+2` draw calls per camera, `+0` shadow draw calls.
- `r1` stats (`High-clear` / `High-overcast`):
  - `edge-north`: `objects=12 drawsEst=47 shadowDrawsEst=81 trisK=75`
  - `edge-east`: `objects=10 drawsEst=48 shadowDrawsEst=102 trisK=74`
  - `edge-south`: `objects=16 drawsEst=118 shadowDrawsEst=270 trisK=167`
  - `edge-west`: `objects=14 drawsEst=48 shadowDrawsEst=102 trisK=83`
  - `dk8-dk19-exit`: `objects=30 drawsEst=96 shadowDrawsEst=51 trisK=157`
  - Total High far-field mesh: `88,151` tris across 4 sectors.
- `r1` visual critique against `docs/06_GRAFIKA_ANTI_AI_SLOP.md` and real Białystok geography:
  1. **What improved in `r1`:**
     - `dk8-dk19-exit`: The bare horizon gap at the end of al. Tysiąclecia N is now filled by layered pine crowns of Las Pietrasze.
     - `edge-east`: Real multi-storey residential blocks (with `_FAR_FACADE` window grids), brick offices, industrial halls, and two red/white-banded chimneys now appear on the eastern horizon in atmospheric haze.
     - `edge-west`: Deduplicating parallel slip-road stubs eliminated the overlapping 4.5 m green embankment wall that blocked the road in `r0-before`.
  2. **Defects identified in `r1` to fix in Round 2 (`r2`):**
     - **D1 — BDOT10k GeoPackage filename & uppercase column names:** `bdot10k-2061/gpkg` files are named `PL.PZGiK.335.BDOT10k.2061__OT_*.gpkg` (not `330`) with uppercase columns (`LOKALNYID`, `KATEGORIA`, `FUNKCJAOGOLNABUDYNKU`, `PRZEWAZAJACAFUNKCJABUDYNKU`, `LICZBAKONDYGNACJI`, `RODZAJ`, `WYSOKOSC`), and `lod1_zip` is `2061_lod1_2024.zip`. Activating the BDOT10k `.gpkg` + LoD1 2024 reader brings in all 60 BDOT10k chimneys (`WYSOKOSC`), 286 BDOT10k power pylons, 30 telecom towers, and exact LoD1 building heights.
     - **D2 — Synthetic `_corridor_treelines` blocking urban/industrial vistas (`edge-south`, `edge-east`, `edge-west`):** In `edge-south`, a synthetic treeline placed right at `N = -1026 m` acted as a dark curtain across the road, hiding all 965 real Białostoczek / Osiedle Tysiąclecia residential blocks, industrial halls, and EC Białystok chimneys behind it! Similarly, in `edge-east` and `edge-west`, synthetic treelines placed 2 m past the border created abrupt dark vertical edges right next to the road.
     - **D3 — Opaque vertical side walls on forest stands (`_add_forest_stand`):** The inner opaque forest volume had `0.68 * h_base` (`~14 m`) vertical side walls (`col_side`), creating a boxy vertical step at stand ends (`edge-east` and `edge-west` center-left). Removing vertical box walls on the under-canopy mound (keeping a low `2.5 m` perimeter skirt sloping up to an interior ridge) and tapering `forest_edge_mixed` curtain height at stand ends eliminates all sharp vertical steps.
     - **D4 — Apron easing to global perimeter `mean` (`edge-west` uphill ramp):** Because the NE corner (Las Pietrasze) is at `158 m` while the W border (`edge-west`) is at `131 m`, easing the apron to the global perimeter `mean` (`143 m`) forced the apron and road stub at `edge-west` to climb `+12 m` uphill over `600 m`, hiding the Bacieczki/Dziesięciny buildings behind an artificial hill. Easing the apron to a locally smoothed border elevation (`±250 m` moving average along the perimeter, with a gentle `-0.8 m` drop in the far field) keeps `edge-west` and `edge-south` level with their real valleys.
     - **D5 — `edge-north` center road corridor:** At `edge-north` (`E ~ +712, N = +1024`), DK8 curves slightly east into Las Pietrasze ~180 m past the border; placing natural tapered pine stand layers beyond `N = 1280..1700 m` closes the narrow center-line gap at the horizon while keeping the immediate road stub open.

- Next step (ready command):
  `uv run --project tools/worldgen python tools/worldgen/streetscape/far_field.py --region bialystok-industrial-c`
