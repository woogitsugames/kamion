# ADR 0099: Road surface wear from existing lane data and small source-backed decals

Date: 2026-11-11. Status: implementation and visual review in progress; no final quality acceptance.

## Context

S10 stream D asks for repair patches, wheel-path polish, cracks, queued-vehicle oil, paint wear and gate tyre marks. Road generators/geometry and overrides belong to another owner. The implementation therefore changes editor masks, material rules and small marking-layer decals. It preserves existing road positions, normals, indices and UV0, the asphalt albedo decision in ADR0080, existing `_Tile` selection, weather/runoff, macro, panel and splash contracts.

The real baseline was rebuilt and canonically imported before changes, including truck/trailer builders and installation. It contains93 distinct views in each Low/High x clear/overcast condition:372 PNGs. The current work uses Medium world material textures with Low/High geometry profiles. The unavailable orthographic Putry request was replaced by the full current perspective scope; no prior vehicle/architectural controls were silently omitted. Original192 raw files and canonical Unity scenes/assets have private byte copies and SHA packets in `artifacts/surface-wear-r1`.

## Decisions implemented

1. Missing asphalt UV1 uses the established no-lane sentinel(-1,5), never valid lane/edge zero. Apply this only to missing `road_asphalt`/`road_asphalt_new` primitives. Preserve valid zero and non-asphalt defaults. Actual native meshes already allocated UV1, so the additional channel allocation is0bytes; the earlier36124-byte forecast was superseded by the native audit. The affected source data is171 asphalt vertices in two chunks per tier.
2. Transfer an existing asphalt lane field to an entire disconnected constant-half paint component only when vertices, edge midpoints and triangle centroids are supported and continuous. Coplanar null/sentinel road triangles are blockers, not invisible holes. Reject height/overlap/lane-wrap ambiguity and nonlinearity; never extrapolate a lane across an unknown junction. Exact coincident position+age vertices participate in grouping metadata without welding geometry. Existing varying paint fields remain untouched. The final conservative result is11 accepted/507 rejected components,356 changed vertices and58.319m2 per tier, not all572.831m2 of constant-half paint. The accepted large controls are hatching; this is not an authored-P8 coverage claim.
3. Retain explicit `public_transport=stop_position` and bus identity in the reproducible source extractor. The pinned original PBF contains20 on-road bus stops omitted by the old selector. Only source node2367445386/ref464 has the reviewed bay context used here: existing Mapillary1170695487387705. The photograph verifies a paved stopping zone, not a measured oil leak. A single radius.22m oil rule at the actual node, with no engine offset, is WORKING_VALUE. Reject all19 unreviewed stops. Require the whole footprint on one actual asphalt level, no paint overlap and an existing same-chunk oil group. Reuse the existing nine-triangle stain/atlas and drape each vertex at road+3.5mm.
4. At the actual gate barrier line, retain152 kerb-scuff triangles and add two modest paired approach-strip cases from the gate builder's real chain/station/travel. Gatehouse proximity is not a gate-entry criterion. Spacing1.6m, width.20m, length4.2m, strength.9, lift5mm and clearance.15m are WORKING_VALUE, not measured tyre traces. Require exact plan coverage, supported heights, island/kerb/paint clearance, one chunk and an existing tyre group; reject the entire pair if either strip fails. Both real cases pass the source preflight and canonical build:64triangles/72vertices per tier, zero new source material groups. They remain unimported/unreviewed visually at this checkpoint.

No road source file, override, road geometry, building set, truck source, global exposure or project setting is changed by these decisions. Reference photographs are never runtime textures.

## Paint readability experiment still pending

The existing `.85` paint wheel-wear term severs an actual P8 turning arrow. A material-only wearOFF control reconnects its arm/head, excluding a geometry gap. One `.425` diagnostic improves it but leaves a dark head band and cleans the P10 control noticeably; it has not been adopted. ROOT authorized the next isolated test: hold `.425` and narrow only the paint wheel denominator`.13 -> .085`, preserving centres`.26/.74`, age and dirt. The nominal full width becomes.595m at a3.5m lane instead of.91m. This is a WORKING_VALUE contact-band adjustment, with no P8-only encoding, new sample or batch. The diagnostic shader is an ignored editor asset assigned only to transient clones with finally restoration and original-material SHA verification.

The separate three-block polish/gutter/longitudinal-wear patch also remains inactive. Neither it nor three small scalar changes alone constitutes completion of the broader wear task.

## Evidence and limits

- `lane-final-native-proof.json`:154 native road/marking meshes preserve positions/normals/indices/UV0;150 actual UV1.y hashes match original semantic data through Unity Half conversion, four channels absent. Paint age stays exact.
- `bus-world-proof.json`:190/192 raw files byte-identical; only4_5 High/Low add10vertices/9triangles, with all old ordered primitives/material definitions/node transforms intact. Actual nested Fab status is15 ready assets and320 props, without fallback.
- `gate-world-proof.json`: relative to bus-only, only6_6 High/Low change; old tyre data matches after removing the72-vertex/64-triangle insertion and rebasing indices. Bus4_5 and all64 instance files remain byte-identical. All2441 cached bus-only Unity files remain unchanged during CPU generation.
- Focused editor tests14/14 pass. Bus/gate source tests16/16 pass. Full GIS passes386 tests with1 expected failure; all192raw and2441cached hashes stay unchanged afterward. Final EditMode, complete matched AFTER matrices and independent visual acceptance are still required.
- Existing patches/cracks are inventoried and photographed in actual controls; their presence alone is not a visual quality claim. Low keeps its existing detail gate and adds no texture fetch.
- Source material-group deltas are0. Added source triangles are exactly9bus+64gate per tier. Captured counter values are pre-SRP estimates with rounded triangle counts, not measured phone GPU cost. Runtime cost remains UNVERIFIED until appropriate evidence exists.
- Preserved scenes match current serialized actor roots and all40 native camera matrices/FOVs. Prefabs match all553truck/253trailer semantic records after local-fileID normalization. A scoped runtime recorder captured the two bus High-overcast camera/actor poses successfully; this does not retroactively prove372 pixel-identical frames.

## Integration

Expected additive conflicts: `RegionImporter.cs` with E's hero-only material hook; `WorldPBR.shader` with C atmosphere/G car-paint work if a paint/polish candidate is finally selected; shared streetscape source/report changes with future generation. Preserve both owners' paths and canonically regenerate tracked manifests. Diagnostic shaders/editor recorders and private raw/cached copies are artifacts, not shipping assets. No main merge/push or phone/ADB action belongs to this stream.
