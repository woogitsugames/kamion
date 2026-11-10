# ADR 0084 — Optional reviewed Fab Megascans world details

Status: implemented on `gpt-megascans`, validation in progress; **not cleared for merge**.

## Context

D45 permits the owner's Fab Standard assets in the compiled game, but prohibits
publishing source or derivative assets in this public repository. Sources are
pinned in `Data/SourceManifests/fab-megascans-2026-11-10.json`. This ADR does not
change project settings, packages, shared scenes, phone policy or the licence.

## Decision

- Offline `tools/worldgen/fab/prepare.py` verifies source SHA256, safe archive
  members and a separately pinned visual approval in `fab/review.json`. Blender
  imports the selected highest source meshes, bakes transforms and produces our
  own decimated LOD0/1/2. Every result, intermediate and provenance file stays in
  ignored `art-source/world/megascans/_generated/`. No downloads or account access.
- Low/Medium consume 512 px maps; High consumes 1024 px. Per-prototype initial
  caps are2400/800/200 triangles (props),8000/16/4 (shrubs) and4000/16/4 (grass), WORKING_VALUE. Near plants retain optimized true geometry; far LODs use silhouette billboards with their own source atlas.
  Actual counts and source dimensions are recorded in the local output manifest.
  Aggressive collapse and leaf removal failed visual review and are not used for active plant variants. Judge silhouettes and coverage in visual QA before accepting them.
- `fab_tree_surfaces.py` crops clean atlas regions into bark_birch, bark_linden
  and curb_concrete. It keeps our trees and Polish kerb geometry. Bark UV scale,
  colour calibration, cropping and source mixing are WORKING_VALUE, not surveyed.
- `FabMaterials` imports albedo, metallic/smoothness and AO into the ignored
  Unity region output, ASTC with mipmaps and streaming-compatible non-readable
  textures. Normals are prepared but deliberately disabled: compact world meshes
  have no tangent attribute and source normal convention is UNVERIFIED.
- `streetscape/fab_details.py` replaces existing 35 m gully materials, adds
  lane-centred 640 mm covers at 90 m spacing, and bounded props by existing
  shelters/gates/parking or on soft verges. These placements/dimensions are
  WORKING_VALUE, not mapped utility positions. No extra road collider obstacles.
  Props use 12/30/65 m LOD/cull distances and a regional 320-instance cap.
  Authored islands require an explicit `fab_plants` list; existing references
  are not replaced by generic shrubs. Scene budgets include measured Fab LODs.
- Public clones retain existing geometry/materials and log a warning. Set
  `KAMION_DISABLE_FAB=1` for a controlled before run even with local products.
  Processing commands are explicit, so missing licensed files do not trigger
  downloads or network/authentication work.
- Reject scans with visible marks: round-manhole-cover (emblem/lettering),
  trash-can (yellow emblem), urban-trash (marked bins/printed packaging).
  pine-bark is a mulch/debris atlas, not pine trunk bark. Linden Branch contains
  wood, not leaves. Existing pine bark and leaves remain; these requirements
  cannot honestly be claimed as replaced by the supplied scans.
- Three local source ZIPs differed from acquisition hashes. CRC and embedded
  Quixel identity were checked; observed pins replace the active pins, while
  original acquisition hashes/byte counts remain in the source manifest. Cause
  of the discrepancy remains UNVERIFIED, not an invented acquisition history.

## Validation and limits

`artifacts/megascans-r1/STATUS.md` is the incremental log; `REPORT.md` contains
final test results, camera comparisons and measured budget changes. Visual QA
and independent critic PASS are required before merge. No phone numbers are
claimed: this task forbids phones/adb. Do not infer Android performance from
editor scene estimates. Fab EULA legal review before store release remains as
already recorded in `docs/LICENSES.md`.

Expected integration conflicts: build_world.py, streetscape stage/materials,
plantings/life_props changes by other world agents and Unity instance/material
import. Regenerate licensed outputs locally after integration; never merge them.
