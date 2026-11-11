DRAFT: Final visual and CI validation remains pending. There is no overall quality PASS.
Branch: gpt-surface-wear. Validated native candidate: f6cc56ca. Base: 901c427f. No merge or push to main.
Fresh canonical baseline: 93 views in four conditions, 372 PNGs; Low/High scenes use Medium world textures.
UV correction: 171 asphalt vertices receive the missing-data sentinel; no extra channel allocation or other defaults change.
Lane transfer: 11 accepted and 507 rejected components; 356 vertices and 58.319 square metres per tier; paint age and geometry stay exact.
Bus stop: one reviewed stop, ref 464, from 20 raw positions; radius 0.22 m is a working value; nine triangles added per tier.
Gate version 1 failed visibility. Version 2 has 16 fresh frames; overcast mean strip darkening is 1.4-4.2 RGB levels. ROOT review is pending.
Gate version 2 reserves negative physical length for 0.65/0.90 m end fades; strength stays 0.9 and legacy data remains exact.
Paint calibration: ROOT retained width 0.085 and fresh nominal wear times 0.5; native uniform is [0.425, 0.25, 0.38, 0.12]. A second import matches exactly.
Raw data: four files differ from pristine; all 64 instance files and road geometry stay exact. Fab has 15 ready assets and 320 props, without fallback.
Tests: final signed-mode GIS passed 388 tests with one expected failure; XML and post-suite cache hashes verified. Editor: 14 passed; full run pending.
Budget: 73 source triangles added per tier, no new material groups; rounded bus/gate counters are unchanged. GPU cost is unverified.
Images: artifacts/surface-wear-r1/{before,before-legacy,bus-only-after,paint-narrow,gate-pair-after}.
Gate frames have matching recorded camera and vehicle poses. Older kerb controls lack historical runtime packets; no retroactive pixel-stability claim.
Pending: ROOT gate review, broader wear probe and selection, 372 final frames, independent review and full editor tests.
Existing Mapillary photographs guide appearance; the bay photograph verifies the zone, not a measured oil leak or tyre dimensions.
Expected additive conflicts: RegionImporter with E, WorldPBR with C/G, material importer with A. Preserve all shared contracts.
The D-only release completed its 16-frame packet. No Unity is active or queued; broader wear awaits ROOT review.
