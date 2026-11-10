# ADR 0039: truck wheel LODs reduced by lathe column/ring, not by edge collapse

Status: accepted (re-exported) · 2026-11-10 · rendering-perf

## Context
REVIEW r5 R-W1 (P0): tractor wheels are shredded on A16 Low in 4/4 exterior frames of build `40ae9c5`; S24+ High
(`9d46b38`) is fine. Low shows only exterior LOD2 (`TruckVisualRig`), High LOD0-1, so the bug is in LOD2 only.

Bisect (manifest `tyre_outer_radius_m` / `width_m` of the LOD2 wheels, LOD0 = 0.5378 m):

| export | commit | LOD2 FL tris | r (m) | width FL / FR |
|---|---|---|---|---|
| A6 r4 | 775d28f | 691 | 0.551 | 0.320 / 0.320 |
| B2 v2 | 062273f | 288 | 0.554 | 0.323 / 0.322 |
| **B2.1** | **bd9047a** (generator aba4c28) | **170** | **0.638** | **0.287 / 0.357** |

The commits between `9d46b38` and `40ae9c5` are world-only and innocent. The truck B2.1 re-export `bd9047a` is
already in `9d46b38`, but S24+ never selects LOD2. The A16 "faceted but whole" frames come from the earlier A8
build, which still had B2 v2. B2.1 added LOD0 detail (exhaust stack, lamps) at an unchanged LOD2 target of 14.5 k.
The area-weighted collapse budget (`decimate_pieces`) then cut the tyres to about 3 % of their triangles. At that
ratio the quadric collapse moves vertices off the torus. The result is radius +19 %, asymmetric widths, spikes and
flipped triangles. Mesh compression, shader stripping and the lean APK were not involved: the 40ae9c5 APK predates
d1357f9/f524390.

## Decision
- In `tools/blender/truck/exterior/a6_export.py`, the tyre and rim lathes at LOD2+ (`ROUND_SEGMENTS`) are kept
  out of the collapse. `reduce_round` keeps every k-th radial column (at least 16 segments around, 24 by default)
  and runs Douglas-Peucker on the meridian. Rings and columns are dissolved, so the kept vertices and their UVs
  are exactly LOD0's.
- `check_export.py` fails an export when a wheel's radius differs from LOD0 by more than 2 % or its width is
  outside 75-105 % of LOD0. The lower bound is 75 % because LOD2 drops the hub and nuts by design.
- The EditMode test `TruckWheelLodGeometryTests` imports every LOD of each tier with the vehicle importer
  settings and checks each wheel: radius, width, at least 16 segments, at least 96 vertices, unit and outward
  normals, and no degenerate or flipped triangles.

## Status (2026-11-10, re-export done)
- The first `reduce_round` dissolved vertices (`bmesh.ops.dissolve_verts`). bmesh merged whole bands into n-gons:
  the front tyres came out as 134 triangles of garbage and the inner rear tyres were not reduced at all (1087).
  To still hit 14.5 k, `lights_min` had been lowered to 0.15, which crushed the lower fairing (black triangles from
  the bumper corner to the arch) and left every other piece at its floor (k = 0).
- Now the piece is rebuilt on the generator grid: every vertex gets (column, ring) from its angle and from the
  generator meridian (`chassis.tyre_profile`, `RIM_PROF + RIM_INNER`), kept columns x Douglas-Peucker rings
  (tyre tolerance 20 mm: tread grooves live in the normal map; rim 4 mm) become new quads on LOD0 vertices with
  LOD0 loop data. A coarse cell exists when any LOD0 cell under it survived hidden-face removal; blocks with a
  culled corner keep their LOD0 cells.
- Budget: `TRI_TARGET[2]` 14 500 -> 15 300 (limit stays 15 500); `MIN_RATIO = {"lower_fairing": 0.3}`.
  Result: LOD0 101 195, LOD1 43 000, LOD2 15 300 (k 40.9, off the floor). Tyres 288-342 tris at 24 segments,
  rims 388-480 at 20-24 segments. `check_export` PASS (radius, width, budgets).
- Open: the rims keep all their rings (candidates for another ~600 tris); trailer exporter (T-2) needs the same rule.

## Consequences
- LOD2 wheels cost more than the shredded 170 tris (expected about 600-800 per axle side). They cost less than
  LOD1 and are always round.
- The same rule should go into the trailer exporter (T-2, trailer wheels faceted on Low).
