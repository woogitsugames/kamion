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
