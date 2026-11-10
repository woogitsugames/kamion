# ADR 0046 - One glass layer per tier: body meshes lose the baked MI_Ext_Glass submesh

Status: accepted (2026-11-10)

## Context
ADR 0045 moved the glazing into the GLASS_* LOD group. The exterior body meshes (CAB_Body_LODn, CHASSIS_LODn) still carried a
MI_Ext_Glass submesh, so on Low (LOD2 body) a second glass layer drew together with GLASS_*_LOD0.

## Decision
`TruckAssetBuilder.StripGlassSubmeshes`: at prefab build, non-GLASS_ renderers with a MI_Ext_Glass slot get a copy of the mesh without
that submesh (`*_NoGlass.asset`) and the slot is dropped from `TruckVisualRig.slots`. Escape hatch: `-keepBodyGlass 1`.
Test: `TruckCabGlassTierTests.Prefab_SingleGlassLayer_OnEveryTier`.

## Evidence (editor, Low overcast WorldC, RTX 5070; phone UNVERIFIED)
cab-dash drawsEst 346 -> 344, shadow 120 -> 118, 305k -> 304k tris; truck-34 224 -> 222, shadow 141 -> 139, 273k -> 272k.
Editor frame time is within noise (2-3 ms). Renders: artifacts/owner/aquarium/glass-dedup/{before,after}.
