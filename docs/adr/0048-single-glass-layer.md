# ADR 0048 - One glass layer per tier: body glass faces that duplicate the glazing are stripped, lamp lenses stay

Status: accepted (2026-11-10)

## Context
ADR 0045 moved the glazing into the GLASS_* LOD group. The exterior body meshes (CAB_Body_LODn, CHASSIS_LODn) still carried
MI_Ext_Glass faces, so on Low (LOD2 body) a second glass layer drew together with GLASS_*_LOD0. The same slot also holds the
clear lamp lens covers (a6_export `slot_of`: `lens_clear`, except rear lenses), which must stay (Fresnel / reflection).

## Decision
`TruckAssetBuilder.StripGlassSubmeshes`: at prefab build, for non-GLASS_ renderers with a MI_Ext_Glass slot, only triangles whose
world-space centroid lies inside a GLASS_* renderer's bounds (+2 cm) are removed (`*_NoGlass.asset`); an emptied submesh is dropped
with its slot from `TruckVisualRig.slots`. Escape hatch: `-keepBodyGlass 1`.
Test: `TruckCabGlassTierTests.Prefab_SingleGlassLayer_OnEveryTier` (no body glass face inside the glazing bounds; lens faces remain).

## Evidence (editor probe on the TRAKT prefab; phone UNVERIFIED)
No MI_Ext_Glass triangle of CAB_Body_LOD0-2 / CHASSIS_LOD0-2 (1912/956/284 and 128/79/31 tris) has its centroid inside the GLASS_*
bounds: the body glass slot holds lamp lenses only, so with the restricted rule the strip is a no-op on the current export (guard
against a re-export that bakes glazing into the body) and the draws/triangles are unchanged (346/224 draws, 305k/273k tris).
The earlier "strip whole slot" variant saved 2 draws per camera but removed lamp lenses (rejected). The double glass seen on Low is
therefore not baked body glass; cause still open.

## Addendum r6 (2026-11-10): exterior transmission, glass p50 ceiling, double-glass check (review r6 E2)
- **Exterior transmission.** From outside, the eye looks through the pane into a cab that our interior leaves nearly
  empty and out again through the far door glass (the "aquarium"). `_ExteriorTransmission` 0.42 (~0.7 surviving the second
  pane and interior clutter x cab occlusion ~0.6, WORKING_VALUE) scales the transmitted scene on outside faces in the cab
  glazing band (1.6-3.2 m above the road, so lamp lenses on the same material keep their reflectors). Driver view
  unchanged. Outside reflection on Low/Medium uses `KamionVehicleEnv` (ADR 0038 addendum r6).
- **p50 >= 60 % is not reachable physically.** Windscreen region 380-460 x 160-200 (truck-34 1024 px), High overcast:
  transmission 1 (HEAD) 42.1 %, 0.42 40.8 %, **0 (reflection + road film only) 37.4 %**. The region is dominated by the
  reflection: rake 19 deg, view 42 deg, two-interface F ~0.08 of a sky at ~33 deg elevation. Darkening the interior can
  only lower p50; 60 % would need ~2.5x the Fresnel reflection. Low 39.2 -> 38.4 %. Proposed acceptance instead: glass
  p50 within the reflection-only value +5 pts (here 37-42 %) and no see-through to the far window (visual).
- **Double glass on Low (HANDOVER suspicion).** Prefab: root LODGroup holds no GLASS_* renderer (parsed
  `Tractor4x2_TRAKT.prefab`; `TruckCabGlassTierTests` green). But the generated **WorldC scene** (built 2026-11-09, before
  ADR 0045) carries prefab-instance overrides of the root LODGroup (`m_LODs` 3 levels, 19/19/17 renderers, target fileID
  8360966181319444439) that still list the glazing: every WorldC load logs "Renderer 'GLASS_Windscreen_LOD0' (and
  DoorL/DoorR, LOD0 and LOD2) is registered with more than one LODGroup ('Tractor4x2_TRAKT' and 'CabGlassLOD')".
  `TruckVisualRig.Apply` (OnEnable, ExecuteAlways) rewrites both groups, so after the first Apply each pane belongs to
  CabGlassLOD only; but any path that skips Apply (rig disabled, scene opened without play/QA) draws the stale chain
  with LOD0 and LOD2 glass at once. Fix (lead / world import): regenerate WorldC from the current prefab, or revert the
  LODGroup and `m_Enabled` overrides of the TRAKT instance in the scene builder.