# ADR 0104 — Cab r1: interior audit and mirror presentation

Status: implemented; editor validation, independent review and device gate are distinct. Stream K only, base main `9e6e9fde`.

## Problem

Gate 3 requires a final cab fragment and usable mirrors. The current TRAKT export had two concrete mirror defects:
- the glass UV basis already presents the reflected-eye camera as a mirror, but the runtime material flipped it again;
  the own vehicle appeared at the outer edge of both main mirrors;
- the detailed aero housing was a solid rounded box. Adjusting its glass embedded part of the wide-angle quad in the
  backing. In a 315-point grid per glass, High WideL/WideR were only 84.1% / 74.9% visible from the design eye.

Correction (ADR 0112, 2026-11-11): the source ray audit established visibility of the glass only, not correct reflected
content. Independent review K1 found seats and other interior geometry in the front/kerb RTs, even though road pixels
were also present. The former claim that these views were correct is withdrawn. The interior instrument/head-box
sightline test passes; it is a separate check.

## Decisions

1. `RenderTextureMirror.flipHorizontally` retains the legacy graybox default. The TRAKT builder sets it false: its
   exported glass UVs and reflected-eye camera already implement the reflection. HUD insets retain their own flip of
   the raw texture; their screen UVs differ from the physical glass UVs. Camera poses, FOV/aspect and captures stay fixed.
   `MirrorPresentationTests` projects a trailer-side point through camera, texture transform and actual glass UVs,
   asserting the own vehicle appears at the inner edge (right in left mirror, left in right mirror).
2. `MirrorHousingRecess` recesses existing inner-backing vertices, with 30 mm depth and 6 mm clearance (WORKING_VALUE).
   Outer bezel and rear cap stay. Only affected normals/tangents are updated. Topology, material slots, UVs, colours and
   bounds stay fixed. The builder applies it to **CAB_Body LOD0 only**. Unity measured 107 moved vertices, with identical
   28500 vertices / 110904 indices. Low/Medium exterior meshes remain original.
3. Add inactive `cab-seat`, `cab-materials`, `cab-seat-entry`, `cab-grain` inspection cameras. Original driver-eye
   cameras remain the driving-legibility gate. The first two are in the matched matrix; entry/grain are separate
   inspection evidence for existing, unchanged interior materials, seams and wear.
4. Keep ADR 0068's RT dimensions, far clips, LOD scales, optics and shared schedules. Low main RT 100x224, High
   171x384; hard caps 1 / 2 renders per frame. High due schedule: main every 2 frames, convex every 4 while driving;
   actual phone refresh Hz is UNVERIFIED. Low weighted cadence depends on visible mirrors, not the diagnostic interval column.

## Evidence and budgets

`artifacts/cab-r1/`: `before/` and `after/` each have 9 cameras x Low/High x overcast/clear (72 PNG total), with six
native mirror RTs per configuration. `after-details/` adds entry/grain inspection. `review/` holds <=960px previews
and matched pairs; `image-metrics.json` and `budget-comparison.json` are reproducible with the adjacent Python tools.
All 36 matched scene-stat rows have **zero delta** for regular/instanced draws, shadows and triangles; all four
mirror configuration data tables are identical. These are CPU visibility estimates before SRP batching, not GPU counters.
Example cab-dash: Low 423+433 draws / 318+30 k triangles; High 781+687 / 1331+74 k (regular+instanced; rounded k).

The full adjusted source-geometry study after recess gives High WideL 97.5%, WideR 88.3%, MainR 99.7%; MainL,
Kerb and Front remain 100%. Low original WideL/WideR are already 97.5%/89.5%, justifying the LOD0-only fix.
These percentages come from Blender rays, including opaque exterior and interior; they are not pixel measurements,
transparency/attenuation tests or certification of the reflected R46 field. Clay/magenta ablations and game PNGs
were inspected. Residual right wide obstruction includes the door/window channel.

GIS: 370 passed / 1 xfailed (643.87 s). Export round-trip: PASS, interior 103285 / 44190 / 21479 tris.
Full EditMode: 230/230 (including presentation, housing invariants and existing R46/budget tests).
BuildBatch + InstallBatch succeeded. Unity batch compilation uses Android target; no new APK or device run by K.
Cab-dash dark<3% pixels after: Low clear/overcast 1.393%/2.191%, High 1.468%/2.790%.

## Limits and handoff

Independent visual review and clean A16/S24+ device verification remain for the leader; no Gate 3 PASS is claimed.
The leader's saved dirty `43bc53a769` A16 frames are auxiliary only (cabView=True; dash dark 2.406% overcast,
4.515% dusk). Existing Scania S730 photo is layout reference only, CC BY-SA 3.0, Herranderssvensson (REFERENCES.md).
No new third-party asset or licence is introduced. Grain/roughness remain authored WORKING_VALUEs, not calibrated
against owner cab photos. Do not infer phone text readability or GPU timing solely from enlarged editor inspection.

No TruckExterior.shader, glazing, TruckLights.cs, world materials, ProjectSettings or Packages edits. Expected merge
conflicts: additive TruckAssetBuilder.cs and RenderTextureMirror.cs changes; regenerate truck prefab and world scenes.
