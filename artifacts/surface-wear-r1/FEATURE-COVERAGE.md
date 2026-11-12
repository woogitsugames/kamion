# D feature coverage - actual source, pending image tests

All area figures describe source geometry, not visible pixels. The raw inventory checks64 HighGLB SHA; separate verify.py checks all192 rawGLB/instance pins. Primitive src IDs are not retained in GLB, so connectivity/proximity alone cannot attribute a stain to a generator.

| Required feature | Current actual source | Candidate / remaining proof |
|---|---|---|
| Road repair patches |312 connected decal_patch footprints, largest27.38m2;1613.442m2 native total; WorldPBR patch material+existing atlas | Target real broad rectangular footprints near Putry references191135/178375. Verify edge/tone and age variation in Low/High; generic d_wear_patch_putry is NOT proof. No new global asphalt tint. |
| Truck wheel polish/ruts | ROADWEAR road UV lane field, existing _WheelPolish.6 old/.25 new | Isolated171 asphalt missing-UV fix first. Broad smoothness increment.12->.18 is inactive WORKING_VALUE; actual matched contrast, wet/dry behavior and new-road negative required. Reflectance-only, no displacement/rut geometry. |
| Longitudinal/network cracks | Existing _CRACKS+maps, gated world detail; Low detail intentionally off | Audit actual long/network mask and surface crop on High, Low grain readability. No added Low sample. Existing source path alone is not visible proof. |
| Oil at queues and bus stops |871 oil footprints /514.561m2; authored junction/gate/parking generators.23 shelter prototypes, nearest oil7.04-92.11m | Junction control must use actual signal plus nearby source footprint. Dedicated bus-stop oil source missing; proximity is not attribution. Reuse same-chunk existing generic oil only if actual stopping-lane field+refs support relocation; otherwise report upstream gap. |
| Worn paint at wheel crossings | White paint4989.216m2; constantUVx.5 area572.831m2 produces wheel-mask0. Age/chips existing | Authored roads/* forbidden. Robust existing-road UV transfer at importer is an investigation, not implemented. Must reject ambiguous multilane/height fields and preserve geometry+UV0+age.12% longitudinal tweak alone does not solve authored glyphs. |
| Tyre marks at gates |799 tyre footprints /5189.475m2 including docks/yard; gate-kit reports152 scuff tris and kerb noses | Isolate real gate component relative gatehouse[642.08,-572.13], not biggest dock track. Current d_wear_gate_tracks lacks readable tread proof. Need near footprint control and preserved gate/dock negatives. |

References are qualitative exposure/weather-dependent appearance, not measured absolute albedo. The4-source photograph set demonstrates repair boundaries/marking wear, not justification to add global dirt or copy photo pixels into runtime maps. No feature is declared visually complete from this inventory.

Broad shader3-block patch remains INACTIVE. UV sentinel correction is a separate causal experiment with immutable372-frame foundation.
